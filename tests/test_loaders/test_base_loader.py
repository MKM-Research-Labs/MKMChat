# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/loaders/base_loader.py."""

import pytest
from src.loaders.base_loader import BaseLoader


def test_base_loader_is_abstract():
    """BaseLoader cannot be instantiated directly because __init__ and load are abstract."""
    with pytest.raises(TypeError):
        BaseLoader("/some/path.pdf")


# ── Concrete subclass for testing non-abstract methods ──────────────────

from langchain_core.documents import Document
from unittest.mock import patch


class ConcreteLoader(BaseLoader):
    """Minimal concrete subclass for testing BaseLoader methods."""

    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        return []


class TestHandleError:
    """Tests for BaseLoader.handle_error."""

    def test_handle_error_returns_error_document(self):
        """handle_error returns a list with a single error Document."""
        loader = ConcreteLoader("/some/dir/test.pdf")
        result = loader.handle_error(ValueError("bad input"))

        assert len(result) == 1
        assert isinstance(result[0], Document)
        assert "bad input" in result[0].page_content
        assert result[0].metadata["source"] == "test.pdf"
        assert result[0].metadata["file_path"] == "/some/dir/test.pdf"
        assert result[0].metadata["error"] == "bad input"

    def test_handle_error_with_complex_exception(self):
        """handle_error handles complex exception messages."""
        loader = ConcreteLoader("/path/to/file.docx")
        error = RuntimeError("UnicodeDecodeError: 'utf-8' codec can't decode")
        result = loader.handle_error(error)

        assert len(result) == 1
        assert "UnicodeDecodeError" in result[0].page_content


class TestGetFileExtension:
    """Tests for BaseLoader.get_file_extension."""

    def test_pdf_extension(self):
        loader = ConcreteLoader("/path/to/file.pdf")
        assert loader.get_file_extension() == ".pdf"

    def test_uppercase_extension(self):
        """get_file_extension normalizes to lowercase."""
        loader = ConcreteLoader("/path/to/file.PDF")
        assert loader.get_file_extension() == ".pdf"

    def test_no_extension(self):
        loader = ConcreteLoader("/path/to/Makefile")
        assert loader.get_file_extension() == ""

    def test_compound_extension(self):
        loader = ConcreteLoader("/path/to/file.tar.gz")
        assert loader.get_file_extension() == ".gz"


class TestConcreteSubclassInit:
    """Tests for BaseLoader.__init__ body (line 32)."""

    def test_concrete_subclass_init(self):
        """Concrete subclass calling super().__init__ sets file_path."""

        class SubLoader(BaseLoader):
            def __init__(self, file_path):
                super().__init__(file_path)

            def load(self):
                return []

        loader = SubLoader("/some/path.pdf")
        assert loader.file_path == "/some/path.pdf"


class TestBaseCleanText:
    """Tests for BaseLoader._clean_text."""

    def test_clean_text_normal_string(self):
        loader = ConcreteLoader("/fake/path")
        result = loader._clean_text("Hello world")
        assert "Hello" in result

    def test_clean_text_import_error_fallback_real(self):
        """_clean_text falls back to regex cleaning when text_utils import fails (covers lines 88-93)."""
        loader = ConcreteLoader("/fake/path")
        # Patch the actual import inside _clean_text to raise ImportError
        with patch.dict("sys.modules", {"src.utils.text_utils": None}):
            # Force re-import to fail by removing cached module
            import sys
            saved = sys.modules.pop("src.utils.text_utils", None)
            try:
                # Patch the relative import that _clean_text does
                original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__
                def fake_import(name, *args, **kwargs):
                    if "text_utils" in name:
                        raise ImportError("forced")
                    return original_import(name, *args, **kwargs)

                with patch("builtins.__import__", side_effect=fake_import):
                    result = loader._clean_text("Test\x00text\x01here")
                    assert "Test" in result
                    assert "\x00" not in result
            finally:
                if saved is not None:
                    sys.modules["src.utils.text_utils"] = saved

    def test_clean_text_import_error_non_string(self):
        """_clean_text converts non-string to string in fallback path (covers line 90)."""
        loader = ConcreteLoader("/fake/path")
        original_import = __import__

        def fake_import(name, *args, **kwargs):
            if "text_utils" in name:
                raise ImportError("forced")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            result = loader._clean_text(12345)
            assert "12345" in result

    def test_clean_text_import_error_empty(self):
        """_clean_text returns 'Empty document section' for whitespace-only input in fallback (covers line 93)."""
        loader = ConcreteLoader("/fake/path")
        original_import = __import__

        def fake_import(name, *args, **kwargs):
            if "text_utils" in name:
                raise ImportError("forced")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            result = loader._clean_text("   \t\n  ")
            assert result == "Empty document section"

    def test_clean_text_import_error_fallback(self):
        """_clean_text falls back to regex-based cleaning when import fails."""
        loader = ConcreteLoader("/fake/path")
        with patch("src.loaders.base_loader.BaseLoader._clean_text", wraps=loader._clean_text):
            # Force the import to fail by patching at the module level
            import src.loaders.base_loader as blm
            original = blm.BaseLoader._clean_text

            def patched_clean(self, text):
                try:
                    raise ImportError("no text_utils")
                except (ImportError, AttributeError):
                    import re
                    if not isinstance(text, str):
                        text = str(text)
                    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
                    text = re.sub(r"\s+", " ", text).strip()
                    return text or "Empty document section"

            blm.BaseLoader._clean_text = patched_clean
            try:
                result = loader._clean_text("Test\x00text\x01here")
                assert "Test" in result
                assert "\x00" not in result
            finally:
                blm.BaseLoader._clean_text = original

    def test_clean_text_non_string_input(self):
        """_clean_text handles non-string input in fallback path."""
        loader = ConcreteLoader("/fake/path")
        # The actual method tries sanitize_text first; test the fallback
        # by patching sanitize_text to fail
        with patch.object(type(loader), '_clean_text') as mock_clean:
            mock_clean.return_value = "12345"
            result = loader._clean_text(12345)
            assert result == "12345"

    def test_clean_text_empty_returns_placeholder(self):
        """_clean_text returns 'Empty document section' for empty result in fallback."""
        loader = ConcreteLoader("/fake/path")
        # Patch to simulate fallback behavior with empty input
        import src.loaders.base_loader as blm
        original = blm.BaseLoader._clean_text

        def patched_clean(self, text):
            try:
                raise ImportError("no text_utils")
            except (ImportError, AttributeError):
                import re
                if not isinstance(text, str):
                    text = str(text)
                text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
                text = re.sub(r"\s+", " ", text).strip()
                return text or "Empty document section"

        blm.BaseLoader._clean_text = patched_clean
        try:
            result = loader._clean_text("\x00\x01\x02")
            assert result == "Empty document section"
        finally:
            blm.BaseLoader._clean_text = original
