# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
"""
Response Synthesizer
--------------------

Synthesizes responses from multiple knowledge bases into a coherent answer.
"""

import traceback
from typing import List

from .models import KBQueryResult
from .model_router import route_to_model_handler


class ResponseSynthesizer:
    """Synthesizes responses from multiple knowledge bases."""

    def __init__(self, app_instance):
        """
        Initialize the response synthesizer.

        Args:
            app_instance: The DocumentQAApp instance
        """
        self.app = app_instance

    def synthesize(
        self,
        query: str,
        kb_results: List[KBQueryResult],
        model: str
    ) -> str:
        """
        Synthesize responses from multiple knowledge bases into a coherent answer.

        Args:
            query: The original research question
            kb_results: List of results from individual KB queries
            model: The LLM model to use for synthesis

        Returns:
            str: Synthesized answer
        """
        # Build the synthesis context
        synthesis_parts = []

        for result in kb_results:
            if result.success and result.response and result.doc_count > 0:
                # Only include KB results that have actual content
                if "no relevant documents" not in result.response.lower():
                    synthesis_parts.append(
                        f"=== {result.kb_name} ===\n"
                        f"{result.response}\n"
                        f"(Based on {result.doc_count} documents)"
                    )

        if not synthesis_parts:
            return (
                "No relevant information was found across any of the knowledge bases "
                "for this query. Please try rephrasing your question or check if the "
                "relevant documents have been indexed."
            )

        # Build the synthesis prompt
        synthesis_context = "\n\n".join(synthesis_parts)

        synthesis_prompt = f"""You are synthesizing research findings from multiple knowledge bases.

Original Question: {query}

Findings from Different Knowledge Bases:
{synthesis_context}

Please synthesize these findings into a comprehensive, coherent answer that:
1. Integrates insights from all relevant knowledge bases
2. Highlights any complementary or contrasting information
3. Notes which knowledge base(s) provided the most relevant information
4. Presents a clear, well-structured response

Synthesized Answer:"""

        system_message = (
            "You are a research assistant synthesizing information from multiple sources. "
            "Provide clear, well-organized responses that integrate multiple perspectives."
        )

        try:
            # Route to appropriate model handler
            response = route_to_model_handler(self.app, model, synthesis_prompt, system_message)
            return response

        except Exception as e:
            print(f"Error during synthesis: {str(e)}")
            print(traceback.format_exc())

            # Fallback: return a simple concatenation
            return self._fallback_synthesis(kb_results)

    def _fallback_synthesis(self, kb_results: List[KBQueryResult]) -> str:
        """Generate fallback synthesis when LLM synthesis fails."""
        fallback = "**Synthesis failed - showing individual responses:**\n\n"
        for result in kb_results:
            if result.success and result.response:
                fallback += f"**{result.kb_name}:**\n{result.response}\n\n"
        return fallback
