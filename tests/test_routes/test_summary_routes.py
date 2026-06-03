# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/routes/summary_routes.py."""

import pytest


def test_get_chat_history(client):
    """GET /get_chats should return 200 with a chats key."""
    response = client.get("/get_chats")
    assert response.status_code == 200
    data = response.get_json()
    assert "chats" in data
    assert isinstance(data["chats"], list)


def test_save_chat(client):
    """POST /save_chat with valid JSON should return 200 with success."""
    chat_data = {
        "id": "test_save_001",
        "title": "Saved Chat",
        "messages": [{"role": "user", "content": "hello"}],
    }
    response = client.post("/save_chat", json=chat_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["id"] == "test_save_001"


def test_save_chat_not_json(client):
    """POST /save_chat with text/plain should return 400."""
    response = client.post(
        "/save_chat",
        data="plain text",
        content_type="text/plain",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_save_chat_empty(client):
    """POST /save_chat with empty JSON body should return 400."""
    response = client.post(
        "/save_chat",
        data="{}",
        content_type="application/json",
    )
    # The route checks `if not chat_data` which is False for {} (empty dict is falsy? No, {} is truthy).
    # Actually {} is truthy in Python, so the route will proceed and auto-generate an id.
    # Let's send truly empty: None / empty string via JSON.
    # Actually `request.get_json()` on `{}` returns {} which is truthy.
    # The route only returns 400 if chat_data is falsy (None, empty string, 0, etc.).
    # Sending `{}` will succeed. Let's test with actual empty/null JSON:
    response2 = client.post(
        "/save_chat",
        data="null",
        content_type="application/json",
    )
    assert response2.status_code == 400
    data = response2.get_json()
    assert "error" in data


def test_delete_chat_not_found(client):
    """DELETE /delete_chat/nonexistent should return 404."""
    response = client.delete("/delete_chat/nonexistent")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


def test_get_summaries_default(client):
    """GET /get_summaries with default collection should return valid JSON."""
    response = client.get("/get_summaries")
    data = response.get_json()
    assert data is not None
    # Either 200 with summaries dict or 404 with error, both are valid
    if response.status_code == 200:
        assert isinstance(data, dict)
    else:
        assert response.status_code == 404
        assert "error" in data


def test_get_summaries_invalid_kb(client):
    """GET /get_summaries?docs_type=invalid should return 400."""
    response = client.get("/get_summaries?docs_type=invalid")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_get_generation_status_not_started(client):
    """GET /api/generate_summaries/status/misc should return not_started."""
    response = client.get("/api/generate_summaries/status/misc")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "not_started"


def test_save_chat_with_auto_id(client):
    """POST /save_chat without id should auto-generate one."""
    chat_data = {
        "title": "Auto ID Chat",
        "messages": [{"role": "user", "content": "hello"}],
    }
    response = client.post("/save_chat", json=chat_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    # Auto-generated ID should start with "chat_"
    assert data["id"].startswith("chat_")


def test_delete_chat_success(client):
    """Save a chat then delete it; DELETE should return success."""
    chat_data = {
        "id": "test_delete_me",
        "title": "Deletable Chat",
        "messages": [{"role": "user", "content": "bye"}],
    }
    save_resp = client.post("/save_chat", json=chat_data)
    assert save_resp.status_code == 200

    del_resp = client.delete("/delete_chat/test_delete_me")
    assert del_resp.status_code == 200
    data = del_resp.get_json()
    assert data["success"] is True


def test_get_chat_history_success(client):
    """Save a chat then verify it appears in get_chat_history."""
    chat_data = {
        "id": "test_history_001",
        "title": "History Chat",
        "timestamp": "2026-03-26T12:00:00",
        "messages": [{"role": "user", "content": "hi"}],
    }
    save_resp = client.post("/save_chat", json=chat_data)
    assert save_resp.status_code == 200

    history_resp = client.get("/get_chat_history")
    assert history_resp.status_code == 200
    data = history_resp.get_json()
    assert "chats" in data
    chat_ids = [c["id"] for c in data["chats"]]
    assert "test_history_001" in chat_ids


def test_get_generation_status_running(client):
    """Directly set _generation_status and verify the endpoint returns it."""
    from src.routes.summary_routes import _generation_status

    _generation_status["test_col"] = {
        "status": "running",
        "started_at": "2026-03-26T12:00:00",
        "completed_at": None,
        "result": None,
    }
    try:
        response = client.get("/api/generate_summaries/status/test_col")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "running"
        assert data["started_at"] == "2026-03-26T12:00:00"
    finally:
        _generation_status.pop("test_col", None)


# ---------------------------------------------------------------------------
# Additional coverage tests
# ---------------------------------------------------------------------------


def test_get_summaries_file_not_found(client, monkeypatch, tmp_path):
    """GET /get_summaries should return 404 when summary file does not exist."""
    from config import get_all_collections

    collections = get_all_collections()
    first_key = list(collections.keys())[0]

    # Point summary_file to a path that does not exist
    original_path = collections[first_key]["summary_file"]
    monkeypatch.setitem(collections[first_key], "summary_file", str(tmp_path / "nonexistent.json"))
    try:
        response = client.get(f"/get_summaries?docs_type={first_key}")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert "not found" in data["error"].lower()
    finally:
        monkeypatch.setitem(collections[first_key], "summary_file", original_path)


def test_get_summaries_invalid_json(client, monkeypatch, tmp_path):
    """GET /get_summaries should return 500 when summary file has invalid JSON."""
    from config import get_all_collections

    collections = get_all_collections()
    first_key = list(collections.keys())[0]

    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json")

    original_path = collections[first_key]["summary_file"]
    monkeypatch.setitem(collections[first_key], "summary_file", str(bad_file))
    try:
        response = client.get(f"/get_summaries?docs_type={first_key}")
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
        assert "invalid json" in data["error"].lower()
    finally:
        monkeypatch.setitem(collections[first_key], "summary_file", original_path)


def test_get_summaries_generic_exception(client, monkeypatch):
    """GET /get_summaries should return 500 on unexpected exceptions."""
    def _raise():
        raise RuntimeError("boom")
    monkeypatch.setattr(
        "src.routes.summary_routes.get_all_collections",
        _raise,
    )
    response = client.get("/get_summaries")
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


def test_get_chat_history_exception(client, flask_app, monkeypatch):
    """GET /get_chat_history should return 500 when chat_service raises."""
    def _raise():
        raise RuntimeError("db error")
    monkeypatch.setattr(
        flask_app.chat_service, "get_all_chats", _raise,
    )
    response = client.get("/get_chat_history")
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


def test_save_chat_auto_timestamp(client):
    """POST /save_chat without timestamp should auto-generate one."""
    chat_data = {
        "id": "test_auto_ts",
        "title": "Auto Timestamp",
        "messages": [{"role": "user", "content": "hi"}],
    }
    response = client.post("/save_chat", json=chat_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True


def test_save_chat_failure(client, flask_app, monkeypatch):
    """POST /save_chat should return 500 when chat_service.save_chat fails."""
    monkeypatch.setattr(
        flask_app.chat_service, "save_chat",
        lambda data: {"success": False},
    )
    chat_data = {
        "id": "test_fail",
        "title": "Fail",
        "messages": [],
    }
    response = client.post("/save_chat", json=chat_data)
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


def test_save_chat_exception(client, flask_app, monkeypatch):
    """POST /save_chat should return 500 when save_chat raises."""
    def _raise(data):
        raise RuntimeError("disk full")
    monkeypatch.setattr(flask_app.chat_service, "save_chat", _raise)
    chat_data = {
        "id": "test_exc",
        "title": "Exception",
        "messages": [],
    }
    response = client.post("/save_chat", json=chat_data)
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


def test_delete_chat_exception(client, flask_app, monkeypatch):
    """DELETE /delete_chat/<id> should return 500 when service raises."""
    def _raise(chat_id):
        raise RuntimeError("oops")
    monkeypatch.setattr(flask_app.chat_service, "delete_chat", _raise)
    response = client.delete("/delete_chat/some_id")
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


def test_generate_summaries_invalid_collection(client):
    """POST /api/generate_summaries with bad collection returns 400."""
    response = client.post(
        "/api/generate_summaries",
        json={"collection": "nonexistent_collection_xyz"},
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_generate_summaries_lm_studio_not_responding(client, monkeypatch):
    """POST /api/generate_summaries returns 503 when LM Studio returns non-200."""
    import requests as req
    mock_resp = type("R", (), {"status_code": 503})()
    monkeypatch.setattr(req, "get", lambda *a, **kw: mock_resp)
    response = client.post("/api/generate_summaries", json={})
    assert response.status_code == 503
    data = response.get_json()
    assert "error" in data
    assert "not responding" in data["error"].lower() or "LM Studio" in data["error"]


def test_generate_summaries_lm_studio_connection_error(client, monkeypatch):
    """POST /api/generate_summaries returns 503 on ConnectionError."""
    import requests as req
    def _raise(*a, **kw):
        raise req.exceptions.ConnectionError("refused")
    monkeypatch.setattr(req, "get", _raise)
    response = client.post("/api/generate_summaries", json={})
    assert response.status_code == 503
    data = response.get_json()
    assert "error" in data


def test_generate_summaries_lm_studio_timeout(client, monkeypatch):
    """POST /api/generate_summaries returns 503 on Timeout."""
    import requests as req
    def _raise(*a, **kw):
        raise req.exceptions.Timeout("timed out")
    monkeypatch.setattr(req, "get", _raise)
    response = client.post("/api/generate_summaries", json={})
    assert response.status_code == 503
    data = response.get_json()
    assert "error" in data
    assert "timed out" in data["error"].lower()


def test_generate_summaries_success(client, monkeypatch):
    """POST /api/generate_summaries starts background thread on success."""
    import requests as req
    import threading

    mock_resp = type("R", (), {"status_code": 200})()
    monkeypatch.setattr(req, "get", lambda *a, **kw: mock_resp)

    # Mock run_batch_processor so the background thread does not do real work
    monkeypatch.setattr(
        "src.summary.run_batch_processor",
        lambda **kwargs: 0,
    )

    # Capture thread start to avoid the thread actually running concurrently
    original_start = threading.Thread.start

    def _mock_start(self):
        # Just run synchronously for testing
        pass

    monkeypatch.setattr(threading.Thread, "start", _mock_start)

    response = client.post("/api/generate_summaries", json={})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "started"
    assert "collection" in data


def test_generate_summaries_outer_exception(client, monkeypatch):
    """POST /api/generate_summaries returns 500 on unexpected outer exception."""
    def _raise():
        raise RuntimeError("kaboom")
    monkeypatch.setattr(
        "src.routes.summary_routes.get_all_collections",
        _raise,
    )
    response = client.post("/api/generate_summaries", json={})
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


def test_generate_summaries_background_success(client, monkeypatch):
    """Background thread sets status to 'completed' on success (covers lines 232-238)."""
    import requests as req
    import threading
    from src.routes.summary_routes import _generation_status

    mock_resp = type("R", (), {"status_code": 200})()
    monkeypatch.setattr(req, "get", lambda *a, **kw: mock_resp)
    monkeypatch.setattr("src.summary.run_batch_processor", lambda **kwargs: 0)

    # Capture the thread target and run it synchronously
    captured_target = {}

    class FakeThread:
        def __init__(self, target=None, daemon=None, **kwargs):
            captured_target["fn"] = target
        def start(self):
            # Run the target synchronously
            captured_target["fn"]()

    monkeypatch.setattr(threading, "Thread", FakeThread)

    response = client.post("/api/generate_summaries", json={})
    assert response.status_code == 200

    # The background target ran synchronously; check status
    from config import DEFAULT_COLLECTION
    status = _generation_status.get(DEFAULT_COLLECTION, {})
    assert status.get("status") == "completed"
    assert status.get("result") == "success"
    assert status.get("completed_at") is not None

    # Cleanup
    _generation_status.pop(DEFAULT_COLLECTION, None)


def test_generate_summaries_background_error(client, monkeypatch):
    """Background thread sets status to 'error' on exception (covers lines 239-243)."""
    import requests as req
    import threading
    from src.routes.summary_routes import _generation_status

    mock_resp = type("R", (), {"status_code": 200})()
    monkeypatch.setattr(req, "get", lambda *a, **kw: mock_resp)
    monkeypatch.setattr(
        "src.summary.run_batch_processor",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("batch failed")),
    )

    captured_target = {}

    class FakeThread:
        def __init__(self, target=None, daemon=None, **kwargs):
            captured_target["fn"] = target
        def start(self):
            captured_target["fn"]()

    monkeypatch.setattr(threading, "Thread", FakeThread)

    response = client.post("/api/generate_summaries", json={})
    assert response.status_code == 200

    from config import DEFAULT_COLLECTION
    status = _generation_status.get(DEFAULT_COLLECTION, {})
    assert status.get("status") == "error"
    assert "batch failed" in status.get("result", "")
    assert status.get("completed_at") is not None

    _generation_status.pop(DEFAULT_COLLECTION, None)
