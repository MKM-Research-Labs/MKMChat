# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/summary/summariser.py."""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

from src.summary.models import SummaryResult


@patch("src.summary.summariser.HuggingFaceEmbeddings")
@patch("src.summary.summariser.ensure_directory_exists")
@patch("src.summary.summariser.get_collection_config")
def test_summarise_document(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_summarize_single_document returns a SummaryResult with the LLM summary."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    json_dir = tmp_path / "json"
    json_dir.mkdir()

    # Create a dummy document
    doc_file = docs_dir / "test_book.pdf"
    doc_file.write_bytes(b"%PDF-1.4 fake")

    mock_get_config.return_value = {
        "name": "Test",
        "description": "test",
        "docs_folder": str(docs_dir),
        "faiss_index": str(tmp_path / "faiss"),
        "processed_file": str(json_dir / "processed.json"),
        "summary_file": str(json_dir / "summaries.json"),
    }
    mock_hf_embed.return_value = MagicMock()

    with patch("src.summary.summariser.CONFIG", {
        "embedding_model": "all-MiniLM-L6-v2",
        "default_max_docs": 100,
    }):
        from src.summary.summariser import DocumentSummariser
        summariser = DocumentSummariser(docs_type="misc")

    # Mock the FAISS chunk extraction and LLM call
    fake_chunks = [MagicMock(content="Some text", metadata={"page": 1})]

    with patch("src.summary.summariser.get_document_chunks_from_faiss", return_value=fake_chunks), \
         patch("src.summary.summariser.query_local_model_with_chunks", return_value="A great summary of the book."), \
         patch("src.summary.summariser.get_file_hash", return_value="hash_abc"):

        mock_vector_store = MagicMock()
        summarised_files = {}

        result = summariser._summarize_single_document(
            "test_book.pdf", mock_vector_store, summarised_files, force_reprocess=False
        )

    assert isinstance(result, SummaryResult)
    assert result.success is True
    assert result.status == "SUCCESS"
    assert result.summary == "A great summary of the book."
    assert "test_book.pdf" in summarised_files
    assert summarised_files["test_book.pdf"]["summary_type"] == "FULL"


@patch("src.summary.summariser.HuggingFaceEmbeddings")
@patch("src.summary.summariser.ensure_directory_exists")
@patch("src.summary.summariser.get_collection_config")
def test_summarise_skip_existing(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_summarize_single_document skips documents that already have a matching hash."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    json_dir = tmp_path / "json"
    json_dir.mkdir()

    doc_file = docs_dir / "existing.pdf"
    doc_file.write_bytes(b"%PDF-1.4 fake")

    mock_get_config.return_value = {
        "name": "Test", "description": "test",
        "docs_folder": str(docs_dir),
        "faiss_index": str(tmp_path / "faiss"),
        "processed_file": str(json_dir / "processed.json"),
        "summary_file": str(json_dir / "summaries.json"),
    }
    mock_hf_embed.return_value = MagicMock()

    with patch("src.summary.summariser.CONFIG", {
        "embedding_model": "all-MiniLM-L6-v2", "default_max_docs": 100,
    }):
        from src.summary.summariser import DocumentSummariser
        summariser = DocumentSummariser(docs_type="misc")

    with patch("src.summary.summariser.get_file_hash", return_value="same_hash"):
        summarised_files = {
            "existing.pdf": {"hash": "same_hash", "summary": "Old summary", "summary_type": "FULL"}
        }
        result = summariser._summarize_single_document(
            "existing.pdf", MagicMock(), summarised_files, force_reprocess=False
        )

    assert result.status == "SKIPPED"
    assert result.success is True


@patch("src.summary.summariser.HuggingFaceEmbeddings")
@patch("src.summary.summariser.ensure_directory_exists")
@patch("src.summary.summariser.get_collection_config")
def test_summarise_fallback(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_summarize_single_document falls back to basic summary when LLM fails."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    json_dir = tmp_path / "json"
    json_dir.mkdir()

    doc_file = docs_dir / "fallback.pdf"
    doc_file.write_bytes(b"%PDF-1.4 fake")

    mock_get_config.return_value = {
        "name": "Test", "description": "test",
        "docs_folder": str(docs_dir),
        "faiss_index": str(tmp_path / "faiss"),
        "processed_file": str(json_dir / "processed.json"),
        "summary_file": str(json_dir / "summaries.json"),
    }
    mock_hf_embed.return_value = MagicMock()

    with patch("src.summary.summariser.CONFIG", {
        "embedding_model": "all-MiniLM-L6-v2", "default_max_docs": 100,
    }):
        from src.summary.summariser import DocumentSummariser
        summariser = DocumentSummariser(docs_type="misc")

    # Chunks found but LLM returns None
    fake_chunks = [MagicMock(content="text", metadata={"page": 1})]
    with patch("src.summary.summariser.get_document_chunks_from_faiss", return_value=fake_chunks), \
         patch("src.summary.summariser.query_local_model_with_chunks", return_value=None), \
         patch("src.summary.summariser.get_file_hash", return_value="hash1"), \
         patch("src.summary.summariser.generate_basic_summary", return_value="Basic fallback text"):

        summarised_files = {}
        result = summariser._summarize_single_document(
            "fallback.pdf", MagicMock(), summarised_files, force_reprocess=False
        )

    assert result.status == "BASIC_FALLBACK"
    assert result.success is True
    assert summarised_files["fallback.pdf"]["summary_type"] == "BASIC_FALLBACK"


@patch("src.summary.summariser.HuggingFaceEmbeddings")
@patch("src.summary.summariser.ensure_directory_exists")
@patch("src.summary.summariser.get_collection_config")
def test_summarise_no_chunks_fallback(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_summarize_single_document falls back when no chunks found in FAISS."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    json_dir = tmp_path / "json"
    json_dir.mkdir()

    doc_file = docs_dir / "nochunks.pdf"
    doc_file.write_bytes(b"%PDF-1.4 fake")

    mock_get_config.return_value = {
        "name": "Test", "description": "test",
        "docs_folder": str(docs_dir),
        "faiss_index": str(tmp_path / "faiss"),
        "processed_file": str(json_dir / "processed.json"),
        "summary_file": str(json_dir / "summaries.json"),
    }
    mock_hf_embed.return_value = MagicMock()

    with patch("src.summary.summariser.CONFIG", {
        "embedding_model": "all-MiniLM-L6-v2", "default_max_docs": 100,
    }):
        from src.summary.summariser import DocumentSummariser
        summariser = DocumentSummariser(docs_type="misc")

    with patch("src.summary.summariser.get_document_chunks_from_faiss", return_value=[]), \
         patch("src.summary.summariser.get_file_hash", return_value="hash2"), \
         patch("src.summary.summariser.generate_basic_summary", return_value="Placeholder"):

        summarised_files = {}
        result = summariser._summarize_single_document(
            "nochunks.pdf", MagicMock(), summarised_files, force_reprocess=False
        )

    assert result.status == "BASIC_FALLBACK"


@patch("src.summary.summariser.HuggingFaceEmbeddings")
@patch("src.summary.summariser.ensure_directory_exists")
@patch("src.summary.summariser.get_collection_config")
def test_summarize_documents_no_vector_store(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """summarize_documents returns False when FAISS copy fails."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    json_dir = tmp_path / "json"
    json_dir.mkdir()

    mock_get_config.return_value = {
        "name": "Test", "description": "test",
        "docs_folder": str(docs_dir),
        "faiss_index": str(tmp_path / "faiss"),
        "processed_file": str(json_dir / "processed.json"),
        "summary_file": str(json_dir / "summaries.json"),
    }
    mock_hf_embed.return_value = MagicMock()

    with patch("src.summary.summariser.CONFIG", {
        "embedding_model": "all-MiniLM-L6-v2", "default_max_docs": 100,
    }):
        from src.summary.summariser import DocumentSummariser
        summariser = DocumentSummariser(docs_type="misc")

    with patch("src.summary.summariser.create_safe_faiss_copy", return_value=(None, None)):
        result = summariser.summarize_documents()

    assert result is False


@patch("src.summary.summariser.HuggingFaceEmbeddings")
@patch("src.summary.summariser.ensure_directory_exists")
@patch("src.summary.summariser.get_collection_config")
def test_load_processed_files(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """load_processed_files returns data from the processed files JSON."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    json_dir = tmp_path / "json"
    json_dir.mkdir()

    proc_file = json_dir / "processed.json"
    import json
    proc_file.write_text(json.dumps({"a.pdf": {"status": "SUCCESS"}}))

    mock_get_config.return_value = {
        "name": "Test", "description": "test",
        "docs_folder": str(docs_dir),
        "faiss_index": str(tmp_path / "faiss"),
        "processed_file": str(proc_file),
        "summary_file": str(json_dir / "summaries.json"),
    }
    mock_hf_embed.return_value = MagicMock()

    with patch("src.summary.summariser.CONFIG", {
        "embedding_model": "all-MiniLM-L6-v2", "default_max_docs": 100,
    }):
        from src.summary.summariser import DocumentSummariser
        summariser = DocumentSummariser(docs_type="misc")

    result = summariser.load_processed_files()
    assert "a.pdf" in result


def test_get_summariser():
    """get_summariser returns a DocumentSummariser instance."""
    with patch("src.summary.summariser.HuggingFaceEmbeddings") as mock_hf, \
         patch("src.summary.summariser.ensure_directory_exists"), \
         patch("src.summary.summariser.get_collection_config", return_value={
             "name": "Test", "description": "test",
             "docs_folder": "/tmp/docs", "faiss_index": "/tmp/faiss",
             "processed_file": "/tmp/proc.json", "summary_file": "/tmp/sum.json",
         }), \
         patch("src.summary.summariser.CONFIG", {
             "embedding_model": "all-MiniLM-L6-v2", "default_max_docs": 100,
         }):
        mock_hf.return_value = MagicMock()
        from src.summary.summariser import get_summariser
        s = get_summariser("misc")
        assert s.docs_type == "misc"


# ---------------------------------------------------------------------------
# Additional coverage: summarize_documents full path & _print_results
# ---------------------------------------------------------------------------


def _make_summariser(tmp_path, mock_get_config, mock_ensure_dir, mock_hf_embed):
    """Helper to construct a DocumentSummariser with mocked deps."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(exist_ok=True)
    json_dir = tmp_path / "json"
    json_dir.mkdir(exist_ok=True)

    mock_get_config.return_value = {
        "name": "Test", "description": "test",
        "docs_folder": str(docs_dir),
        "faiss_index": str(tmp_path / "faiss"),
        "processed_file": str(json_dir / "processed.json"),
        "summary_file": str(json_dir / "summaries.json"),
    }
    mock_hf_embed.return_value = MagicMock()

    with patch("src.summary.summariser.CONFIG", {
        "embedding_model": "all-MiniLM-L6-v2", "default_max_docs": 100,
    }):
        from src.summary.summariser import DocumentSummariser
        return DocumentSummariser(docs_type="misc"), docs_dir, json_dir


@patch("src.summary.summariser.HuggingFaceEmbeddings")
@patch("src.summary.summariser.ensure_directory_exists")
@patch("src.summary.summariser.get_collection_config")
def test_summarize_documents_success(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """summarize_documents processes docs end-to-end and returns True."""
    summariser, docs_dir, json_dir = _make_summariser(
        tmp_path, mock_get_config, mock_ensure_dir, mock_hf_embed
    )

    # Create dummy doc
    (docs_dir / "a.pdf").write_bytes(b"%PDF-1.4 content")

    # Write processed files
    proc_file = json_dir / "processed.json"
    proc_file.write_text(json.dumps({"a.pdf": {"status": "SUCCESS"}}))

    mock_vs = MagicMock()
    fake_chunks = [MagicMock(content="text", metadata={"page": 1})]

    with patch("src.summary.summariser.create_safe_faiss_copy", return_value=("/tmp/copy", mock_vs)), \
         patch("src.summary.summariser.cleanup_faiss_copy") as mock_cleanup, \
         patch("src.summary.summariser.load_json_file", side_effect=[{}, {"a.pdf": {"status": "SUCCESS"}}]), \
         patch("src.summary.summariser.save_json_file"), \
         patch("src.summary.summariser.get_document_chunks_from_faiss", return_value=fake_chunks), \
         patch("src.summary.summariser.query_local_model_with_chunks", return_value="Summary here"), \
         patch("src.summary.summariser.get_file_hash", return_value="hash1"):

        result = summariser.summarize_documents(max_docs=5, force_reprocess=False, clean=False)

    assert result is True
    mock_cleanup.assert_called_once_with("/tmp/copy")


@patch("src.summary.summariser.HuggingFaceEmbeddings")
@patch("src.summary.summariser.ensure_directory_exists")
@patch("src.summary.summariser.get_collection_config")
def test_summarize_documents_no_processed_files(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """summarize_documents returns False when no successfully processed docs exist."""
    summariser, docs_dir, json_dir = _make_summariser(
        tmp_path, mock_get_config, mock_ensure_dir, mock_hf_embed
    )

    mock_vs = MagicMock()
    with patch("src.summary.summariser.create_safe_faiss_copy", return_value=("/tmp/c", mock_vs)), \
         patch("src.summary.summariser.cleanup_faiss_copy"), \
         patch("src.summary.summariser.load_json_file", return_value={}):

        result = summariser.summarize_documents()

    assert result is False


@patch("src.summary.summariser.HuggingFaceEmbeddings")
@patch("src.summary.summariser.ensure_directory_exists")
@patch("src.summary.summariser.get_collection_config")
def test_summarize_documents_clean_mode(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """summarize_documents with clean=True starts with empty summaries."""
    summariser, docs_dir, json_dir = _make_summariser(
        tmp_path, mock_get_config, mock_ensure_dir, mock_hf_embed
    )
    (docs_dir / "b.pdf").write_bytes(b"%PDF-1.4")

    mock_vs = MagicMock()
    fake_chunks = [MagicMock(content="text", metadata={"page": 1})]

    load_calls = []
    original_load = None

    def mock_load(path, default=None):
        load_calls.append(path)
        # Second call is for processed files
        if len(load_calls) == 1:
            return {"b.pdf": {"status": "SUCCESS"}}
        return default or {}

    with patch("src.summary.summariser.create_safe_faiss_copy", return_value=("/tmp/c", mock_vs)), \
         patch("src.summary.summariser.cleanup_faiss_copy"), \
         patch("src.summary.summariser.load_json_file", side_effect=mock_load), \
         patch("src.summary.summariser.save_json_file"), \
         patch("src.summary.summariser.get_document_chunks_from_faiss", return_value=fake_chunks), \
         patch("src.summary.summariser.query_local_model_with_chunks", return_value="clean summary"), \
         patch("src.summary.summariser.get_file_hash", return_value="hash2"):

        result = summariser.summarize_documents(clean=True)

    assert result is True


@patch("src.summary.summariser.HuggingFaceEmbeddings")
@patch("src.summary.summariser.ensure_directory_exists")
@patch("src.summary.summariser.get_collection_config")
def test_summarize_documents_handles_single_doc_exception(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """summarize_documents catches per-document exceptions and continues."""
    summariser, docs_dir, json_dir = _make_summariser(
        tmp_path, mock_get_config, mock_ensure_dir, mock_hf_embed
    )

    mock_vs = MagicMock()

    def mock_load(path, default=None):
        # Return processed files with one doc
        return {"err.pdf": {"status": "SUCCESS"}}

    with patch("src.summary.summariser.create_safe_faiss_copy", return_value=("/tmp/c", mock_vs)), \
         patch("src.summary.summariser.cleanup_faiss_copy"), \
         patch("src.summary.summariser.load_json_file", side_effect=mock_load), \
         patch("src.summary.summariser.save_json_file"), \
         patch.object(summariser, "_summarize_single_document", side_effect=RuntimeError("parse error")):

        result = summariser.summarize_documents()

    # No successful docs, so returns False
    assert result is False


@patch("src.summary.summariser.HuggingFaceEmbeddings")
@patch("src.summary.summariser.ensure_directory_exists")
@patch("src.summary.summariser.get_collection_config")
def test_print_results(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path, capsys):
    """_print_results prints a summary table."""
    summariser, _, _ = _make_summariser(
        tmp_path, mock_get_config, mock_ensure_dir, mock_hf_embed
    )

    results = [
        SummaryResult(document_name="a.pdf", success=True, message="ok", status="SUCCESS"),
        SummaryResult(document_name="b.pdf", success=False, message="fail", status="FAILED"),
    ]
    summariser._print_results(results)

    captured = capsys.readouterr()
    assert "SUMMARIZATION RESULTS" in captured.out
    assert "a.pdf" in captured.out
    assert "b.pdf" in captured.out
    assert "1/2" in captured.out


@patch("src.summary.summariser.HuggingFaceEmbeddings")
@patch("src.summary.summariser.ensure_directory_exists")
@patch("src.summary.summariser.get_collection_config")
def test_summarize_documents_max_docs_truncation(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """summarize_documents truncates document list when max_docs is exceeded."""
    summariser, docs_dir, json_dir = _make_summariser(
        tmp_path, mock_get_config, mock_ensure_dir, mock_hf_embed
    )

    # Create 3 dummy docs
    for name in ["a.pdf", "b.pdf", "c.pdf"]:
        (docs_dir / name).write_bytes(b"%PDF-1.4")

    mock_vs = MagicMock()
    fake_chunks = [MagicMock(content="text", metadata={"page": 1})]

    processed = {
        "a.pdf": {"status": "SUCCESS"},
        "b.pdf": {"status": "SUCCESS"},
        "c.pdf": {"status": "SUCCESS"},
    }

    summarise_calls = []
    original_summarize = summariser._summarize_single_document

    def mock_summarize(doc_name, vs, sf, force_reprocess):
        summarise_calls.append(doc_name)
        return SummaryResult(document_name=doc_name, success=True, message="ok", status="SUCCESS")

    with patch("src.summary.summariser.create_safe_faiss_copy", return_value=("/tmp/c", mock_vs)), \
         patch("src.summary.summariser.cleanup_faiss_copy"), \
         patch("src.summary.summariser.load_json_file", side_effect=[{}, processed]), \
         patch("src.summary.summariser.save_json_file"), \
         patch.object(summariser, "_summarize_single_document", side_effect=mock_summarize):

        result = summariser.summarize_documents(max_docs=2, force_reprocess=False, clean=False)

    assert result is True
    # Only 2 docs should have been processed due to max_docs=2
    assert len(summarise_calls) == 2
