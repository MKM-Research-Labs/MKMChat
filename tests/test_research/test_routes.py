# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/research/routes.py (research query endpoints)."""

from unittest.mock import patch, MagicMock

from src.research.models import KBQueryResult, ResearchResult


def test_research_query_not_json(client):
    """POST /research_query with text/plain should return 400."""
    response = client.post(
        "/research_query",
        data="plain text",
        content_type="text/plain",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_research_query_missing_query(client):
    """POST /research_query without 'query' field should return 400."""
    response = client.post("/research_query", json={"model": "sonar-pro"})
    assert response.status_code == 400
    data = response.get_json()
    assert "query" in data["error"].lower()


def test_research_query_missing_model(client):
    """POST /research_query without 'model' field should return 400."""
    response = client.post("/research_query", json={"query": "test"})
    assert response.status_code == 400
    data = response.get_json()
    assert "model" in data["error"].lower()


def test_research_query_invalid_model(client):
    """POST /research_query with an invalid model should return 400."""
    response = client.post(
        "/research_query",
        json={"query": "test", "model": "nonexistent-model"},
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_research_query_invalid_kb_keys(client):
    """POST /research_query with invalid kb_keys should return 400."""
    response = client.post(
        "/research_query",
        json={"query": "test", "model": "sonar-pro", "kb_keys": ["nonexistent"]},
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_research_query_kb_keys_not_list(client):
    """POST /research_query with kb_keys as a string should return 400."""
    response = client.post(
        "/research_query",
        json={"query": "test", "model": "sonar-pro", "kb_keys": "misc"},
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "list" in data["error"].lower()


def test_research_query_success(client):
    """POST /research_query with valid data should return 200."""
    mock_result = ResearchResult(
        query="test query",
        model="sonar-pro",
        kb_results=[
            KBQueryResult(
                kb_key="misc",
                kb_name="Miscellaneous",
                success=True,
                response="Answer from misc.",
                sources=[{"file": "doc.pdf", "page": "1", "kb": "misc"}],
                doc_count=2,
                query_time_ms=100,
            )
        ],
        synthesized_answer="Synthesized answer.",
        total_sources=1,
        total_time_ms=200,
        timestamp="2026-03-26T12:00:00",
        success=True,
    )

    with patch(
        "src.research.handler.ResearchQueryHandler.execute_research_query",
        return_value=mock_result,
    ):
        response = client.post(
            "/research_query",
            json={"query": "test query", "model": "sonar-pro", "kb_keys": ["misc"]},
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["query"] == "test query"
    assert len(data["kb_results"]) == 1


def test_research_query_exception(client):
    """POST /research_query should return 500 when handler raises."""
    with patch(
        "src.research.handler.ResearchQueryHandler.execute_research_query",
        side_effect=RuntimeError("boom"),
    ):
        response = client.post(
            "/research_query",
            json={"query": "test", "model": "sonar-pro"},
        )

    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
    assert "boom" in data["error"]


def test_research_stream_missing_params(client):
    """GET /research_query_stream without query/model should return error event."""
    response = client.get("/research_query_stream")
    assert response.status_code == 200  # SSE always returns 200
    assert response.content_type.startswith("text/event-stream")
    data = response.get_data(as_text=True)
    assert "error" in data


def test_research_stream_invalid_model(client):
    """GET /research_query_stream with invalid model should return error event."""
    response = client.get("/research_query_stream?query=test&model=bad-model")
    data = response.get_data(as_text=True)
    assert "error" in data
    assert "Invalid model" in data


# ── Additional coverage tests ───────────────────────────────────────────


def test_research_stream_post_method(client):
    """POST /research_query_stream reads params from JSON body."""
    response = client.post(
        "/research_query_stream",
        json={"query": "test", "model": "bad-model"},
    )
    data = response.get_data(as_text=True)
    assert "error" in data
    assert "Invalid model" in data


def test_research_stream_post_missing_params(client):
    """POST /research_query_stream without query/model returns error event."""
    response = client.post(
        "/research_query_stream",
        json={},
    )
    data = response.get_data(as_text=True)
    assert "error" in data
    assert "Missing" in data


def test_research_stream_post_no_json(client):
    """POST /research_query_stream with non-JSON content returns error.

    Flask returns 415 Unsupported Media Type when get_json() is called
    on a request with non-JSON content type, so we expect either that
    or an SSE error event.
    """
    response = client.post(
        "/research_query_stream",
        data="plain text",
        content_type="text/plain",
    )
    # Flask rejects non-JSON content with 415 before the route handler runs
    # or the route handles it and returns an SSE error event
    data = response.get_data(as_text=True)
    assert response.status_code in (200, 415)
    assert "error" in data.lower() or "unsupported" in data.lower()


def test_research_stream_get_with_kb_keys(client):
    """GET /research_query_stream parses comma-separated kb_keys from query string."""
    with patch(
        "src.research.handler.ResearchQueryHandler.execute_research_query_streaming",
        return_value=[
            'event: done\ndata: {"success": true}\n\n'
        ],
    ):
        response = client.get(
            "/research_query_stream?query=test&model=sonar-pro&kb_keys=misc"
        )
    data = response.get_data(as_text=True)
    assert response.status_code == 200


def test_research_stream_success(client):
    """GET /research_query_stream with valid params streams events."""
    mock_events = [
        'event: progress\ndata: {"step": "querying"}\n\n',
        'event: done\ndata: {"success": true}\n\n',
    ]

    with patch(
        "src.research.handler.ResearchQueryHandler.execute_research_query_streaming",
        return_value=iter(mock_events),
    ):
        response = client.get(
            "/research_query_stream?query=test&model=sonar-pro"
        )

    assert response.status_code == 200
    data = response.get_data(as_text=True)
    assert "progress" in data
    assert "done" in data


def test_research_stream_handler_exception(client):
    """Streaming endpoint handles exceptions from the handler."""
    with patch(
        "src.research.handler.ResearchQueryHandler.execute_research_query_streaming",
        side_effect=RuntimeError("stream crash"),
    ):
        response = client.get(
            "/research_query_stream?query=test&model=sonar-pro"
        )

    data = response.get_data(as_text=True)
    assert "error" in data
    assert "stream crash" in data


def test_research_stream_response_headers(client):
    """Streaming endpoint sets correct headers for SSE."""
    with patch(
        "src.research.handler.ResearchQueryHandler.execute_research_query_streaming",
        return_value=iter(['event: done\ndata: {}\n\n']),
    ):
        response = client.get(
            "/research_query_stream?query=test&model=sonar-pro"
        )

    assert response.content_type.startswith("text/event-stream")
    assert response.headers.get("Cache-Control") == "no-cache"
