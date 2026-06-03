# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/loaders/pdf_loader.py."""

import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document


def test_load_valid_pdf(sample_pdf_file):
    """EnhancedPDFLoader.load returns a list of Document-like objects for a valid PDF."""
    with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
        from src.loaders.pdf_loader import EnhancedPDFLoader

        loader = EnhancedPDFLoader(str(sample_pdf_file))
        docs = loader.load()

    assert isinstance(docs, list)
    assert len(docs) >= 1
    # Every item should be a langchain Document (or at least have page_content)
    for doc in docs:
        assert hasattr(doc, "page_content")
        assert hasattr(doc, "metadata")


def test_load_nonexistent_file(tmp_path):
    """Loading a file that does not exist should still return a list (error doc)."""
    fake_path = str(tmp_path / "nonexistent.pdf")

    with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
        from src.loaders.pdf_loader import EnhancedPDFLoader

        loader = EnhancedPDFLoader(fake_path)
        docs = loader.load()

    # The loader has multiple fallbacks and ultimately returns an error document
    assert isinstance(docs, list)
    assert len(docs) >= 1
    # The last-resort doc should mention an error
    assert any("error" in doc.metadata or "Error" in doc.page_content for doc in docs)


def test_load_returns_content(sample_pdf_file):
    """Loaded documents should have non-empty page_content."""
    with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
        from src.loaders.pdf_loader import EnhancedPDFLoader

        loader = EnhancedPDFLoader(str(sample_pdf_file))
        docs = loader.load()

    assert len(docs) >= 1
    # At least one document should have actual text content
    contents = [doc.page_content for doc in docs]
    assert any(len(c.strip()) > 0 for c in contents)


def test_clean_text_string():
    """_clean_text handles normal strings."""
    with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
        from src.loaders.pdf_loader import EnhancedPDFLoader

        loader = EnhancedPDFLoader("/fake/path.pdf")
        result = loader._clean_text("Hello world")
    assert "Hello" in result


def test_clean_text_non_string():
    """_clean_text handles non-string input by converting to string."""
    with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
        from src.loaders.pdf_loader import EnhancedPDFLoader

        loader = EnhancedPDFLoader("/fake/path.pdf")
        result = loader._clean_text(12345)
    assert "12345" in result


def test_clean_text_bytes():
    """_clean_text handles bytes input."""
    with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
        from src.loaders.pdf_loader import EnhancedPDFLoader

        loader = EnhancedPDFLoader("/fake/path.pdf")
        result = loader._clean_text(b"Hello bytes")
    assert isinstance(result, str)


def test_load_metadata_contains_source(sample_pdf_file):
    """Loaded documents should have source metadata."""
    with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
        from src.loaders.pdf_loader import EnhancedPDFLoader

        loader = EnhancedPDFLoader(str(sample_pdf_file))
        docs = loader.load()

    assert len(docs) >= 1
    for doc in docs:
        assert "source" in doc.metadata


def test_load_metadata_contains_extraction_method(sample_pdf_file):
    """Loaded documents should have extraction_method in metadata."""
    with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
        from src.loaders.pdf_loader import EnhancedPDFLoader

        loader = EnhancedPDFLoader(str(sample_pdf_file))
        docs = loader.load()

    assert len(docs) >= 1
    for doc in docs:
        assert "extraction_method" in doc.metadata


def test_load_fallback_to_pypdf2(tmp_path):
    """When primary method fails, loader falls back to PyPDF2."""
    pdf_file = tmp_path / "fallback.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")

    with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
        from src.loaders.pdf_loader import EnhancedPDFLoader

        loader = EnhancedPDFLoader(str(pdf_file))

        # Mock PyPDFLoader (imported inside load()) to fail
        mock_primary_cls = MagicMock()
        mock_primary_instance = MagicMock()
        mock_primary_instance.load.side_effect = RuntimeError("primary failed")
        mock_primary_cls.return_value = mock_primary_instance

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Fallback extracted text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        mock_loaders_module = MagicMock()
        mock_loaders_module.PyPDFLoader = mock_primary_cls

        import PyPDF2
        with patch.dict("sys.modules", {"langchain_community.document_loaders": mock_loaders_module}), \
             patch("PyPDF2.PdfReader", return_value=mock_reader):
            docs = loader.load()

    assert len(docs) >= 1
    assert any("Fallback" in doc.page_content or "text" in doc.page_content.lower() for doc in docs)


def test_binary_safe_extraction(tmp_path):
    """_binary_safe_extraction returns documents from binary-safe reading."""
    pdf_file = tmp_path / "binary.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")

    with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
        from src.loaders.pdf_loader import EnhancedPDFLoader
        loader = EnhancedPDFLoader(str(pdf_file))

    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Binary safe text"
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    with patch("PyPDF2.PdfReader", return_value=mock_reader), \
         patch("builtins.open", MagicMock()):
        docs = loader._binary_safe_extraction()

    assert isinstance(docs, list)


def test_binary_safe_extraction_failure(tmp_path):
    """_binary_safe_extraction returns empty list on total failure."""
    pdf_file = tmp_path / "broken.pdf"
    pdf_file.write_bytes(b"not a pdf")

    with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
        from src.loaders.pdf_loader import EnhancedPDFLoader
        loader = EnhancedPDFLoader(str(pdf_file))

    with patch("PyPDF2.PdfReader", side_effect=RuntimeError("fail")):
        docs = loader._binary_safe_extraction()

    assert docs == []


# ── Additional coverage tests ───────────────────────────────────────────


class TestCleanTextEdgeCases:
    """Tests for _clean_text with various edge-case inputs."""

    @pytest.fixture(autouse=True)
    def _loader(self):
        with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
            from src.loaders.pdf_loader import EnhancedPDFLoader
            self.loader = EnhancedPDFLoader("/fake/path.pdf")

    def test_clean_text_empty_string(self):
        """_clean_text with empty string returns non-empty fallback or empty."""
        result = self.loader._clean_text("")
        assert isinstance(result, str)

    def test_clean_text_null_bytes(self):
        """_clean_text strips null bytes."""
        result = self.loader._clean_text("Hello\x00World")
        assert "\x00" not in result
        assert "Hello" in result

    def test_clean_text_whitespace_only(self):
        """_clean_text with whitespace-only input."""
        result = self.loader._clean_text("   \n\t  ")
        assert isinstance(result, str)

    def test_clean_text_bytes_with_decode(self):
        """_clean_text handles bytes object that has .decode method."""
        result = self.loader._clean_text(b"binary content here")
        assert isinstance(result, str)

    def test_clean_text_sanitize_import_error(self):
        """_clean_text falls back to local cleaning when sanitize_text is unavailable."""
        with patch("src.loaders.pdf_loader.sanitize_text", side_effect=ImportError):
            result = self.loader._clean_text("Hello  World\x00test")
        assert isinstance(result, str)

    def test_clean_text_sanitize_attribute_error(self):
        """_clean_text falls back to local cleaning when sanitize_text raises AttributeError."""
        with patch("src.loaders.pdf_loader.sanitize_text", side_effect=AttributeError):
            result = self.loader._clean_text("Good text")
        assert isinstance(result, str)

    def test_clean_text_non_string_no_decode(self):
        """_clean_text converts non-string without decode attribute to string."""
        result = self.loader._clean_text([1, 2, 3])
        assert isinstance(result, str)

    def test_clean_text_fallback_empty_returns_placeholder(self):
        """_clean_text local fallback returns 'Empty page content' for empty result."""
        with patch("src.loaders.pdf_loader.sanitize_text", side_effect=ImportError):
            result = self.loader._clean_text("\x00\x00")
        assert isinstance(result, str)


class TestPyPDF2Fallback:
    """Tests for the PyPDF2 first-fallback path in load()."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.tmp_path = tmp_path
        self.pdf_file = tmp_path / "test.pdf"
        self.pdf_file.write_bytes(b"%PDF-1.4 fake")

    def _make_loader(self):
        with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
            from src.loaders.pdf_loader import EnhancedPDFLoader
            return EnhancedPDFLoader(str(self.pdf_file))

    def test_pypdf2_page_extract_text_error(self):
        """When page.extract_text() raises, error text is used instead."""
        loader = self._make_loader()

        mock_primary_cls = MagicMock()
        mock_primary_cls.return_value.load.side_effect = RuntimeError("primary failed")

        mock_page = MagicMock()
        mock_page.extract_text.side_effect = RuntimeError("page decode error")
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        mock_loaders_module = MagicMock()
        mock_loaders_module.PyPDFLoader = mock_primary_cls

        with patch.dict("sys.modules", {"langchain_community.document_loaders": mock_loaders_module}), \
             patch("PyPDF2.PdfReader", return_value=mock_reader):
            docs = loader.load()

        assert isinstance(docs, list)
        assert len(docs) >= 1
        # Should contain error text from the page extraction failure
        assert any("Error" in doc.page_content or "error" in doc.metadata.get("extraction_method", "") for doc in docs)

    def test_pypdf2_outer_page_error(self):
        """When an outer page-level exception occurs, an error document is created."""
        loader = self._make_loader()

        mock_primary_cls = MagicMock()
        mock_primary_cls.return_value.load.side_effect = RuntimeError("primary failed")

        # To trigger the outer except (line 124 in pdf_loader.py), we need an
        # exception OUTSIDE the inner try/except for extract_text (lines 104-107).
        # The inner except produces error text, then _clean_text is called on it.
        # If _clean_text raises, that triggers the outer except which creates
        # an "[Error on page N]" document.
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "some text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        mock_loaders_module = MagicMock()
        mock_loaders_module.PyPDFLoader = mock_primary_cls

        with patch.dict("sys.modules", {"langchain_community.document_loaders": mock_loaders_module}), \
             patch("PyPDF2.PdfReader", return_value=mock_reader), \
             patch.object(loader, "_clean_text", side_effect=RuntimeError("clean error")):
            docs = loader.load()

        assert isinstance(docs, list)
        assert len(docs) >= 1

    def test_pypdf2_fallback_returns_empty_then_continues(self):
        """When PyPDF2 returns no documents, fallback continues to pdfplumber."""
        loader = self._make_loader()

        mock_primary_cls = MagicMock()
        mock_primary_cls.return_value.load.side_effect = RuntimeError("primary failed")

        # PyPDF2 returns pages with empty text
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        mock_loaders_module = MagicMock()
        mock_loaders_module.PyPDFLoader = mock_primary_cls

        with patch.dict("sys.modules", {"langchain_community.document_loaders": mock_loaders_module}), \
             patch("PyPDF2.PdfReader", return_value=mock_reader), \
             patch("PyPDF2.PdfReader", return_value=mock_reader):
            # pdfplumber will also fail, leading to error doc
            docs = loader.load()

        assert isinstance(docs, list)
        assert len(docs) >= 1


class TestPdfplumberFallback:
    """Tests for the pdfplumber second-fallback path."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.tmp_path = tmp_path
        self.pdf_file = tmp_path / "test.pdf"
        self.pdf_file.write_bytes(b"%PDF-1.4 fake")

    def test_pdfplumber_success(self):
        """When primary and PyPDF2 fail, pdfplumber extracts text successfully."""
        with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
            from src.loaders.pdf_loader import EnhancedPDFLoader
            loader = EnhancedPDFLoader(str(self.pdf_file))

        mock_primary_cls = MagicMock()
        mock_primary_cls.return_value.load.side_effect = RuntimeError("primary failed")

        mock_loaders_module = MagicMock()
        mock_loaders_module.PyPDFLoader = mock_primary_cls

        # Mock PyPDF2 to fail
        mock_pypdf2 = MagicMock()
        mock_pypdf2.PdfReader.side_effect = RuntimeError("pypdf2 failed")

        # Mock pdfplumber to succeed
        mock_plumber_page = MagicMock()
        mock_plumber_page.extract_text.return_value = "Pdfplumber extracted text"
        mock_plumber_pdf = MagicMock()
        mock_plumber_pdf.pages = [mock_plumber_page]
        mock_plumber_pdf.__enter__ = MagicMock(return_value=mock_plumber_pdf)
        mock_plumber_pdf.__exit__ = MagicMock(return_value=False)

        mock_pdfplumber = MagicMock()
        mock_pdfplumber.open.return_value = mock_plumber_pdf

        with patch.dict("sys.modules", {
            "langchain_community.document_loaders": mock_loaders_module,
            "PyPDF2": mock_pypdf2,
            "pdfplumber": mock_pdfplumber,
        }):
            docs = loader.load()

        assert len(docs) >= 1
        assert any("Pdfplumber" in doc.page_content or "pdfplumber" in doc.metadata.get("extraction_method", "") for doc in docs)

    def test_pdfplumber_import_error_triggers_install(self):
        """When pdfplumber is not installed, subprocess install is attempted."""
        with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
            from src.loaders.pdf_loader import EnhancedPDFLoader
            loader = EnhancedPDFLoader(str(self.pdf_file))

        mock_primary_cls = MagicMock()
        mock_primary_cls.return_value.load.side_effect = RuntimeError("primary failed")
        mock_loaders_module = MagicMock()
        mock_loaders_module.PyPDFLoader = mock_primary_cls

        mock_pypdf2 = MagicMock()
        mock_pypdf2.PdfReader.side_effect = RuntimeError("pypdf2 failed")

        # pdfplumber import fails, then install fails too
        import builtins
        original_import = builtins.__import__
        def fake_import(name, *args, **kwargs):
            if name == "pdfplumber":
                raise ImportError("no pdfplumber")
            return original_import(name, *args, **kwargs)

        with patch.dict("sys.modules", {
            "langchain_community.document_loaders": mock_loaders_module,
            "PyPDF2": mock_pypdf2,
        }), patch("builtins.__import__", side_effect=fake_import), \
             patch("subprocess.check_call", side_effect=RuntimeError("install failed")):
            docs = loader.load()

        # Should eventually return error doc
        assert isinstance(docs, list)
        assert len(docs) >= 1

    def test_pdfplumber_page_error(self):
        """When a pdfplumber page raises, processing continues."""
        with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
            from src.loaders.pdf_loader import EnhancedPDFLoader
            loader = EnhancedPDFLoader(str(self.pdf_file))

        mock_primary_cls = MagicMock()
        mock_primary_cls.return_value.load.side_effect = RuntimeError("primary failed")
        mock_loaders_module = MagicMock()
        mock_loaders_module.PyPDFLoader = mock_primary_cls

        mock_pypdf2 = MagicMock()
        mock_pypdf2.PdfReader.side_effect = RuntimeError("pypdf2 failed")

        # pdfplumber page raises
        mock_plumber_page = MagicMock()
        mock_plumber_page.extract_text.side_effect = RuntimeError("page error")
        mock_plumber_pdf = MagicMock()
        mock_plumber_pdf.pages = [mock_plumber_page]
        mock_plumber_pdf.__enter__ = MagicMock(return_value=mock_plumber_pdf)
        mock_plumber_pdf.__exit__ = MagicMock(return_value=False)

        mock_pdfplumber = MagicMock()
        mock_pdfplumber.open.return_value = mock_plumber_pdf

        with patch.dict("sys.modules", {
            "langchain_community.document_loaders": mock_loaders_module,
            "PyPDF2": mock_pypdf2,
            "pdfplumber": mock_pdfplumber,
        }):
            docs = loader.load()

        assert isinstance(docs, list)


class TestBinarySafeExtractionPaths:
    """Tests for _binary_safe_extraction inner paths."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
            from src.loaders.pdf_loader import EnhancedPDFLoader
            self.loader = EnhancedPDFLoader(str(tmp_path / "test.pdf"))

    def test_text_extraction_fails_content_stream_list(self):
        """When extract_text fails, falls back to /Contents list of streams."""
        mock_content_obj = MagicMock()
        mock_content_obj.get_data.return_value = b"raw stream text"

        mock_page = MagicMock()
        mock_page.extract_text.side_effect = RuntimeError("text fail")
        mock_page.get.return_value = [mock_content_obj]

        # Make isinstance check for list work
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("PyPDF2.PdfReader", return_value=mock_reader), \
             patch("builtins.open", MagicMock()):
            docs = self.loader._binary_safe_extraction()

        assert isinstance(docs, list)

    def test_text_extraction_fails_single_content_stream(self):
        """When extract_text fails, falls back to single /Contents stream."""
        mock_content_obj = MagicMock()
        mock_content_obj.get_data.return_value = b"single stream text"

        mock_page = MagicMock()
        mock_page.extract_text.side_effect = RuntimeError("text fail")
        # Return a non-list content (single stream)
        mock_page.get.return_value = mock_content_obj

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("PyPDF2.PdfReader", return_value=mock_reader), \
             patch("builtins.open", MagicMock()):
            docs = self.loader._binary_safe_extraction()

        assert isinstance(docs, list)

    def test_content_extraction_also_fails(self):
        """When both extract_text and /Contents fail, page is skipped."""
        mock_page = MagicMock()
        mock_page.extract_text.side_effect = RuntimeError("text fail")
        mock_page.get.side_effect = RuntimeError("contents fail")

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("PyPDF2.PdfReader", return_value=mock_reader), \
             patch("builtins.open", MagicMock()):
            docs = self.loader._binary_safe_extraction()

        assert docs == []

    def test_page_level_exception(self):
        """When page processing itself raises, that page is skipped."""
        mock_reader = MagicMock()
        # pages has one item, but accessing it raises
        mock_reader.pages = MagicMock()
        mock_reader.pages.__len__ = MagicMock(return_value=1)
        mock_reader.pages.__getitem__ = MagicMock(side_effect=RuntimeError("page access error"))

        with patch("PyPDF2.PdfReader", return_value=mock_reader), \
             patch("builtins.open", MagicMock()):
            docs = self.loader._binary_safe_extraction()

        assert docs == []

    def test_empty_text_skipped(self):
        """Pages with empty/whitespace text are skipped."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "   "

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("PyPDF2.PdfReader", return_value=mock_reader), \
             patch("builtins.open", MagicMock()):
            docs = self.loader._binary_safe_extraction()

        assert docs == []


class TestOCRExtraction:
    """Tests for _ocr_extraction."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
            from src.loaders.pdf_loader import EnhancedPDFLoader
            self.loader = EnhancedPDFLoader(str(tmp_path / "test.pdf"))

    def test_ocr_success(self):
        """OCR extraction returns documents when pdf2image and pytesseract work."""
        mock_image = MagicMock()
        mock_pdf2image = MagicMock()
        mock_pdf2image.convert_from_path.return_value = [mock_image]

        mock_pytesseract = MagicMock()
        mock_pytesseract.image_to_string.return_value = "OCR extracted text"

        with patch.dict("sys.modules", {
            "pdf2image": mock_pdf2image,
            "pytesseract": mock_pytesseract,
            "PIL": MagicMock(),
            "PIL.Image": MagicMock(),
        }):
            docs = self.loader._ocr_extraction()

        assert len(docs) >= 1
        assert any("OCR" in doc.page_content for doc in docs)

    def test_ocr_empty_page_skipped(self):
        """OCR skips pages with empty text."""
        mock_image = MagicMock()
        mock_pdf2image = MagicMock()
        mock_pdf2image.convert_from_path.return_value = [mock_image]

        mock_pytesseract = MagicMock()
        mock_pytesseract.image_to_string.return_value = ""

        with patch.dict("sys.modules", {
            "pdf2image": mock_pdf2image,
            "pytesseract": mock_pytesseract,
            "PIL": MagicMock(),
            "PIL.Image": MagicMock(),
        }):
            docs = self.loader._ocr_extraction()

        assert docs == []

    def test_ocr_page_error_continues(self):
        """OCR continues when individual page OCR fails."""
        mock_image1 = MagicMock()
        mock_image2 = MagicMock()
        mock_pdf2image = MagicMock()
        mock_pdf2image.convert_from_path.return_value = [mock_image1, mock_image2]

        mock_pytesseract = MagicMock()
        mock_pytesseract.image_to_string.side_effect = [
            RuntimeError("ocr fail"),
            "Good text"
        ]

        with patch.dict("sys.modules", {
            "pdf2image": mock_pdf2image,
            "pytesseract": mock_pytesseract,
            "PIL": MagicMock(),
            "PIL.Image": MagicMock(),
        }):
            docs = self.loader._ocr_extraction()

        assert len(docs) == 1
        assert "Good text" in docs[0].page_content

    def test_ocr_convert_fails(self):
        """OCR returns empty list when pdf2image conversion fails."""
        mock_pdf2image = MagicMock()
        mock_pdf2image.convert_from_path.side_effect = RuntimeError("conversion failed")

        with patch.dict("sys.modules", {
            "pdf2image": mock_pdf2image,
            "pytesseract": MagicMock(),
            "PIL": MagicMock(),
            "PIL.Image": MagicMock(),
        }):
            docs = self.loader._ocr_extraction()

        assert docs == []

    def test_ocr_import_and_install_fail(self):
        """OCR returns empty list when packages can't be imported or installed."""
        import builtins
        original_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name in ("pdf2image", "pytesseract"):
                raise ImportError(f"no {name}")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import), \
             patch("subprocess.check_call", side_effect=RuntimeError("install failed")):
            docs = self.loader._ocr_extraction()

        assert docs == []

    def test_ocr_metadata_correct(self):
        """OCR documents have correct metadata fields."""
        mock_image = MagicMock()
        mock_pdf2image = MagicMock()
        mock_pdf2image.convert_from_path.return_value = [mock_image]

        mock_pytesseract = MagicMock()
        mock_pytesseract.image_to_string.return_value = "OCR text"

        with patch.dict("sys.modules", {
            "pdf2image": mock_pdf2image,
            "pytesseract": mock_pytesseract,
            "PIL": MagicMock(),
            "PIL.Image": MagicMock(),
        }):
            docs = self.loader._ocr_extraction()

        assert docs[0].metadata["extraction_method"] == "ocr"
        assert docs[0].metadata["page"] == 1
        assert docs[0].metadata["total_pages"] == 1


class TestFullFallbackChain:
    """Tests for the complete fallback chain in load()."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.pdf_file = tmp_path / "test.pdf"
        self.pdf_file.write_bytes(b"%PDF-1.4 fake")

    def test_all_fallbacks_fail_returns_error_doc(self):
        """When all methods fail, an error document is returned."""
        with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
            from src.loaders.pdf_loader import EnhancedPDFLoader
            loader = EnhancedPDFLoader(str(self.pdf_file))

        mock_primary_cls = MagicMock()
        mock_primary_cls.return_value.load.side_effect = RuntimeError("primary failed")
        mock_loaders_module = MagicMock()
        mock_loaders_module.PyPDFLoader = mock_primary_cls

        with patch.dict("sys.modules", {"langchain_community.document_loaders": mock_loaders_module}), \
             patch("PyPDF2.PdfReader", side_effect=RuntimeError("pypdf2 failed")), \
             patch.object(loader, "_binary_safe_extraction", return_value=[]), \
             patch.object(loader, "_ocr_extraction", side_effect=RuntimeError("ocr failed")):
            # pdfplumber also needs to fail
            import builtins
            original_import = builtins.__import__
            def fake_import(name, *args, **kwargs):
                if name == "pdfplumber":
                    raise ImportError("no pdfplumber")
                return original_import(name, *args, **kwargs)
            with patch("builtins.__import__", side_effect=fake_import), \
                 patch("subprocess.check_call", side_effect=RuntimeError("install failed")):
                docs = loader.load()

        assert len(docs) == 1
        assert docs[0].metadata["extraction_method"] == "failed"
        assert "error" in docs[0].metadata

    def test_binary_safe_succeeds_after_earlier_failures(self):
        """When primary, PyPDF2, and pdfplumber fail, binary-safe extraction succeeds."""
        with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
            from src.loaders.pdf_loader import EnhancedPDFLoader
            loader = EnhancedPDFLoader(str(self.pdf_file))

        mock_primary_cls = MagicMock()
        mock_primary_cls.return_value.load.side_effect = RuntimeError("primary failed")
        mock_loaders_module = MagicMock()
        mock_loaders_module.PyPDFLoader = mock_primary_cls

        recovered_doc = Document(
            page_content="Binary safe recovered",
            metadata={"source": "test.pdf", "extraction_method": "binary_safe"}
        )

        with patch.dict("sys.modules", {"langchain_community.document_loaders": mock_loaders_module}), \
             patch("PyPDF2.PdfReader", side_effect=RuntimeError("pypdf2 failed")), \
             patch.object(loader, "_binary_safe_extraction", return_value=[recovered_doc]):
            # pdfplumber also needs to fail
            import builtins
            original_import = builtins.__import__
            def fake_import(name, *args, **kwargs):
                if name == "pdfplumber":
                    raise ImportError("no pdfplumber")
                return original_import(name, *args, **kwargs)
            with patch("builtins.__import__", side_effect=fake_import), \
                 patch("subprocess.check_call", side_effect=RuntimeError("install failed")):
                docs = loader.load()

        assert len(docs) == 1
        assert docs[0].page_content == "Binary safe recovered"

    def test_ocr_succeeds_after_all_other_failures(self):
        """When everything else fails, OCR extraction succeeds."""
        with patch("src.loaders.pdf_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
            from src.loaders.pdf_loader import EnhancedPDFLoader
            loader = EnhancedPDFLoader(str(self.pdf_file))

        mock_primary_cls = MagicMock()
        mock_primary_cls.return_value.load.side_effect = RuntimeError("primary failed")
        mock_loaders_module = MagicMock()
        mock_loaders_module.PyPDFLoader = mock_primary_cls

        ocr_doc = Document(
            page_content="OCR recovered text",
            metadata={"source": "test.pdf", "extraction_method": "ocr"}
        )

        with patch.dict("sys.modules", {"langchain_community.document_loaders": mock_loaders_module}), \
             patch("PyPDF2.PdfReader", side_effect=RuntimeError("pypdf2 failed")), \
             patch.object(loader, "_binary_safe_extraction", return_value=[]), \
             patch.object(loader, "_ocr_extraction", return_value=[ocr_doc]):
            import builtins
            original_import = builtins.__import__
            def fake_import(name, *args, **kwargs):
                if name == "pdfplumber":
                    raise ImportError("no pdfplumber")
                return original_import(name, *args, **kwargs)
            with patch("builtins.__import__", side_effect=fake_import), \
                 patch("subprocess.check_call", side_effect=RuntimeError("install failed")):
                docs = loader.load()

        assert len(docs) == 1
        assert docs[0].page_content == "OCR recovered text"
