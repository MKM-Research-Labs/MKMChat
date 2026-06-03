# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.

"""
Deep Research Function Test (Integration)
==========================================

Comprehensive test of the deep research functionality.
Tests querying ALL knowledge bases and verifies complete output.

Run with: pytest tests/test_deep_research.py -m integration -v -s
Results are saved to: tests/results/deep_research_<timestamp>.json
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

import pytest

from config import AVAILABLE_MODELS, get_all_collections, paths

pytestmark = pytest.mark.integration

TEST_MODEL = "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M"
TEST_QUERY = "MKM Research Labs, David Kelly and Johnny Mattimore"
RESULTS_DIR = Path(__file__).parent.parent / "tests" / "results"


@pytest.fixture(scope="module")
def research_app():
    """Create a real (non-mocked) app for integration testing."""
    from src.app import DocumentQAApp

    qa_app = DocumentQAApp()
    qa_app.app.config["TESTING"] = True
    return qa_app


@pytest.fixture(scope="module")
def research_client(research_app):
    return research_app.app.test_client()


@pytest.fixture(scope="module")
def available_kbs():
    return list(get_all_collections().keys())


class TestDeepResearch:
    """Comprehensive test of deep research across all knowledge bases."""

    research_result = None
    test_chat_id = None

    def test_execute_deep_research(self, research_client, available_kbs):
        """Execute deep research query across ALL knowledge bases."""
        start_time = time.time()

        response = research_client.post(
            "/research_query",
            json={"query": TEST_QUERY, "model": TEST_MODEL},
            content_type="application/json",
        )
        elapsed = time.time() - start_time

        assert response.status_code == 200, f"Research query should return 200, got {response.status_code}"

        data = response.get_json()
        assert data is not None
        assert "kb_results" in data
        assert "synthesized_answer" in data
        assert "total_sources" in data

        TestDeepResearch.research_result = data

    def test_analyze_kb_results(self, available_kbs):
        """Analyze results from each knowledge base."""
        if TestDeepResearch.research_result is None:
            pytest.skip("Research query did not complete")

        data = TestDeepResearch.research_result
        kb_results = data.get("kb_results", [])

        assert len(kb_results) == len(available_kbs), (
            f"Should have results from all {len(available_kbs)} KBs"
        )

        successful = [r for r in kb_results if r.get("success")]
        failed = [r for r in kb_results if not r.get("success")]

        print(f"\nKB Results: {len(successful)} successful, {len(failed)} failed")
        for r in kb_results:
            status = "OK" if r.get("success") else "FAIL"
            print(f"  [{status}] {r.get('kb_key')}: {r.get('doc_count', 0)} docs")

    def test_analyze_synthesized_answer(self):
        """Analyze the synthesized answer."""
        if TestDeepResearch.research_result is None:
            pytest.skip("Research query did not complete")

        synthesized = TestDeepResearch.research_result.get("synthesized_answer", "")
        assert synthesized is not None
        assert len(synthesized) > 0

    def test_save_complete_research_chat(self, research_client):
        """Save the complete research results to all_chats.json."""
        if TestDeepResearch.research_result is None:
            pytest.skip("Research query did not complete")

        data = TestDeepResearch.research_result
        chat_id = f"test_deep_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        TestDeepResearch.test_chat_id = chat_id

        messages = [
            {"role": "user", "content": f"[DEEP RESEARCH] {TEST_QUERY}"},
            {
                "role": "assistant",
                "content": data.get("synthesized_answer", ""),
                "type": "synthesis",
            },
        ]

        for kb_result in data.get("kb_results", []):
            if kb_result.get("success") and kb_result.get("doc_count", 0) > 0:
                kb_response = kb_result.get("response", "")
                if kb_response and "no relevant documents" not in kb_response.lower():
                    messages.append({
                        "role": "assistant",
                        "content": kb_response,
                        "type": "kb_result",
                        "kb_key": kb_result.get("kb_key"),
                        "kb_name": kb_result.get("kb_name"),
                    })

        chat_data = {
            "id": chat_id,
            "title": f"Deep Research: {TEST_QUERY[:40]}...",
            "type": "deep_research",
            "model": TEST_MODEL,
            "query": TEST_QUERY,
            "timestamp": datetime.now().isoformat(),
            "messages": messages,
            "kb_results": data.get("kb_results", []),
            "synthesized_answer": data.get("synthesized_answer", ""),
            "total_sources": data.get("total_sources", 0),
            "total_time_ms": data.get("total_time_ms", 0),
            "success": data.get("success", False),
        }

        response = research_client.post(
            "/save_chat", json=chat_data, content_type="application/json"
        )
        assert response.status_code == 200
        assert response.get_json().get("success") is True

    def test_save_results_to_json(self):
        """Save research results to JSON file."""
        if TestDeepResearch.research_result is None:
            pytest.skip("Research query did not complete")

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = RESULTS_DIR / f"deep_research_{timestamp}.json"

        result_data = {
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "query": TEST_QUERY,
                "model": TEST_MODEL,
                "test_chat_id": TestDeepResearch.test_chat_id,
            },
            "research_result": TestDeepResearch.research_result,
        }

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)

        assert json_file.exists()
