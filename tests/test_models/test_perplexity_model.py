# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/models/perplexity_model.py (PerplexityHandler)."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.models.perplexity_model import PerplexityHandler
from data import SAMPLE_LLM_RESPONSE_PERPLEXITY


@pytest.fixture
def handler():
    """Create a PerplexityHandler with a fake API key."""
    return PerplexityHandler(api_key="test-pplx-key-456")


# ── query ────────────────────────────────────────────────────────────────


class TestQuery:
    def test_query_success(self, handler):
        """Mock 200 response, verify response text with replace_terms applied."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_LLM_RESPONSE_PERPLEXITY

        with patch("src.models.perplexity_model.requests.post", return_value=mock_resp):
            result = handler.query("test question", "test context")

        assert isinstance(result, str)
        assert "Error" not in result
        assert "test response" in result

    def test_query_api_error(self, handler):
        """Mock 500 response, verify error message."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Service Unavailable"

        with patch("src.models.perplexity_model.requests.post", return_value=mock_resp):
            result = handler.query("test question", "test context")

        assert "Error from Perplexity API" in result
        assert "Service Unavailable" in result

    def test_query_network_error(self, handler):
        """Mock ConnectionError, verify error message."""
        with patch(
            "src.models.perplexity_model.requests.post",
            side_effect=requests.exceptions.ConnectionError("Connection refused"),
        ):
            result = handler.query("test question", "test context")

        assert "Error with Perplexity model" in result


# ── _build_headers ───────────────────────────────────────────────────────


class TestBuildHeaders:
    def test_build_headers(self, handler):
        headers = handler._build_headers()
        assert headers["Authorization"] == "Bearer test-pplx-key-456"
        assert headers["Content-Type"] == "application/json"


# ── _build_payload ───────────────────────────────────────────────────────


class TestBuildPayload:
    def test_build_payload(self, handler):
        payload = handler._build_payload("my question", "my context", "sonar-pro")
        assert payload["model"] == "sonar-pro"
        assert len(payload["messages"]) == 2

        system_msg = payload["messages"][0]
        assert system_msg["role"] == "system"

        user_msg = payload["messages"][1]
        assert user_msg["role"] == "user"
        assert "my question" in user_msg["content"]
        assert "my context" in user_msg["content"]
