# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
"""
Document Summariser

Main DocumentSummariser class for summarizing documents using FAISS indexes.
"""

import os
from datetime import datetime
from typing import List, Optional, Tuple

from tqdm import tqdm
from langchain_huggingface import HuggingFaceEmbeddings

from config import CONFIG, get_collection_config
from ..utils.file_utils import get_file_hash, ensure_directory_exists
from .models import SummaryResult, SummaryEntry
from .storage import load_json_file, save_json_file
from .faiss_reader import (
    create_safe_faiss_copy,
    cleanup_faiss_copy,
    get_document_chunks_from_faiss
)
from .llm_client import query_local_model_with_chunks, generate_basic_summary


class DocumentSummariser:
    """
    Handles document summarization using existing FAISS indexes.
    Creates a read-only copy to prevent corruption of production indexes.
    """

    def __init__(self, docs_type: str = "misc"):
        """
        Initialize the document summariser for a specific document collection.

        Args:
            docs_type: Type of document collection
                      ("misc", "phys", "pops", "hist", "mods", "corp")
        """
        self.docs_type = docs_type

        # Get collection configuration from centralized config
        self.collection_config = get_collection_config(docs_type)

        # Configure paths from centralized config
        self.docs_folder = self.collection_config['docs_folder']
        self.processed_files_path = self.collection_config['processed_file']
        self.faiss_path = self.collection_config['faiss_index']
        self.summary_file = self.collection_config['summary_file']

        # Initialize the text embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name=CONFIG['embedding_model'],
            encode_kwargs={'normalize_embeddings': True}
        )

        # Processing settings
        self.show_progress = True
        self.max_documents = CONFIG['default_max_docs']

        # Ensure directories exist
        ensure_directory_exists(self.docs_folder)
        ensure_directory_exists(os.path.dirname(self.summary_file))

    def load_processed_files(self) -> dict:
        """
        Load the record of processed files from JSON.

        Returns:
            Dictionary of processed file records
        """
        return load_json_file(self.processed_files_path, default={})

    def summarize_documents(
        self,
        max_docs: Optional[int] = None,
        force_reprocess: bool = False,
        clean: bool = False
    ) -> bool:
        """
        Summarize documents using existing FAISS index safely.
        Creates a temporary copy of FAISS index to prevent corruption.

        Args:
            max_docs: Maximum number of documents to summarize
            force_reprocess: Whether to reprocess even if already summarized
            clean: Whether to clear existing summaries before processing

        Returns:
            True if summarization completed successfully, False otherwise
        """
        # Create safe copy of FAISS index
        temp_dir = os.path.join(
            os.path.dirname(self.summary_file),
            f'temp_faiss_copy_{self.docs_type}'
        )
        temp_faiss_path, vector_store = create_safe_faiss_copy(
            self.faiss_path, temp_dir, self.embeddings
        )

        if not vector_store:
            print("Failed to create safe FAISS copy - cannot proceed")
            return False

        try:
            # Load existing summaries
            summarised_files = {} if clean else load_json_file(
                self.summary_file, default={}
            )

            # Get documents to summarize from processed files
            processed_files = self.load_processed_files()
            processed_success = [
                f for f, info in processed_files.items()
                if info.get('status') == 'SUCCESS'
            ]

            # Apply document limit
            if max_docs is None:
                max_docs = self.max_documents

            if max_docs and len(processed_success) > max_docs:
                document_files = processed_success[:max_docs]
            else:
                document_files = processed_success

            if not document_files:
                print("No successfully processed documents found to summarize.")
                return False

            print(f"\nSummarizing {len(document_files)} documents in {self.docs_type} collection")
            print("Using safe copy of FAISS index for chunk extraction")

            results: List[SummaryResult] = []

            # Process each document
            with tqdm(
                total=len(document_files),
                desc="Summarizing documents",
                disable=not self.show_progress
            ) as pbar:

                for document_name in document_files:
                    pbar.set_description(f"Summarizing {document_name}")

                    try:
                        result = self._summarize_single_document(
                            document_name,
                            vector_store,
                            summarised_files,
                            force_reprocess
                        )
                        results.append(result)

                        # Save after each document
                        save_json_file(self.summary_file, summarised_files)

                    except Exception as e:
                        print(f"Error summarizing {document_name}: {str(e)}")
                        results.append(SummaryResult(
                            document_name=document_name,
                            success=False,
                            message=str(e),
                            status="FAILED"
                        ))

                    pbar.update(1)

            # Print results summary
            self._print_results(results)

            success_count = sum(1 for r in results if r.success)
            return success_count > 0

        finally:
            cleanup_faiss_copy(temp_faiss_path)

    def _summarize_single_document(
        self,
        document_name: str,
        vector_store,
        summarised_files: dict,
        force_reprocess: bool
    ) -> SummaryResult:
        """
        Summarize a single document.

        Args:
            document_name: Name of the document
            vector_store: FAISS vector store
            summarised_files: Dictionary of existing summaries (modified in place)
            force_reprocess: Whether to reprocess even if already summarized

        Returns:
            SummaryResult with operation outcome
        """
        # Get file hash for change tracking
        document_path = os.path.join(self.docs_folder, document_name)
        file_hash = get_file_hash(document_path)

        # Skip if already summarized and hasn't changed
        if (not force_reprocess and
            document_name in summarised_files and
            summarised_files[document_name].get('hash') == file_hash):
            return SummaryResult(
                document_name=document_name,
                success=True,
                message="Used existing summary",
                status="SKIPPED"
            )

        # Extract chunks from FAISS index
        document_chunks = get_document_chunks_from_faiss(vector_store, document_name)

        if document_chunks:
            # Convert DocumentChunk objects to format expected by LLM client
            chunks_for_llm = [
                type('Chunk', (), {
                    'content': c.content,
                    'metadata': c.metadata
                })()
                for c in document_chunks
            ]

            # Get summary from local model
            summary = query_local_model_with_chunks(document_name, chunks_for_llm)

            if summary:
                summarised_files[document_name] = {
                    'hash': file_hash,
                    'summarised_date': datetime.now().isoformat(),
                    'num_chunks': len(document_chunks),
                    'summary': summary,
                    'summary_type': 'FULL'
                }

                return SummaryResult(
                    document_name=document_name,
                    success=True,
                    message="Summary from FAISS chunks",
                    status="SUCCESS",
                    summary=summary,
                    num_chunks=len(document_chunks)
                )

        # Generate basic fallback summary
        basic_summary = generate_basic_summary(document_name)

        summarised_files[document_name] = {
            'hash': file_hash,
            'summarised_date': datetime.now().isoformat(),
            'num_chunks': 0,
            'summary': basic_summary,
            'summary_type': 'BASIC_FALLBACK'
        }

        return SummaryResult(
            document_name=document_name,
            success=True,
            message="Basic summary",
            status="BASIC_FALLBACK",
            summary=basic_summary
        )

    def _print_results(self, results: List[SummaryResult]) -> None:
        """Print summary of results."""
        print("\n" + "=" * 60)
        print("SUMMARIZATION RESULTS")
        print("=" * 60)

        success_count = sum(1 for r in results if r.success)

        for result in results:
            status_symbol = "\u2713" if result.success else "\u2717"
            print(f"{status_symbol} {result.status}: {result.document_name}")

        print(f"\nCompleted: {success_count}/{len(results)} documents")
        print(f"Summary file: {self.summary_file}")


def get_summariser(collection_type: str) -> DocumentSummariser:
    """
    Get a document summariser for a specific collection type.

    Args:
        collection_type: Collection type
                        ('misc', 'phys', 'pops', 'hist', 'mods', 'corp')

    Returns:
        Initialized DocumentSummariser instance
    """
    return DocumentSummariser(docs_type=collection_type)
