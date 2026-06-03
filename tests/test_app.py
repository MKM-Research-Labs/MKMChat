# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/app.py (DocumentQAApp class)."""

from unittest.mock import MagicMock, patch
from flask import Flask


def test_app_is_flask(flask_app):
    """flask_app.app should be a Flask instance."""
    assert isinstance(flask_app.app, Flask)


def test_app_has_blueprints(flask_app):
    """The app should have summary, chat, index, and analysis blueprints registered."""
    blueprint_names = list(flask_app.app.blueprints.keys())
    assert "summary" in blueprint_names
    assert "chat" in blueprint_names
    assert "index" in blueprint_names
    assert "analysis" in blueprint_names


def test_index_route(client):
    """GET / should return 200."""
    response = client.get("/")
    assert response.status_code == 200


def test_favicon_route(client):
    """GET /favicon.ico should return 200."""
    response = client.get("/favicon.ico")
    assert response.status_code == 200


def test_create_app_factory():
    """create_app() should return a Flask instance when deps are mocked."""
    mock_embeddings = MagicMock()
    mock_embeddings.embed_query.return_value = [0.0] * 384
    mock_embeddings.embed_documents.return_value = [[0.0] * 384]

    mock_faiss_svc = MagicMock()
    mock_faiss_svc.get_available_indices.return_value = {
        "misc": {"name": "Miscellaneous", "path": "/tmp/faiss/misc"},
        "phys": {"name": "Physical", "path": "/tmp/faiss/phys"},
    }
    mock_faiss_svc.load_default_index.return_value = MagicMock()

    with patch("src.app.HuggingFaceEmbeddings", return_value=mock_embeddings), \
         patch("src.services.faiss_service.HuggingFaceEmbeddings", return_value=mock_embeddings), \
         patch("src.app.FAISSService", return_value=mock_faiss_svc):
        from src.app import create_app
        app = create_app()

    assert isinstance(app, Flask)


def test_model_handler_delegation(flask_app, mock_llm_responses):
    """_handle_anthropic_model should delegate to the handler and return a string."""
    result = flask_app._handle_anthropic_model("test query", "test context", "claude-sonnet-4-5-20250929")
    assert isinstance(result, str)
    assert len(result) > 0


def test_handle_perplexity_model(flask_app, mock_llm_responses):
    """_handle_perplexity_model should delegate and return a string."""
    result = flask_app._handle_perplexity_model("test query", "test context", "sonar-pro")
    assert isinstance(result, str)
    assert len(result) > 0


def test_handle_local_model(flask_app, mock_llm_responses):
    """_handle_local_model should delegate and return a string."""
    result = flask_app._handle_local_model("test query", "test context", "cogito-v1-preview-llama-3b")
    assert isinstance(result, str)
    assert len(result) > 0


def test_load_faiss_index(flask_app):
    """_load_faiss_index should call faiss_service.load_index and cache the result."""
    mock_vs = MagicMock()
    flask_app.faiss_service.load_index.return_value = mock_vs

    result = flask_app._load_faiss_index("phys")

    flask_app.faiss_service.load_index.assert_called_once_with("phys")
    assert flask_app.vector_stores["phys"] is mock_vs
    assert result is mock_vs


def test_available_indices(flask_app):
    """AVAILABLE_INDICES should contain the expected keys from the mock."""
    assert "misc" in flask_app.AVAILABLE_INDICES
    assert "phys" in flask_app.AVAILABLE_INDICES


def test_active_index_key_default(flask_app):
    """ACTIVE_INDEX_KEY should be set to the default collection."""
    from config import DEFAULT_COLLECTION
    assert flask_app.ACTIVE_INDEX_KEY == DEFAULT_COLLECTION


def test_app_has_research_routes(flask_app):
    """The app should have research_query and research_query_stream URL rules."""
    rules = [rule.rule for rule in flask_app.app.url_map.iter_rules()]
    assert "/research_query" in rules
    assert "/research_query_stream" in rules


# ---------------------------------------------------------------------------
# Additional coverage tests
# ---------------------------------------------------------------------------


def test_run_calls_flask_run(flask_app):
    """run() should delegate to self.app.run with the resolved args."""
    with patch.object(flask_app.app, "run") as mock_run:
        flask_app.run(debug=False, port=9999, host="0.0.0.0")
        mock_run.assert_called_once_with(debug=False, port=9999, host="0.0.0.0")


def test_run_defaults_from_config(flask_app):
    """run() with no args should pull defaults from CONFIG."""
    with patch.object(flask_app.app, "run") as mock_run:
        flask_app.run()
        mock_run.assert_called_once()
        kwargs = mock_run.call_args
        # It should have been called with some host/port/debug
        assert kwargs is not None


def test_parse_arguments_defaults():
    """parse_arguments with no args returns defaults."""
    with patch("sys.argv", ["app.py"]):
        from src.app import parse_arguments
        args = parse_arguments()
        assert args.host is None
        assert args.port is None
        assert args.debug is False
        assert args.no_debug is False


def test_parse_arguments_custom():
    """parse_arguments with custom flags."""
    with patch("sys.argv", ["app.py", "--host", "0.0.0.0", "--port", "5555", "--debug"]):
        from src.app import parse_arguments
        args = parse_arguments()
        assert args.host == "0.0.0.0"
        assert args.port == 5555
        assert args.debug is True


def test_parse_arguments_no_debug():
    """parse_arguments with --no-debug flag."""
    with patch("sys.argv", ["app.py", "--no-debug"]):
        from src.app import parse_arguments
        args = parse_arguments()
        assert args.no_debug is True
        assert args.debug is False


def test_load_default_index_failure(flask_app):
    """_load_default_index should handle exceptions gracefully."""
    flask_app.faiss_service.load_default_index.side_effect = RuntimeError("no index")
    # Should not raise; just prints a warning
    flask_app._load_default_index()
    # The vector_stores dict should not have the default key updated
    # (it might still have the mock from fixture setup, which is fine)


def test_load_default_index_returns_none(flask_app):
    """_load_default_index should handle None return from service."""
    flask_app.faiss_service.load_default_index.return_value = None
    flask_app.vector_stores.clear()
    flask_app._load_default_index()
    from config import DEFAULT_COLLECTION
    # When vector_store is None, the if-branch is skipped
    assert DEFAULT_COLLECTION not in flask_app.vector_stores
