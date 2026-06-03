# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/loaders/epub_loader.py."""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from langchain_core.documents import Document


@pytest.fixture
def mock_config():
    """Patch CONFIG for epub loader."""
    with patch("src.loaders.epub_loader.CONFIG", {"chunk_size": 500, "chunk_overlap": 50}):
        yield


@pytest.fixture
def loader(mock_config):
    """Create an ImprovedEPubLoader instance."""
    from src.loaders.epub_loader import ImprovedEPubLoader
    return ImprovedEPubLoader("/fake/book.epub")


class TestEpubLoadSuccess:
    """Tests for successful EPUB loading."""

    def test_load_basic_epub(self, mock_config):
        """load() returns documents from a mocked EPUB file."""
        from src.loaders.epub_loader import ImprovedEPubLoader

        # Create mock epub objects
        mock_item = MagicMock()
        mock_item.id = "chapter1"
        mock_item.get_content.return_value = b"<html><body><h1>Chapter 1</h1><p>Some text content here.</p></body></html>"

        mock_book = MagicMock()
        mock_book.get_metadata.side_effect = lambda ns, key: {
            ('DC', 'title'): [("Test Book", {})],
            ('DC', 'creator'): [("Test Author", {})],
        }.get((ns, key), [])
        mock_book.get_items_of_type.return_value = [mock_item]
        mock_book.spine = [("chapter1", "linear")]

        with patch("src.loaders.epub_loader.epub.read_epub", return_value=mock_book):
            loader = ImprovedEPubLoader("/fake/book.epub")
            docs = loader.load()

        assert isinstance(docs, list)
        assert len(docs) >= 1
        assert docs[0].metadata["book_title"] == "Test Book"
        assert docs[0].metadata["book_author"] == "Test Author"
        assert docs[0].metadata["source"] == "book.epub"

    def test_load_multiple_chapters(self, mock_config):
        """load() processes multiple items maintaining chapter info."""
        from src.loaders.epub_loader import ImprovedEPubLoader

        mock_item1 = MagicMock()
        mock_item1.id = "ch1"
        mock_item1.get_content.return_value = b"<html><body><h1>Introduction</h1><p>Intro text.</p></body></html>"

        mock_item2 = MagicMock()
        mock_item2.id = "ch2"
        mock_item2.get_content.return_value = b"<html><body><h2>Methods</h2><p>Method text.</p></body></html>"

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = []
        mock_book.get_items_of_type.return_value = [mock_item1, mock_item2]
        mock_book.spine = [("ch1", "linear"), ("ch2", "linear")]

        with patch("src.loaders.epub_loader.epub.read_epub", return_value=mock_book):
            loader = ImprovedEPubLoader("/fake/book.epub")
            docs = loader.load()

        assert len(docs) == 2
        assert "Chapter 1" in docs[0].metadata["chapter"]
        assert "Chapter 2" in docs[1].metadata["chapter"]

    def test_load_skips_empty_content(self, mock_config):
        """load() skips items with empty text content."""
        from src.loaders.epub_loader import ImprovedEPubLoader

        mock_item_empty = MagicMock()
        mock_item_empty.id = "empty"
        mock_item_empty.get_content.return_value = b"<html><body></body></html>"

        mock_item_content = MagicMock()
        mock_item_content.id = "content"
        mock_item_content.get_content.return_value = b"<html><body><p>Real content.</p></body></html>"

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = []
        mock_book.get_items_of_type.return_value = [mock_item_empty, mock_item_content]
        mock_book.spine = []

        with patch("src.loaders.epub_loader.epub.read_epub", return_value=mock_book):
            loader = ImprovedEPubLoader("/fake/book.epub")
            docs = loader.load()

        assert len(docs) == 1
        assert "Real content" in docs[0].page_content

    def test_load_no_spine(self, mock_config):
        """load() handles books without spine order."""
        from src.loaders.epub_loader import ImprovedEPubLoader

        mock_item = MagicMock()
        mock_item.id = "ch1"
        mock_item.get_content.return_value = b"<html><body><p>Content.</p></body></html>"

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = []
        mock_book.get_items_of_type.return_value = [mock_item]
        mock_book.spine = None

        with patch("src.loaders.epub_loader.epub.read_epub", return_value=mock_book):
            loader = ImprovedEPubLoader("/fake/book.epub")
            docs = loader.load()

        assert len(docs) == 1


class TestEpubLoadFailure:
    """Tests for EPUB load error handling."""

    def test_load_exception_returns_error_doc(self, mock_config):
        """load() returns an error document when epub reading fails."""
        from src.loaders.epub_loader import ImprovedEPubLoader

        with patch("src.loaders.epub_loader.epub.read_epub", side_effect=RuntimeError("corrupt epub")):
            loader = ImprovedEPubLoader("/fake/book.epub")
            docs = loader.load()

        assert len(docs) == 1
        assert "Error" in docs[0].page_content
        assert "error" in docs[0].metadata
        assert "corrupt epub" in docs[0].metadata["error"]

    def test_load_file_not_found(self, mock_config):
        """load() handles FileNotFoundError gracefully."""
        from src.loaders.epub_loader import ImprovedEPubLoader

        with patch("src.loaders.epub_loader.epub.read_epub", side_effect=FileNotFoundError("not found")):
            loader = ImprovedEPubLoader("/nonexistent/book.epub")
            docs = loader.load()

        assert len(docs) == 1
        assert "error" in docs[0].metadata


class TestEpubMetadata:
    """Tests for metadata extraction helpers."""

    def test_get_book_title_success(self, mock_config):
        """_get_book_title extracts title from metadata."""
        from src.loaders.epub_loader import ImprovedEPubLoader
        loader = ImprovedEPubLoader("/fake/book.epub")

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = [("My Book Title", {})]

        assert loader._get_book_title(mock_book) == "My Book Title"

    def test_get_book_title_missing(self, mock_config):
        """_get_book_title falls back to filename when metadata is missing."""
        from src.loaders.epub_loader import ImprovedEPubLoader
        loader = ImprovedEPubLoader("/fake/book.epub")

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = []

        assert loader._get_book_title(mock_book) == "book.epub"

    def test_get_book_title_exception(self, mock_config):
        """_get_book_title falls back to filename on exception."""
        from src.loaders.epub_loader import ImprovedEPubLoader
        loader = ImprovedEPubLoader("/fake/book.epub")

        mock_book = MagicMock()
        mock_book.get_metadata.side_effect = RuntimeError("metadata error")

        assert loader._get_book_title(mock_book) == "book.epub"

    def test_get_book_author_success(self, mock_config):
        """_get_book_author extracts author from metadata."""
        from src.loaders.epub_loader import ImprovedEPubLoader
        loader = ImprovedEPubLoader("/fake/book.epub")

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = [("Jane Doe", {})]

        assert loader._get_book_author(mock_book) == "Jane Doe"

    def test_get_book_author_missing(self, mock_config):
        """_get_book_author falls back to 'Unknown Author' when metadata is missing."""
        from src.loaders.epub_loader import ImprovedEPubLoader
        loader = ImprovedEPubLoader("/fake/book.epub")

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = []

        assert loader._get_book_author(mock_book) == "Unknown Author"

    def test_get_book_author_exception(self, mock_config):
        """_get_book_author falls back to 'Unknown Author' on exception."""
        from src.loaders.epub_loader import ImprovedEPubLoader
        loader = ImprovedEPubLoader("/fake/book.epub")

        mock_book = MagicMock()
        mock_book.get_metadata.side_effect = RuntimeError("metadata error")

        assert loader._get_book_author(mock_book) == "Unknown Author"


class TestHtmlToText:
    """Tests for _html_to_text conversion."""

    def test_html_to_text_basic(self, mock_config):
        """_html_to_text extracts text from basic HTML."""
        from src.loaders.epub_loader import ImprovedEPubLoader
        from bs4 import BeautifulSoup

        loader = ImprovedEPubLoader("/fake/book.epub")
        soup = BeautifulSoup("<p>Hello world</p>", "html.parser")
        result = loader._html_to_text(soup)

        assert "Hello world" in result

    def test_html_to_text_removes_scripts(self, mock_config):
        """_html_to_text strips script and style elements."""
        from src.loaders.epub_loader import ImprovedEPubLoader
        from bs4 import BeautifulSoup

        loader = ImprovedEPubLoader("/fake/book.epub")
        html = "<p>Content</p><script>alert('bad')</script><style>.hidden{}</style>"
        soup = BeautifulSoup(html, "html.parser")
        result = loader._html_to_text(soup)

        assert "Content" in result
        assert "alert" not in result
        assert ".hidden" not in result

    def test_html_to_text_preserves_headings(self, mock_config):
        """_html_to_text preserves heading text."""
        from src.loaders.epub_loader import ImprovedEPubLoader
        from bs4 import BeautifulSoup

        loader = ImprovedEPubLoader("/fake/book.epub")
        html = "<h1>Title</h1><p>Body text</p>"
        soup = BeautifulSoup(html, "html.parser")
        result = loader._html_to_text(soup)

        assert "Title" in result
        assert "Body text" in result

    def test_html_to_text_handles_lists(self, mock_config):
        """_html_to_text adds bullet markers to list items."""
        from src.loaders.epub_loader import ImprovedEPubLoader
        from bs4 import BeautifulSoup

        loader = ImprovedEPubLoader("/fake/book.epub")
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        soup = BeautifulSoup(html, "html.parser")
        result = loader._html_to_text(soup)

        assert "Item 1" in result
        assert "Item 2" in result

    def test_html_to_text_empty(self, mock_config):
        """_html_to_text handles empty HTML."""
        from src.loaders.epub_loader import ImprovedEPubLoader
        from bs4 import BeautifulSoup

        loader = ImprovedEPubLoader("/fake/book.epub")
        soup = BeautifulSoup("", "html.parser")
        result = loader._html_to_text(soup)

        assert result == ""
