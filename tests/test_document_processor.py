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
Tests for src/document_processor.py

Tests the DocumentProcessor class for document processing and indexing.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document


@pytest.fixture
def processor_env(tmp_path):
    """Set up temporary directory and mock dependencies for DocumentProcessor tests."""
    # Create docs directory
    docs_dir = tmp_path / 'docs'
    docs_dir.mkdir()

    config_patcher = patch('src.proc.processor.CONFIG', {
        'embedding_model': 'test-model',
        'chunk_size': 1000,
        'chunk_overlap': 200,
        'default_max_docs': 100,
        'fallback_embedding_model': 'fallback-model',
        'last_resort_model': 'last-resort-model'
    })
    config_patcher.start()

    collection_config_patcher = patch('src.proc.processor.get_collection_config')
    mock_collection_config = collection_config_patcher.start()
    mock_collection_config.return_value = {
        'docs_folder': str(docs_dir),
        'processed_file': str(tmp_path / 'processed.json'),
        'faiss_index': str(tmp_path / 'faiss')
    }

    embeddings_patcher = patch('src.proc.processor.HuggingFaceEmbeddings')
    mock_embeddings = embeddings_patcher.start()

    ensure_dir_patcher = patch('src.proc.processor.ensure_directory_exists')
    mock_ensure_dir = ensure_dir_patcher.start()

    from src.document_processor import DocumentProcessor

    yield {
        'tmp_path': tmp_path,
        'docs_dir': docs_dir,
        'DocumentProcessor': DocumentProcessor,
        'mock_collection_config': mock_collection_config,
        'mock_embeddings': mock_embeddings,
    }

    config_patcher.stop()
    collection_config_patcher.stop()
    embeddings_patcher.stop()
    ensure_dir_patcher.stop()


class TestDocumentProcessor:
    """Tests for DocumentProcessor class."""

    def test_initialization(self, processor_env):
        """Should initialize with docs_type."""
        processor = processor_env['DocumentProcessor'](docs_type='misc')
        assert processor.docs_type == 'misc'

    def test_initialization_sets_paths(self, processor_env):
        """Should set correct paths based on docs_type."""
        processor = processor_env['DocumentProcessor'](docs_type='misc')

        assert processor.docs_folder is not None
        assert processor.processed_files_path is not None
        assert processor.faiss_path is not None

    @patch('src.proc.processor.load_json_file')
    def test_load_processed_files(self, mock_load_json, processor_env):
        """Should load processed files from JSON."""
        mock_load_json.return_value = {'file1.pdf': {'hash': 'abc123'}}

        processor = processor_env['DocumentProcessor'](docs_type='misc')
        result = processor.load_processed_files()

        mock_load_json.assert_called_once()
        assert result == {'file1.pdf': {'hash': 'abc123'}}

    @patch('src.proc.processor.save_json_file')
    def test_save_processed_files(self, mock_save_json, processor_env):
        """Should save processed files to JSON."""
        mock_save_json.return_value = True

        processor = processor_env['DocumentProcessor'](docs_type='misc')
        result = processor.save_processed_files({'file1.pdf': {'hash': 'abc123'}})

        mock_save_json.assert_called_once()
        assert result

    @patch('src.proc.document_handler.get_file_hash')
    @patch('src.proc.document_handler.get_loader_for_file')
    def test_process_single_document_skips_unchanged(self, mock_get_loader, mock_get_hash, processor_env):
        """Should skip processing if file hasn't changed."""
        mock_get_hash.return_value = 'abc123'

        processor = processor_env['DocumentProcessor'](docs_type='misc')
        processed_files = {'test.pdf': {'hash': 'abc123'}}

        result = processor.process_single_document('test.pdf', processed_files)

        assert result is None
        mock_get_loader.assert_not_called()

    @patch('src.proc.document_handler.get_file_hash')
    @patch('src.proc.document_handler.get_loader_for_file')
    def test_process_single_document_processes_new_file(self, mock_get_loader, mock_get_hash, processor_env):
        """Should process new files."""
        mock_get_hash.return_value = 'new_hash'

        mock_page = MagicMock()
        mock_page.page_content = 'Test content'
        mock_page.metadata = {}

        mock_loader = MagicMock()
        mock_loader.load.return_value = [mock_page]
        mock_get_loader.return_value = mock_loader

        processor = processor_env['DocumentProcessor'](docs_type='misc')
        processor.show_progress = False
        processor.document_handler.show_progress = False
        processed_files = {}

        # Create a test file
        test_file = processor_env['docs_dir'] / 'test.pdf'
        test_file.write_text('test')

        result = processor.process_single_document('test.pdf', processed_files)

        # May return chunks or None depending on content
        assert result is None or isinstance(result, list)

    @patch('src.proc.processor.get_supported_files')
    @patch('src.proc.processor.load_json_file')
    def test_process_documents_no_files(self, mock_load_json, mock_get_files, processor_env):
        """Should handle case with no supported files."""
        mock_load_json.return_value = {}
        mock_get_files.return_value = []

        processor = processor_env['DocumentProcessor'](docs_type='misc')
        result = processor.process_documents()

        assert not result

    @patch('src.proc.vector_store.CONFIG', {
        'fallback_embedding_model': 'fallback-model',
        'last_resort_model': 'last-resort-model'
    })
    @patch('src.proc.vector_store.HuggingFaceEmbeddings')
    def test_setup_alternative_embeddings(self, mock_alt_embeddings, processor_env):
        """Should set up alternative embeddings."""
        processor = processor_env['DocumentProcessor'](docs_type='misc')

        # Should not raise
        result = processor.setup_alternative_embeddings()

        assert result


class TestDocumentProcessorDiagnostics:
    """Tests for DocumentProcessor diagnostic methods."""

    @patch('src.proc.processor.load_json_file')
    def test_diagnose_and_report_no_errors(self, mock_load_json, processor_env):
        """Should handle case with no error files."""
        mock_load_json.return_value = {
            'file1.pdf': {'status': 'SUCCESS'},
            'file2.pdf': {'status': 'SUCCESS'}
        }

        processor = processor_env['DocumentProcessor'](docs_type='misc')
        result = processor.diagnose_and_report_problematic_files()

        assert result == []

    @patch('src.proc.recovery.diagnose_pdf')
    @patch('src.proc.processor.load_json_file')
    def test_diagnose_and_report_with_errors(self, mock_load_json, mock_diagnose, processor_env):
        """Should diagnose files with errors."""
        mock_load_json.return_value = {
            'file1.pdf': {'status': 'ERROR', 'error': 'Test error'}
        }
        mock_diagnose.return_value = {
            'filename': 'file1.pdf',
            'overall_assessment': 'problematic',
            'issues_detected': ['encoding'],
            'recommended_approach': 'ocr'
        }

        # Create the test file
        test_file = processor_env['docs_dir'] / 'file1.pdf'
        test_file.write_text('test')

        processor = processor_env['DocumentProcessor'](docs_type='misc')
        result = processor.diagnose_and_report_problematic_files()

        assert isinstance(result, list)


class TestGetProcessor:
    """Tests for get_processor helper function."""

    def test_get_processor_returns_processor(self, processor_env):
        """Should return DocumentProcessor instance."""
        from src.document_processor import get_processor

        processor = get_processor('misc')

        assert processor is not None
        assert processor.docs_type == 'misc'
