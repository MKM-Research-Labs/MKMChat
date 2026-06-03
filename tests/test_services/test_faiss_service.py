# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/services/faiss_service.py (FAISSService)."""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from config import get_all_collections


@pytest.fixture
def faiss_svc():
    """Create a FAISSService with mocked embeddings to avoid downloading models."""
    with patch("src.services.faiss_service.HuggingFaceEmbeddings") as MockEmbed:
        mock_embed_instance = MagicMock()
        mock_embed_instance.embed_query.return_value = [0.1] * 384
        MockEmbed.return_value = mock_embed_instance

        from src.services.faiss_service import FAISSService

        svc = FAISSService()
        yield svc


# ── get_available_indices ────────────────────────────────────────────────


class TestAvailableIndices:
    def test_get_available_indices(self, faiss_svc):
        """Verify returns dict of all collections with name and path keys."""
        indices = faiss_svc.get_available_indices()
        all_collections = get_all_collections()

        assert isinstance(indices, dict)
        assert set(indices.keys()) == set(all_collections.keys())

        for key, info in indices.items():
            assert "name" in info
            assert "path" in info


# ── load_index ───────────────────────────────────────────────────────────


class TestLoadIndex:
    def test_load_index_valid(self, faiss_svc):
        """Mock FAISS.load_local success, verify vector store returned."""
        mock_vs = MagicMock()

        with patch("src.services.faiss_service.FAISS.load_local", return_value=mock_vs):
            result = faiss_svc.load_index("misc")

        assert result is mock_vs
        assert faiss_svc.is_loaded("misc")

    def test_load_index_invalid_key(self, faiss_svc):
        """Invalid key should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid index key"):
            faiss_svc.load_index("nonexistent_collection")

    def test_load_index_caching(self, faiss_svc):
        """Loading the same key twice should only call FAISS.load_local once."""
        mock_vs = MagicMock()

        with patch(
            "src.services.faiss_service.FAISS.load_local", return_value=mock_vs
        ) as mock_load:
            faiss_svc.load_index("misc")
            faiss_svc.load_index("misc")

        mock_load.assert_called_once()


# ── search ───────────────────────────────────────────────────────────────


class TestSearch:
    def test_search(self, faiss_svc):
        """Mock load_index and similarity_search_with_score, verify results."""
        mock_doc = MagicMock()
        mock_doc.page_content = "sample text"
        expected_results = [(mock_doc, 0.85)]

        mock_vs = MagicMock()
        mock_vs.similarity_search_with_score.return_value = expected_results

        with patch("src.services.faiss_service.FAISS.load_local", return_value=mock_vs):
            results = faiss_svc.search("misc", "test query", k=3)

        assert results == expected_results
        mock_vs.similarity_search_with_score.assert_called_once_with("test query", k=3)


# ── clear_cache ──────────────────────────────────────────────────────────


class TestClearCache:
    def test_clear_cache_specific(self, faiss_svc):
        """Clear one key, others remain."""
        mock_vs = MagicMock()

        with patch("src.services.faiss_service.FAISS.load_local", return_value=mock_vs):
            faiss_svc.load_index("misc")
            faiss_svc.load_index("phys")

        assert faiss_svc.is_loaded("misc")
        assert faiss_svc.is_loaded("phys")

        faiss_svc.clear_cache("misc")
        assert not faiss_svc.is_loaded("misc")
        assert faiss_svc.is_loaded("phys")

    def test_clear_cache_all(self, faiss_svc):
        """Clear everything."""
        mock_vs = MagicMock()

        with patch("src.services.faiss_service.FAISS.load_local", return_value=mock_vs):
            faiss_svc.load_index("misc")
            faiss_svc.load_index("phys")

        faiss_svc.clear_cache()
        assert faiss_svc.get_loaded_indices() == []


# ── is_loaded / get_loaded_indices ───────────────────────────────────────


class TestLoadedState:
    def test_is_loaded(self, faiss_svc):
        """Check before and after loading."""
        assert not faiss_svc.is_loaded("misc")

        mock_vs = MagicMock()
        with patch("src.services.faiss_service.FAISS.load_local", return_value=mock_vs):
            faiss_svc.load_index("misc")

        assert faiss_svc.is_loaded("misc")

    def test_get_loaded_indices(self, faiss_svc):
        """Verify list of loaded keys."""
        mock_vs = MagicMock()

        with patch("src.services.faiss_service.FAISS.load_local", return_value=mock_vs):
            faiss_svc.load_index("misc")
            faiss_svc.load_index("phys")

        loaded = faiss_svc.get_loaded_indices()
        assert set(loaded) == {"misc", "phys"}


# ── Additional coverage tests ───────────────────────────────────────────


class TestLoadDefaultIndex:
    def test_load_default_index_success(self, faiss_svc):
        """load_default_index returns the vector store on success."""
        mock_vs = MagicMock()
        with patch("src.services.faiss_service.FAISS.load_local", return_value=mock_vs):
            result = faiss_svc.load_default_index()
        assert result is mock_vs

    def test_load_default_index_failure(self, faiss_svc):
        """load_default_index returns None when loading fails."""
        with patch("src.services.faiss_service.FAISS.load_local", side_effect=RuntimeError("load failed")):
            result = faiss_svc.load_default_index()
        assert result is None

    def test_load_default_index_invalid_key(self, faiss_svc):
        """load_default_index returns None for an invalid default key."""
        result = faiss_svc.load_default_index(default_key="nonexistent")
        assert result is None


class TestLoadIndexException:
    def test_load_index_raises_on_load_failure(self, faiss_svc):
        """load_index re-raises when FAISS.load_local fails."""
        with patch("src.services.faiss_service.FAISS.load_local", side_effect=RuntimeError("corrupt index")):
            with pytest.raises(RuntimeError, match="corrupt index"):
                faiss_svc.load_index("misc")

    def test_load_index_not_cached_after_failure(self, faiss_svc):
        """load_index does not cache the index when loading fails."""
        with patch("src.services.faiss_service.FAISS.load_local", side_effect=RuntimeError("fail")):
            with pytest.raises(RuntimeError):
                faiss_svc.load_index("misc")
        assert not faiss_svc.is_loaded("misc")


class TestGetCachedIndex:
    def test_get_cached_index_not_loaded(self, faiss_svc):
        """get_cached_index returns None when index is not loaded."""
        result = faiss_svc.get_cached_index("misc")
        assert result is None

    def test_get_cached_index_loaded(self, faiss_svc):
        """get_cached_index returns the store when it is loaded."""
        mock_vs = MagicMock()
        with patch("src.services.faiss_service.FAISS.load_local", return_value=mock_vs):
            faiss_svc.load_index("misc")
        result = faiss_svc.get_cached_index("misc")
        assert result is mock_vs

    def test_get_cached_index_invalid_key(self, faiss_svc):
        """get_cached_index returns None for a key that was never loaded."""
        result = faiss_svc.get_cached_index("nonexistent")
        assert result is None


class TestClearCacheNonExistentKey:
    def test_clear_cache_key_not_loaded(self, faiss_svc):
        """clear_cache with a key that is not loaded does nothing."""
        # Should not raise
        faiss_svc.clear_cache("misc")
        assert not faiss_svc.is_loaded("misc")
