# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Flask test app and client fixtures."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_REAL_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def flask_app(temp_data_dir, monkeypatch):
    """Create a Flask test app with mocked heavy dependencies.

    Monkeypatches config.paths to use temp directories for data but
    keeps real templates/static so Flask can render pages.
    """
    import config as cfg

    # Build a mock PathManager: temp dirs for data, real dirs for templates/static
    mock_paths = MagicMock()
    mock_paths.project_root = temp_data_dir
    mock_paths.src_dir = temp_data_dir / "src"
    mock_paths.data_dir = temp_data_dir / "data"
    mock_paths.json_dir = temp_data_dir / "json"
    mock_paths.docs_root = temp_data_dir / "docs"
    mock_paths.faiss_root = temp_data_dir / "faiss"
    mock_paths.templates_dir = _REAL_PROJECT_ROOT / "templates"
    mock_paths.static_dir = _REAL_PROJECT_ROOT / "static"
    mock_paths.chats_file = temp_data_dir / "json" / "all_chats.json"

    # Ensure the chats file exists
    mock_paths.chats_file.parent.mkdir(parents=True, exist_ok=True)
    if not mock_paths.chats_file.exists():
        mock_paths.chats_file.write_text('{"chats": []}')

    monkeypatch.setattr(cfg, "paths", mock_paths)

    # Mock HuggingFaceEmbeddings to avoid downloading the model
    mock_embeddings = MagicMock()
    mock_embeddings.embed_query.return_value = [0.0] * 384
    mock_embeddings.embed_documents.return_value = [[0.0] * 384]

    with patch("src.app.HuggingFaceEmbeddings", return_value=mock_embeddings), \
         patch("src.services.faiss_service.HuggingFaceEmbeddings", return_value=mock_embeddings):

        # Mock FAISSService to avoid loading real indices
        mock_faiss_svc = MagicMock()
        mock_faiss_svc.get_available_indices.return_value = {
            "misc": {"name": "Miscellaneous", "path": str(temp_data_dir / "faiss" / "misc")},
            "phys": {"name": "Physical", "path": str(temp_data_dir / "faiss" / "phys")},
        }
        mock_faiss_svc.load_default_index.return_value = MagicMock()

        with patch("src.app.FAISSService", return_value=mock_faiss_svc):
            from src.app import DocumentQAApp

            qa_app = DocumentQAApp()
            qa_app.app.config["TESTING"] = True

            # Store mock vector store so routes can use it
            mock_vs = MagicMock()
            mock_vs.similarity_search.return_value = []
            mock_vs.similarity_search_with_score.return_value = []
            qa_app.vector_stores["misc"] = mock_vs

            yield qa_app


@pytest.fixture
def client(flask_app):
    """Flask test client."""
    return flask_app.app.test_client()


@pytest.fixture
def mock_llm_responses(monkeypatch):
    """Patch all three model handlers to return canned responses."""
    from data import (
        SAMPLE_LLM_RESPONSE_ANTHROPIC,
        SAMPLE_LLM_RESPONSE_LOCAL,
        SAMPLE_LLM_RESPONSE_PERPLEXITY,
    )

    mock_response = MagicMock()
    mock_response.status_code = 200

    def _make_json_side_effect(data):
        def _json():
            return data
        return _json

    def _mock_post(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if "anthropic" in url:
            resp.json = _make_json_side_effect(SAMPLE_LLM_RESPONSE_ANTHROPIC)
        elif "perplexity" in url:
            resp.json = _make_json_side_effect(SAMPLE_LLM_RESPONSE_PERPLEXITY)
        else:
            resp.json = _make_json_side_effect(SAMPLE_LLM_RESPONSE_LOCAL)
        return resp

    monkeypatch.setattr("requests.post", _mock_post)
