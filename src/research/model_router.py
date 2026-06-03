# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
"""
Model Router
------------

Routes queries to appropriate model handlers based on model name patterns.
Uses config.py as the source of truth for available models.
"""

from config import AVAILABLE_MODELS


def route_to_model_handler(app, model: str, query: str, context: str) -> str:
    """
    Route query to appropriate model handler.
    Infers handler type from model name patterns in AVAILABLE_MODELS.

    Args:
        app: DocumentQAApp instance
        model: Model identifier (from AVAILABLE_MODELS keys)
        query: Query text
        context: Context text

    Returns:
        str: Model response
    """
    # Check if model exists in config
    if model not in AVAILABLE_MODELS:
        # Unknown model - try fallback
        model_lower = model.lower()
        if "claude" in model_lower:
            return app._handle_anthropic_model(query, context, model)
        elif "sonar" in model_lower:
            return app._handle_perplexity_model(query, context, model)
        else:
            return app._handle_local_model(query, context, model)

    # Infer handler from model name pattern
    model_lower = model.lower()

    # Anthropic models (contain "claude")
    if "claude" in model_lower:
        return app._handle_anthropic_model(query, context, model)

    # Perplexity models (contain "sonar")
    elif "sonar" in model_lower:
        return app._handle_perplexity_model(query, context, model)

    # Local models (everything else: mistral, cogito, deepseek, etc.)
    else:
        return app._handle_local_model(query, context, model)
