# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for chat.py CLI helpers (parse_arguments, _resolve_collections_arg, etc.)."""

import json
import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from config import get_all_collections, CONFIG


# ── parse_arguments ──────────────────────────────────────────────────────


class TestParseArguments:
    def test_parse_arguments_defaults(self):
        """Verify default values when no args are supplied."""
        with patch("sys.argv", ["chat.py"]):
            from chat import parse_arguments

            args = parse_arguments()

        assert args.web_only is False
        assert args.process_only is False
        assert args.summarize_only is False
        assert args.list_summaries is False
        assert args.port == CONFIG["server_port"]
        assert args.host == CONFIG["server_host"]
        assert args.debug is True
        assert args.collection == "all"
        assert args.max_docs == 50
        assert args.force is False
        assert args.no_progress is False
        assert args.summarize is False


# ── _resolve_collections_arg ─────────────────────────────────────────────


class TestResolveCollections:
    def test_resolve_collections_all(self):
        """'all' should return every collection key."""
        from chat import _resolve_collections_arg

        result = _resolve_collections_arg("all")
        expected = list(get_all_collections().keys())
        assert result == expected

    def test_resolve_collections_single(self):
        """A single collection key should return a one-element list."""
        from chat import _resolve_collections_arg

        result = _resolve_collections_arg("misc")
        assert result == ["misc"]


# ── load_json_file ───────────────────────────────────────────────────────


class TestLoadJsonFile:
    def test_load_json_file_valid(self, tmp_path):
        """Create a JSON file, load it, verify contents."""
        from chat import load_json_file

        data = {"key": "value", "count": 42}
        json_path = tmp_path / "test.json"
        json_path.write_text(json.dumps(data))

        loaded = load_json_file(str(json_path))
        assert loaded == data

    def test_load_json_file_missing(self, tmp_path):
        """Missing file returns the default."""
        from chat import load_json_file

        result = load_json_file(str(tmp_path / "nonexistent.json"))
        assert result == {}

    def test_load_json_file_missing_custom_default(self, tmp_path):
        """Missing file with custom default returns that default."""
        from chat import load_json_file

        result = load_json_file(str(tmp_path / "nonexistent.json"), default=[])
        assert result == []

    def test_load_json_file_invalid_json(self, tmp_path):
        """Invalid JSON returns the default."""
        from chat import load_json_file

        bad_path = tmp_path / "bad.json"
        bad_path.write_text("{not valid json!!!")

        result = load_json_file(str(bad_path))
        assert result == {}


# ── get_file_hash ────────────────────────────────────────────────────────


class TestGetFileHash:
    def test_get_file_hash(self, tmp_path):
        """Create a file, verify hash is consistent and matches sha256."""
        from chat import get_file_hash

        test_file = tmp_path / "hashme.txt"
        content = b"Hello, hash world!"
        test_file.write_bytes(content)

        expected = hashlib.sha256(content).hexdigest()
        result = get_file_hash(str(test_file))
        assert result == expected

        # Calling again should produce the same result (deterministic)
        assert get_file_hash(str(test_file)) == expected

    def test_get_file_hash_missing(self, tmp_path):
        """Missing file returns empty string."""
        from chat import get_file_hash

        result = get_file_hash(str(tmp_path / "nope.txt"))
        assert result == ""
