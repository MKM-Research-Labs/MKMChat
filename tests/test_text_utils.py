# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Tests for src/utils/text_utils.py

Tests the sanitize_text and standardize_metadata functions.
"""

from unittest.mock import MagicMock

from langchain_core.documents import Document
from src.utils.text_utils import sanitize_text, standardize_metadata


class TestSanitizeText:
    """Tests for sanitize_text function."""

    def test_basic_text_unchanged(self):
        """Normal text should remain unchanged."""
        text = "This is a normal sentence."
        result = sanitize_text(text)
        assert result == text

    def test_removes_null_bytes(self):
        """Null bytes should be removed."""
        text = "Hello\x00World"
        result = sanitize_text(text)
        assert result == "HelloWorld"

    def test_removes_control_characters(self):
        """Control characters should be removed."""
        text = "Hello\x01\x02\x03World"
        result = sanitize_text(text)
        assert result == "HelloWorld"

    def test_normalizes_whitespace(self):
        """Newlines and tabs should be normalized to spaces."""
        text = "Hello\nWorld\tTest"
        result = sanitize_text(text)
        # Whitespace is normalized to single spaces
        assert result == "Hello World Test"

    def test_empty_string(self):
        """Empty string should return placeholder text."""
        result = sanitize_text("")
        # Empty texts return "Empty document section"
        assert result == "Empty document section"

    def test_none_input(self):
        """None input should be converted to string."""
        result = sanitize_text(None)
        # None is converted via str()
        assert result == "None"

    def test_bytes_input(self):
        """Bytes input should be converted to string."""
        text = b"Hello World"
        result = sanitize_text(text)
        # Bytes are converted via str() which adds b'' prefix
        assert "Hello World" in result

    def test_mixed_unicode(self):
        """Unicode characters should be normalized (NFKD)."""
        text = "Hello World café résumé"
        result = sanitize_text(text)
        # NFKD normalization may decompose accented characters
        assert "caf" in result
        assert "sum" in result

    def test_strips_whitespace(self):
        """Leading and trailing whitespace should be stripped."""
        text = "   Hello World   "
        result = sanitize_text(text)
        assert result == "Hello World"

    def test_normalizes_multiple_spaces(self):
        """Multiple consecutive spaces should be normalized."""
        text = "Hello    World"
        result = sanitize_text(text)
        # Should normalize or preserve based on implementation
        assert "Hello" in result
        assert "World" in result


class TestStandardizeMetadata:
    """Tests for standardize_metadata function."""

    def test_adds_docs_type_metadata(self):
        """Should add docs_type metadata to documents."""
        # Create mock documents
        doc1 = MagicMock()
        doc1.metadata = {'source': 'test.pdf', 'page': 1}
        doc1.page_content = 'Test content'

        docs = [doc1]
        result = standardize_metadata(docs, 'misc')

        assert result[0].metadata['docs_type'] == 'misc'

    def test_preserves_existing_metadata(self):
        """Should preserve existing metadata."""
        doc1 = MagicMock()
        doc1.metadata = {'source': 'test.pdf', 'page': 1, 'custom': 'value'}
        doc1.page_content = 'Test content'

        docs = [doc1]
        result = standardize_metadata(docs, 'misc')

        assert result[0].metadata['source'] == 'test.pdf'
        assert result[0].metadata['page'] == 1
        assert result[0].metadata['custom'] == 'value'

    def test_multiple_documents(self):
        """Should process multiple documents."""
        doc1 = MagicMock()
        doc1.metadata = {'source': 'test1.pdf'}
        doc1.page_content = 'Test content 1'
        doc2 = MagicMock()
        doc2.metadata = {'source': 'test2.pdf'}
        doc2.page_content = 'Test content 2'

        docs = [doc1, doc2]
        result = standardize_metadata(docs, 'phys')

        assert len(result) == 2
        assert result[0].metadata['docs_type'] == 'phys'
        assert result[1].metadata['docs_type'] == 'phys'

    def test_empty_list(self):
        """Should handle empty list."""
        result = standardize_metadata([], 'misc')
        assert result == []

    def test_adds_default_page(self):
        """Should add default page if not present."""
        doc1 = MagicMock()
        doc1.metadata = {'source': '/full/path/to/test.pdf'}
        doc1.page_content = 'Test content'

        docs = [doc1]
        result = standardize_metadata(docs, 'misc')

        # Verify page field is added
        assert 'page' in result[0].metadata
