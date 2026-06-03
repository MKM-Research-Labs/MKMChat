# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/proc/document_handler.py."""

import os
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document

from src.loaders import SUPPORTED_EXTENSIONS, get_loader_for_file


def test_filter_supported_files(temp_data_dir):
    """Only files with supported extensions should be accepted by get_loader_for_file."""
    supported_file = temp_data_dir / "docs" / "report.pdf"
    supported_file.write_bytes(b"%PDF-1.4 fake")

    unsupported_file = temp_data_dir / "docs" / "readme.txt"
    unsupported_file.write_text("hello")

    # Supported extension should not raise
    with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
        loader = get_loader_for_file(str(supported_file))
    assert loader is not None

    # Unsupported extension should raise ValueError
    with pytest.raises(ValueError, match="Unsupported file format"):
        get_loader_for_file(str(unsupported_file))


def test_load_document_dispatch(temp_data_dir):
    """DocumentHandler.process dispatches to the correct loader for .pdf files."""
    from src.proc.document_handler import DocumentHandler

    pdf_file = temp_data_dir / "docs" / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")

    mock_splitter = MagicMock()
    mock_splitter.split_documents.return_value = [
        Document(page_content="chunk1", metadata={"source": "test.pdf"})
    ]

    handler = DocumentHandler(
        docs_folder=str(temp_data_dir / "docs"),
        text_splitter=mock_splitter,
        docs_type="misc",
        show_progress=False,
    )

    fake_doc = Document(page_content="Test content", metadata={"source": "test.pdf"})

    with patch("src.proc.document_handler.get_loader_for_file") as mock_get_loader, \
         patch("src.proc.document_handler.get_file_hash", return_value="hash123"), \
         patch("src.proc.document_handler.create_processed_record", return_value={"hash": "hash123", "status": "SUCCESS"}), \
         patch("src.proc.document_handler.sanitize_text", side_effect=lambda x: x), \
         patch("src.proc.document_handler.standardize_metadata", side_effect=lambda chunks, dt: chunks):

        mock_loader = MagicMock()
        mock_loader.load.return_value = [fake_doc]
        mock_get_loader.return_value = mock_loader

        processed_files = {}
        result = handler.process("test.pdf", processed_files)

    # get_loader_for_file should have been called with the full path
    mock_get_loader.assert_called_once_with(os.path.join(str(temp_data_dir / "docs"), "test.pdf"))
    assert result is not None
    assert len(result) >= 1


def test_process_skip_unchanged(temp_data_dir):
    """DocumentHandler.process returns None for files with matching hash."""
    from src.proc.document_handler import DocumentHandler

    handler = DocumentHandler(
        docs_folder=str(temp_data_dir / "docs"),
        text_splitter=MagicMock(),
        docs_type="misc",
        show_progress=False,
    )

    processed_files = {"test.pdf": {"hash": "abc123"}}

    with patch("src.proc.document_handler.get_file_hash", return_value="abc123"):
        result = handler.process("test.pdf", processed_files)

    assert result is None


def test_process_empty_document(temp_data_dir):
    """DocumentHandler.process handles empty documents gracefully."""
    from src.proc.document_handler import DocumentHandler

    pdf_file = temp_data_dir / "docs" / "empty.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")

    mock_splitter = MagicMock()
    handler = DocumentHandler(
        docs_folder=str(temp_data_dir / "docs"),
        text_splitter=mock_splitter,
        docs_type="misc",
        show_progress=False,
    )

    mock_loader = MagicMock()
    mock_loader.load.return_value = []  # Empty document

    with patch("src.proc.document_handler.get_loader_for_file", return_value=mock_loader), \
         patch("src.proc.document_handler.get_file_hash", return_value="hash1"), \
         patch("src.proc.document_handler.create_processed_record", return_value={"status": "EMPTY"}):

        processed_files = {}
        save_callback = MagicMock()
        result = handler.process("empty.pdf", processed_files, save_callback=save_callback)

    assert result is None
    save_callback.assert_called_once()


def test_process_no_chunks_generated(temp_data_dir):
    """DocumentHandler.process handles case where splitting produces no chunks."""
    from src.proc.document_handler import DocumentHandler

    pdf_file = temp_data_dir / "docs" / "tiny.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")

    mock_splitter = MagicMock()
    mock_splitter.split_documents.return_value = []  # No chunks

    handler = DocumentHandler(
        docs_folder=str(temp_data_dir / "docs"),
        text_splitter=mock_splitter,
        docs_type="misc",
        show_progress=False,
    )

    fake_doc = Document(page_content="tiny text", metadata={"source": "tiny.pdf"})
    mock_loader = MagicMock()
    mock_loader.load.return_value = [fake_doc]

    with patch("src.proc.document_handler.get_loader_for_file", return_value=mock_loader), \
         patch("src.proc.document_handler.get_file_hash", return_value="hash1"), \
         patch("src.proc.document_handler.create_processed_record", return_value={"status": "NO_CHUNKS"}), \
         patch("src.proc.document_handler.sanitize_text", side_effect=lambda x: x):

        processed_files = {}
        result = handler.process("tiny.pdf", processed_files)

    assert result is None


def test_process_loader_exception_with_recovery(temp_data_dir):
    """DocumentHandler.process uses recovery callback when loader raises exception."""
    from src.proc.document_handler import DocumentHandler

    pdf_file = temp_data_dir / "docs" / "broken.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")

    handler = DocumentHandler(
        docs_folder=str(temp_data_dir / "docs"),
        text_splitter=MagicMock(),
        docs_type="misc",
        show_progress=False,
    )

    mock_loader = MagicMock()
    mock_loader.load.side_effect = RuntimeError("corrupt file")

    recovered_chunks = [Document(page_content="recovered", metadata={"source": "broken.pdf"})]
    recovery_callback = MagicMock(return_value=recovered_chunks)

    with patch("src.proc.document_handler.get_loader_for_file", return_value=mock_loader), \
         patch("src.proc.document_handler.get_file_hash", return_value="hash1"):

        processed_files = {}
        result = handler.process(
            "broken.pdf", processed_files,
            recovery_callback=recovery_callback,
        )

    assert result == recovered_chunks
    recovery_callback.assert_called_once()


def test_process_loader_exception_no_recovery(temp_data_dir):
    """DocumentHandler.process records error when loader fails and no recovery."""
    from src.proc.document_handler import DocumentHandler

    pdf_file = temp_data_dir / "docs" / "broken.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")

    handler = DocumentHandler(
        docs_folder=str(temp_data_dir / "docs"),
        text_splitter=MagicMock(),
        docs_type="misc",
        show_progress=False,
    )

    mock_loader = MagicMock()
    mock_loader.load.side_effect = RuntimeError("corrupt file")

    with patch("src.proc.document_handler.get_loader_for_file", return_value=mock_loader), \
         patch("src.proc.document_handler.get_file_hash", return_value="hash1"), \
         patch("src.proc.document_handler.create_processed_record", return_value={"status": "ERROR"}):

        processed_files = {}
        save_callback = MagicMock()
        result = handler.process("broken.pdf", processed_files, save_callback=save_callback)

    assert result is None
    save_callback.assert_called()


def test_process_outer_exception(temp_data_dir):
    """DocumentHandler.process handles exception from get_loader_for_file."""
    from src.proc.document_handler import DocumentHandler

    pdf_file = temp_data_dir / "docs" / "bad.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")

    handler = DocumentHandler(
        docs_folder=str(temp_data_dir / "docs"),
        text_splitter=MagicMock(),
        docs_type="misc",
        show_progress=False,
    )

    with patch("src.proc.document_handler.get_loader_for_file", side_effect=ValueError("unsupported")), \
         patch("src.proc.document_handler.get_file_hash", return_value="hash1"), \
         patch("src.proc.document_handler.create_processed_record", return_value={"status": "ERROR"}):

        processed_files = {}
        save_callback = MagicMock()
        result = handler.process("bad.pdf", processed_files, save_callback=save_callback)

    assert result is None
    save_callback.assert_called()


def test_needs_processing_new_file(temp_data_dir):
    """needs_processing returns True for files not in processed_files."""
    from src.proc.document_handler import DocumentHandler

    handler = DocumentHandler(
        docs_folder=str(temp_data_dir / "docs"),
        text_splitter=MagicMock(),
        docs_type="misc",
    )

    with patch("src.proc.document_handler.get_file_hash", return_value="h1"):
        assert handler.needs_processing("new.pdf", {}) is True


def test_needs_processing_changed_file(temp_data_dir):
    """needs_processing returns True when hash has changed."""
    from src.proc.document_handler import DocumentHandler

    handler = DocumentHandler(
        docs_folder=str(temp_data_dir / "docs"),
        text_splitter=MagicMock(),
        docs_type="misc",
    )

    with patch("src.proc.document_handler.get_file_hash", return_value="new_hash"):
        assert handler.needs_processing(
            "test.pdf", {"test.pdf": {"hash": "old_hash"}},
        ) is True


def test_needs_processing_unchanged_file(temp_data_dir):
    """needs_processing returns False when hash matches."""
    from src.proc.document_handler import DocumentHandler

    handler = DocumentHandler(
        docs_folder=str(temp_data_dir / "docs"),
        text_splitter=MagicMock(),
        docs_type="misc",
    )

    with patch("src.proc.document_handler.get_file_hash", return_value="same"):
        assert handler.needs_processing(
            "test.pdf", {"test.pdf": {"hash": "same"}},
        ) is False


def test_needs_processing_force(temp_data_dir):
    """needs_processing returns True when force_reprocess is True."""
    from src.proc.document_handler import DocumentHandler

    handler = DocumentHandler(
        docs_folder=str(temp_data_dir / "docs"),
        text_splitter=MagicMock(),
        docs_type="misc",
    )

    assert handler.needs_processing(
        "test.pdf", {"test.pdf": {"hash": "same"}}, force_reprocess=True,
    ) is True


def test_process_no_chunks_calls_save_callback(temp_data_dir):
    """DocumentHandler.process calls save_callback when NO_CHUNKS status (covers line 100)."""
    from src.proc.document_handler import DocumentHandler

    pdf_file = temp_data_dir / "docs" / "nochunks.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")

    mock_splitter = MagicMock()
    mock_splitter.split_documents.return_value = []  # No chunks produced

    handler = DocumentHandler(
        docs_folder=str(temp_data_dir / "docs"),
        text_splitter=mock_splitter,
        docs_type="misc",
        show_progress=False,
    )

    fake_doc = Document(page_content="Some content", metadata={"source": "nochunks.pdf"})
    mock_loader = MagicMock()
    mock_loader.load.return_value = [fake_doc]

    save_callback = MagicMock()

    with patch("src.proc.document_handler.get_loader_for_file", return_value=mock_loader), \
         patch("src.proc.document_handler.get_file_hash", return_value="hash1"), \
         patch("src.proc.document_handler.create_processed_record", return_value={"status": "NO_CHUNKS", "hash": "hash1"}), \
         patch("src.proc.document_handler.sanitize_text", side_effect=lambda x: x):

        processed_files = {}
        result = handler.process("nochunks.pdf", processed_files, save_callback=save_callback)

    assert result is None
    save_callback.assert_called_once_with(processed_files)


def test_process_index_error(temp_data_dir):
    """DocumentHandler.process handles IndexError from loader (covers lines 110-113)."""
    from src.proc.document_handler import DocumentHandler

    pdf_file = temp_data_dir / "docs" / "indexerr.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")

    handler = DocumentHandler(
        docs_folder=str(temp_data_dir / "docs"),
        text_splitter=MagicMock(),
        docs_type="misc",
        show_progress=False,
    )

    mock_loader = MagicMock()
    mock_loader.load.side_effect = IndexError("list index out of range")

    save_callback = MagicMock()

    with patch("src.proc.document_handler.get_loader_for_file", return_value=mock_loader), \
         patch("src.proc.document_handler.get_file_hash", return_value="hash1"), \
         patch("src.proc.document_handler.create_processed_record", return_value={"status": "ERROR", "hash": "hash1"}):

        processed_files = {}
        result = handler.process("indexerr.pdf", processed_files, save_callback=save_callback)

    assert result is None
    save_callback.assert_called()
