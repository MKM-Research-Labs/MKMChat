# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/proc/processor.py."""

import os
import json
import pytest
from unittest.mock import patch, MagicMock


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_processor_init(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """DocumentProcessor initialises with the given collection type."""
    mock_get_config.return_value = {
        "name": "Test",
        "description": "test",
        "docs_folder": str(tmp_path / "docs"),
        "faiss_index": str(tmp_path / "faiss"),
        "processed_file": str(tmp_path / "json" / "processed.json"),
        "summary_file": str(tmp_path / "json" / "summaries.json"),
    }
    mock_hf_embed.return_value = MagicMock()

    with patch("src.proc.processor.CONFIG", {
        "embedding_model": "all-MiniLM-L6-v2",
        "chunk_size": 500,
        "chunk_overlap": 50,
        "default_max_docs": 100,
    }):
        from src.proc.processor import DocumentProcessor
        proc = DocumentProcessor(docs_type="misc")

    assert proc.docs_type == "misc"
    assert proc.docs_folder == str(tmp_path / "docs")
    mock_hf_embed.assert_called_once()


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_skip_already_processed(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """Files whose hash matches the tracking record are skipped."""
    json_dir = tmp_path / "json"
    json_dir.mkdir(parents=True, exist_ok=True)
    processed_path = json_dir / "processed.json"

    mock_get_config.return_value = {
        "name": "Test",
        "description": "test",
        "docs_folder": str(tmp_path / "docs"),
        "faiss_index": str(tmp_path / "faiss"),
        "processed_file": str(processed_path),
        "summary_file": str(json_dir / "summaries.json"),
    }
    mock_hf_embed.return_value = MagicMock()

    # Create a docs directory with a PDF
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    pdf = docs_dir / "test.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    # Write a tracking file that claims test.pdf is already processed with matching hash
    file_hash = str(os.path.getmtime(str(pdf)))
    processed_data = {
        "test.pdf": {
            "hash": file_hash,
            "status": "SUCCESS",
            "num_chunks": 5,
        }
    }
    processed_path.write_text(json.dumps(processed_data))

    with patch("src.proc.processor.CONFIG", {
        "embedding_model": "all-MiniLM-L6-v2",
        "chunk_size": 500,
        "chunk_overlap": 50,
        "default_max_docs": 100,
    }):
        from src.proc.processor import DocumentProcessor
        proc = DocumentProcessor(docs_type="misc")

    # process_single_document should return None (skip) when hash matches
    processed_files = proc.load_processed_files()
    with patch.object(proc.document_handler, "process", wraps=proc.document_handler.process) as mock_process, \
         patch("src.proc.document_handler.get_file_hash", return_value=file_hash):
        result = proc.process_single_document("test.pdf", processed_files)

    # The document handler returns None for already-processed files
    assert result is None


def _make_processor(mock_get_config, mock_hf_embed, tmp_path):
    """Helper to create a mocked DocumentProcessor."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    json_dir = tmp_path / "json"
    json_dir.mkdir(parents=True, exist_ok=True)
    faiss_dir = tmp_path / "faiss"
    faiss_dir.mkdir(parents=True, exist_ok=True)

    mock_get_config.return_value = {
        "name": "Test", "description": "test",
        "docs_folder": str(docs_dir),
        "faiss_index": str(faiss_dir),
        "processed_file": str(json_dir / "processed.json"),
        "summary_file": str(json_dir / "summaries.json"),
    }
    mock_hf_embed.return_value = MagicMock()

    with patch("src.proc.processor.CONFIG", {
        "embedding_model": "all-MiniLM-L6-v2",
        "chunk_size": 500, "chunk_overlap": 50, "default_max_docs": 100,
    }):
        from src.proc.processor import DocumentProcessor
        return DocumentProcessor(docs_type="misc")


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_process_documents_no_files(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """process_documents returns False when no supported files are found."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    with patch("src.proc.processor.get_supported_files", return_value=[]):
        result = proc.process_documents()

    assert result is False


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_process_documents_all_up_to_date(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """process_documents returns True when all files are already processed."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    # Create a doc
    docs_dir = tmp_path / "docs"
    (docs_dir / "test.pdf").write_bytes(b"%PDF")

    with patch("src.proc.processor.get_supported_files", return_value=["test.pdf"]), \
         patch("src.proc.processor.get_file_hash", return_value="hash1"), \
         patch("src.proc.processor.load_json_file", return_value={
             "test.pdf": {"hash": "hash1", "status": "SUCCESS"}
         }), \
         patch("src.proc.processor.save_json_file"):
        result = proc.process_documents()

    assert result is True


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_get_files_needing_processing(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_get_files_needing_processing identifies files with changed hashes."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    docs_dir = tmp_path / "docs"
    (docs_dir / "a.pdf").write_bytes(b"%PDF")
    (docs_dir / "b.pdf").write_bytes(b"%PDF")

    processed_files = {"a.pdf": {"hash": "old_hash"}}

    with patch("src.proc.processor.get_file_hash", return_value="new_hash"):
        result = proc._get_files_needing_processing(
            ["a.pdf", "b.pdf"], processed_files, False
        )

    # Both should need processing: a.pdf hash changed, b.pdf is new
    assert "a.pdf" in result
    assert "b.pdf" in result


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_get_files_needing_processing_force(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_get_files_needing_processing returns all files when force_reprocess is True."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    with patch("src.proc.processor.get_file_hash", return_value="hash1"):
        result = proc._get_files_needing_processing(
            ["a.pdf"], {"a.pdf": {"hash": "hash1"}}, True
        )

    assert result == ["a.pdf"]


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_apply_document_limit(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_apply_document_limit truncates the file list when max_documents is set."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)
    proc.max_documents = 2

    files = ["a.pdf", "b.pdf", "c.pdf", "d.pdf"]
    result = proc._apply_document_limit(files)
    assert len(result) == 2


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_apply_document_limit_none(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_apply_document_limit returns all files when max_documents is None."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)
    proc.max_documents = None

    files = ["a.pdf", "b.pdf", "c.pdf"]
    result = proc._apply_document_limit(files)
    assert len(result) == 3


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_cleanup_processed_files(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_cleanup_processed_files removes records for deleted files."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    docs_dir = tmp_path / "docs"
    (docs_dir / "still_here.pdf").write_bytes(b"%PDF")
    # "gone.pdf" doesn't exist on disk

    processed_files = {
        "still_here.pdf": {"hash": "h1"},
        "gone.pdf": {"hash": "h2"},
    }

    with patch.object(proc, "save_processed_files") as mock_save:
        proc._cleanup_processed_files(processed_files)
        saved = mock_save.call_args[0][0]
        assert "still_here.pdf" in saved
        assert "gone.pdf" not in saved


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_save_processed_files(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """save_processed_files delegates to save_json_file."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    with patch("src.proc.processor.save_json_file") as mock_save:
        proc.save_processed_files({"a.pdf": {"hash": "h"}})
        mock_save.assert_called_once()


def test_get_processor():
    """get_processor returns a DocumentProcessor instance."""
    with patch("src.proc.processor.HuggingFaceEmbeddings") as mock_hf, \
         patch("src.proc.processor.ensure_directory_exists"), \
         patch("src.proc.processor.get_collection_config", return_value={
             "name": "Test", "description": "test",
             "docs_folder": "/tmp/docs", "faiss_index": "/tmp/faiss",
             "processed_file": "/tmp/proc.json", "summary_file": "/tmp/sum.json",
         }), \
         patch("src.proc.processor.CONFIG", {
             "embedding_model": "all-MiniLM-L6-v2",
             "chunk_size": 500, "chunk_overlap": 50, "default_max_docs": 100,
         }):
        mock_hf.return_value = MagicMock()
        from src.proc.processor import get_processor
        p = get_processor("misc")
        assert p.docs_type == "misc"


# ── Additional coverage tests ───────────────────────────────────────────


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_handle_problematic_document(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """handle_problematic_document delegates to recovery_handler."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    with patch.object(proc.recovery_handler, "handle_problematic_document", return_value=None) as mock_recovery:
        result = proc.handle_problematic_document("test.pdf", {}, "some error")
        mock_recovery.assert_called_once_with("test.pdf", {}, "some error")
        assert result is None


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_process_documents_with_chunks(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """process_documents processes files and updates vector index."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    docs_dir = tmp_path / "docs"
    (docs_dir / "new.pdf").write_bytes(b"%PDF")

    mock_chunk = MagicMock()
    mock_chunk.page_content = "chunk text"
    mock_chunk.metadata = {"source": "new.pdf"}

    with patch("src.proc.processor.get_supported_files", return_value=["new.pdf"]), \
         patch("src.proc.processor.get_file_hash", return_value="new_hash"), \
         patch("src.proc.processor.load_json_file", return_value={}), \
         patch("src.proc.processor.save_json_file"), \
         patch.object(proc.document_handler, "process", return_value=[mock_chunk]), \
         patch.object(proc, "_update_vector_index", return_value=True) as mock_update, \
         patch.object(proc, "_cleanup_processed_files"):
        result = proc.process_documents()

    assert result is True
    mock_update.assert_called_once()


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_process_documents_no_new_chunks(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """process_documents handles case where processing yields no chunks."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    docs_dir = tmp_path / "docs"
    (docs_dir / "empty.pdf").write_bytes(b"%PDF")

    with patch("src.proc.processor.get_supported_files", return_value=["empty.pdf"]), \
         patch("src.proc.processor.get_file_hash", return_value="new_hash"), \
         patch("src.proc.processor.load_json_file", return_value={}), \
         patch("src.proc.processor.save_json_file") as mock_save, \
         patch.object(proc.document_handler, "process", return_value=None), \
         patch.object(proc, "_cleanup_processed_files"):
        result = proc.process_documents()

    assert result is True
    mock_save.assert_called()


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_process_documents_update_fails(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """process_documents returns False when vector index update fails."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    docs_dir = tmp_path / "docs"
    (docs_dir / "test.pdf").write_bytes(b"%PDF")

    mock_chunk = MagicMock()

    with patch("src.proc.processor.get_supported_files", return_value=["test.pdf"]), \
         patch("src.proc.processor.get_file_hash", return_value="hash"), \
         patch("src.proc.processor.load_json_file", return_value={}), \
         patch("src.proc.processor.save_json_file"), \
         patch.object(proc.document_handler, "process", return_value=[mock_chunk]), \
         patch.object(proc, "_update_vector_index", return_value=False):
        result = proc.process_documents()

    assert result is False


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_apply_document_limit_under_max(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_apply_document_limit returns all files when count is under max."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)
    proc.max_documents = 10

    files = ["a.pdf", "b.pdf"]
    result = proc._apply_document_limit(files)
    assert len(result) == 2


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_update_vector_index_create_new(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_update_vector_index creates a new index when none exists."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    mock_chunk = MagicMock()
    mock_chunk.page_content = "text"
    mock_chunk.metadata = {"source": "test.pdf"}

    mock_store = MagicMock()

    with patch.object(proc.vector_store_manager, "prepare_texts", return_value=(["text"], [{"source": "test.pdf"}])), \
         patch.object(proc.vector_store_manager, "create_new", return_value=mock_store), \
         patch.object(proc.vector_store_manager, "save", return_value=True), \
         patch.object(proc.vector_store_manager, "verify"), \
         patch.object(proc, "save_processed_files"), \
         patch("os.path.exists", return_value=False):
        result = proc._update_vector_index([mock_chunk], {}, False)

    assert result is True


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_update_vector_index_merge_existing(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_update_vector_index merges with existing store when available."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    mock_chunk = MagicMock()
    mock_existing = MagicMock()
    mock_merged = MagicMock()

    with patch.object(proc.vector_store_manager, "prepare_texts", return_value=(["text"], [{}])), \
         patch.object(proc.vector_store_manager, "load_existing", return_value=mock_existing), \
         patch.object(proc.vector_store_manager, "add_to_existing", return_value=mock_merged), \
         patch.object(proc.vector_store_manager, "save", return_value=True), \
         patch.object(proc.vector_store_manager, "verify"), \
         patch.object(proc, "save_processed_files"), \
         patch("os.path.exists", return_value=True):
        result = proc._update_vector_index([mock_chunk], {}, False)

    assert result is True


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_update_vector_index_create_fails_alternative(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_update_vector_index tries alternative embeddings when creation fails."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    mock_chunk = MagicMock()

    with patch.object(proc.vector_store_manager, "prepare_texts", return_value=(["text"], [{}])), \
         patch.object(proc.vector_store_manager, "create_new", return_value=None), \
         patch.object(proc.vector_store_manager, "try_alternative_embeddings", return_value=(False, None)), \
         patch("os.path.exists", return_value=False):
        result = proc._update_vector_index([mock_chunk], {}, True)

    assert result is False


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_update_vector_index_save_fails(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_update_vector_index returns False when save fails."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    mock_store = MagicMock()

    with patch.object(proc.vector_store_manager, "prepare_texts", return_value=(["text"], [{}])), \
         patch.object(proc.vector_store_manager, "create_new", return_value=mock_store), \
         patch.object(proc.vector_store_manager, "save", return_value=False), \
         patch("os.path.exists", return_value=False):
        result = proc._update_vector_index([MagicMock()], {}, True)

    assert result is False


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_cleanup_processed_files_exception(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """_cleanup_processed_files handles exceptions gracefully."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    with patch("os.listdir", side_effect=OSError("permission denied")):
        # Should not raise
        proc._cleanup_processed_files({"a.pdf": {"hash": "h"}})


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_setup_alternative_embeddings_success(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """setup_alternative_embeddings updates embeddings on success."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)
    mock_new_embed = MagicMock()

    with patch.object(proc.vector_store_manager, "setup_alternative_embeddings",
                      return_value=(True, mock_new_embed)):
        result = proc.setup_alternative_embeddings()

    assert result is True
    assert proc.embeddings is mock_new_embed


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_setup_alternative_embeddings_failure(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """setup_alternative_embeddings returns False on failure."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    with patch.object(proc.vector_store_manager, "setup_alternative_embeddings",
                      return_value=(False, None)):
        result = proc.setup_alternative_embeddings()

    assert result is False


@patch("src.proc.processor.HuggingFaceEmbeddings")
@patch("src.proc.processor.ensure_directory_exists")
@patch("src.proc.processor.get_collection_config")
def test_diagnose_and_report(mock_get_config, mock_ensure_dir, mock_hf_embed, tmp_path):
    """diagnose_and_report_problematic_files delegates to recovery handler."""
    proc = _make_processor(mock_get_config, mock_hf_embed, tmp_path)

    with patch.object(proc, "load_processed_files", return_value={"f.pdf": {"status": "ERROR"}}), \
         patch.object(proc.recovery_handler, "diagnose_and_report", return_value=[]) as mock_diag:
        result = proc.diagnose_and_report_problematic_files()

    mock_diag.assert_called_once()
    assert result == []
