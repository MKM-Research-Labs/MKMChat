# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/research/model_router.py."""

from unittest.mock import MagicMock, call


def test_route_to_anthropic():
    """Models containing 'claude' should route to _handle_anthropic_model."""
    from src.research.model_router import route_to_model_handler

    app = MagicMock()
    app._handle_anthropic_model.return_value = "anthropic response"

    result = route_to_model_handler(app, "claude-sonnet-4-5-20250929", "q", "ctx")

    app._handle_anthropic_model.assert_called_once_with("q", "ctx", "claude-sonnet-4-5-20250929")
    assert result == "anthropic response"


def test_route_to_perplexity():
    """Models containing 'sonar' should route to _handle_perplexity_model."""
    from src.research.model_router import route_to_model_handler

    app = MagicMock()
    app._handle_perplexity_model.return_value = "perplexity response"

    result = route_to_model_handler(app, "sonar-pro", "q", "ctx")

    app._handle_perplexity_model.assert_called_once_with("q", "ctx", "sonar-pro")
    assert result == "perplexity response"


def test_route_to_local():
    """Models not matching claude/sonar should route to _handle_local_model."""
    from src.research.model_router import route_to_model_handler

    app = MagicMock()
    app._handle_local_model.return_value = "local response"

    result = route_to_model_handler(app, "cogito-v1-preview-llama-3b", "q", "ctx")

    app._handle_local_model.assert_called_once_with("q", "ctx", "cogito-v1-preview-llama-3b")
    assert result == "local response"


def test_route_unknown_model():
    """Unknown models not in AVAILABLE_MODELS should still route via name pattern fallback."""
    from src.research.model_router import route_to_model_handler

    app = MagicMock()
    app._handle_local_model.return_value = "fallback local"

    # A model name not in AVAILABLE_MODELS and not containing claude/sonar
    result = route_to_model_handler(app, "totally-unknown-model", "q", "ctx")

    app._handle_local_model.assert_called_once_with("q", "ctx", "totally-unknown-model")
    assert result == "fallback local"


def test_route_unknown_claude_model():
    """Unknown model containing 'claude' should still route to anthropic."""
    from src.research.model_router import route_to_model_handler

    app = MagicMock()
    app._handle_anthropic_model.return_value = "anthropic fallback"

    result = route_to_model_handler(app, "claude-unknown-version", "q", "ctx")

    app._handle_anthropic_model.assert_called_once_with("q", "ctx", "claude-unknown-version")
    assert result == "anthropic fallback"


def test_route_unknown_sonar_model():
    """Unknown model containing 'sonar' should still route to perplexity."""
    from src.research.model_router import route_to_model_handler

    app = MagicMock()
    app._handle_perplexity_model.return_value = "perplexity fallback"

    result = route_to_model_handler(app, "sonar-ultra-future", "q", "ctx")

    app._handle_perplexity_model.assert_called_once_with("q", "ctx", "sonar-ultra-future")
    assert result == "perplexity fallback"
