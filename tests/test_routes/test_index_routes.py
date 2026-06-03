# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/routes/index_routes.py."""

import pytest
from unittest.mock import patch


def test_get_available_indices(client):
    """GET /get_available_indices should return indices and active key."""
    response = client.get("/get_available_indices")
    assert response.status_code == 200
    data = response.get_json()
    assert "indices" in data
    assert "active" in data
    # Fixture sets up "misc" and "phys"
    assert "misc" in data["indices"]
    assert "phys" in data["indices"]
    assert data["active"] == "misc"


def test_get_available_models(client):
    """GET /get_available_models should return a models key."""
    response = client.get("/get_available_models")
    assert response.status_code == 200
    data = response.get_json()
    assert "models" in data
    assert isinstance(data["models"], dict)
    assert len(data["models"]) > 0


def test_switch_index_valid(client, flask_app):
    """POST /switch_index with a valid key should succeed."""
    response = client.post("/switch_index", json={"index_key": "misc"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["active_index"] == "misc"


def test_switch_index_invalid(client):
    """POST /switch_index with a nonexistent key should return 400."""
    response = client.post("/switch_index", json={"index_key": "nonexistent"})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_switch_index_not_json(client):
    """POST /switch_index with text/plain should return 400."""
    response = client.post(
        "/switch_index",
        data="not json",
        content_type="text/plain",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_switch_index_missing_key(client):
    """POST /switch_index JSON without index_key should return 400."""
    response = client.post("/switch_index", json={"other_field": "value"})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_get_available_indices_exception(client, flask_app):
    """When AVAILABLE_INDICES access raises, expect 500."""
    original = flask_app.AVAILABLE_INDICES

    # Make AVAILABLE_INDICES a property-like object that raises on access
    class _Bomb:
        """Object that raises on iteration / JSON serialization."""
        def __iter__(self):
            raise RuntimeError("indices unavailable")
        def items(self):
            raise RuntimeError("indices unavailable")
        def keys(self):
            raise RuntimeError("indices unavailable")

    flask_app.AVAILABLE_INDICES = _Bomb()
    try:
        response = client.get("/get_available_indices")
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
    finally:
        flask_app.AVAILABLE_INDICES = original


def test_get_available_models_exception(client, flask_app):
    """When AVAILABLE_MODELS access raises, expect 500."""
    original = flask_app.AVAILABLE_MODELS

    class _Bomb:
        def __iter__(self):
            raise RuntimeError("models unavailable")
        def items(self):
            raise RuntimeError("models unavailable")
        def keys(self):
            raise RuntimeError("models unavailable")

    flask_app.AVAILABLE_MODELS = _Bomb()
    try:
        response = client.get("/get_available_models")
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
    finally:
        flask_app.AVAILABLE_MODELS = original


def test_switch_index_load_exception(client, flask_app):
    """When _load_faiss_index raises during switch, expect 500."""
    with patch.object(flask_app, "_load_faiss_index", side_effect=RuntimeError("FAISS load failed")):
        response = client.post("/switch_index", json={"index_key": "phys"})
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
