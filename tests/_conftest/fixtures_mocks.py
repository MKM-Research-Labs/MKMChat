# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Mock objects for external dependencies."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_embeddings():
    """Return a mock HuggingFaceEmbeddings that produces deterministic vectors."""
    mock = MagicMock()
    mock.embed_query.return_value = [0.1] * 384
    mock.embed_documents.return_value = [[0.1] * 384]
    mock.model_name = "all-MiniLM-L6-v2"
    return mock


@pytest.fixture
def mock_faiss_service(monkeypatch):
    """Patch FAISSService globally to avoid loading real indices."""
    mock_svc = MagicMock()
    mock_svc.get_available_indices.return_value = {
        "misc": {"name": "Miscellaneous", "path": "/tmp/faiss/misc"},
        "phys": {"name": "Physical", "path": "/tmp/faiss/phys"},
    }
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = []
    mock_vs.similarity_search_with_score.return_value = []
    mock_svc.load_index.return_value = mock_vs
    mock_svc.load_default_index.return_value = mock_vs
    return mock_svc


@pytest.fixture
def mock_anthropic_api(monkeypatch):
    """Patch requests.post for Anthropic API calls."""
    from data import SAMPLE_LLM_RESPONSE_ANTHROPIC

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_LLM_RESPONSE_ANTHROPIC

    monkeypatch.setattr(
        "src.models.anthropic_model.requests.post",
        MagicMock(return_value=mock_resp),
    )
    return mock_resp


@pytest.fixture
def mock_perplexity_api(monkeypatch):
    """Patch requests.post for Perplexity API calls."""
    from data import SAMPLE_LLM_RESPONSE_PERPLEXITY

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_LLM_RESPONSE_PERPLEXITY

    monkeypatch.setattr(
        "src.models.perplexity_model.requests.post",
        MagicMock(return_value=mock_resp),
    )
    return mock_resp


@pytest.fixture
def mock_lm_studio_api(monkeypatch):
    """Patch requests.post for LM Studio API calls."""
    from data import SAMPLE_LLM_RESPONSE_LOCAL

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_LLM_RESPONSE_LOCAL

    monkeypatch.setattr(
        "src.models.local_model.requests.post",
        MagicMock(return_value=mock_resp),
    )
    return mock_resp
