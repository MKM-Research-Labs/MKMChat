# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
