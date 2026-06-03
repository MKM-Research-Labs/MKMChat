# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/summary/llm_client.py."""

import pytest
from unittest.mock import patch, MagicMock

from src.summary.llm_client import call_llm_for_summary, clean_summary_text


def test_call_llm_success():
    """call_llm_for_summary returns cleaned text on a 200 response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "<think>reasoning</think>\n\n### Overview\nA detailed analysis of yield curve models and their applications."}}
        ]
    }

    with patch("src.summary.llm_client.requests.post", return_value=mock_response):
        result = call_llm_for_summary(
            book_name="Test Book",
            context="Some context text",
            url="http://localhost:1234/v1/chat/completions",
            model="test-model",
            max_tokens=512,
            temperature=0.3,
        )

    assert result is not None
    # The <think> block should be stripped by clean_summary_text
    assert "<think>" not in result
    assert "yield curve models" in result


def test_clean_response_text():
    """clean_summary_text removes <think> blocks and extra whitespace."""
    raw = "<think>Some internal reasoning\nmore thinking</think>\n\n\n\nMain themes and topics\n\n\n\nKey ideas"
    cleaned = clean_summary_text(raw)

    assert "<think>" not in cleaned
    assert "Some internal reasoning" not in cleaned
    # Should still contain the actual summary content
    assert "Main themes" in cleaned or "Key ideas" in cleaned
    # Triple newlines should be collapsed
    assert "\n\n\n" not in cleaned


def test_call_llm_non_200_response():
    """call_llm_for_summary returns None on non-200 status."""
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("src.summary.llm_client.requests.post", return_value=mock_response):
        result = call_llm_for_summary("Test Book", "context")
    assert result is None


def test_call_llm_connection_error():
    """call_llm_for_summary returns None on ConnectionError."""
    import requests as req

    with patch("src.summary.llm_client.requests.post", side_effect=req.exceptions.ConnectionError):
        result = call_llm_for_summary("Test Book", "context")
    assert result is None


def test_call_llm_generic_exception():
    """call_llm_for_summary returns None on unexpected exception."""
    with patch("src.summary.llm_client.requests.post", side_effect=RuntimeError("boom")):
        result = call_llm_for_summary("Test Book", "context")
    assert result is None


def test_query_local_model_with_chunks_success():
    """query_local_model_with_chunks returns summary on success."""
    from src.summary.llm_client import query_local_model_with_chunks
    from src.summary.models import DocumentChunk

    chunks = [
        DocumentChunk(content="Chapter 1 text", metadata={"page": 1}, doc_id="d1", page=1),
        DocumentChunk(content="Chapter 2 text", metadata={"page": 2}, doc_id="d2", page=2),
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "A great summary"}}]
    }

    with patch("src.summary.llm_client.requests.post", return_value=mock_resp):
        result = query_local_model_with_chunks("test.pdf", chunks)

    assert result == "A great summary"


def test_query_local_model_with_chunks_empty():
    """query_local_model_with_chunks returns None for empty chunks."""
    from src.summary.llm_client import query_local_model_with_chunks
    result = query_local_model_with_chunks("test.pdf", [])
    assert result is None


def test_query_local_model_with_chunks_retries():
    """query_local_model_with_chunks retries on failure and returns None after max retries."""
    from src.summary.llm_client import query_local_model_with_chunks
    from src.summary.models import DocumentChunk

    chunks = [DocumentChunk(content="text", metadata={"page": 1}, doc_id="d1", page=1)]

    with patch("src.summary.llm_client.requests.post", side_effect=RuntimeError("fail")):
        result = query_local_model_with_chunks("test.pdf", chunks, max_retries=2)

    assert result is None


def test_query_local_model_unexpected_format():
    """query_local_model_with_chunks raises on unexpected response format and retries."""
    from src.summary.llm_client import query_local_model_with_chunks
    from src.summary.models import DocumentChunk

    chunks = [DocumentChunk(content="text", metadata={"page": 1}, doc_id="d1", page=1)]

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"unexpected": "format"}

    with patch("src.summary.llm_client.requests.post", return_value=mock_resp):
        result = query_local_model_with_chunks("test.pdf", chunks, max_retries=1)

    assert result is None


def test_generate_basic_summary():
    """generate_basic_summary returns a placeholder summary with the document name."""
    from src.summary.llm_client import generate_basic_summary

    result = generate_basic_summary("my_great_book.pdf")
    assert "my great book" in result
    assert "my_great_book.pdf" in result
    assert "placeholder" in result.lower() or "fallback" in result.lower()


def test_clean_summary_text_empty():
    """clean_summary_text handles empty string."""
    result = clean_summary_text("")
    assert result == ""


def test_query_local_model_with_chunks_zero_retries():
    """query_local_model_with_chunks returns None when max_retries=0."""
    from src.summary.llm_client import query_local_model_with_chunks
    from src.summary.models import DocumentChunk

    chunks = [DocumentChunk(content="text", metadata={"page": 1}, doc_id="d1", page=1)]
    result = query_local_model_with_chunks("test.pdf", chunks, max_retries=0)
    assert result is None


def test_clean_summary_text_no_think_tags():
    """clean_summary_text passes through text without think tags."""
    text = "### Overview\nThis is a normal summary."
    result = clean_summary_text(text)
    assert "Overview" in result
    assert "normal summary" in result
