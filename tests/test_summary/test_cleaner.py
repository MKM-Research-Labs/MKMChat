# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/summary/cleaner.py."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.summary.cleaner import SummaryCleaner
from src.summary.models import CleaningStats


@pytest.fixture
def cleaner():
    """Create a SummaryCleaner with mocked config."""
    with patch("src.summary.cleaner.get_all_collections", return_value={
        "misc": {"name": "Misc", "description": "test"},
        "phys": {"name": "Phys", "description": "test"},
    }):
        return SummaryCleaner(base_dir="/tmp/test")


def test_clean_summary_text(cleaner):
    """_clean_fallback_only removes BASIC_FALLBACK entries and keeps FULL entries."""
    data = {
        "book_a.pdf": {"summary": "Good summary", "summary_type": "FULL"},
        "book_b.pdf": {"summary": "Placeholder", "summary_type": "BASIC_FALLBACK"},
        "book_c.pdf": {"summary": "Another good one", "summary_type": "FULL"},
    }

    cleaned, fallback_count = cleaner._clean_fallback_only(data)

    assert fallback_count == 1
    assert "book_a.pdf" in cleaned
    assert "book_c.pdf" in cleaned
    assert "book_b.pdf" not in cleaned
    assert len(cleaned) == 2


def test_batch_clean(cleaner, tmp_path):
    """clean_file processes a file and returns correct CleaningStats."""
    summary_file = tmp_path / "summaries.json"
    data = {
        "book1.pdf": {"summary": "ok", "summary_type": "FULL"},
        "book2.pdf": {"summary": "placeholder", "summary_type": "BASIC_FALLBACK"},
        "book3.pdf": {"summary": "placeholder2", "summary_type": "BASIC_FALLBACK"},
    }
    summary_file.write_text(json.dumps(data))

    with patch("src.summary.cleaner.ensure_file_exists"):
        stats = cleaner.clean_file(summary_file, "misc", "fallback_only")

    assert isinstance(stats, CleaningStats)
    assert stats.total_before == 3
    assert stats.total_after == 1
    assert stats.removed_count == 2

    # Verify the file was actually cleaned
    result = json.loads(summary_file.read_text())
    assert "book1.pdf" in result
    assert "book2.pdf" not in result
    assert "book3.pdf" not in result


def test_clean_force_all(cleaner):
    """_clean_force_all modifies hashes to force reprocessing."""
    data = {
        "book_a.pdf": {"hash": "abc123", "summary_type": "FULL"},
        "book_b.pdf": {"hash": "def456", "summary_type": "FULL"},
    }
    result = cleaner._clean_force_all(data)

    assert result["book_a.pdf"]["hash"].startswith("modified_")
    assert result["book_b.pdf"]["hash"].startswith("modified_")
    # Original data should not be modified
    assert data["book_a.pdf"]["hash"] == "abc123"


def test_clean_all(cleaner):
    """_clean_all returns an empty dictionary."""
    data = {"book.pdf": {"summary": "text", "summary_type": "FULL"}}
    result = cleaner._clean_all(data)
    assert result == {}


def test_clean_file_clean_all_mode(cleaner, tmp_path):
    """clean_file with clean_all mode removes all entries."""
    summary_file = tmp_path / "summaries.json"
    data = {
        "book1.pdf": {"summary": "ok", "summary_type": "FULL"},
        "book2.pdf": {"summary": "ok2", "summary_type": "FULL"},
    }
    summary_file.write_text(json.dumps(data))

    with patch("src.summary.cleaner.ensure_file_exists"):
        stats = cleaner.clean_file(summary_file, "misc", "clean_all")

    assert stats.total_before == 2
    assert stats.total_after == 0
    assert stats.removed_count == 2


def test_clean_file_force_all_mode(cleaner, tmp_path):
    """clean_file with force_all mode modifies hashes but keeps entries."""
    summary_file = tmp_path / "summaries.json"
    data = {"book1.pdf": {"hash": "h1", "summary_type": "FULL"}}
    summary_file.write_text(json.dumps(data))

    with patch("src.summary.cleaner.ensure_file_exists"):
        stats = cleaner.clean_file(summary_file, "misc", "force_all")

    assert stats.total_before == 1
    assert stats.total_after == 1
    assert stats.removed_count == 0

    result = json.loads(summary_file.read_text())
    assert result["book1.pdf"]["hash"].startswith("modified_")


def test_clean_file_invalid_mode(cleaner, tmp_path):
    """clean_file raises ValueError for unknown mode."""
    summary_file = tmp_path / "summaries.json"
    summary_file.write_text("{}")

    with patch("src.summary.cleaner.ensure_file_exists"):
        with pytest.raises(ValueError, match="Unknown cleaning mode"):
            cleaner.clean_file(summary_file, "misc", "invalid_mode")


def test_clean_method_validates_mode(cleaner):
    """clean() raises ValueError for invalid mode."""
    with pytest.raises(ValueError, match="Invalid mode"):
        cleaner.clean(mode="bad_mode")


def test_clean_method_validates_docs_type(cleaner):
    """clean() raises ValueError for invalid docs_type."""
    with pytest.raises(ValueError, match="Invalid docs_type"):
        cleaner.clean(docs_type="nonexistent")


def test_clean_method_processes_files(cleaner, tmp_path):
    """clean() processes files returned by get_files_to_process."""
    summary_file = tmp_path / "summaries.json"
    data = {"book.pdf": {"summary": "x", "summary_type": "BASIC_FALLBACK"}}
    summary_file.write_text(json.dumps(data))

    with patch("src.summary.cleaner.get_files_to_process", return_value=[("misc", summary_file)]), \
         patch("src.summary.cleaner.ensure_file_exists"):
        results = cleaner.clean(docs_type="misc", mode="fallback_only")

    assert "misc" in results
    assert results["misc"].removed_count == 1


def test_clean_method_handles_exception(cleaner, tmp_path):
    """clean() catches exceptions and stores error in results."""
    with patch("src.summary.cleaner.get_files_to_process", return_value=[("misc", tmp_path / "bad.json")]), \
         patch("src.summary.cleaner.ensure_file_exists", side_effect=RuntimeError("boom")):
        results = cleaner.clean(docs_type="misc", mode="fallback_only")

    assert results["misc"].error is not None


def test_get_stats(cleaner, tmp_path):
    """get_stats returns correct statistics for summary files."""
    summary_file = tmp_path / "summaries.json"
    data = {
        "a.pdf": {"summary_type": "FULL"},
        "b.pdf": {"summary_type": "BASIC_FALLBACK"},
        "c.pdf": {"summary_type": "FULL"},
    }
    summary_file.write_text(json.dumps(data))

    with patch("src.summary.cleaner.get_files_to_process", return_value=[("misc", summary_file)]), \
         patch("src.summary.cleaner.ensure_file_exists"):
        stats = cleaner.get_stats(docs_type="misc")

    assert stats["misc"]["total_entries"] == 3
    assert stats["misc"]["fallback_entries"] == 1
    assert stats["misc"]["processed_entries"] == 2


def test_get_stats_handles_error(cleaner):
    """get_stats records error for problematic files."""
    with patch("src.summary.cleaner.get_files_to_process", return_value=[("misc", Path("/nonexistent"))]), \
         patch("src.summary.cleaner.ensure_file_exists", side_effect=RuntimeError("fail")):
        stats = cleaner.get_stats(docs_type="misc")

    assert "error" in stats["misc"]


def test_run_cleaner_stats_only():
    """run_cleaner with stats_only=True returns 0."""
    from src.summary.cleaner import run_cleaner

    with patch("src.summary.cleaner.get_all_collections", return_value={
        "misc": {"name": "Misc", "description": "test"},
    }), patch.object(
        __import__("src.summary.cleaner", fromlist=["SummaryCleaner"]).SummaryCleaner,
        "get_stats",
        return_value={"misc": {"total_entries": 5, "fallback_entries": 1, "processed_entries": 4, "file_path": "/tmp/f"}},
    ):
        result = run_cleaner(stats_only=True)
    assert result == 0


def test_run_cleaner_clean():
    """run_cleaner without stats_only runs cleaning and returns 0."""
    from src.summary.cleaner import run_cleaner

    with patch("src.summary.cleaner.get_all_collections", return_value={
        "misc": {"name": "Misc", "description": "test"},
    }), patch.object(
        __import__("src.summary.cleaner", fromlist=["SummaryCleaner"]).SummaryCleaner,
        "clean",
        return_value={"misc": CleaningStats(total_before=3, total_after=2, removed_count=1)},
    ):
        result = run_cleaner(mode="fallback_only")
    assert result == 0


def test_run_cleaner_stats_with_error():
    """run_cleaner stats_only prints error for collections with errors."""
    from src.summary.cleaner import run_cleaner

    with patch("src.summary.cleaner.get_all_collections", return_value={
        "misc": {"name": "Misc", "description": "test"},
    }), patch.object(
        __import__("src.summary.cleaner", fromlist=["SummaryCleaner"]).SummaryCleaner,
        "get_stats",
        return_value={"misc": {"error": "file not found"}},
    ):
        result = run_cleaner(stats_only=True)
    assert result == 0


def test_run_cleaner_clean_with_errors():
    """run_cleaner prints error count when some files have errors."""
    from src.summary.cleaner import run_cleaner

    error_stats = CleaningStats(total_before=0, total_after=0, removed_count=0, error="boom")
    with patch("src.summary.cleaner.get_all_collections", return_value={
        "misc": {"name": "Misc", "description": "test"},
    }), patch.object(
        __import__("src.summary.cleaner", fromlist=["SummaryCleaner"]).SummaryCleaner,
        "clean",
        return_value={"misc": error_stats},
    ):
        result = run_cleaner(mode="fallback_only")
    assert result == 0
