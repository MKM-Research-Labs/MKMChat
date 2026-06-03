# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/book_summary.py CLI wrapper."""

import sys
from unittest.mock import patch, MagicMock


def test_main_processes_all_by_default():
    """main() with no args calls run_batch_processor with collections=None."""
    with patch("sys.argv", ["book_summary.py"]), \
         patch("src.book_summary.run_batch_processor", return_value=0) as mock_run, \
         patch("src.book_summary.get_all_collections", return_value={
             "misc": {}, "phys": {},
         }):
        from src.book_summary import main
        result = main()

    assert result == 0
    mock_run.assert_called_once_with(collections=None, list_only=False)


def test_main_processes_single_collection():
    """main() with -c misc calls run_batch_processor for that collection."""
    with patch("sys.argv", ["book_summary.py", "-c", "misc"]), \
         patch("src.book_summary.run_batch_processor", return_value=0) as mock_run, \
         patch("src.book_summary.get_all_collections", return_value={
             "misc": {}, "phys": {},
         }):
        from src.book_summary import main
        result = main()

    assert result == 0
    mock_run.assert_called_once_with(collections=["misc"], list_only=False)


def test_main_list_only():
    """main() with --list passes list_only=True."""
    with patch("sys.argv", ["book_summary.py", "--list"]), \
         patch("src.book_summary.run_batch_processor", return_value=0) as mock_run, \
         patch("src.book_summary.get_all_collections", return_value={
             "misc": {}, "phys": {},
         }):
        from src.book_summary import main
        result = main()

    assert result == 0
    mock_run.assert_called_once_with(collections=None, list_only=True)


def test_main_returns_nonzero_on_failure():
    """main() passes through non-zero return code from run_batch_processor."""
    with patch("sys.argv", ["book_summary.py"]), \
         patch("src.book_summary.run_batch_processor", return_value=1) as mock_run, \
         patch("src.book_summary.get_all_collections", return_value={
             "misc": {},
         }):
        from src.book_summary import main
        result = main()

    assert result == 1


def test_main_with_all_explicit():
    """main() with -c all passes collections=None."""
    with patch("sys.argv", ["book_summary.py", "-c", "all"]), \
         patch("src.book_summary.run_batch_processor", return_value=0) as mock_run, \
         patch("src.book_summary.get_all_collections", return_value={
             "misc": {}, "phys": {},
         }):
        from src.book_summary import main
        result = main()

    assert result == 0
    mock_run.assert_called_once_with(collections=None, list_only=False)
