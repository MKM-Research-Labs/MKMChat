#!/usr/bin/env python3
# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
