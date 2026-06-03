# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.

"""
API Connection Tests (Integration)
===================================

Tests for external API connections (Anthropic, Perplexity, LM Studio).
These tests make REAL API calls to verify connectivity and responses.

Run with: pytest tests/test_api_connections.py -m integration -v
"""

import time

import pytest
import requests

from config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_API_URL,
    LM_STUDIO_API_URL,
    PERPLEXITY_API_KEY,
    PERPLEXITY_API_URL,
)
from src.models import AnthropicHandler, LocalModelHandler, PerplexityHandler

pytestmark = pytest.mark.integration

TEST_QUERY = "What is 2+2? Reply with just the number."
TEST_CONTEXT = "This is a simple math test."


class TestAnthropicAPI:
    """Test Anthropic (Claude) API connection."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.handler = AnthropicHandler(ANTHROPIC_API_KEY, ANTHROPIC_API_URL)

    def test_api_key_configured(self):
        assert ANTHROPIC_API_KEY is not None
        assert len(ANTHROPIC_API_KEY) > 0

    def test_handler_instantiation(self):
        assert self.handler is not None

    def test_api_call_claude_sonnet(self):
        if not ANTHROPIC_API_KEY:
            pytest.skip("API key not configured")

        response = self.handler.query(
            query=TEST_QUERY, context=TEST_CONTEXT, model="claude-sonnet-4-5-20250929"
        )
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


class TestPerplexityAPI:
    """Test Perplexity API connection."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.handler = PerplexityHandler(PERPLEXITY_API_KEY, PERPLEXITY_API_URL)

    def test_api_key_configured(self):
        assert PERPLEXITY_API_KEY is not None
        assert len(PERPLEXITY_API_KEY) > 0

    def test_handler_instantiation(self):
        assert self.handler is not None

    def test_api_call_sonar_pro(self):
        if not PERPLEXITY_API_KEY:
            pytest.skip("API key not configured")

        response = self.handler.query(
            query=TEST_QUERY, context=TEST_CONTEXT, model="sonar-pro"
        )
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_api_call_sonar_reasoning(self):
        if not PERPLEXITY_API_KEY:
            pytest.skip("API key not configured")

        response = self.handler.query(
            query=TEST_QUERY, context=TEST_CONTEXT, model="sonar-reasoning-pro"
        )
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


class TestLMStudioAPI:
    """Test LM Studio local API connection."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.handler = LocalModelHandler(LM_STUDIO_API_URL)
        self.models_url = LM_STUDIO_API_URL.replace("/chat/completions", "/models")

    def _check_lm_studio_running(self):
        try:
            requests.get(self.models_url, timeout=2)
        except Exception:
            pytest.skip("LM Studio not running")

    def test_check_connectivity(self):
        try:
            response = requests.get(self.models_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                assert len(models) >= 0
        except requests.exceptions.ConnectionError:
            pytest.skip("LM Studio not reachable")

    def test_api_call_deepseek(self):
        self._check_lm_studio_running()

        response = self.handler.query(
            query=TEST_QUERY,
            context=TEST_CONTEXT,
            model="DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M",
        )
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


class TestAllAPIsComparison:
    """Compare responses from all APIs."""

    def test_compare_all_apis(self):
        results = {}
        comparison_query = "In one sentence, what is machine learning?"

        if ANTHROPIC_API_KEY:
            try:
                handler = AnthropicHandler(ANTHROPIC_API_KEY, ANTHROPIC_API_URL)
                response = handler.query(comparison_query, "", "claude-sonnet-4-5-20250929")
                results["Anthropic"] = {"success": True, "response": response[:150]}
            except Exception as e:
                results["Anthropic"] = {"success": False, "error": str(e)}

        if PERPLEXITY_API_KEY:
            try:
                handler = PerplexityHandler(PERPLEXITY_API_KEY, PERPLEXITY_API_URL)
                response = handler.query(comparison_query, "", "sonar-pro")
                results["Perplexity"] = {"success": True, "response": response[:150]}
            except Exception as e:
                results["Perplexity"] = {"success": False, "error": str(e)}

        try:
            models_url = LM_STUDIO_API_URL.replace("/chat/completions", "/models")
            requests.get(models_url, timeout=2)
            handler = LocalModelHandler(LM_STUDIO_API_URL)
            response = handler.query(comparison_query, "", "default")
            results["LM Studio"] = {"success": True, "response": response[:150]}
        except Exception:
            results["LM Studio"] = {"success": False, "error": "Not running"}

        successful = [k for k, v in results.items() if v.get("success")]
        assert len(successful) > 0, "At least one API should be working"
