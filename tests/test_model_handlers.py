# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Tests for src/models module

Tests for LocalModelHandler, PerplexityHandler, and AnthropicHandler.

NOTE: These tests overlap significantly with tests/test_models/.
They are kept for any unique edge-case coverage (e.g. custom URL init,
opus model ID mapping, API error status codes).
"""

from unittest.mock import patch, MagicMock

import pytest

from src.models.local_model import LocalModelHandler
from src.models.perplexity_model import PerplexityHandler
from src.models.anthropic_model import AnthropicHandler


class TestLocalModelHandler:
    """Tests for LocalModelHandler class."""

    def test_initialization(self):
        """Should initialize with default API URL."""
        handler = LocalModelHandler()
        assert handler.api_url == "http://localhost:1234/v1/chat/completions"

    def test_initialization_custom_url(self):
        """Should accept custom API URL."""
        handler = LocalModelHandler(api_url="http://custom:8080/v1/chat/completions")
        assert handler.api_url == "http://custom:8080/v1/chat/completions"

    def test_truncate_context_short(self):
        """Should not truncate short context."""
        handler = LocalModelHandler()
        context = "Short context"
        result = handler._truncate_context(context)
        assert result == context

    def test_truncate_context_long(self):
        """Should truncate long context."""
        handler = LocalModelHandler()
        handler.max_context_length = 100
        context = "A" * 200
        result = handler._truncate_context(context)
        assert len(result) < 200
        assert "[context truncated" in result

    def test_build_payload(self):
        """Should build correct payload structure."""
        handler = LocalModelHandler()
        payload = handler._build_payload("test query", "test context")

        assert "messages" in payload
        assert "temperature" in payload
        assert "max_tokens" in payload
        assert len(payload["messages"]) == 2

    @patch('src.models.local_model.requests.post')
    def test_query_success(self, mock_post):
        """Should return response on success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        handler = LocalModelHandler()
        result = handler.query("test query", "test context")

        assert result == "Test response"

    @patch('src.models.local_model.requests.post')
    def test_query_connection_error(self, mock_post):
        """Should return error message on connection failure."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()

        handler = LocalModelHandler()
        result = handler.query("test query", "test context")

        assert "Error" in result or "connect" in result.lower() or "LM Studio" in result

    @patch('src.models.local_model.requests.post')
    def test_query_timeout(self, mock_post):
        """Should return error message on timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()

        handler = LocalModelHandler()
        result = handler.query("test query", "test context")

        assert "timed out" in result

    @patch('src.models.local_model.requests.post')
    def test_query_api_error(self, mock_post):
        """Should return error message on API error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.side_effect = Exception()
        mock_post.return_value = mock_response

        handler = LocalModelHandler()
        result = handler.query("test query", "test context")

        assert "Error" in result or "error" in result.lower()


class TestPerplexityHandler:
    """Tests for PerplexityHandler class."""

    def test_initialization(self):
        """Should initialize with API key."""
        handler = PerplexityHandler(api_key="test_key")
        assert handler.api_key == "test_key"
        assert handler.api_url == "https://api.perplexity.ai/chat/completions"

    def test_initialization_custom_url(self):
        """Should accept custom API URL."""
        handler = PerplexityHandler(api_key="test_key", api_url="https://custom.api/")
        assert handler.api_url == "https://custom.api/"

    def test_build_headers(self):
        """Should build correct headers."""
        handler = PerplexityHandler(api_key="test_key")
        headers = handler._build_headers()

        assert "Authorization" in headers
        assert "Bearer test_key" in headers["Authorization"]
        assert headers["Content-Type"] == "application/json"

    def test_build_payload(self):
        """Should build correct payload structure."""
        handler = PerplexityHandler(api_key="test_key")
        payload = handler._build_payload("test query", "test context", "sonar")

        assert payload["model"] == "sonar"
        assert "messages" in payload
        assert len(payload["messages"]) == 2

    @patch('src.models.perplexity_model.replace_terms')
    @patch('src.models.perplexity_model.requests.post')
    def test_query_success(self, mock_post, mock_replace):
        """Should return response on success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response
        mock_replace.return_value = "Processed response"

        handler = PerplexityHandler(api_key="test_key")
        result = handler.query("test query", "test context")

        assert result == "Processed response"
        mock_replace.assert_called_once()

    @patch('src.models.perplexity_model.requests.post')
    def test_query_api_error(self, mock_post):
        """Should return error message on API error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        handler = PerplexityHandler(api_key="bad_key")
        result = handler.query("test query", "test context")

        assert "Error" in result

    @patch('src.models.perplexity_model.requests.post')
    def test_query_exception(self, mock_post):
        """Should return error message on exception."""
        mock_post.side_effect = Exception("Network error")

        handler = PerplexityHandler(api_key="test_key")
        result = handler.query("test query", "test context")

        assert "Error" in result


class TestAnthropicHandler:
    """Tests for AnthropicHandler class."""

    def test_initialization(self):
        """Should initialize with API key."""
        handler = AnthropicHandler(api_key="test_key")
        assert handler.api_key == "test_key"
        assert handler.api_url == "https://api.anthropic.com/v1/messages"

    def test_initialization_custom_url(self):
        """Should accept custom API URL."""
        handler = AnthropicHandler(api_key="test_key", api_url="https://custom.api/")
        assert handler.api_url == "https://custom.api/"

    def test_get_model_id_default(self):
        """Should return correct model ID for default model."""
        handler = AnthropicHandler(api_key="test_key")
        model_id = handler._get_model_id("claude-sonnet-4.5")
        assert model_id == "claude-sonnet-4-5-20250929"

    def test_get_model_id_opus(self):
        """Should return correct model ID for opus."""
        handler = AnthropicHandler(api_key="test_key")
        model_id = handler._get_model_id("claude-3-opus")
        assert model_id == "claude-3-opus-20240229"

    def test_get_model_id_unknown(self):
        """Should return default model ID for unknown model."""
        handler = AnthropicHandler(api_key="test_key")
        model_id = handler._get_model_id("unknown-model")
        assert model_id == "claude-sonnet-4-5-20250929"

    def test_build_headers(self):
        """Should build correct headers."""
        handler = AnthropicHandler(api_key="test_key")
        headers = handler._build_headers()

        assert headers["x-api-key"] == "test_key"
        assert headers["anthropic-version"] == "2023-06-01"
        assert headers["Content-Type"] == "application/json"

    def test_build_payload(self):
        """Should build correct payload structure."""
        handler = AnthropicHandler(api_key="test_key")
        payload = handler._build_payload("test query", "test context", "claude-sonnet-4-5-20250929")

        assert payload["model"] == "claude-sonnet-4-5-20250929"
        assert payload["max_tokens"] == 4096
        assert "messages" in payload
        assert len(payload["messages"]) == 1

    @patch('src.models.anthropic_model.replace_terms')
    @patch('src.models.anthropic_model.requests.post')
    def test_query_success(self, mock_post, mock_replace):
        """Should return response on success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Test response"}]
        }
        mock_post.return_value = mock_response
        mock_replace.return_value = "Processed response"

        handler = AnthropicHandler(api_key="test_key")
        result = handler.query("test query", "test context")

        assert result == "Processed response"
        mock_replace.assert_called_once()

    @patch('src.models.anthropic_model.requests.post')
    def test_query_api_error(self, mock_post):
        """Should return error message on API error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        handler = AnthropicHandler(api_key="bad_key")
        result = handler.query("test query", "test context")

        assert "Error" in result

    @patch('src.models.anthropic_model.requests.post')
    def test_query_exception(self, mock_post):
        """Should return error message on exception."""
        mock_post.side_effect = Exception("Network error")

        handler = AnthropicHandler(api_key="test_key")
        result = handler.query("test query", "test context")

        assert "Error" in result
