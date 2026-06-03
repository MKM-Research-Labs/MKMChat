# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
"""
Summary Package

Document summarization functionality for MKMChat.
Provides batch processing, document summarization, and summary management.
"""

# Models
from .models import (
    SummaryResult,
    ProcessingStats,
    CleaningStats,
    DocumentChunk,
    SummaryEntry,
)

# Storage utilities
from .storage import (
    get_paths,
    load_json_file,
    save_json_file,
    get_summary_files,
)

# FAISS operations
from .faiss_reader import (
    load_faiss_index,
    search_book_content,
    get_document_chunks_from_faiss,
)

# LLM client
from .llm_client import (
    call_llm_for_summary,
    generate_basic_summary,
    clean_summary_text,
)

# Main classes
from .summariser import DocumentSummariser, get_summariser
from .cleaner import SummaryCleaner, run_cleaner, CLEANING_MODES

# Batch processing
from .batch import (
    run_batch_processor,
    process_single_collection,
    initialize_embedding_model,
)

__all__ = [
    # Models
    'SummaryResult',
    'ProcessingStats',
    'CleaningStats',
    'DocumentChunk',
    'SummaryEntry',
    # Storage
    'get_paths',
    'load_json_file',
    'save_json_file',
    'get_summary_files',
    # FAISS
    'load_faiss_index',
    'search_book_content',
    'get_document_chunks_from_faiss',
    # LLM
    'call_llm_for_summary',
    'generate_basic_summary',
    'clean_summary_text',
    # Classes
    'DocumentSummariser',
    'get_summariser',
    'SummaryCleaner',
    'run_cleaner',
    'CLEANING_MODES',
    # Batch
    'run_batch_processor',
    'process_single_collection',
    'initialize_embedding_model',
]
