# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/research/handler.py (ResearchQueryHandler)."""

import json
from unittest.mock import MagicMock, patch

from src.research.handler import ResearchQueryHandler
from src.research.models import KBQueryResult


def _make_mock_app():
    """Create a mock app instance with AVAILABLE_INDICES and handlers."""
    app = MagicMock()
    app.AVAILABLE_INDICES = {
        "misc": {"name": "Miscellaneous", "path": "/tmp/faiss/misc"},
        "phys": {"name": "Physical", "path": "/tmp/faiss/phys"},
    }
    app.vector_stores = {
        "misc": MagicMock(),
        "phys": MagicMock(),
    }
    return app


def _make_kb_result(kb_key, kb_name, success=True, response="Answer text", doc_count=3):
    """Helper to create a KBQueryResult."""
    return KBQueryResult(
        kb_key=kb_key,
        kb_name=kb_name,
        success=success,
        response=response,
        sources=[{"file": "doc.pdf", "page": "1", "kb": kb_key}] if success else [],
        doc_count=doc_count,
        query_time_ms=50,
    )


class TestFormatSSEEvent:
    """Tests for _format_sse_event."""

    def test_format_sse_event(self):
        app = _make_mock_app()
        handler = ResearchQueryHandler(app)
        event = handler._format_sse_event("start", {"query": "test"})
        assert event.startswith("event: start\n")
        assert '"query": "test"' in event
        assert event.endswith("\n\n")


class TestExecuteResearchQueryStreaming:
    """Tests for execute_research_query_streaming (happy path)."""

    def test_streaming_produces_expected_events(self):
        app = _make_mock_app()

        kb_result_misc = _make_kb_result("misc", "Miscellaneous")
        kb_result_phys = _make_kb_result("phys", "Physical")

        with patch(
            "src.research.handler.KBQueryExecutor"
        ) as MockKBExec, patch(
            "src.research.handler.ResponseSynthesizer"
        ) as MockSynth:
            mock_kb_exec = MockKBExec.return_value
            mock_kb_exec.query_single_kb.side_effect = [kb_result_misc, kb_result_phys]

            mock_synth = MockSynth.return_value
            mock_synth.synthesize.return_value = "Synthesized answer across KBs."

            handler = ResearchQueryHandler(app)

            events = list(handler.execute_research_query_streaming(
                "What is flood risk?", "claude-sonnet-4-5-20250929"
            ))

        # Should have: start, querying, kb_complete, querying, kb_complete, synthesizing, complete
        event_types = []
        for ev in events:
            for line in ev.strip().split("\n"):
                if line.startswith("event: "):
                    event_types.append(line.replace("event: ", ""))

        assert event_types[0] == "start"
        assert "querying" in event_types
        assert "kb_complete" in event_types
        assert "synthesizing" in event_types
        assert event_types[-1] == "complete"

        # Parse the complete event data
        complete_event = events[-1]
        data_line = complete_event.split("data: ")[1].strip()
        result = json.loads(data_line)
        assert result["success"] is True
        assert result["query"] == "What is flood risk?"
        assert len(result["kb_results"]) == 2

    def test_streaming_with_specific_kb_keys(self):
        """Passing kb_keys should only query those KBs."""
        app = _make_mock_app()

        kb_result = _make_kb_result("misc", "Miscellaneous")

        with patch(
            "src.research.handler.KBQueryExecutor"
        ) as MockKBExec, patch(
            "src.research.handler.ResponseSynthesizer"
        ) as MockSynth:
            mock_kb_exec = MockKBExec.return_value
            mock_kb_exec.query_single_kb.return_value = kb_result

            mock_synth = MockSynth.return_value
            mock_synth.synthesize.return_value = "Answer from misc only."

            handler = ResearchQueryHandler(app)

            events = list(handler.execute_research_query_streaming(
                "test query", "sonar-pro", kb_keys=["misc"]
            ))

        # Only one KB queried
        mock_kb_exec.query_single_kb.assert_called_once_with("test query", "misc", "sonar-pro")


class TestExecuteResearchQuery:
    """Tests for execute_research_query (non-streaming wrapper)."""

    def test_non_streaming_returns_research_result(self):
        app = _make_mock_app()

        kb_result = _make_kb_result("misc", "Miscellaneous")

        with patch(
            "src.research.handler.KBQueryExecutor"
        ) as MockKBExec, patch(
            "src.research.handler.ResponseSynthesizer"
        ) as MockSynth:
            mock_kb_exec = MockKBExec.return_value
            mock_kb_exec.query_single_kb.return_value = kb_result

            mock_synth = MockSynth.return_value
            mock_synth.synthesize.return_value = "Final answer."

            handler = ResearchQueryHandler(app)

            result = handler.execute_research_query(
                "test query", "claude-sonnet-4-5-20250929", kb_keys=["misc"]
            )

        assert result is not None
        assert result.query == "test query"
        assert result.success is True
        assert len(result.kb_results) == 1

    def test_non_streaming_all_failed_kbs(self):
        """When all KBs fail, success should be False."""
        app = _make_mock_app()

        failed_result = _make_kb_result("misc", "Miscellaneous", success=False, response="", doc_count=0)

        with patch(
            "src.research.handler.KBQueryExecutor"
        ) as MockKBExec, patch(
            "src.research.handler.ResponseSynthesizer"
        ) as MockSynth:
            mock_kb_exec = MockKBExec.return_value
            mock_kb_exec.query_single_kb.return_value = failed_result

            mock_synth = MockSynth.return_value
            mock_synth.synthesize.return_value = "No info found."

            handler = ResearchQueryHandler(app)

            result = handler.execute_research_query(
                "test query", "sonar-pro", kb_keys=["misc"]
            )

        assert result is not None
        assert result.success is False
