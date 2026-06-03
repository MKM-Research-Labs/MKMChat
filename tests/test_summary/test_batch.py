# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/summary/batch.py."""

import pytest
from unittest.mock import patch, MagicMock

from src.summary.batch import process_single_collection
from src.summary.models import ProcessingStats


@patch("src.summary.batch.get_collection_config")
@patch("src.summary.batch.get_paths")
@patch("src.summary.batch.load_faiss_index")
@patch("src.summary.batch.load_json_file")
@patch("src.summary.batch.save_json_file")
@patch("src.summary.batch.call_llm_for_summary")
@patch("src.summary.batch.search_book_content")
def test_batch_process_skips_already_done(
    mock_search, mock_llm, mock_save, mock_load_json, mock_load_faiss,
    mock_get_paths, mock_get_config
):
    """Books that already have summaries are skipped in batch processing."""
    mock_get_config.return_value = {
        "name": "Test Collection",
        "description": "test",
        "docs_folder": "/tmp/docs",
        "faiss_index": "/tmp/faiss",
        "processed_file": "/tmp/processed.json",
        "summary_file": "/tmp/summaries.json",
    }
    mock_get_paths.return_value = {
        "faiss_index": "/tmp/faiss/index.faiss",
        "faiss_pkl": "/tmp/faiss/index.pkl",
        "proc_files": "/tmp/processed.json",
        "output_file": "/tmp/summaries.json",
    }
    mock_load_faiss.return_value = (MagicMock(), MagicMock())

    # Two books in processed files
    proc_files = {"bookA.pdf": {"status": "SUCCESS"}, "bookB.pdf": {"status": "SUCCESS"}}
    # bookA already summarised
    existing_summaries = {"bookA.pdf": {"summary": "Already done", "summary_type": "FULL"}}

    # load_json_file is called twice: once for proc_files, once for existing_summaries
    mock_load_json.side_effect = [proc_files, existing_summaries]

    # Only bookB needs summarising
    mock_search.return_value = "Some context"
    mock_llm.return_value = "Summary for book B"

    mock_embedding_model = MagicMock()

    stats = process_single_collection("misc", mock_embedding_model)

    assert isinstance(stats, ProcessingStats)
    assert stats.skipped == 1  # bookA was skipped
    assert stats.successful == 1  # bookB was summarised
    # LLM should only have been called once (for bookB)
    mock_llm.assert_called_once()


@patch("src.summary.batch.get_collection_config")
@patch("src.summary.batch.get_paths")
@patch("src.summary.batch.load_faiss_index")
@patch("src.summary.batch.load_json_file")
def test_batch_process_faiss_load_failure(
    mock_load_json, mock_load_faiss, mock_get_paths, mock_get_config
):
    """process_single_collection returns error stats when FAISS load fails."""
    mock_get_config.return_value = {
        "name": "Test", "description": "test",
        "docs_folder": "/tmp/docs", "faiss_index": "/tmp/faiss",
        "processed_file": "/tmp/proc.json", "summary_file": "/tmp/sum.json",
    }
    mock_get_paths.return_value = {
        "faiss_index": "/tmp/faiss/index.faiss", "faiss_pkl": "/tmp/faiss/index.pkl",
        "proc_files": "/tmp/proc.json", "output_file": "/tmp/sum.json",
    }
    mock_load_faiss.return_value = (None, None)

    stats = process_single_collection("misc", MagicMock())

    assert stats.error == "Failed to load FAISS index"


@patch("src.summary.batch.get_collection_config")
@patch("src.summary.batch.get_paths")
@patch("src.summary.batch.load_faiss_index")
@patch("src.summary.batch.load_json_file")
def test_batch_process_no_proc_files(
    mock_load_json, mock_load_faiss, mock_get_paths, mock_get_config
):
    """process_single_collection returns error when no processed files found."""
    mock_get_config.return_value = {
        "name": "Test", "description": "test",
        "docs_folder": "/tmp/docs", "faiss_index": "/tmp/faiss",
        "processed_file": "/tmp/proc.json", "summary_file": "/tmp/sum.json",
    }
    mock_get_paths.return_value = {
        "faiss_index": "/tmp/faiss/index.faiss", "faiss_pkl": "/tmp/faiss/index.pkl",
        "proc_files": "/tmp/proc.json", "output_file": "/tmp/sum.json",
    }
    mock_load_faiss.return_value = (MagicMock(), MagicMock())
    mock_load_json.side_effect = [{}, {}]  # empty proc_files

    stats = process_single_collection("misc", MagicMock())
    assert stats.error == "No processed files found"


@patch("src.summary.batch.get_collection_config")
@patch("src.summary.batch.get_paths")
@patch("src.summary.batch.load_faiss_index")
@patch("src.summary.batch.load_json_file")
@patch("src.summary.batch.save_json_file")
@patch("src.summary.batch.call_llm_for_summary")
@patch("src.summary.batch.search_book_content")
def test_batch_process_llm_failure(
    mock_search, mock_llm, mock_save, mock_load_json, mock_load_faiss,
    mock_get_paths, mock_get_config
):
    """Books where LLM fails are counted as failed."""
    mock_get_config.return_value = {
        "name": "Test", "description": "test",
        "docs_folder": "/tmp/docs", "faiss_index": "/tmp/faiss",
        "processed_file": "/tmp/proc.json", "summary_file": "/tmp/sum.json",
    }
    mock_get_paths.return_value = {
        "faiss_index": "/tmp/faiss/index.faiss", "faiss_pkl": "/tmp/faiss/index.pkl",
        "proc_files": "/tmp/proc.json", "output_file": "/tmp/sum.json",
    }
    mock_load_faiss.return_value = (MagicMock(), MagicMock())
    mock_load_json.side_effect = [
        {"book.pdf": {"status": "SUCCESS"}},
        {},  # no existing summaries
    ]
    mock_search.return_value = "Some context"
    mock_llm.return_value = None  # LLM fails

    stats = process_single_collection("misc", MagicMock())
    assert stats.failed == 1
    assert stats.successful == 0


@patch("src.summary.batch.get_collection_config")
@patch("src.summary.batch.get_paths")
@patch("src.summary.batch.load_faiss_index")
@patch("src.summary.batch.load_json_file")
@patch("src.summary.batch.search_book_content")
def test_batch_process_no_context(
    mock_search, mock_load_json, mock_load_faiss, mock_get_paths, mock_get_config
):
    """Books with no relevant context are counted as failed."""
    mock_get_config.return_value = {
        "name": "Test", "description": "test",
        "docs_folder": "/tmp/docs", "faiss_index": "/tmp/faiss",
        "processed_file": "/tmp/proc.json", "summary_file": "/tmp/sum.json",
    }
    mock_get_paths.return_value = {
        "faiss_index": "/tmp/faiss/index.faiss", "faiss_pkl": "/tmp/faiss/index.pkl",
        "proc_files": "/tmp/proc.json", "output_file": "/tmp/sum.json",
    }
    mock_load_faiss.return_value = (MagicMock(), MagicMock())
    mock_load_json.side_effect = [
        {"book.pdf": {"status": "SUCCESS"}},
        {},
    ]
    mock_search.return_value = ""  # No context found

    stats = process_single_collection("misc", MagicMock())
    assert stats.failed == 1


@patch("src.summary.batch.get_collection_config")
@patch("src.summary.batch.get_paths")
@patch("src.summary.batch.load_faiss_index")
@patch("src.summary.batch.load_json_file")
def test_batch_all_already_done(
    mock_load_json, mock_load_faiss, mock_get_paths, mock_get_config
):
    """process_single_collection returns early when all books are already summarised."""
    mock_get_config.return_value = {
        "name": "Test", "description": "test",
        "docs_folder": "/tmp/docs", "faiss_index": "/tmp/faiss",
        "processed_file": "/tmp/proc.json", "summary_file": "/tmp/sum.json",
    }
    mock_get_paths.return_value = {
        "faiss_index": "/tmp/faiss/index.faiss", "faiss_pkl": "/tmp/faiss/index.pkl",
        "proc_files": "/tmp/proc.json", "output_file": "/tmp/sum.json",
    }
    mock_load_faiss.return_value = (MagicMock(), MagicMock())
    mock_load_json.side_effect = [
        {"bookA.pdf": {}},
        {"bookA.pdf": {"summary": "Done"}},
    ]

    stats = process_single_collection("misc", MagicMock())
    assert stats.skipped == 1
    assert stats.successful == 0


def test_run_batch_processor_list_only():
    """run_batch_processor with list_only=True returns 0 and does not process."""
    from src.summary.batch import run_batch_processor

    with patch("src.summary.batch.get_all_collections", return_value={
        "misc": {"name": "Misc", "description": "test"},
    }):
        result = run_batch_processor(list_only=True)
    assert result == 0


def test_run_batch_processor_embedding_failure():
    """run_batch_processor returns 1 when embedding model fails to load."""
    from src.summary.batch import run_batch_processor

    with patch("src.summary.batch.get_all_collections", return_value={
        "misc": {"name": "Misc", "description": "test"},
    }), patch("src.summary.batch.initialize_embedding_model", return_value=None):
        result = run_batch_processor(collections=["misc"])
    assert result == 1


def test_run_batch_processor_all_errors():
    """run_batch_processor returns 1 when all collections error."""
    from src.summary.batch import run_batch_processor

    error_stats = ProcessingStats(collection="misc", name="Misc", error="fail")

    with patch("src.summary.batch.get_all_collections", return_value={
        "misc": {"name": "Misc", "description": "test"},
    }), patch("src.summary.batch.initialize_embedding_model", return_value=MagicMock()), \
         patch("src.summary.batch.process_single_collection", return_value=error_stats):
        result = run_batch_processor(collections=["misc"])
    assert result == 1


def test_run_batch_processor_success():
    """run_batch_processor returns 0 when at least one collection succeeds."""
    from src.summary.batch import run_batch_processor

    ok_stats = ProcessingStats(collection="misc", name="Misc", successful=1)

    with patch("src.summary.batch.get_all_collections", return_value={
        "misc": {"name": "Misc", "description": "test"},
    }), patch("src.summary.batch.initialize_embedding_model", return_value=MagicMock()), \
         patch("src.summary.batch.process_single_collection", return_value=ok_stats):
        result = run_batch_processor(collections=["misc"])
    assert result == 0


def test_initialize_embedding_model_failure():
    """initialize_embedding_model returns None when model loading fails."""
    from src.summary.batch import initialize_embedding_model
    import importlib

    # Patch the import inside the function by making SentenceTransformer raise
    with patch.dict("sys.modules", {"sentence_transformers": MagicMock(
        SentenceTransformer=MagicMock(side_effect=RuntimeError("no GPU"))
    )}):
        result = initialize_embedding_model()
    assert result is None


def test_initialize_embedding_model_success():
    """initialize_embedding_model returns a model on success."""
    from src.summary.batch import initialize_embedding_model

    mock_model = MagicMock()
    with patch.dict("sys.modules", {"sentence_transformers": MagicMock(
        SentenceTransformer=MagicMock(return_value=mock_model)
    )}):
        result = initialize_embedding_model()
    assert result is mock_model


def test_run_batch_processor_collections_none():
    """run_batch_processor with collections=None processes all collections."""
    from src.summary.batch import run_batch_processor

    ok_stats = ProcessingStats(collection="misc", name="Misc", successful=1)

    with patch("src.summary.batch.get_all_collections", return_value={
        "misc": {"name": "Misc", "description": "test"},
    }), patch("src.summary.batch.initialize_embedding_model", return_value=MagicMock()), \
         patch("src.summary.batch.process_single_collection", return_value=ok_stats):
        result = run_batch_processor(collections=None)
    assert result == 0


def test_run_batch_processor_collection_exception():
    """run_batch_processor handles exception from process_single_collection."""
    from src.summary.batch import run_batch_processor

    with patch("src.summary.batch.get_all_collections", return_value={
        "misc": {"name": "Misc", "description": "test"},
    }), patch("src.summary.batch.initialize_embedding_model", return_value=MagicMock()), \
         patch("src.summary.batch.process_single_collection", side_effect=RuntimeError("boom")):
        result = run_batch_processor(collections=["misc"])
    assert result == 1


def test_print_batch_summary_with_failures():
    """_print_batch_summary prints warning when there are failed books."""
    from src.summary.batch import _print_batch_summary

    results = [
        ProcessingStats(collection="misc", name="Misc", successful=1, failed=2, total_books=3),
    ]
    # Should not raise, just prints
    _print_batch_summary(results)
