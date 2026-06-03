# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/loaders/office_loaders.py."""

import pytest
from src.loaders import get_loader_for_file


def test_unsupported_extension(sample_text_file):
    """get_loader_for_file raises ValueError for an unsupported file extension like .txt."""
    with pytest.raises(ValueError, match="Unsupported file format"):
        get_loader_for_file(str(sample_text_file))


# ── DocxLoader tests ────────────────────────────────────────────────────

from unittest.mock import patch, MagicMock
from langchain_core.documents import Document


class TestDocxLoader:
    """Tests for DocxLoader."""

    def test_load_success(self):
        """DocxLoader.load returns enhanced documents on success."""
        mock_base = MagicMock()
        mock_base.load.return_value = [
            Document(page_content="Word content", metadata={"source": "test.docx"})
        ]

        with patch("src.loaders.office_loaders.Docx2txtLoader", return_value=mock_base), \
             patch("src.loaders.office_loaders.sanitize_text", side_effect=lambda t: t):
            from src.loaders.office_loaders import DocxLoader
            loader = DocxLoader("/fake/test.docx")
            docs = loader.load()

        assert len(docs) == 1
        assert docs[0].page_content == "Word content"
        assert docs[0].metadata["doc_type"] == "docx"
        assert docs[0].metadata["source"] == "test.docx"
        assert docs[0].metadata["page"] == 1

    def test_load_multiple_docs(self):
        """DocxLoader.load handles multiple document sections."""
        mock_base = MagicMock()
        mock_base.load.return_value = [
            Document(page_content="Section 1", metadata={}),
            Document(page_content="Section 2", metadata={}),
        ]

        with patch("src.loaders.office_loaders.Docx2txtLoader", return_value=mock_base), \
             patch("src.loaders.office_loaders.sanitize_text", side_effect=lambda t: t):
            from src.loaders.office_loaders import DocxLoader
            loader = DocxLoader("/fake/test.docx")
            docs = loader.load()

        assert len(docs) == 2
        assert docs[0].metadata["page"] == 1
        assert docs[1].metadata["page"] == 2

    def test_load_error_returns_error_doc(self):
        """DocxLoader.load returns an error document on failure."""
        mock_base = MagicMock()
        mock_base.load.side_effect = RuntimeError("docx parse error")

        with patch("src.loaders.office_loaders.Docx2txtLoader", return_value=mock_base):
            from src.loaders.office_loaders import DocxLoader
            loader = DocxLoader("/fake/broken.docx")
            docs = loader.load()

        assert len(docs) == 1
        assert "Error" in docs[0].page_content
        assert "error" in docs[0].metadata
        assert "docx parse error" in docs[0].metadata["error"]


class TestDocLoader:
    """Tests for DocLoader alias."""

    def test_doc_loader_is_docx_loader(self):
        """DocLoader should be an alias for DocxLoader."""
        from src.loaders.office_loaders import DocLoader, DocxLoader
        assert DocLoader is DocxLoader


class TestPowerPointLoader:
    """Tests for PowerPointLoader."""

    def test_load_success(self):
        """PowerPointLoader.load returns enhanced documents on success."""
        mock_base = MagicMock()
        mock_base.load.return_value = [
            Document(page_content="Slide content", metadata={"page_number": 1})
        ]

        with patch("src.loaders.office_loaders.UnstructuredPowerPointLoader", return_value=mock_base), \
             patch("src.loaders.office_loaders.sanitize_text", side_effect=lambda t: t):
            from src.loaders.office_loaders import PowerPointLoader
            loader = PowerPointLoader("/fake/test.pptx")
            docs = loader.load()

        assert len(docs) == 1
        assert docs[0].page_content == "Slide content"
        assert docs[0].metadata["doc_type"] == "powerpoint"
        assert docs[0].metadata["source"] == "test.pptx"
        assert docs[0].metadata["slide"] == 1

    def test_load_error_returns_error_doc(self):
        """PowerPointLoader.load returns an error document on failure."""
        mock_base = MagicMock()
        mock_base.load.side_effect = RuntimeError("pptx parse error")

        with patch("src.loaders.office_loaders.UnstructuredPowerPointLoader", return_value=mock_base):
            from src.loaders.office_loaders import PowerPointLoader
            loader = PowerPointLoader("/fake/broken.pptx")
            docs = loader.load()

        assert len(docs) == 1
        assert "Error" in docs[0].page_content
        assert "pptx parse error" in docs[0].metadata["error"]

    def test_load_uses_page_number_from_metadata(self):
        """PowerPointLoader uses page_number from base metadata for slide field."""
        mock_base = MagicMock()
        mock_base.load.return_value = [
            Document(page_content="Slide 3", metadata={"page_number": 3})
        ]

        with patch("src.loaders.office_loaders.UnstructuredPowerPointLoader", return_value=mock_base), \
             patch("src.loaders.office_loaders.sanitize_text", side_effect=lambda t: t):
            from src.loaders.office_loaders import PowerPointLoader
            loader = PowerPointLoader("/fake/test.pptx")
            docs = loader.load()

        assert docs[0].metadata["slide"] == 3
        assert docs[0].metadata["page"] == 3


class TestExcelLoader:
    """Tests for ExcelLoader."""

    def test_load_success(self):
        """ExcelLoader.load returns enhanced documents on success."""
        mock_base = MagicMock()
        mock_base.load.return_value = [
            Document(page_content="Cell data", metadata={"sheet_name": "Sheet1"})
        ]

        with patch("src.loaders.office_loaders.UnstructuredExcelLoader", return_value=mock_base), \
             patch("src.loaders.office_loaders.sanitize_text", side_effect=lambda t: t):
            from src.loaders.office_loaders import ExcelLoader
            loader = ExcelLoader("/fake/test.xlsx")
            docs = loader.load()

        assert len(docs) == 1
        assert docs[0].page_content == "Cell data"
        assert docs[0].metadata["doc_type"] == "excel"
        assert docs[0].metadata["source"] == "test.xlsx"
        assert docs[0].metadata["sheet_element"] == 1
        assert docs[0].metadata["page"] == "Sheet1_1"

    def test_load_multiple_sheets(self):
        """ExcelLoader.load tracks elements per sheet."""
        mock_base = MagicMock()
        mock_base.load.return_value = [
            Document(page_content="Data A", metadata={"sheet_name": "Sheet1"}),
            Document(page_content="Data B", metadata={"sheet_name": "Sheet1"}),
            Document(page_content="Data C", metadata={"sheet_name": "Sheet2"}),
        ]

        with patch("src.loaders.office_loaders.UnstructuredExcelLoader", return_value=mock_base), \
             patch("src.loaders.office_loaders.sanitize_text", side_effect=lambda t: t):
            from src.loaders.office_loaders import ExcelLoader
            loader = ExcelLoader("/fake/test.xlsx")
            docs = loader.load()

        assert len(docs) == 3
        assert docs[0].metadata["sheet_element"] == 1
        assert docs[0].metadata["page"] == "Sheet1_1"
        assert docs[1].metadata["sheet_element"] == 2
        assert docs[1].metadata["page"] == "Sheet1_2"
        assert docs[2].metadata["sheet_element"] == 1
        assert docs[2].metadata["page"] == "Sheet2_1"

    def test_load_unknown_sheet(self):
        """ExcelLoader.load handles missing sheet_name metadata."""
        mock_base = MagicMock()
        mock_base.load.return_value = [
            Document(page_content="Data", metadata={})
        ]

        with patch("src.loaders.office_loaders.UnstructuredExcelLoader", return_value=mock_base), \
             patch("src.loaders.office_loaders.sanitize_text", side_effect=lambda t: t):
            from src.loaders.office_loaders import ExcelLoader
            loader = ExcelLoader("/fake/test.xlsx")
            docs = loader.load()

        assert docs[0].metadata["page"] == "unknown_1"

    def test_load_error_returns_error_doc(self):
        """ExcelLoader.load returns an error document on failure."""
        mock_base = MagicMock()
        mock_base.load.side_effect = RuntimeError("xlsx parse error")

        with patch("src.loaders.office_loaders.UnstructuredExcelLoader", return_value=mock_base):
            from src.loaders.office_loaders import ExcelLoader
            loader = ExcelLoader("/fake/broken.xlsx")
            docs = loader.load()

        assert len(docs) == 1
        assert "Error" in docs[0].page_content
        assert "xlsx parse error" in docs[0].metadata["error"]

    def test_custom_mode(self):
        """ExcelLoader accepts a custom mode parameter."""
        with patch("src.loaders.office_loaders.UnstructuredExcelLoader") as MockLoader:
            MockLoader.return_value = MagicMock()
            from src.loaders.office_loaders import ExcelLoader
            loader = ExcelLoader("/fake/test.xlsx", mode="single")
            assert loader.mode == "single"
            MockLoader.assert_called_with("/fake/test.xlsx", mode="single")


class TestGetLoaderForXlsx:
    """Tests for get_loader_for_file with .xlsx (covers __init__.py line 61)."""

    def test_get_loader_for_xlsx(self):
        """get_loader_for_file returns an ExcelLoader with mode='elements' for .xlsx."""
        from src.loaders.office_loaders import ExcelLoader

        with patch("src.loaders.office_loaders.UnstructuredExcelLoader") as MockLoader:
            MockLoader.return_value = MagicMock()
            loader = get_loader_for_file("/fake/data.xlsx")

        assert isinstance(loader, ExcelLoader)
        assert loader.mode == "elements"

    def test_get_loader_for_xls(self):
        """get_loader_for_file returns an ExcelLoader with mode='elements' for .xls."""
        from src.loaders.office_loaders import ExcelLoader

        with patch("src.loaders.office_loaders.UnstructuredExcelLoader") as MockLoader:
            MockLoader.return_value = MagicMock()
            loader = get_loader_for_file("/fake/data.xls")

        assert isinstance(loader, ExcelLoader)
        assert loader.mode == "elements"
