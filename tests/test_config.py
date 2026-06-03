# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for config.py (PathManager, get_collection_config, etc.)."""

import pytest
from pathlib import Path

from config import (
    PathManager,
    CONFIG,
    paths,
    get_collection_config,
    get_all_collections,
)

ALL_COLLECTION_KEYS = ["misc", "phys", "pops", "hist", "mods", "corp", "back"]


# ── PathManager._ensure_directories ─────────────────────────────────────


class TestPathManagerDirs:
    def test_path_manager_creates_dirs(self):
        """Verify _ensure_directories creates the expected directories."""
        pm = paths  # singleton already created at import

        assert pm.data_dir.is_dir()
        assert pm.json_dir.is_dir()
        assert pm.docs_root.is_dir()
        assert pm.faiss_root.is_dir()
        assert pm.templates_dir.is_dir()
        assert pm.static_dir.is_dir()


# ── get_docs_dir ─────────────────────────────────────────────────────────


class TestGetDocsDir:
    @pytest.mark.parametrize("collection", ALL_COLLECTION_KEYS)
    def test_get_docs_dir(self, collection):
        """Each of the 7 collections should return a valid Path."""
        result = paths.get_docs_dir(collection)
        assert isinstance(result, Path)
        assert collection in str(result)

    def test_get_docs_dir_invalid(self):
        """Invalid collection raises ValueError."""
        with pytest.raises(ValueError, match="Unknown collection type"):
            paths.get_docs_dir("nonexistent")


# ── get_faiss_dir ────────────────────────────────────────────────────────


class TestGetFaissDir:
    @pytest.mark.parametrize("collection", ALL_COLLECTION_KEYS)
    def test_get_faiss_dir(self, collection):
        """Each valid collection returns a Path containing the key."""
        result = paths.get_faiss_dir(collection)
        assert isinstance(result, Path)
        assert collection in str(result)

    def test_get_faiss_dir_invalid(self):
        """Invalid collection raises ValueError."""
        with pytest.raises(ValueError, match="Unknown collection type"):
            paths.get_faiss_dir("nonexistent")


# ── get_collection_config ────────────────────────────────────────────────


class TestGetCollectionConfig:
    @pytest.mark.parametrize("collection", ALL_COLLECTION_KEYS)
    def test_get_collection_config_valid(self, collection):
        """Verify returns dict with expected keys for each collection."""
        cfg = get_collection_config(collection)
        assert isinstance(cfg, dict)
        for key in ("name", "description", "docs_folder", "faiss_index", "summary_file"):
            assert key in cfg, f"Missing key '{key}' in {collection} config"

    def test_get_collection_config_invalid(self):
        """Invalid collection raises ValueError."""
        with pytest.raises(ValueError, match="Unknown collection type"):
            get_collection_config("nonexistent")


# ── get_all_collections ──────────────────────────────────────────────────


class TestGetAllCollections:
    def test_get_all_collections(self):
        """Verify returns all 7 collections."""
        all_cols = get_all_collections()
        assert isinstance(all_cols, dict)
        assert set(all_cols.keys()) == set(ALL_COLLECTION_KEYS)


# ── CONFIG structure ─────────────────────────────────────────────────────


class TestConfigStructure:
    def test_config_has_expected_keys(self):
        """Verify CONFIG dict contains essential top-level keys."""
        expected_keys = [
            "chunk_size",
            "chunk_overlap",
            "default_max_docs",
            "embedding_model",
            "supported_extensions",
            "collections",
            "server_host",
            "server_port",
            "server_debug",
        ]
        for key in expected_keys:
            assert key in CONFIG, f"Missing expected key '{key}' in CONFIG"

        # Verify collections is a dict with 7 entries
        assert isinstance(CONFIG["collections"], dict)
        assert len(CONFIG["collections"]) == 7
