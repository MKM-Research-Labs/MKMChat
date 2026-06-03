# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

"""
Document handling for individual document processing.
Handles loading, sanitization, and chunking of documents.
"""

import os
from typing import List, Optional
from tqdm import tqdm

# Updated: was 'from langchain.schema import Document'
from langchain_core.documents import Document

from ..loaders import get_loader_for_file
from ..utils.text_utils import sanitize_text, standardize_metadata
from ..utils.file_utils import get_file_hash, create_processed_record


class DocumentHandler:
    """Handles processing of individual documents."""

    def __init__(self, docs_folder: str, text_splitter, docs_type: str, show_progress: bool = True):
        """
        Initialize the document handler.

        Args:
            docs_folder (str): Path to documents folder
            text_splitter: Text splitter instance
            docs_type (str): Document collection type
            show_progress (bool): Whether to show progress bars
        """
        self.docs_folder = docs_folder
        self.text_splitter = text_splitter
        self.docs_type = docs_type
        self.show_progress = show_progress

    def process(
        self,
        filename: str,
        processed_files: dict,
        force_reprocess: bool = False,
        save_callback=None,
        recovery_callback=None,
    ) -> Optional[List[Document]]:
        """
        Process a single document and generate chunks.

        Args:
            filename (str): Name of the document file
            processed_files (dict): Dictionary of processed file records
            force_reprocess (bool): Whether to reprocess even if unchanged
            save_callback: Callback to save processed files
            recovery_callback: Callback for document recovery

        Returns:
            Optional[List[Document]]: List of document chunks if successful, else None
        """
        file_path = os.path.join(self.docs_folder, filename)
        file_hash = get_file_hash(file_path)

        # Skip if file hasn't changed
        if not force_reprocess and filename in processed_files:
            if processed_files[filename]["hash"] == file_hash:
                return None

        try:
            print(f"\nProcessing {filename} from {self.docs_type}...")
            loader = get_loader_for_file(file_path)

            try:
                pages = loader.load()

                if not pages:
                    print(f"Document {filename} appears to be empty or unreadable")
                    processed_files[filename] = create_processed_record(
                        filename, file_path, status="EMPTY", num_chunks=0
                    )
                    if save_callback:
                        save_callback(processed_files)
                    return None

                sanitized_pages = self._sanitize_pages(pages)
                chunks = self._split_pages(sanitized_pages)

                if not chunks:
                    print(f"No chunks were generated from {filename}")
                    processed_files[filename] = create_processed_record(
                        filename, file_path, status="NO_CHUNKS", num_chunks=0
                    )
                    if save_callback:
                        save_callback(processed_files)
                    return None

                processed_files[filename] = create_processed_record(
                    filename, file_path, status="SUCCESS", num_chunks=len(chunks)
                )
                print(f"Generated {len(chunks)} chunks from {filename}")
                chunks = standardize_metadata(chunks, self.docs_type)
                return chunks

            except IndexError as e:
                error_msg = str(e)
                print(f"Index error with {filename}: {error_msg}")
                return self._handle_processing_error(
                    filename, file_path, error_msg, processed_files, save_callback, recovery_callback
                )

            except Exception as e:
                error_msg = str(e)
                print(f"Error processing {filename}: {error_msg}")
                return self._handle_processing_error(
                    filename, file_path, error_msg, processed_files, save_callback, recovery_callback
                )

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            processed_files[filename] = create_processed_record(
                filename, file_path, status="ERROR", num_chunks=0, error=str(e)
            )
            if save_callback:
                save_callback(processed_files)
            return None

    def _handle_processing_error(
        self,
        filename: str,
        file_path: str,
        error_msg: str,
        processed_files: dict,
        save_callback=None,
        recovery_callback=None,
    ) -> Optional[List[Document]]:
        """Shared error handling for inner processing exceptions."""
        if recovery_callback:
            recovery_chunks = recovery_callback(filename, processed_files, error_msg)
            if recovery_chunks:
                return recovery_chunks

        processed_files[filename] = create_processed_record(
            filename, file_path, status="ERROR", num_chunks=0, error=error_msg
        )
        if save_callback:
            save_callback(processed_files)
        return None

    def _sanitize_pages(self, pages: List[Document]) -> List[Document]:
        """
        Sanitize page content.

        Args:
            pages (List[Document]): List of Document pages

        Returns:
            List[Document]: List of sanitized Document pages
        """
        return [
            Document(
                page_content=sanitize_text(page.page_content),
                metadata=page.metadata,
            )
            for page in pages
        ]

    def _split_pages(self, pages: List[Document]) -> List[Document]:
        """
        Split pages into chunks with progress tracking.

        Args:
            pages (List[Document]): List of Document pages

        Returns:
            List[Document]: List of Document chunks
        """
        chunks = []
        with tqdm(total=len(pages), desc="Splitting document", disable=not self.show_progress) as pbar:
            for page in pages:
                chunks.extend(self.text_splitter.split_documents([page]))
                pbar.update(1)
        return chunks

    def needs_processing(self, filename: str, processed_files: dict, force_reprocess: bool = False) -> bool:
        """
        Check if a file needs processing.

        Args:
            filename (str): Name of the file
            processed_files (dict): Dictionary of processed file records
            force_reprocess (bool): Whether to force reprocessing

        Returns:
            bool: True if file needs processing
        """
        if force_reprocess:
            return True

        file_path = os.path.join(self.docs_folder, filename)
        file_hash = get_file_hash(file_path)

        if filename not in processed_files:
            return True

        return processed_files[filename]["hash"] != file_hash
