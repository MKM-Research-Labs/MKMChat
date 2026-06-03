# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
"""
Summary Storage

Handles JSON file I/O and path management for summaries.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from config import get_collection_config, get_all_collections, PathManager


def get_paths(collection_config: Dict[str, Any]) -> Dict[str, str]:
    """
    Get file paths based on central CONFIG collection entry.

    Args:
        collection_config: Collection configuration dictionary

    Returns:
        Dictionary with paths for faiss_index, faiss_pkl, proc_files, output_file
    """
    faiss_dir = collection_config["faiss_index"]
    return {
        "faiss_index": os.path.join(faiss_dir, "index.faiss"),
        "faiss_pkl": os.path.join(faiss_dir, "index.pkl"),
        "proc_files": collection_config["processed_file"],
        "output_file": collection_config["summary_file"],
    }


def load_json_file(file_path: str, default: Optional[Any] = None) -> Any:
    """
    Load JSON file with error handling.

    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is invalid

    Returns:
        Loaded JSON data or default value
    """
    if default is None:
        default = {}

    if not os.path.exists(file_path):
        return default

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load {file_path}: {e}")
        return default


def save_json_file(file_path: str, data: Any) -> bool:
    """
    Save data to JSON file.

    Args:
        file_path: Path to JSON file
        data: Data to save

    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {e}")
        return False


def ensure_file_exists(file_path: Path) -> None:
    """
    Ensure the file exists, creating it as empty JSON if it doesn't.

    Args:
        file_path: Path to the file to check/create
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if not file_path.exists():
        with open(file_path, 'w') as f:
            json.dump({}, f)
        print(f"Created empty file: {file_path}")


def get_summary_files() -> Dict[str, Path]:
    """
    Get all summary file paths from config.

    Returns:
        Dictionary mapping collection key to summary file path
    """
    all_collections = get_all_collections()
    return {
        key: Path(config['summary_file'])
        for key, config in all_collections.items()
    }


def get_legacy_summary_path() -> Path:
    """
    Get path to legacy summary file for backward compatibility.

    Returns:
        Path to legacy summarised_files.json
    """
    paths = PathManager()
    return paths.json_dir / 'summarised_files.json'


def get_files_to_process(
    docs_type: Optional[str] = None
) -> List[Tuple[str, Path]]:
    """
    Get list of files to process based on docs_type.

    Args:
        docs_type: Type of document collection, or None for all

    Returns:
        List of tuples (collection_type, file_path)

    Raises:
        ValueError: If docs_type is not a valid collection
    """
    summary_files = get_summary_files()
    files_to_process = []

    if docs_type is not None:
        if docs_type in summary_files:
            files_to_process.append((docs_type, summary_files[docs_type]))
        else:
            raise ValueError(
                f"Unknown collection: {docs_type}. "
                f"Available: {list(summary_files.keys())}"
            )
    else:
        for collection_key, file_path in summary_files.items():
            files_to_process.append((collection_key, file_path))
        # Add legacy file for backward compatibility
        files_to_process.append(('legacy', get_legacy_summary_path()))

    return files_to_process
