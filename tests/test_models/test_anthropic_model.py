# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/models/anthropic_model.py (AnthropicHandler)."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.models.anthropic_model import AnthropicHandler
from config import ANTHROPIC_API_VERSION, MODEL_ID
from data import SAMPLE_LLM_RESPONSE_ANTHROPIC


@pytest.fixture
def handler():
    """Create an AnthropicHandler with a fake API key."""
    return AnthropicHandler(api_key="test-api-key-123")


# ── query ────────────────────────────────────────────────────────────────


class TestQuery:
    def test_query_success(self, handler):
        """Mock 200 response, verify response text returned with replace_terms applied."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_LLM_RESPONSE_ANTHROPIC

        with patch("src.models.anthropic_model.requests.post", return_value=mock_resp):
            result = handler.query("test question", "test context")

        # replace_terms should have been applied (result should be a string)
        assert isinstance(result, str)
        assert "Error" not in result
        # The sample response text is "This is a test response from Claude."
        # replace_terms won't change it much but it should still come through
        assert "test response" in result

    def test_query_api_error(self, handler):
        """Mock 500 response, verify error message returned."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"

        with patch("src.models.anthropic_model.requests.post", return_value=mock_resp):
            result = handler.query("test question", "test context")

        assert "Error from Anthropic API" in result
        assert "Internal Server Error" in result

    def test_query_network_error(self, handler):
        """Mock ConnectionError, verify error message."""
        with patch(
            "src.models.anthropic_model.requests.post",
            side_effect=requests.exceptions.ConnectionError("Connection refused"),
        ):
            result = handler.query("test question", "test context")

        assert "Error with Anthropic model" in result


# ── _get_model_id ────────────────────────────────────────────────────────


class TestGetModelId:
    def test_get_model_id_known(self, handler):
        """Verify 'claude-sonnet-4.5' maps to the configured MODEL_ID."""
        assert handler._get_model_id("claude-sonnet-4.5") == MODEL_ID

    def test_get_model_id_unknown(self, handler):
        """Unknown model name falls back to the default (claude-sonnet-4.5)."""
        assert handler._get_model_id("nonexistent-model") == MODEL_ID


# ── _build_headers ───────────────────────────────────────────────────────


class TestBuildHeaders:
    def test_build_headers(self, handler):
        headers = handler._build_headers()
        assert headers["x-api-key"] == "test-api-key-123"
        assert headers["anthropic-version"] == ANTHROPIC_API_VERSION
        assert headers["Content-Type"] == "application/json"


# ── _build_payload ───────────────────────────────────────────────────────


class TestBuildPayload:
    def test_build_payload(self, handler):
        payload = handler._build_payload("my question", "my context", "model-xyz")
        assert payload["model"] == "model-xyz"
        assert payload["max_tokens"] == handler.max_tokens
        assert len(payload["messages"]) == 1
        msg = payload["messages"][0]
        assert msg["role"] == "user"
        assert "my question" in msg["content"]
        assert "my context" in msg["content"]
