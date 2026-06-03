# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/summary/storage.py."""

import json
import pytest
from unittest.mock import patch

from src.summary.storage import load_json_file, save_json_file


def test_read_write_json_roundtrip(tmp_path):
    """Data saved with save_json_file can be loaded back with load_json_file."""
    file_path = str(tmp_path / "data.json")
    data = {"book.pdf": {"hash": "abc", "summary": "A great book", "summary_type": "FULL"}}

    assert save_json_file(file_path, data) is True

    loaded = load_json_file(file_path)
    assert loaded == data


def test_read_missing_file_returns_default(tmp_path):
    """load_json_file returns the default value when the file does not exist."""
    missing = str(tmp_path / "no_such_file.json")

    result = load_json_file(missing, default={})
    assert result == {}

    result_list = load_json_file(missing, default=[])
    assert result_list == []


def test_load_json_file_default_none(tmp_path):
    """load_json_file with default=None falls back to empty dict."""
    missing = str(tmp_path / "missing.json")
    result = load_json_file(missing)
    assert result == {}


def test_load_json_file_invalid_json(tmp_path):
    """load_json_file returns default when file contains invalid JSON."""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not valid json {{{")

    result = load_json_file(str(bad_file), default={"fallback": True})
    assert result == {"fallback": True}


def test_save_json_file_creates_parent_dirs(tmp_path):
    """save_json_file creates intermediate directories if they don't exist."""
    nested = str(tmp_path / "a" / "b" / "c" / "data.json")
    assert save_json_file(nested, {"key": "val"}) is True
    loaded = load_json_file(nested)
    assert loaded == {"key": "val"}


def test_save_json_file_unicode(tmp_path):
    """save_json_file preserves unicode characters."""
    path = str(tmp_path / "unicode.json")
    data = {"title": "Les Mis\u00e9rables", "author": "\u5c0f\u5c71"}
    save_json_file(path, data)
    loaded = load_json_file(path)
    assert loaded["title"] == "Les Mis\u00e9rables"
    assert loaded["author"] == "\u5c0f\u5c71"


def test_ensure_file_exists_creates_file(tmp_path):
    """ensure_file_exists creates an empty JSON file when it doesn't exist."""
    from src.summary.storage import ensure_file_exists
    target = tmp_path / "sub" / "new.json"
    ensure_file_exists(target)
    assert target.exists()
    import json
    assert json.loads(target.read_text()) == {}


def test_ensure_file_exists_no_overwrite(tmp_path):
    """ensure_file_exists does not overwrite an existing file."""
    from src.summary.storage import ensure_file_exists
    target = tmp_path / "existing.json"
    target.write_text('{"existing": true}')
    ensure_file_exists(target)
    import json
    assert json.loads(target.read_text()) == {"existing": True}


def test_get_paths():
    """get_paths returns correct derived paths from collection config."""
    from src.summary.storage import get_paths
    config = {
        "faiss_index": "/data/faiss",
        "processed_file": "/data/processed.json",
        "summary_file": "/data/summaries.json",
    }
    paths = get_paths(config)
    assert paths["faiss_index"] == "/data/faiss/index.faiss"
    assert paths["faiss_pkl"] == "/data/faiss/index.pkl"
    assert paths["proc_files"] == "/data/processed.json"
    assert paths["output_file"] == "/data/summaries.json"


@pytest.fixture
def mock_collections():
    """Patch get_all_collections and get_collection_config for storage tests."""
    collections = {
        "misc": {
            "name": "Misc",
            "summary_file": "/tmp/misc_summaries.json",
        },
        "phys": {
            "name": "Phys",
            "summary_file": "/tmp/phys_summaries.json",
        },
    }
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.summary.storage.get_all_collections", lambda: collections)
        yield collections


def test_get_summary_files(mock_collections):
    """get_summary_files returns a dict mapping keys to Path objects."""
    from src.summary.storage import get_summary_files
    from pathlib import Path
    result = get_summary_files()
    assert set(result.keys()) == {"misc", "phys"}
    assert result["misc"] == Path("/tmp/misc_summaries.json")


def test_get_files_to_process_specific(mock_collections):
    """get_files_to_process with a specific docs_type returns only that collection."""
    from src.summary.storage import get_files_to_process
    result = get_files_to_process("misc")
    assert len(result) == 1
    assert result[0][0] == "misc"


def test_get_files_to_process_invalid(mock_collections):
    """get_files_to_process raises ValueError for unknown collection."""
    from src.summary.storage import get_files_to_process
    with pytest.raises(ValueError, match="Unknown collection"):
        get_files_to_process("nonexistent")


def test_get_files_to_process_all(mock_collections):
    """get_files_to_process with None returns all collections plus legacy."""
    from src.summary.storage import get_files_to_process
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "src.summary.storage.get_legacy_summary_path",
            lambda: __import__("pathlib").Path("/tmp/legacy.json"),
        )
        result = get_files_to_process(None)
    # misc + phys + legacy
    assert len(result) == 3
    types = [r[0] for r in result]
    assert "legacy" in types


# ---------------------------------------------------------------------------
# SummaryEntry tests (covers models.py lines 72-86, 91)
# ---------------------------------------------------------------------------

from src.summary.models import SummaryEntry


def test_summary_entry_to_dict():
    """SummaryEntry.to_dict returns all fields when populated."""
    entry = SummaryEntry(
        hash="abc123",
        summarised_date="2026-03-26",
        summary="A great summary",
        summary_type="FULL",
        num_chunks=10,
        method="map_reduce",
        model="deepseek-r1",
        knowledge_type="physics",
    )
    d = entry.to_dict()
    assert d["hash"] == "abc123"
    assert d["summarised_date"] == "2026-03-26"
    assert d["summary"] == "A great summary"
    assert d["summary_type"] == "FULL"
    assert d["num_chunks"] == 10
    assert d["method"] == "map_reduce"
    assert d["model"] == "deepseek-r1"
    assert d["knowledge_type"] == "physics"


def test_summary_entry_to_dict_optional_fields():
    """SummaryEntry.to_dict omits optional fields when they are None/zero."""
    entry = SummaryEntry(
        hash="abc",
        summarised_date="2026-01-01",
        summary="short",
        summary_type="BASIC_FALLBACK",
    )
    d = entry.to_dict()
    assert "hash" in d
    assert "summarised_date" in d
    assert "summary" in d
    assert "summary_type" in d
    # Optional fields should be absent
    assert "num_chunks" not in d
    assert "method" not in d
    assert "model" not in d
    assert "knowledge_type" not in d


def test_save_json_file_error(tmp_path):
    """save_json_file returns False when writing fails."""
    # Use a path that will fail (directory that can't be created)
    with patch("src.summary.storage.open", side_effect=OSError("disk full")):
        result = save_json_file(str(tmp_path / "fail.json"), {"key": "val"})
    assert result is False


def test_get_legacy_summary_path():
    """get_legacy_summary_path returns a Path to summarised_files.json."""
    from src.summary.storage import get_legacy_summary_path
    result = get_legacy_summary_path()
    assert str(result).endswith("summarised_files.json")


def test_summary_entry_from_dict():
    """SummaryEntry round-trips through to_dict/from_dict."""
    original = SummaryEntry(
        hash="xyz789",
        summarised_date="2026-03-26",
        summary="Round-trip test",
        summary_type="FULL",
        num_chunks=5,
        method="stuff",
        model="gpt-4",
        knowledge_type="misc",
    )
    d = original.to_dict()
    restored = SummaryEntry.from_dict(d)
    assert restored.hash == original.hash
    assert restored.summarised_date == original.summarised_date
    assert restored.summary == original.summary
    assert restored.summary_type == original.summary_type
    assert restored.num_chunks == original.num_chunks
    assert restored.method == original.method
    assert restored.model == original.model
    assert restored.knowledge_type == original.knowledge_type
