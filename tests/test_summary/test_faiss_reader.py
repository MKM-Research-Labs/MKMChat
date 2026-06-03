# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/summary/faiss_reader.py."""

import os
import json
import shutil
import pytest
from unittest.mock import patch, MagicMock, mock_open

from src.summary.faiss_reader import (
    load_faiss_index,
    search_book_content,
    create_safe_faiss_copy,
    cleanup_faiss_copy,
    get_document_chunks_from_faiss,
)
from src.summary.models import DocumentChunk


# --- load_faiss_index ---

def test_load_faiss_index_file_not_found(tmp_path):
    """load_faiss_index returns (None, None) when index file doesn't exist."""
    paths = {
        "faiss_index": str(tmp_path / "nonexistent" / "index.faiss"),
        "faiss_pkl": str(tmp_path / "nonexistent" / "index.pkl"),
    }
    result = load_faiss_index(paths)
    assert result == (None, None)


def test_load_faiss_index_success(tmp_path):
    """load_faiss_index returns (index, metadata) on success."""
    index_file = tmp_path / "index.faiss"
    pkl_file = tmp_path / "index.pkl"
    index_file.write_bytes(b"fake")
    pkl_file.write_bytes(b"fake")

    mock_index = MagicMock()
    mock_index.ntotal = 100

    mock_docstore = MagicMock()
    mock_id_map = {0: "doc1", 1: "doc2"}

    with patch("src.summary.faiss_reader.faiss.read_index", return_value=mock_index), \
         patch("builtins.open", mock_open()), \
         patch("src.summary.faiss_reader.pickle.load", return_value=(mock_docstore, mock_id_map)), \
         patch("os.path.exists", return_value=True):
        index, metadata = load_faiss_index({
            "faiss_index": str(index_file),
            "faiss_pkl": str(pkl_file),
        })

    assert index is mock_index
    assert metadata == (mock_docstore, mock_id_map)


def test_load_faiss_index_exception(tmp_path):
    """load_faiss_index returns (None, None) on exception."""
    index_file = tmp_path / "index.faiss"
    index_file.write_bytes(b"fake")

    with patch("os.path.exists", return_value=True), \
         patch("src.summary.faiss_reader.faiss.read_index", side_effect=RuntimeError("fail")):
        result = load_faiss_index({
            "faiss_index": str(index_file),
            "faiss_pkl": str(tmp_path / "index.pkl"),
        })

    assert result == (None, None)


def test_load_faiss_index_non_tuple_metadata(tmp_path):
    """load_faiss_index handles non-tuple metadata."""
    index_file = tmp_path / "index.faiss"
    pkl_file = tmp_path / "index.pkl"
    index_file.write_bytes(b"fake")
    pkl_file.write_bytes(b"fake")

    mock_index = MagicMock()
    mock_index.ntotal = 10
    plain_metadata = {"key": "value"}

    with patch("os.path.exists", return_value=True), \
         patch("src.summary.faiss_reader.faiss.read_index", return_value=mock_index), \
         patch("builtins.open", mock_open()), \
         patch("src.summary.faiss_reader.pickle.load", return_value=plain_metadata):
        index, metadata = load_faiss_index({
            "faiss_index": str(index_file),
            "faiss_pkl": str(pkl_file),
        })

    assert index is mock_index
    assert metadata == plain_metadata


# --- search_book_content ---

def test_search_book_content_langchain_structure():
    """search_book_content returns combined text for LangChain metadata structure."""
    mock_embedding_model = MagicMock()
    mock_embedding_model.encode.return_value = [[0.1, 0.2, 0.3]]

    mock_index = MagicMock()
    mock_index.search.return_value = ([0.5], [[0, 1]])

    mock_doc1 = MagicMock()
    mock_doc1.page_content = "Chapter 1 content"
    mock_doc2 = MagicMock()
    mock_doc2.page_content = "Chapter 2 content"

    mock_docstore = MagicMock()
    mock_docstore.search.side_effect = lambda doc_id: {
        "id1": mock_doc1, "id2": mock_doc2
    }.get(doc_id)

    index_to_docstore_id = {0: "id1", 1: "id2"}
    metadata = (mock_docstore, index_to_docstore_id)

    result = search_book_content("test.pdf", mock_embedding_model, mock_index, metadata)
    assert "Chapter 1 content" in result
    assert "Chapter 2 content" in result


def test_search_book_content_non_tuple_metadata():
    """search_book_content returns empty string for non-tuple metadata."""
    result = search_book_content("test.pdf", MagicMock(), MagicMock(), {"plain": "dict"})
    assert result == ""


def test_search_book_content_exception():
    """search_book_content returns empty string on exception."""
    mock_model = MagicMock()
    mock_model.encode.side_effect = RuntimeError("fail")
    metadata = (MagicMock(), {0: "id1"})

    result = search_book_content("test.pdf", mock_model, MagicMock(), metadata)
    assert result == ""


def test_search_book_content_no_relevant_chunks():
    """search_book_content returns empty string when no chunks have page_content."""
    mock_model = MagicMock()
    mock_model.encode.return_value = [[0.1]]

    mock_index = MagicMock()
    mock_index.search.return_value = ([0.5], [[0]])

    mock_docstore = MagicMock()
    mock_docstore.search.return_value = None  # document not found

    metadata = (mock_docstore, {0: "id1"})

    result = search_book_content("test.pdf", mock_model, mock_index, metadata)
    assert result == ""


# --- create_safe_faiss_copy ---

def test_create_safe_faiss_copy_path_not_found(tmp_path):
    """create_safe_faiss_copy returns (None, None) when source doesn't exist."""
    result = create_safe_faiss_copy(
        str(tmp_path / "nonexistent"),
        str(tmp_path / "temp"),
        MagicMock(),
    )
    assert result == (None, None)


def test_create_safe_faiss_copy_success(tmp_path):
    """create_safe_faiss_copy copies files and loads vector store."""
    src_dir = tmp_path / "faiss_src"
    src_dir.mkdir()
    (src_dir / "index.faiss").write_bytes(b"fake")
    (src_dir / "index.pkl").write_bytes(b"fake")
    temp_dir = str(tmp_path / "faiss_temp")

    mock_vs = MagicMock()
    mock_vs.index.ntotal = 50

    mock_faiss_cls = MagicMock()
    mock_faiss_cls.load_local.return_value = mock_vs
    mock_vectorstores = MagicMock()
    mock_vectorstores.FAISS = mock_faiss_cls

    with patch.dict("sys.modules", {"langchain_community.vectorstores": mock_vectorstores}):
        temp_path, vs = create_safe_faiss_copy(str(src_dir), temp_dir, MagicMock())

    assert temp_path == temp_dir
    assert vs is mock_vs
    assert os.path.exists(temp_dir)

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_create_safe_faiss_copy_load_failure(tmp_path):
    """create_safe_faiss_copy returns (None, None) when FAISS.load_local fails."""
    src_dir = tmp_path / "faiss_src"
    src_dir.mkdir()
    (src_dir / "index.faiss").write_bytes(b"fake")
    temp_dir = str(tmp_path / "faiss_temp")

    mock_faiss_cls = MagicMock()
    mock_faiss_cls.load_local.side_effect = RuntimeError("fail")
    mock_vectorstores = MagicMock()
    mock_vectorstores.FAISS = mock_faiss_cls

    with patch.dict("sys.modules", {"langchain_community.vectorstores": mock_vectorstores}):
        temp_path, vs = create_safe_faiss_copy(str(src_dir), temp_dir, MagicMock())

    assert temp_path is None
    assert vs is None


# --- cleanup_faiss_copy ---

def test_cleanup_faiss_copy_removes_directory(tmp_path):
    """cleanup_faiss_copy removes the temporary directory."""
    temp_dir = tmp_path / "temp_faiss"
    temp_dir.mkdir()
    (temp_dir / "index.faiss").write_bytes(b"fake")

    cleanup_faiss_copy(str(temp_dir))
    assert not temp_dir.exists()


def test_cleanup_faiss_copy_none_path():
    """cleanup_faiss_copy does nothing when path is None."""
    cleanup_faiss_copy(None)  # Should not raise


def test_cleanup_faiss_copy_nonexistent_path():
    """cleanup_faiss_copy does nothing when path doesn't exist."""
    cleanup_faiss_copy("/nonexistent/path/abc123")  # Should not raise


# --- get_document_chunks_from_faiss ---

def test_get_document_chunks_from_faiss_found():
    """get_document_chunks_from_faiss extracts and sorts chunks for a document."""
    mock_doc1 = MagicMock()
    mock_doc1.metadata = {"source": "/docs/test.pdf", "page": 2}
    mock_doc1.page_content = "Page 2 content"

    mock_doc2 = MagicMock()
    mock_doc2.metadata = {"source": "/docs/test.pdf", "page": 1}
    mock_doc2.page_content = "Page 1 content"

    mock_doc3 = MagicMock()
    mock_doc3.metadata = {"source": "/docs/other.pdf", "page": 1}
    mock_doc3.page_content = "Other doc"

    mock_vector_store = MagicMock()
    mock_vector_store.docstore._dict = {
        "d1": mock_doc1,
        "d2": mock_doc2,
        "d3": mock_doc3,
    }

    chunks = get_document_chunks_from_faiss(mock_vector_store, "test.pdf")

    assert len(chunks) == 2
    assert isinstance(chunks[0], DocumentChunk)
    # Should be sorted by page
    assert chunks[0].page == 1
    assert chunks[1].page == 2


def test_get_document_chunks_from_faiss_not_found():
    """get_document_chunks_from_faiss returns empty list when no chunks match."""
    mock_doc = MagicMock()
    mock_doc.metadata = {"source": "/docs/other.pdf", "page": 1}
    mock_doc.page_content = "other"

    mock_vector_store = MagicMock()
    mock_vector_store.docstore._dict = {"d1": mock_doc}

    chunks = get_document_chunks_from_faiss(mock_vector_store, "test.pdf")
    assert chunks == []


def test_get_document_chunks_from_faiss_exception():
    """get_document_chunks_from_faiss returns empty list on exception."""
    mock_vector_store = MagicMock()
    mock_vector_store.docstore._dict = property(lambda self: (_ for _ in ()).throw(RuntimeError("fail")))

    # Force the attribute access to raise
    type(mock_vector_store.docstore)._dict = property(lambda self: (_ for _ in ()).throw(RuntimeError("fail")))

    chunks = get_document_chunks_from_faiss(mock_vector_store, "test.pdf")
    assert chunks == []


def test_get_document_chunks_from_faiss_basename_match():
    """get_document_chunks_from_faiss matches by basename."""
    mock_doc = MagicMock()
    mock_doc.metadata = {"source": "/long/path/to/mybook.pdf", "page": 1}
    mock_doc.page_content = "Content"

    mock_vector_store = MagicMock()
    mock_vector_store.docstore._dict = {"d1": mock_doc}

    chunks = get_document_chunks_from_faiss(mock_vector_store, "mybook.pdf")
    assert len(chunks) == 1


def test_search_book_content_docstore_exception():
    """search_book_content continues when docstore.search raises."""
    mock_model = MagicMock()
    mock_model.encode.return_value = [[0.1]]

    mock_index = MagicMock()
    mock_index.search.return_value = ([0.5], [[0]])

    mock_docstore = MagicMock()
    mock_docstore.search.side_effect = RuntimeError("corrupt")

    metadata = (mock_docstore, {0: "id1"})
    result = search_book_content("test.pdf", mock_model, mock_index, metadata)
    assert result == ""


def test_create_safe_faiss_copy_removes_existing_temp(tmp_path):
    """create_safe_faiss_copy removes existing temp dir before copying."""
    src_dir = tmp_path / "faiss_src"
    src_dir.mkdir()
    (src_dir / "index.faiss").write_bytes(b"fake")
    (src_dir / "index.pkl").write_bytes(b"fake")

    temp_dir = tmp_path / "faiss_temp"
    temp_dir.mkdir()
    (temp_dir / "old_file.txt").write_text("stale")

    mock_vs = MagicMock()
    mock_vs.index.ntotal = 50
    mock_faiss_cls = MagicMock()
    mock_faiss_cls.load_local.return_value = mock_vs
    mock_vectorstores = MagicMock()
    mock_vectorstores.FAISS = mock_faiss_cls

    with patch.dict("sys.modules", {"langchain_community.vectorstores": mock_vectorstores}):
        temp_path, vs = create_safe_faiss_copy(str(src_dir), str(temp_dir), MagicMock())

    assert vs is mock_vs
    # Old file should be gone
    assert not (temp_dir / "old_file.txt").exists()

    shutil.rmtree(str(temp_dir), ignore_errors=True)


def test_cleanup_faiss_copy_exception(tmp_path):
    """cleanup_faiss_copy handles rmtree failure gracefully."""
    temp_dir = tmp_path / "temp_faiss"
    temp_dir.mkdir()

    with patch("src.summary.faiss_reader.shutil.rmtree", side_effect=OSError("perm denied")):
        cleanup_faiss_copy(str(temp_dir))  # Should not raise


def test_get_document_chunks_per_chunk_exception():
    """get_document_chunks_from_faiss skips chunks that raise exceptions."""
    good_doc = MagicMock()
    good_doc.metadata = {"source": "/docs/test.pdf", "page": 1}
    good_doc.page_content = "Good content"

    bad_doc = MagicMock()
    bad_doc.metadata = property(lambda self: (_ for _ in ()).throw(RuntimeError("broken")))
    # Make metadata access raise
    type(bad_doc).metadata = property(lambda self: (_ for _ in ()).throw(RuntimeError("broken")))

    mock_vector_store = MagicMock()
    mock_vector_store.docstore._dict = {"d1": bad_doc, "d2": good_doc}

    chunks = get_document_chunks_from_faiss(mock_vector_store, "test.pdf")
    # Should get the good chunk, bad one is skipped
    assert len(chunks) == 1
