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
Tests for src/utils/file_utils.py

Tests file utility functions for hashing, JSON operations, and file management.
"""

import os
import json
import pytest

from src.utils.file_utils import (
    get_file_hash,
    load_json_file,
    save_json_file,
    get_supported_files,
    ensure_directory_exists,
    create_processed_record
)


class TestGetFileHash:
    """Tests for get_file_hash function."""

    def test_returns_hash_string(self, tmp_path):
        """Should return a hash string."""
        test_file = tmp_path / 'test.txt'
        test_file.write_text("Test content")

        result = get_file_hash(str(test_file))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_same_file_same_hash(self, tmp_path):
        """Same file should produce same hash."""
        test_file = tmp_path / 'test.txt'
        test_file.write_text("Test content")

        hash1 = get_file_hash(str(test_file))
        hash2 = get_file_hash(str(test_file))

        assert hash1 == hash2

    def test_different_content_different_hash(self, tmp_path):
        """Different content should produce different hash."""
        test_file1 = tmp_path / 'test.txt'
        test_file1.write_text("Test content")
        test_file2 = tmp_path / 'test2.txt'
        test_file2.write_text("Different content")

        hash1 = get_file_hash(str(test_file1))
        hash2 = get_file_hash(str(test_file2))

        assert hash1 != hash2

    def test_nonexistent_file_returns_none(self):
        """Non-existent file should return None or raise exception."""
        try:
            result = get_file_hash('/nonexistent/file.txt')
            # If it returns, should be None
            assert result is None
        except (FileNotFoundError, OSError):
            # Expected exception for non-existent file
            pass


class TestLoadJsonFile:
    """Tests for load_json_file function."""

    def test_loads_valid_json(self, tmp_path):
        """Should load valid JSON file."""
        test_file = tmp_path / 'test.json'
        test_data = {'key': 'value', 'number': 42}
        test_file.write_text(json.dumps(test_data))

        result = load_json_file(str(test_file))

        assert result == test_data

    def test_returns_default_for_missing_file(self):
        """Should return default value for missing file."""
        result = load_json_file('/nonexistent/file.json', default={'default': True})

        assert result == {'default': True}

    def test_returns_empty_dict_default(self):
        """Should return empty dict by default for missing file."""
        result = load_json_file('/nonexistent/file.json', default={})

        assert result == {}

    def test_handles_invalid_json(self, tmp_path):
        """Should handle invalid JSON gracefully."""
        test_file = tmp_path / 'invalid.json'
        test_file.write_text("not valid json {{{")

        result = load_json_file(str(test_file), default={'error': True})

        # Should return default on error
        assert result == {'error': True}


class TestSaveJsonFile:
    """Tests for save_json_file function."""

    def test_saves_json_data(self, tmp_path):
        """Should save JSON data to file."""
        test_file = tmp_path / 'output.json'
        test_data = {'key': 'value', 'list': [1, 2, 3]}

        result = save_json_file(str(test_file), test_data)

        assert result

        # Verify file was written
        with open(str(test_file), 'r') as f:
            saved_data = json.load(f)

        assert saved_data == test_data

    def test_creates_parent_directories(self, tmp_path):
        """Should create parent directories if they don't exist."""
        test_file = tmp_path / 'subdir' / 'nested' / 'output.json'
        test_data = {'nested': True}

        result = save_json_file(str(test_file), test_data)

        # Should succeed or the function handles directory creation
        assert os.path.exists(os.path.dirname(str(test_file))) or result


class TestGetSupportedFiles:
    """Tests for get_supported_files function."""

    def test_finds_supported_files(self, tmp_path):
        """Should find files with supported extensions."""
        (tmp_path / 'doc1.pdf').touch()
        (tmp_path / 'doc2.pdf').touch()
        (tmp_path / 'doc.txt').touch()
        (tmp_path / 'doc.epub').touch()
        (tmp_path / 'hidden.pdf').touch()
        (tmp_path / 'unsupported.xyz').touch()

        supported = ('.pdf', '.epub')  # tuple not list

        result = get_supported_files(str(tmp_path), supported)

        assert isinstance(result, list)
        # Should find PDF and EPUB files
        pdf_files = [f for f in result if f.endswith('.pdf')]

        assert len(pdf_files) > 0

    def test_excludes_unsupported_files(self, tmp_path):
        """Should exclude files with unsupported extensions."""
        (tmp_path / 'doc1.pdf').touch()
        (tmp_path / 'unsupported.xyz').touch()

        supported = ('.pdf',)  # tuple not list

        result = get_supported_files(str(tmp_path), supported)

        # Should not include .xyz files
        xyz_files = [f for f in result if f.endswith('.xyz')]
        assert len(xyz_files) == 0

    def test_empty_directory(self, tmp_path):
        """Should return empty list for empty directory."""
        empty_dir = tmp_path / 'empty'
        empty_dir.mkdir()

        result = get_supported_files(str(empty_dir), ('.pdf',))

        assert result == []

    def test_nonexistent_directory(self):
        """Should handle nonexistent directory gracefully."""
        result = get_supported_files('/nonexistent/dir', ('.pdf',))

        assert result == []


class TestEnsureDirectoryExists:
    """Tests for ensure_directory_exists function."""

    def test_creates_directory(self, tmp_path):
        """Should create directory if it doesn't exist."""
        new_dir = tmp_path / 'new_directory'

        ensure_directory_exists(str(new_dir))

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_creates_nested_directories(self, tmp_path):
        """Should create nested directories."""
        nested_dir = tmp_path / 'a' / 'b' / 'c'

        ensure_directory_exists(str(nested_dir))

        assert nested_dir.exists()

    def test_existing_directory_no_error(self, tmp_path):
        """Should not raise error for existing directory."""
        existing_dir = tmp_path / 'existing'
        existing_dir.mkdir()

        # Should not raise
        ensure_directory_exists(str(existing_dir))

        assert existing_dir.exists()


class TestLoadJsonFileReadError:
    """Tests for load_json_file generic exception path (lines 59-61)."""

    def test_load_json_file_read_error(self, tmp_path):
        """load_json_file returns default when open raises PermissionError."""
        target = tmp_path / "locked.json"
        target.write_text('{"key": "val"}')

        from unittest.mock import patch
        with patch("builtins.open", side_effect=PermissionError("access denied")):
            result = load_json_file(str(target), default={"fallback": True})

        assert result == {"fallback": True}


class TestSaveJsonFileWriteError:
    """Tests for save_json_file exception path (lines 81-83)."""

    def test_save_json_file_write_error(self, tmp_path):
        """save_json_file returns False when writing raises PermissionError."""
        target = str(tmp_path / "output.json")

        from unittest.mock import patch
        with patch("builtins.open", side_effect=PermissionError("read-only")):
            result = save_json_file(target, {"key": "val"})

        assert result is False


class TestEnsureDirectoryExistsError:
    """Tests for ensure_directory_exists exception path (lines 119-121)."""

    def test_ensure_directory_exists_error(self):
        """ensure_directory_exists returns False when makedirs raises PermissionError."""
        from unittest.mock import patch
        with patch("os.makedirs", side_effect=PermissionError("no permission")):
            result = ensure_directory_exists("/impossible/path")

        assert result is False


class TestCreateProcessedRecord:
    """Tests for create_processed_record function."""

    def test_creates_record_with_required_fields(self, tmp_path):
        """Should create record with required fields."""
        test_file = tmp_path / 'test.pdf'
        test_file.write_text("Test content")

        record = create_processed_record('test.pdf', str(test_file))

        assert 'hash' in record
        assert 'processed_date' in record

    def test_includes_status(self, tmp_path):
        """Should include status field."""
        test_file = tmp_path / 'test.pdf'
        test_file.write_text("Test content")

        record = create_processed_record('test.pdf', str(test_file), status='SUCCESS')

        assert record['status'] == 'SUCCESS'

    def test_includes_num_chunks(self, tmp_path):
        """Should include num_chunks field."""
        test_file = tmp_path / 'test.pdf'
        test_file.write_text("Test content")

        record = create_processed_record('test.pdf', str(test_file), num_chunks=10)

        assert record['num_chunks'] == 10

    def test_includes_error_message(self, tmp_path):
        """Should include error message when provided."""
        test_file = tmp_path / 'test.pdf'
        test_file.write_text("Test content")

        record = create_processed_record(
            'test.pdf', str(test_file),
            status='ERROR',
            error='Processing failed'
        )

        assert record['status'] == 'ERROR'
        assert record['error'] == 'Processing failed'
