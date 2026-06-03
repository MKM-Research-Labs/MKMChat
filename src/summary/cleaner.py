# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
"""
Summary Cleaner

Clean and manage summary JSON files for document collections.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from config import get_all_collections
from .models import CleaningStats
from .storage import (
    load_json_file,
    save_json_file,
    ensure_file_exists,
    get_summary_files,
    get_legacy_summary_path,
    get_files_to_process
)


# Available cleaning modes (centralised in config.py)
from config import CLEANING_MODES


class SummaryCleaner:
    """
    A class to clean and manage summary JSON files for document collections.

    Cleaning modes:
    - fallback_only: Remove only BASIC_FALLBACK entries
    - force_all: Keep entries but force reprocessing by changing hashes
    - clean_all: Remove all entries (start fresh)
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize the SummaryCleaner.

        Args:
            base_dir: Base directory path. If None, auto-detects from script location.
        """
        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.base_dir = Path(base_dir).resolve()

        # Get all collections from centralized config
        all_collections = get_all_collections()

        # Available collections - dynamically from config
        self.COLLECTIONS = list(all_collections.keys())
        self.MODES = CLEANING_MODES

    def _clean_fallback_only(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Clean data by removing only BASIC_FALLBACK entries.

        Args:
            data: Original data dictionary

        Returns:
            Tuple of (cleaned_data, fallback_count)
        """
        fallback_count = sum(
            1 for info in data.values()
            if info.get('summary_type') == 'BASIC_FALLBACK'
        )

        cleaned_data = {
            k: v for k, v in data.items()
            if v.get('summary_type') != 'BASIC_FALLBACK'
        }

        return cleaned_data, fallback_count

    def _clean_force_all(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean data by modifying hash values to force reprocessing.

        Args:
            data: Original data dictionary

        Returns:
            Modified data dictionary (deep copy; original is not mutated)
        """
        import copy
        cleaned_data = copy.deepcopy(data)
        for key in cleaned_data:
            if 'hash' in cleaned_data[key]:
                cleaned_data[key]['hash'] = "modified_" + cleaned_data[key]['hash']

        return cleaned_data

    def _clean_all(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean data by removing all entries.

        Args:
            data: Original data dictionary

        Returns:
            Empty dictionary
        """
        return {}

    def clean_file(
        self,
        file_path: Path,
        collection_type: str,
        mode: str
    ) -> CleaningStats:
        """
        Clean a single summary file.

        Args:
            file_path: Path to the file to clean
            collection_type: Type of collection being cleaned
            mode: Cleaning mode

        Returns:
            CleaningStats with operation results
        """
        print(f"Processing {collection_type} summary file: {file_path}")

        # Ensure file exists
        ensure_file_exists(file_path)

        # Load existing file
        data = load_json_file(str(file_path), default={})

        # Count before cleaning
        total_before = len(data)

        # Apply cleaning based on mode
        if mode == "clean_all":
            cleaned_data = self._clean_all(data)
            print(f"Removing all {total_before} entries")
            removed_count = total_before

        elif mode == "fallback_only":
            cleaned_data, fallback_count = self._clean_fallback_only(data)
            print(f"Removing {fallback_count} fallback entries")
            removed_count = fallback_count

        elif mode == "force_all":
            cleaned_data = self._clean_force_all(data)
            print(f"Modified hashes for {len(cleaned_data)} entries to force reprocessing")
            removed_count = 0

        else:
            raise ValueError(f"Unknown cleaning mode: {mode}")

        # Save cleaned data
        save_json_file(str(file_path), cleaned_data)

        # Count after cleaning
        total_after = len(cleaned_data)

        print(f"Cleaned {file_path}")
        print(f"  - Entries before: {total_before}")
        print(f"  - Entries after: {total_after}")

        return CleaningStats(
            total_before=total_before,
            total_after=total_after,
            removed_count=removed_count
        )

    def clean(
        self,
        docs_type: Optional[str] = None,
        mode: str = "fallback_only"
    ) -> Dict[str, CleaningStats]:
        """
        Clean summary JSON files based on the selected mode.

        Args:
            docs_type: Type of document collection to clean, or None for all
            mode: Cleaning mode ("fallback_only", "force_all", or "clean_all")

        Returns:
            Dictionary containing CleaningStats for each processed file

        Raises:
            ValueError: If invalid docs_type or mode is provided
        """
        # Validate inputs
        if docs_type is not None and docs_type not in self.COLLECTIONS:
            raise ValueError(
                f"Invalid docs_type: {docs_type}. Must be one of: {self.COLLECTIONS}"
            )

        if mode not in self.MODES:
            raise ValueError(
                f"Invalid mode: {mode}. Must be one of: {self.MODES}"
            )

        print(f"Base directory: {self.base_dir}")

        # Get files to process
        files_to_process = get_files_to_process(docs_type)

        # Process each file
        results: Dict[str, CleaningStats] = {}
        for collection_type, file_path in files_to_process:
            try:
                stats = self.clean_file(file_path, collection_type, mode)
                results[collection_type] = stats
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                results[collection_type] = CleaningStats(error=str(e))

        return results

    def get_stats(
        self,
        docs_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics about the current state of summary files.

        Args:
            docs_type: Type of document collection to check, or None for all

        Returns:
            Dictionary containing statistics for each file
        """
        files_to_process = get_files_to_process(docs_type)
        stats: Dict[str, Dict[str, Any]] = {}

        for collection_type, file_path in files_to_process:
            try:
                ensure_file_exists(file_path)
                data = load_json_file(str(file_path), default={})

                total_entries = len(data)
                fallback_entries = sum(
                    1 for info in data.values()
                    if info.get('summary_type') == 'BASIC_FALLBACK'
                )

                stats[collection_type] = {
                    'total_entries': total_entries,
                    'fallback_entries': fallback_entries,
                    'processed_entries': total_entries - fallback_entries,
                    'file_path': str(file_path)
                }

            except Exception as e:
                stats[collection_type] = {'error': str(e)}

        return stats


def run_cleaner(
    collection: Optional[str] = None,
    mode: str = "fallback_only",
    stats_only: bool = False
) -> int:
    """
    Run the summary cleaner.

    Args:
        collection: Collection to clean, or None for all
        mode: Cleaning mode
        stats_only: If True, just show stats without cleaning

    Returns:
        Exit code (0 for success)
    """
    cleaner = SummaryCleaner()

    if stats_only:
        stats = cleaner.get_stats(collection)
        print("\nSummary File Statistics:")
        print("=" * 50)
        for coll, data in stats.items():
            if 'error' in data:
                print(f"{coll.upper()}: Error - {data['error']}")
            else:
                print(f"{coll.upper()}:")
                print(f"  Total entries: {data['total_entries']}")
                print(f"  Fallback entries: {data['fallback_entries']}")
                print(f"  Processed entries: {data['processed_entries']}")
                print(f"  File: {data['file_path']}")
    else:
        results = cleaner.clean(collection, mode)
        print("\nCleaning completed!")

        total_processed = sum(1 for r in results.values() if r.error is None)
        total_errors = sum(1 for r in results.values() if r.error is not None)

        print(f"Files processed successfully: {total_processed}")
        if total_errors > 0:
            print(f"Files with errors: {total_errors}")

    return 0
