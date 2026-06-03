# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Tests for src/services/chat_service.py (ChatService)."""

import json

import pytest

from src.services.chat_service import ChatService
from data import SAMPLE_CHAT, SAMPLE_CHAT_2


@pytest.fixture
def service(temp_chats_file):
    """Instantiate a ChatService backed by the temporary chats file."""
    return ChatService(temp_chats_file)


# ── Initialization ───────────────────────────────────────────────────────


class TestInit:
    def test_init_creates_file(self, temp_chats_file):
        """Verify the storage file exists after init."""
        svc = ChatService(temp_chats_file)
        from pathlib import Path

        assert Path(temp_chats_file).exists()
        data = json.loads(Path(temp_chats_file).read_text())
        assert "chats" in data


# ── save_chat / get_all_chats ────────────────────────────────────────────


class TestSaveAndRetrieve:
    def test_save_new_chat(self, service):
        """Save a chat, then verify get_all_chats returns it."""
        result = service.save_chat(SAMPLE_CHAT.copy())
        assert result["success"] is True

        all_chats = service.get_all_chats()
        assert len(all_chats["chats"]) == 1
        assert all_chats["chats"][0]["id"] == SAMPLE_CHAT["id"]

    def test_save_updates_existing(self, service):
        """Saving twice with the same ID should update, not duplicate."""
        service.save_chat(SAMPLE_CHAT.copy())

        updated = SAMPLE_CHAT.copy()
        updated["title"] = "Updated Title"
        service.save_chat(updated)

        all_chats = service.get_all_chats()
        assert len(all_chats["chats"]) == 1
        assert all_chats["chats"][0]["title"] == "Updated Title"


# ── get_chat_by_id ───────────────────────────────────────────────────────


class TestGetById:
    def test_get_chat_by_id(self, service):
        """Save then retrieve by ID."""
        service.save_chat(SAMPLE_CHAT.copy())
        chat = service.get_chat_by_id(SAMPLE_CHAT["id"])
        assert chat is not None
        assert chat["id"] == SAMPLE_CHAT["id"]

    def test_get_chat_by_id_not_found(self, service):
        """Non-existent ID returns None."""
        assert service.get_chat_by_id("does_not_exist") is None


# ── delete_chat ──────────────────────────────────────────────────────────


class TestDelete:
    def test_delete_chat(self, service):
        """Save and delete, verify gone."""
        service.save_chat(SAMPLE_CHAT.copy())
        assert service.delete_chat(SAMPLE_CHAT["id"]) is True
        assert service.get_chat_by_id(SAMPLE_CHAT["id"]) is None

    def test_delete_chat_not_found(self, service):
        """Deleting non-existent chat returns False."""
        assert service.delete_chat("does_not_exist") is False


# ── clear_all_chats ──────────────────────────────────────────────────────


class TestClear:
    def test_clear_all_chats(self, service):
        """Save multiple, clear, verify empty."""
        service.save_chat(SAMPLE_CHAT.copy())
        service.save_chat(SAMPLE_CHAT_2.copy())
        assert service.get_chat_count() == 2

        service.clear_all_chats()
        assert service.get_chat_count() == 0


# ── get_chat_count ───────────────────────────────────────────────────────


class TestCount:
    def test_get_chat_count(self, service):
        """Save 2 chats, verify count is 2."""
        service.save_chat(SAMPLE_CHAT.copy())
        service.save_chat(SAMPLE_CHAT_2.copy())
        assert service.get_chat_count() == 2


# ── get_recent_chats ─────────────────────────────────────────────────────


class TestRecent:
    def test_get_recent_chats(self, service):
        """Save 3 chats, get recent 2, verify order (newest first)."""
        service.save_chat(SAMPLE_CHAT.copy())
        service.save_chat(SAMPLE_CHAT_2.copy())

        third = {
            "id": "test_chat_003",
            "title": "Third Chat",
            "timestamp": "2026-03-25T12:00:00",
            "messages": [],
            "knowledge_base": "misc",
            "model": "sonar",
        }
        service.save_chat(third)

        recent = service.get_recent_chats(limit=2)
        assert len(recent) == 2
        # Newest (highest timestamp) should be first
        assert recent[0]["id"] == "test_chat_003"
        assert recent[1]["id"] == "test_chat_002"


# ── corrupted file ───────────────────────────────────────────────────────


class TestCorruptedFile:
    def test_corrupted_file(self, temp_chats_file):
        """Write invalid JSON; ChatService should handle it gracefully."""
        from pathlib import Path

        Path(temp_chats_file).write_text("NOT VALID JSON {{{")

        svc = ChatService(temp_chats_file)
        all_chats = svc.get_all_chats()
        # Should fall back to empty structure
        assert all_chats == {"chats": []}


# ── Additional coverage tests ───────────────────────────────────────────


class TestInitStorage:
    def test_init_prints_when_creating_file(self, tmp_path, capsys):
        """Verify _init_storage prints a message when creating the file."""
        chats_file = str(tmp_path / "new_dir" / "chats.json")
        svc = ChatService(chats_file)
        captured = capsys.readouterr()
        assert "Initialized chat storage" in captured.out

    def test_init_does_not_overwrite_existing(self, temp_chats_file):
        """_init_storage does not overwrite an existing valid file."""
        from pathlib import Path

        # Pre-populate with some data
        data = {"chats": [{"id": "existing", "title": "Keep me"}]}
        Path(temp_chats_file).write_text(json.dumps(data))

        svc = ChatService(temp_chats_file)
        all_chats = svc.get_all_chats()
        assert len(all_chats["chats"]) == 1
        assert all_chats["chats"][0]["id"] == "existing"


class TestReadChatsInvalidStructure:
    def test_invalid_structure_not_dict(self, temp_chats_file):
        """_read_chats resets when file contains a non-dict JSON value."""
        from pathlib import Path

        Path(temp_chats_file).write_text(json.dumps([1, 2, 3]))
        svc = ChatService(temp_chats_file)
        all_chats = svc.get_all_chats()
        assert all_chats == {"chats": []}

    def test_invalid_structure_missing_chats_key(self, temp_chats_file):
        """_read_chats resets when file is dict but missing 'chats' key."""
        from pathlib import Path

        Path(temp_chats_file).write_text(json.dumps({"other": "data"}))
        svc = ChatService(temp_chats_file)
        all_chats = svc.get_all_chats()
        assert all_chats == {"chats": []}


class TestSaveChatEdgeCases:
    def test_save_empty_chat_raises(self, service):
        """save_chat raises ValueError for empty/None chat_data."""
        with pytest.raises(ValueError, match="empty"):
            service.save_chat(None)

        with pytest.raises(ValueError, match="empty"):
            service.save_chat({})

    def test_save_chat_without_id_auto_generates(self, service):
        """save_chat auto-generates an ID when 'id' is missing."""
        chat = {"title": "No ID Chat", "messages": []}
        result = service.save_chat(chat)
        assert result["success"] is True
        assert result["id"] is not None
        assert len(result["id"]) > 0

    def test_save_chat_prints_action(self, service, capsys):
        """save_chat prints created/updated action."""
        service.save_chat(SAMPLE_CHAT.copy())
        captured = capsys.readouterr()
        assert "created" in captured.out

        service.save_chat(SAMPLE_CHAT.copy())
        captured = capsys.readouterr()
        assert "updated" in captured.out


class TestGetRecentChatsEdgeCases:
    def test_get_recent_chats_unsortable(self, service):
        """get_recent_chats handles unsortable chats by reversing."""
        # Save chats with mixed types that could cause sort issues
        chat1 = {"id": "1", "title": "Chat 1", "messages": []}
        chat2 = {"id": "2", "title": "Chat 2", "timestamp": None, "messages": []}
        service.save_chat(chat1)
        service.save_chat(chat2)

        # This should not raise, even if sorting fails
        recent = service.get_recent_chats(limit=5)
        assert len(recent) == 2

    def test_get_recent_chats_limit_larger_than_total(self, service):
        """get_recent_chats with limit > total chats returns all chats."""
        service.save_chat(SAMPLE_CHAT.copy())
        recent = service.get_recent_chats(limit=100)
        assert len(recent) == 1


class TestDeleteAndClearPrints:
    def test_delete_prints(self, service, capsys):
        """delete_chat prints deletion message."""
        service.save_chat(SAMPLE_CHAT.copy())
        service.delete_chat(SAMPLE_CHAT["id"])
        captured = capsys.readouterr()
        assert "deleted" in captured.out

    def test_clear_prints(self, service, capsys):
        """clear_all_chats prints message."""
        service.clear_all_chats()
        captured = capsys.readouterr()
        assert "cleared" in captured.out
