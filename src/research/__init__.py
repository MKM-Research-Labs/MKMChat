# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
"""
Research Query Module
---------------------

Provides deep research functionality by querying all available knowledge bases
sequentially and synthesizing the results into a coherent response.

This version supports Server-Sent Events (SSE) for real-time progress updates.

Usage:
    from src.research import ResearchQueryHandler, create_research_route

    # Create handler
    researcher = ResearchQueryHandler(app_instance)

    # Standard (blocking) mode:
    result = researcher.execute_research_query(query, model)

    # Streaming mode (for SSE):
    for event in researcher.execute_research_query_streaming(query, model):
        yield event

    # Flask routes:
    app.add_url_rule('/research_query', view_func=create_research_route(app_instance), methods=['POST'])
"""

from .models import KBQueryResult, ResearchResult
from .model_router import route_to_model_handler
from .kb_query import KBQueryExecutor
from .synthesizer import ResponseSynthesizer
from .handler import ResearchQueryHandler
from .routes import create_research_route, create_research_stream_route

__all__ = [
    # Data models
    'KBQueryResult',
    'ResearchResult',
    # Components
    'route_to_model_handler',
    'KBQueryExecutor',
    'ResponseSynthesizer',
    'ResearchQueryHandler',
    # Route factories
    'create_research_route',
    'create_research_stream_route',
]
