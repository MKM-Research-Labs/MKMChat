# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# src/proc/processor.py
# Version: 2.0
# Last Updated: Feb 2026
"""
Main document processor class.
Orchestrates document processing and vector embedding.
"""

import os
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

from config import CONFIG, get_collection_config
from ..loaders import SUPPORTED_EXTENSIONS
from ..utils.file_utils import (
    load_json_file,
    save_json_file,
    get_supported_files,
    ensure_directory_exists,
    get_file_hash
)
from .vector_store import VectorStoreManager
from .document_handler import DocumentHandler
from .recovery import RecoveryHandler


class DocumentProcessor:
    """
    Handles document processing, indexing, and vector embedding.
    """

    def __init__(self, docs_type="misc"):
        """
        Initialize the document processor for a specific document collection.

        Args:
            docs_type (str): Type of document collection ("misc" or "phys")
        """
        self.docs_type = docs_type

        # Get collection configuration
        self.collection_config = get_collection_config(docs_type)

        # Configure paths
        self.docs_folder = self.collection_config['docs_folder']
        self.processed_files_path = self.collection_config['processed_file']
        self.faiss_path = self.collection_config['faiss_index']

        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name=CONFIG['embedding_model'],
            encode_kwargs={'normalize_embeddings': True}
        )

        # Create text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CONFIG['chunk_size'],
            chunk_overlap=CONFIG['chunk_overlap']
        )

        # Processing settings
        self.show_progress = True
        self.max_documents = CONFIG['default_max_docs']

        # Ensure directories exist
        ensure_directory_exists(self.docs_folder)
        ensure_directory_exists(os.path.dirname(self.processed_files_path))
        ensure_directory_exists(self.faiss_path)

        # Initialize sub-handlers
        self._init_handlers()

    def _init_handlers(self):
        """Initialize the modular handlers."""
        self.vector_store_manager = VectorStoreManager(
            self.faiss_path, self.embeddings, self.show_progress
        )
        self.document_handler = DocumentHandler(
            self.docs_folder, self.text_splitter, self.docs_type, self.show_progress
        )
        self.recovery_handler = RecoveryHandler(
            self.docs_folder, self.text_splitter, self.docs_type, self.processed_files_path
        )

    def load_processed_files(self):
        """Load the record of processed files from JSON."""
        return load_json_file(self.processed_files_path, default={})

    def save_processed_files(self, processed_files):
        """Save the record of processed files to JSON."""
        return save_json_file(self.processed_files_path, processed_files)

    def process_single_document(self, filename, processed_files, force_reprocess=False):
        """Process a single document and generate chunks."""
        return self.document_handler.process(
            filename, processed_files, force_reprocess,
            save_callback=self.save_processed_files,
            recovery_callback=self.recovery_handler.handle_problematic_document
        )

    def handle_problematic_document(self, filename, processed_files, error_msg=None):
        """Handle problematic documents by attempting recovery."""
        return self.recovery_handler.handle_problematic_document(
            filename, processed_files, error_msg
        )

    def diagnose_and_report_problematic_files(self):
        """Run diagnostics on error files and generate a report."""
        processed_files = self.load_processed_files()
        return self.recovery_handler.diagnose_and_report(processed_files)

    def setup_alternative_embeddings(self):
        """Set up alternative embeddings when default model fails."""
        success, embeddings = self.vector_store_manager.setup_alternative_embeddings()
        if success:
            self.embeddings = embeddings
            self._init_handlers()
        return success

    def process_documents(self, force_reprocess=False):
        """
        Process all supported documents with progress tracking.

        Args:
            force_reprocess (bool): Whether to reprocess all documents

        Returns:
            bool: True if processing completed successfully
        """
        processed_files = {} if force_reprocess else self.load_processed_files()
        all_chunks = []

        # Get list of supported files
        document_files = get_supported_files(self.docs_folder, SUPPORTED_EXTENSIONS)

        if not document_files:
            print(f"No supported files found in {self.docs_folder}.")
            print(f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")
            return False

        total_documents = len(document_files)

        # Identify files needing processing
        files_needing_processing = self._get_files_needing_processing(
            document_files, processed_files, force_reprocess
        )

        if not files_needing_processing:
            print(f"\nNo files need processing out of {total_documents} total documents")
            return True

        # Apply document limit
        files_to_process = self._apply_document_limit(files_needing_processing)

        print(f"\nProcessing {len(files_to_process)} out of {total_documents} total documents")
        file_indices = {f: idx for idx, f in enumerate(document_files, 1)}

        # Process each file
        with tqdm(total=len(files_to_process), desc="Processing documents",
                  unit="file", disable=not self.show_progress) as pbar:
            for filename in files_to_process:
                doc_position = file_indices[filename]
                pbar.set_description(f"Processing document {doc_position}/{total_documents}")
                chunks = self.process_single_document(filename, processed_files, force_reprocess)
                if chunks:
                    all_chunks.extend(chunks)
                pbar.update(1)

        # Update vector index
        if all_chunks:
            success = self._update_vector_index(all_chunks, processed_files, force_reprocess)
            if not success:
                return False
        else:
            print("\nNo new or modified files to process")
            self.save_processed_files(processed_files)

        # Cleanup
        self._cleanup_processed_files(processed_files)
        return True

    def _get_files_needing_processing(self, document_files, processed_files, force_reprocess):
        """Get list of files that need processing."""
        files_needing_processing = []

        for filename in document_files:
            file_path = os.path.join(self.docs_folder, filename)
            file_hash = get_file_hash(file_path)

            if (force_reprocess or
                filename not in processed_files or
                    processed_files[filename]['hash'] != file_hash):
                files_needing_processing.append(filename)

        return files_needing_processing

    def _apply_document_limit(self, files_needing_processing):
        """Apply max_documents limit if specified."""
        if self.max_documents is None:
            print(f"\nProcessing all {len(files_needing_processing)} files that need updating")
            return files_needing_processing

        if len(files_needing_processing) > self.max_documents:
            print(f"\nFound {len(files_needing_processing)} files needing processing")
            print(f"Limiting to {self.max_documents} files due to max_documents setting")
            return files_needing_processing[:self.max_documents]

        print(f"\nProcessing all {len(files_needing_processing)} files that need updating")
        return files_needing_processing

    def _update_vector_index(self, all_chunks, processed_files, force_reprocess):
        """Update or create the vector index with new chunks."""
        print(f"\nProcessing new content ({len(all_chunks)} chunks)...")

        texts, metadatas = self.vector_store_manager.prepare_texts(all_chunks)
        vector_store = None

        # Try to merge with existing index
        if os.path.exists(self.faiss_path) and not force_reprocess:
            existing_store = self.vector_store_manager.load_existing()
            if existing_store:
                print(f"Adding {len(all_chunks)} new chunks to existing store")
                vector_store = self.vector_store_manager.add_to_existing(
                    existing_store, texts, metadatas
                )
                print("Successfully merged new documents")
            else:
                vector_store = self.vector_store_manager.create_new(texts, metadatas)
        else:
            print("Creating new index...")
            vector_store = self.vector_store_manager.create_new(texts, metadatas)

        # Handle creation failure
        if vector_store is None:
            success, new_embeddings = self.vector_store_manager.try_alternative_embeddings(
                texts, metadatas
            )
            if success:
                self.embeddings = new_embeddings
                self._init_handlers()
            return success

        # Save and verify
        if not self.vector_store_manager.save(vector_store):
            return False

        self.save_processed_files(processed_files)
        self.vector_store_manager.verify()
        return True

    def _cleanup_processed_files(self, processed_files):
        """Remove records for files that no longer exist."""
        try:
            print("\nCleaning up processed files record...")
            current_files = set(os.listdir(self.docs_folder))
            processed_files = {k: v for k, v in processed_files.items() if k in current_files}
            self.save_processed_files(processed_files)
        except Exception as e:
            print(f"Warning during cleanup: {str(e)}")


def get_processor(collection_type):
    """
    Get a document processor for a specific collection type.

    Args:
        collection_type (str): Collection type ('misc' or 'phys')

    Returns:
        DocumentProcessor: Initialized document processor
    """
    return DocumentProcessor(docs_type=collection_type)
