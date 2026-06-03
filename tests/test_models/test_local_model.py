# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/models/local_model.py (LocalModelHandler)."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.models.local_model import LocalModelHandler
from config import LOCAL_MODEL_MAX_CONTEXT, LOCAL_MODEL_TEMPERATURE, LOCAL_MODEL_MAX_TOKENS
from data import SAMPLE_LLM_RESPONSE_LOCAL


@pytest.fixture
def handler():
    """Create a LocalModelHandler with the default LM Studio URL."""
    return LocalModelHandler()


# ── query ────────────────────────────────────────────────────────────────


class TestQuery:
    def test_query_success(self, handler):
        """Mock 200 response, verify response text returned."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_LLM_RESPONSE_LOCAL

        with patch("src.models.local_model.requests.post", return_value=mock_resp):
            result = handler.query("test question", "test context")

        assert isinstance(result, str)
        assert "test response from LM Studio" in result

    def test_query_timeout(self, handler):
        """Mock Timeout exception, verify error message."""
        with patch(
            "src.models.local_model.requests.post",
            side_effect=requests.exceptions.Timeout("Request timed out"),
        ):
            result = handler.query("test question", "test context")

        assert "timed out" in result

    def test_query_connection_error(self, handler):
        """Mock ConnectionError, verify error message about LM Studio."""
        with patch(
            "src.models.local_model.requests.post",
            side_effect=requests.exceptions.ConnectionError("Connection refused"),
        ):
            result = handler.query("test question", "test context")

        assert "Could not connect to LM Studio" in result


# ── _truncate_context ────────────────────────────────────────────────────


class TestTruncateContext:
    def test_truncate_context_short(self, handler):
        """Context under the limit should be returned unchanged."""
        short_text = "A short context string."
        assert handler._truncate_context(short_text) == short_text

    def test_truncate_context_long(self, handler):
        """Context over the limit should be truncated with a marker."""
        long_text = "x" * (handler.max_context_length + 500)
        result = handler._truncate_context(long_text)
        assert len(result) < len(long_text)
        assert result.endswith("... [context truncated for length]")
        # The prefix should be exactly max_context_length characters
        assert result.startswith("x" * handler.max_context_length)


# ── _build_payload ───────────────────────────────────────────────────────


class TestBuildPayload:
    def test_build_payload(self, handler):
        payload = handler._build_payload("my question", "my context")
        assert payload["temperature"] == LOCAL_MODEL_TEMPERATURE
        assert payload["max_tokens"] == LOCAL_MODEL_MAX_TOKENS
        assert len(payload["messages"]) == 2

        system_msg = payload["messages"][0]
        assert system_msg["role"] == "system"

        user_msg = payload["messages"][1]
        assert user_msg["role"] == "user"
        assert "my question" in user_msg["content"]
        assert "my context" in user_msg["content"]


# ── _handle_response ─────────────────────────────────────────────────────


class TestHandleResponse:
    def test_handle_response_success(self, handler):
        """Mock 200 response object, verify content extraction."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_LLM_RESPONSE_LOCAL

        result = handler._handle_response(mock_resp)
        assert "test response from LM Studio" in result

    def test_handle_response_error(self, handler):
        """Mock 400 response, verify error message."""
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"error": "Bad request"}
        mock_resp.text = "Bad request"

        result = handler._handle_response(mock_resp)
        assert "Error from local model" in result
        assert "400" in result


class TestQueryGenericException:
    def test_query_generic_exception(self, handler):
        """Generic exceptions should return an error message."""
        with patch(
            "src.models.local_model.requests.post",
            side_effect=ValueError("unexpected error"),
        ):
            result = handler.query("test question", "test context")

        assert "Error with local model" in result
        assert "unexpected error" in result
