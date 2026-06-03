# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
"""
Research Query Handler
----------------------

Main orchestrator for research queries across multiple knowledge bases.
Supports both streaming (SSE) and non-streaming execution modes.
"""

import json
import time
from typing import List, Optional, Generator
from datetime import datetime

from .models import KBQueryResult, ResearchResult
from .kb_query import KBQueryExecutor
from .synthesizer import ResponseSynthesizer


class ResearchQueryHandler:
    """
    Handles research queries that span all knowledge bases.

    This class orchestrates:
    1. Sequential querying of each available FAISS index
    2. Per-KB answer generation using the selected LLM
    3. Synthesis of all answers into a coherent final response
    """

    def __init__(self, app_instance):
        """
        Initialize the research query handler.

        Args:
            app_instance: The DocumentQAApp instance providing access to
                         vector stores, embeddings, and LLM handlers
        """
        self.app = app_instance
        self.kb_executor = KBQueryExecutor(app_instance)
        self.synthesizer = ResponseSynthesizer(app_instance)

    def _format_sse_event(self, event_type: str, data: dict) -> str:
        """Format data as a Server-Sent Event"""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    def execute_research_query_streaming(
        self,
        query: str,
        model: str,
        kb_keys: Optional[List[str]] = None
    ) -> Generator[str, None, None]:
        """
        Execute a research query with streaming progress updates via SSE.

        Args:
            query: The research question
            model: The LLM model to use
            kb_keys: Optional list of specific KB keys to query

        Yields:
            SSE-formatted events as each step completes.
        """
        start_time = time.time()

        # Determine which knowledge bases to query
        if kb_keys is None:
            kb_keys = list(self.app.AVAILABLE_INDICES.keys())

        total_kbs = len(kb_keys)

        # Send initial event
        yield self._format_sse_event("start", {
            "query": query,
            "model": model,
            "total_kbs": total_kbs,
            "kb_keys": kb_keys,
            "kb_names": {k: self.app.AVAILABLE_INDICES[k]["name"] for k in kb_keys}
        })

        print(f"\n{'='*60}")
        print(f"RESEARCH QUERY (Streaming): {query[:50]}...")
        print(f"Model: {model}")
        print(f"Knowledge Bases: {', '.join(kb_keys)}")
        print(f"{'='*60}\n")

        # Query each knowledge base sequentially
        kb_results: List[KBQueryResult] = []

        for i, kb_key in enumerate(kb_keys, 1):
            kb_name = self.app.AVAILABLE_INDICES[kb_key]["name"]

            # Send "querying" event
            yield self._format_sse_event("querying", {
                "step": i,
                "total": total_kbs,
                "kb_key": kb_key,
                "kb_name": kb_name
            })

            print(f"[{i}/{total_kbs}] Querying {kb_key}...")

            # Execute the query
            result = self.kb_executor.query_single_kb(query, kb_key, model)
            kb_results.append(result)

            status = "✓" if result.success else "✗"
            print(f"  {status} {result.kb_name}: {result.doc_count} docs, "
                  f"{result.query_time_ms}ms")

            # Send "kb_complete" event with the result
            yield self._format_sse_event("kb_complete", {
                "step": i,
                "total": total_kbs,
                "kb_key": kb_key,
                "kb_name": kb_name,
                "result": result.to_dict()
            })

        # Send "synthesizing" event
        yield self._format_sse_event("synthesizing", {
            "message": "Synthesizing responses from all knowledge bases..."
        })

        print(f"\nSynthesizing responses from {len(kb_results)} knowledge bases...")

        # Synthesize the responses
        synthesized = self.synthesizer.synthesize(query, kb_results, model)

        # Calculate totals
        total_sources = sum(len(r.sources) for r in kb_results)
        total_time = int((time.time() - start_time) * 1000)

        # Check overall success
        any_success = any(r.success and r.doc_count > 0 for r in kb_results)

        # Build final result
        final_result = ResearchResult(
            query=query,
            model=model,
            kb_results=kb_results,
            synthesized_answer=synthesized,
            total_sources=total_sources,
            total_time_ms=total_time,
            timestamp=datetime.now().isoformat(),
            success=any_success
        )

        print(f"\n{'='*60}")
        print(f"Research complete: {total_sources} total sources, {total_time}ms")
        print(f"{'='*60}\n")

        # Send "complete" event with full results
        yield self._format_sse_event("complete", final_result.to_dict())

    def execute_research_query(
        self,
        query: str,
        model: str,
        kb_keys: Optional[List[str]] = None
    ) -> ResearchResult:
        """
        Execute a research query (non-streaming version).

        This collects all streaming events and returns the final result.

        Args:
            query: The research question
            model: The LLM model to use
            kb_keys: Optional list of specific KB keys to query

        Returns:
            ResearchResult with the complete research findings
        """
        result = None
        for event in self.execute_research_query_streaming(query, model, kb_keys):
            # Parse the event to check if it's the final result
            if "event: complete" in event:
                # Extract the data portion
                data_line = event.split("data: ")[1].strip()
                result_dict = json.loads(data_line)

                # Reconstruct KBQueryResult objects
                kb_results = [
                    KBQueryResult(**kb) for kb in result_dict['kb_results']
                ]

                result = ResearchResult(
                    query=result_dict['query'],
                    model=result_dict['model'],
                    kb_results=kb_results,
                    synthesized_answer=result_dict['synthesized_answer'],
                    total_sources=result_dict['total_sources'],
                    total_time_ms=result_dict['total_time_ms'],
                    timestamp=result_dict['timestamp'],
                    success=result_dict['success']
                )

        return result
