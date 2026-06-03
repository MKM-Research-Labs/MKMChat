# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/research/kb_query.py (KBQueryExecutor)."""

from unittest.mock import MagicMock, patch


def _make_mock_doc(content="Test content", source="doc.pdf", page=1):
    """Helper to create a mock document with page_content and metadata."""
    doc = MagicMock()
    doc.page_content = content
    doc.metadata = {"source": source, "page": page}
    return doc


def test_query_single_kb():
    """query_single_kb should return a successful KBQueryResult when docs are found."""
    from src.research.kb_query import KBQueryExecutor

    # Set up mock app
    app = MagicMock()
    app.AVAILABLE_INDICES = {
        "misc": {"name": "Miscellaneous", "path": "/tmp/faiss/misc"},
    }

    mock_vs = MagicMock()
    mock_docs = [
        _make_mock_doc("Chunk 1 about floods", "floods.pdf", 1),
        _make_mock_doc("Chunk 2 about risk", "risk.pdf", 3),
    ]
    mock_vs.similarity_search.return_value = mock_docs
    app.vector_stores = {"misc": mock_vs}

    # Mock the model handler to return a valid response
    app._handle_anthropic_model.return_value = "Synthesized answer about floods."

    executor = KBQueryExecutor(app, max_docs_per_kb=5)

    with patch(
        "src.research.kb_query.route_to_model_handler",
        return_value="Synthesized answer about floods.",
    ):
        result = executor.query_single_kb("What is flood risk?", "misc", "claude-sonnet-4-5-20250929")

    assert result.success is True
    assert result.kb_key == "misc"
    assert result.kb_name == "Miscellaneous"
    assert result.doc_count == 2
    assert result.response == "Synthesized answer about floods."
    assert len(result.sources) == 2
    assert result.query_time_ms >= 0


def test_query_with_no_results():
    """query_single_kb should return success with 'no relevant documents' when search is empty."""
    from src.research.kb_query import KBQueryExecutor

    app = MagicMock()
    app.AVAILABLE_INDICES = {
        "misc": {"name": "Miscellaneous", "path": "/tmp/faiss/misc"},
    }

    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = []
    app.vector_stores = {"misc": mock_vs}

    executor = KBQueryExecutor(app, max_docs_per_kb=5)
    result = executor.query_single_kb("Obscure question", "misc", "claude-sonnet-4-5-20250929")

    assert result.success is True
    assert result.doc_count == 0
    assert "no relevant documents" in result.response.lower()


def test_query_kb_not_loaded():
    """query_single_kb should handle an unloaded KB that fails to load."""
    from src.research.kb_query import KBQueryExecutor

    app = MagicMock()
    app.AVAILABLE_INDICES = {
        "misc": {"name": "Miscellaneous", "path": "/tmp/faiss/misc"},
    }
    app.vector_stores = {}  # Not loaded
    app._load_faiss_index.side_effect = RuntimeError("Index file missing")

    executor = KBQueryExecutor(app, max_docs_per_kb=5)
    result = executor.query_single_kb("test", "misc", "claude-sonnet-4-5-20250929")

    assert result.success is False
    assert "Failed to load index" in result.error


def test_query_kb_none_response():
    """query_single_kb handles None response from model (covers line 101, 104-105)."""
    from src.research.kb_query import KBQueryExecutor

    app = MagicMock()
    app.AVAILABLE_INDICES = {"misc": {"name": "Miscellaneous"}}
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = [_make_mock_doc()]
    app.vector_stores = {"misc": mock_vs}

    executor = KBQueryExecutor(app, max_docs_per_kb=5)

    with patch("src.research.kb_query.route_to_model_handler", return_value=None):
        result = executor.query_single_kb("test", "misc", "claude-sonnet-4-5-20250929")

    assert result.success is False
    assert "Invalid response" in result.error


def test_query_kb_non_string_response():
    """query_single_kb handles non-string response from model (covers line 105)."""
    from src.research.kb_query import KBQueryExecutor

    app = MagicMock()
    app.AVAILABLE_INDICES = {"misc": {"name": "Miscellaneous"}}
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = [_make_mock_doc()]
    app.vector_stores = {"misc": mock_vs}

    executor = KBQueryExecutor(app, max_docs_per_kb=5)

    with patch("src.research.kb_query.route_to_model_handler", return_value=42):
        result = executor.query_single_kb("test", "misc", "claude-sonnet-4-5-20250929")

    # The int response hits len() which raises TypeError, caught by the outer except
    assert result.success is False
    assert result.error is not None


def test_query_kb_error_response():
    """query_single_kb handles error string response (covers line 116)."""
    from src.research.kb_query import KBQueryExecutor

    app = MagicMock()
    app.AVAILABLE_INDICES = {"misc": {"name": "Miscellaneous"}}
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = [_make_mock_doc()]
    app.vector_stores = {"misc": mock_vs}

    executor = KBQueryExecutor(app, max_docs_per_kb=5)

    with patch("src.research.kb_query.route_to_model_handler", return_value="Error: something failed"):
        result = executor.query_single_kb("test", "misc", "claude-sonnet-4-5-20250929")

    assert result.success is False
    assert "Error" in result.error


def test_query_kb_exception():
    """query_single_kb handles exception in processing (covers lines 138-141)."""
    from src.research.kb_query import KBQueryExecutor

    app = MagicMock()
    app.AVAILABLE_INDICES = {"misc": {"name": "Miscellaneous"}}
    mock_vs = MagicMock()
    mock_vs.similarity_search.side_effect = RuntimeError("FAISS crashed")
    app.vector_stores = {"misc": mock_vs}

    executor = KBQueryExecutor(app, max_docs_per_kb=5)
    result = executor.query_single_kb("test", "misc", "claude-sonnet-4-5-20250929")

    assert result.success is False
    assert "FAISS crashed" in result.error
