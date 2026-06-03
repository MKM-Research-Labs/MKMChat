# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
"""
Knowledge Base Query Module
---------------------------

Handles querying individual knowledge bases and generating responses.
"""

import time
import traceback
from typing import List

from .models import KBQueryResult
from .model_router import route_to_model_handler
from config import RESEARCH_MAX_DOCS_PER_KB


class KBQueryExecutor:
    """Executes queries against individual knowledge bases."""

    def __init__(self, app_instance, max_docs_per_kb: int = RESEARCH_MAX_DOCS_PER_KB):
        """
        Initialize the KB query executor.

        Args:
            app_instance: The DocumentQAApp instance
            max_docs_per_kb: Maximum documents to retrieve per KB
        """
        self.app = app_instance
        self.max_docs_per_kb = max_docs_per_kb

    def query_single_kb(
        self,
        query: str,
        kb_key: str,
        model: str
    ) -> KBQueryResult:
        """
        Query a single knowledge base and generate a response.

        Args:
            query: The user's research question
            kb_key: The knowledge base key (e.g., 'misc', 'phys')
            model: The LLM model to use for response generation

        Returns:
            KBQueryResult with the response or error information
        """
        start_time = time.time()

        kb_info = self.app.AVAILABLE_INDICES.get(kb_key, {})
        kb_name = kb_info.get("name", kb_key)

        try:
            # Load the FAISS index if not already loaded
            vector_store = self.app.vector_stores.get(kb_key)
            if vector_store is None:
                try:
                    vector_store = self.app._load_faiss_index(kb_key)
                except Exception as load_error:
                    return KBQueryResult(
                        kb_key=kb_key,
                        kb_name=kb_name,
                        success=False,
                        error=f"Failed to load index: {str(load_error)}",
                        query_time_ms=int((time.time() - start_time) * 1000)
                    )

            # Perform similarity search
            docs = vector_store.similarity_search(query, self.max_docs_per_kb)

            if not docs:
                return KBQueryResult(
                    kb_key=kb_key,
                    kb_name=kb_name,
                    success=True,
                    response="No relevant documents found in this knowledge base.",
                    doc_count=0,
                    query_time_ms=int((time.time() - start_time) * 1000)
                )

            # Build context from retrieved documents
            context = self._build_context(docs)

            # Generate response using the appropriate LLM handler
            kb_specific_query = (
                f"Based on the {kb_name} knowledge base, answer this question: {query}\n\n"
                f"If this knowledge base doesn't contain relevant information, "
                f"clearly state that. Be concise but comprehensive."
            )

            # Route to appropriate model handler
            response = route_to_model_handler(self.app, model, kb_specific_query, context)

            # Debug logging
            print(f"  Model response type: {type(response)}")
            print(f"  Model response length: {len(response) if response else 0}")
            if response:
                print(f"  Model response preview: {response[:100]}...")
            else:
                print(f"  Model response is None or empty!")

            # Validate response
            if not response or not isinstance(response, str):
                return KBQueryResult(
                    kb_key=kb_key,
                    kb_name=kb_name,
                    success=False,
                    error=f"Invalid response from model (type: {type(response)})",
                    doc_count=len(docs),
                    query_time_ms=int((time.time() - start_time) * 1000)
                )

            # Check for error responses
            if response.startswith("Error") or "failed" in response.lower():
                return KBQueryResult(
                    kb_key=kb_key,
                    kb_name=kb_name,
                    success=False,
                    error=response,
                    doc_count=len(docs),
                    query_time_ms=int((time.time() - start_time) * 1000)
                )

            # Extract source information
            sources = self._extract_sources(docs, kb_key)

            return KBQueryResult(
                kb_key=kb_key,
                kb_name=kb_name,
                success=True,
                response=response,
                sources=sources,
                doc_count=len(docs),
                query_time_ms=int((time.time() - start_time) * 1000)
            )

        except Exception as e:
            print(f"Error querying KB {kb_key}: {str(e)}")
            print(traceback.format_exc())
            return KBQueryResult(
                kb_key=kb_key,
                kb_name=kb_name,
                success=False,
                error=str(e),
                query_time_ms=int((time.time() - start_time) * 1000)
            )

    def _build_context(self, docs: List) -> str:
        """Build context string from retrieved documents."""
        return "\n\n".join([
            f"From {doc.metadata.get('source', 'Unknown')} "
            f"(Page {doc.metadata.get('page', doc.metadata.get('page_number', '?'))}): "
            f"{doc.page_content}"
            for doc in docs
        ])

    def _extract_sources(self, docs: List, kb_key: str) -> List[dict]:
        """Extract source information from documents."""
        sources = []
        for doc in docs:
            sources.append({
                "file": doc.metadata.get("source", "Unknown source"),
                "page": str(doc.metadata.get("page",
                           doc.metadata.get("page_number",
                           doc.metadata.get("item_id", "1")))),
                "kb": kb_key
            })
        return sources
