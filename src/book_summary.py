#!/usr/bin/env python3
# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
"""
Batch Book Summary Processor

CLI wrapper for batch summary processing across knowledge collections.

Usage:
    python3 book_summary.py              # Process ALL collections
    python3 book_summary.py -c misc      # Process only 'misc' collection
    python3 book_summary.py -c phys      # Process only 'phys' collection
    python3 book_summary.py --list       # List available collections
"""

import os
import sys
import argparse

# Add the project root to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_all_collections
from src.summary import run_batch_processor


def main():
    """Main entry point for CLI."""
    all_collections = get_all_collections()
    valid_types = list(all_collections.keys())

    parser = argparse.ArgumentParser(
        description="Batch Book Summary Processor - processes knowledge collections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 book_summary.py              # Process all collections
  python3 book_summary.py -c misc      # Process only 'misc' collection
  python3 book_summary.py -c phys      # Process only 'phys' collection
  python3 book_summary.py --list       # List available collections
        """
    )
    parser.add_argument(
        "--collection", "-c",
        choices=valid_types + ["all"],
        default="all",
        help=f"Collection to process: {', '.join(valid_types)}, or 'all' (default: all)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available collections and exit"
    )

    args = parser.parse_args()

    # Determine collections to process
    if args.collection == "all":
        collections = None  # None means all
    else:
        collections = [args.collection]

    return run_batch_processor(
        collections=collections,
        list_only=args.list
    )


if __name__ == "__main__":
    sys.exit(main())
