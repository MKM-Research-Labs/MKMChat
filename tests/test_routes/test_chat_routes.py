# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/routes/chat_routes.py (POST /query)."""

import pytest


def test_query_not_json(client):
    """POST with text/plain should return 400."""
    response = client.post(
        "/query",
        data="plain text body",
        content_type="text/plain",
    )
    data = response.get_json()
    assert response.status_code == 400
    assert "error" in data


def test_query_empty(client):
    """POST JSON with empty query should return 400."""
    response = client.post("/query", json={"query": ""})
    data = response.get_json()
    assert response.status_code == 400
    assert "error" in data


def test_query_success(client, mock_llm_responses):
    """POST valid query should return 200 with response/sources/model keys.

    The mock vector_stores["misc"].similarity_search returns [] so context
    will be empty, but the endpoint should still produce a valid response
    via the mocked LLM handler.
    """
    response = client.post(
        "/query",
        json={"query": "What is flood risk?", "model": "claude-sonnet-4-5-20250929"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "response" in data
    assert "sources" in data
    assert "model" in data
    assert data["model"] == "claude-sonnet-4-5-20250929"


def test_query_perplexity_model(client, flask_app, mock_llm_responses):
    """POST with a Perplexity model should route via _handle_perplexity_model."""
    from unittest.mock import MagicMock

    # Provide documents so context is built (covers lines 80-94)
    mock_doc = MagicMock()
    mock_doc.page_content = "Test content about floods"
    mock_doc.metadata = {"source": "floods.pdf", "page": 1}
    flask_app.vector_stores["misc"].similarity_search.return_value = [mock_doc]

    response = client.post(
        "/query",
        json={"query": "What is flood risk?", "model": "sonar-pro"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["model"] == "sonar-pro"
    assert "response" in data
    assert len(data["sources"]) == 1
    assert data["sources"][0]["file"] == "floods.pdf"


def test_query_anthropic_model(client, flask_app, mock_llm_responses):
    """POST with an Anthropic model (claude-sonnet-4.5) should route via _handle_anthropic_model."""
    from unittest.mock import MagicMock

    mock_doc = MagicMock()
    mock_doc.page_content = "Yield curve modelling data"
    mock_doc.metadata = {"source": "yields.pdf", "page": 5}
    flask_app.vector_stores["misc"].similarity_search.return_value = [mock_doc]

    response = client.post(
        "/query",
        json={"query": "Explain yield curves", "model": "claude-sonnet-4.5"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["model"] == "claude-sonnet-4.5"
    assert "response" in data


def test_query_local_model(client, flask_app, mock_llm_responses):
    """POST with a model not matching perplexity/anthropic should route to local handler."""
    from unittest.mock import MagicMock

    mock_doc = MagicMock()
    mock_doc.page_content = "Some content"
    mock_doc.metadata = {"source": "doc.pdf", "page": 2}
    flask_app.vector_stores["misc"].similarity_search.return_value = [mock_doc]

    response = client.post(
        "/query",
        json={"query": "test question", "model": "cogito-v1-preview-llama-3b"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["model"] == "cogito-v1-preview-llama-3b"


def test_query_empty_response(client, flask_app):
    """When the model handler returns None/empty, the endpoint should return 500."""
    from unittest.mock import MagicMock, patch

    mock_doc = MagicMock()
    mock_doc.page_content = "Content"
    mock_doc.metadata = {"source": "doc.pdf", "page": 1}
    flask_app.vector_stores["misc"].similarity_search.return_value = [mock_doc]

    # Patch local model handler to return None
    with patch.object(flask_app, "_handle_local_model", return_value=None):
        response = client.post(
            "/query",
            json={"query": "test question", "model": "cogito-v1-preview-llama-3b"},
        )
    assert response.status_code == 500
    data = response.get_json()
    assert "Failed to generate response" in data["error"]


def test_query_exception_path(client, flask_app):
    """When similarity_search raises an exception, expect a 500 with error details."""
    flask_app.vector_stores["misc"].similarity_search.side_effect = RuntimeError("FAISS crashed")

    response = client.post(
        "/query",
        json={"query": "test question"},
    )
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
    assert "FAISS crashed" in data["error"]

    # Reset side_effect for other tests
    flask_app.vector_stores["misc"].similarity_search.side_effect = None
    flask_app.vector_stores["misc"].similarity_search.return_value = []


def test_query_index_not_loaded(client, flask_app):
    """When ACTIVE_INDEX_KEY points to a missing index, expect 500."""
    flask_app.ACTIVE_INDEX_KEY = "nonexistent"
    try:
        response = client.post(
            "/query",
            json={"query": "test question"},
        )
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
    finally:
        # Restore default so other tests are not affected
        flask_app.ACTIVE_INDEX_KEY = "misc"
