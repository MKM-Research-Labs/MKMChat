# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
"""
Summary Batch Processor

Batch processing logic for generating book summaries across collections.
"""

import sys
from datetime import datetime
from typing import List, Optional

from config import get_all_collections, get_collection_config
from .models import ProcessingStats
from .storage import get_paths, load_json_file, save_json_file
from .faiss_reader import load_faiss_index, search_book_content
from .llm_client import call_llm_for_summary
from config import LOCAL_SUMMARY_MODEL


def initialize_embedding_model():
    """
    Initialize the embedding model once at startup.

    Returns:
        SentenceTransformer model or None if failed
    """
    print("Loading embedding model (one-time operation)...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded successfully")
        return model
    except Exception as e:
        print(f"Error loading embedding model: {e}")
        return None


def process_single_collection(
    knowledge_type: str,
    embedding_model
) -> ProcessingStats:
    """
    Process a single knowledge collection.

    Args:
        knowledge_type: The collection key (e.g., 'misc', 'phys')
        embedding_model: Pre-loaded embedding model instance

    Returns:
        ProcessingStats with results
    """
    collection_config = get_collection_config(knowledge_type)
    paths = get_paths(collection_config)

    print("\n" + "=" * 70)
    print(f"PROCESSING: {collection_config['name'].upper()} ({knowledge_type})")
    print("=" * 70)

    stats = ProcessingStats(
        collection=knowledge_type,
        name=collection_config["name"]
    )

    # Load FAISS index for this collection
    index, metadata = load_faiss_index(paths)
    if index is None or metadata is None:
        print(f"  Failed to load FAISS index for {knowledge_type}")
        stats.error = "Failed to load FAISS index"
        return stats

    # Load processed files list
    print(f"  Loading processed files from {paths['proc_files']}...")
    proc_files = load_json_file(paths['proc_files'])
    if not proc_files:
        print(f"  No processed files found for {knowledge_type}")
        stats.error = "No processed files found"
        return stats

    stats.total_books = len(proc_files)
    print(f"  Found {len(proc_files)} processed books")

    # Load existing summaries
    print(f"  Loading existing summaries from {paths['output_file']}...")
    existing_summaries = load_json_file(paths['output_file'], default={})
    print(f"  Found {len(existing_summaries)} existing summaries")

    # Identify books needing processing
    books_to_process = []
    books_already_done = []

    for book_name in proc_files.keys():
        if book_name in existing_summaries:
            books_already_done.append(book_name)
        else:
            books_to_process.append(book_name)

    stats.skipped = len(books_already_done)

    print(f"\n  Status for {knowledge_type}:")
    print(f"    Total books: {len(proc_files)}")
    print(f"    Already summarized: {len(books_already_done)}")
    print(f"    Need processing: {len(books_to_process)}")

    if not books_to_process:
        print(f"\n  All books in {knowledge_type} already have summaries!")
        return stats

    # Process books that need summaries
    print(f"\n  Processing {len(books_to_process)} books...")

    for i, book_name in enumerate(books_to_process, 1):
        print(f"\n  [{i}/{len(books_to_process)}] {book_name[:55]}...")

        # Search for relevant content
        context = search_book_content(book_name, embedding_model, index, metadata)

        if not context:
            print("    No relevant content found, skipping")
            stats.failed += 1
            continue

        print(f"    Found {len(context)} chars of context, generating summary...")

        # Generate summary
        summary = call_llm_for_summary(book_name, context)

        if summary:
            # Add to existing summaries
            existing_summaries[book_name] = {
                "hash": "generated",
                "summarised_date": datetime.now().isoformat(),
                "summary": summary,
                "summary_type": "FULL",
                "method": "FAISS_SEARCH_LLM",
                "model": LOCAL_SUMMARY_MODEL,
                "knowledge_type": knowledge_type
            }

            print(f"    Summary generated ({len(summary)} chars)")
            stats.successful += 1

            # Save after each successful summary
            save_json_file(paths['output_file'], existing_summaries)
        else:
            print("    Failed to generate summary (LLM error)")
            stats.failed += 1

    # Collection results
    print(f"\n  Results for {knowledge_type}:")
    print(f"    Successful: {stats.successful}")
    print(f"    Failed: {stats.failed}")
    print(f"    Skipped (already done): {stats.skipped}")
    print(f"    Total summaries now: {len(existing_summaries)}")

    return stats


def run_batch_processor(
    collections: Optional[List[str]] = None,
    list_only: bool = False
) -> int:
    """
    Run the batch processor for specified collections.

    Args:
        collections: List of collection keys to process, or None for all
        list_only: If True, just list available collections and exit

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    all_collections = get_all_collections()
    valid_types = list(all_collections.keys())

    # List mode
    if list_only:
        print("\nAvailable Knowledge Collections:")
        print("=" * 60)
        for key, config in all_collections.items():
            print(f"  {key}: {config['name']}")
            print(f"       {config['description']}")
        print("\nUsage:")
        print("  python3 book_summary.py              # Process all collections")
        print("  python3 book_summary.py -c misc      # Process only 'misc'")
        print("  python3 book_summary.py --list       # List collections")
        return 0

    # Determine which collections to process
    if collections is None:
        collections_to_process = valid_types
    else:
        collections_to_process = collections

    print("=" * 70)
    print("BATCH BOOK SUMMARY PROCESSOR")
    print("=" * 70)
    print(f"Collections to process: {', '.join(collections_to_process)}")
    print(f"Total collections: {len(collections_to_process)}")

    # Initialize embedding model once (shared across all collections)
    print("\n" + "-" * 70)
    print("INITIALIZATION")
    print("-" * 70)

    embedding_model = initialize_embedding_model()
    if embedding_model is None:
        print("Failed to load embedding model - aborting")
        return 1

    # Process each collection
    all_results: List[ProcessingStats] = []

    for idx, knowledge_type in enumerate(collections_to_process, 1):
        print(f"\n{'#' * 70}")
        print(f"# COLLECTION {idx} OF {len(collections_to_process)}: {knowledge_type.upper()}")
        print(f"{'#' * 70}")

        try:
            stats = process_single_collection(knowledge_type, embedding_model)
            all_results.append(stats)
        except Exception as e:
            print(f"Error processing collection {knowledge_type}: {str(e)}")
            all_results.append(ProcessingStats(
                collection=knowledge_type,
                name=all_collections[knowledge_type]["name"],
                error=str(e)
            ))

    # Print final summary
    _print_batch_summary(all_results)

    # Return appropriate exit code
    if all(r.error for r in all_results):
        return 1
    return 0


def _print_batch_summary(results: List[ProcessingStats]) -> None:
    """Print summary across all collections."""
    print("\n" + "=" * 70)
    print("BATCH SUMMARY")
    print("=" * 70)

    total_successful = 0
    total_failed = 0
    total_skipped = 0
    total_books = 0

    print("\nResults by Collection:")
    print("-" * 70)
    print(f"{'Collection':<12} {'Name':<25} {'OK':<8} {'Fail':<8} {'Skip':<8}")
    print("-" * 70)

    for result in results:
        if result.error:
            print(f"{result.collection:<12} {result.name[:25]:<25} ERROR: {result.error[:20]}")
        else:
            print(f"{result.collection:<12} {result.name[:25]:<25} "
                  f"{result.successful:<8} {result.failed:<8} {result.skipped:<8}")
            total_successful += result.successful
            total_failed += result.failed
            total_skipped += result.skipped
            total_books += result.total_books

    print("-" * 70)
    print(f"{'TOTAL':<12} {'':<25} {total_successful:<8} {total_failed:<8} {total_skipped:<8}")
    print("-" * 70)

    print(f"\nOverall Statistics:")
    print(f"  Total books across collections: {total_books}")
    print(f"  Summarized this run: {total_successful}")
    print(f"  Failed this run: {total_failed}")
    print(f"  Already had summaries: {total_skipped}")

    if total_successful > 0:
        print(f"\nSuccessfully added {total_successful} new book summaries!")

    if total_failed > 0:
        print(f"\nWarning: {total_failed} books failed - check LLM connection")
