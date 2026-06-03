# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""E2E tests for chat history panel."""

import pytest


@pytest.mark.e2e
class TestChatHistory:

    def test_history_api_returns_json(self, page, base_url):
        """GET /get_chats returns JSON with chats key."""
        response = page.evaluate(f"""async () => {{
            const resp = await fetch('{base_url}/get_chats');
            return await resp.json();
        }}""")
        assert "chats" in response

    def test_save_and_retrieve_chat(self, page, base_url):
        """Can save a chat via API and retrieve it."""
        # Save a chat
        save_result = page.evaluate(f"""async () => {{
            const resp = await fetch('{base_url}/save_chat', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    id: 'e2e_test_chat',
                    title: 'E2E Test',
                    messages: [{{role: 'user', content: 'Hello'}}],
                    timestamp: new Date().toISOString()
                }})
            }});
            return await resp.json();
        }}""")
        assert save_result.get("success") is True

        # Retrieve and verify
        chats = page.evaluate(f"""async () => {{
            const resp = await fetch('{base_url}/get_chats');
            return await resp.json();
        }}""")
        chat_ids = [c.get("id") for c in chats.get("chats", [])]
        assert "e2e_test_chat" in chat_ids

        # Cleanup
        page.evaluate(f"""async () => {{
            await fetch('{base_url}/delete_chat/e2e_test_chat', {{method: 'DELETE'}});
        }}""")

    def test_delete_chat(self, page, base_url):
        """Can save a chat via API and then delete it."""
        # Save a chat
        save_result = page.evaluate(f"""async () => {{
            const resp = await fetch('{base_url}/save_chat', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    id: 'e2e_delete_chat',
                    title: 'E2E Delete Test',
                    messages: [{{role: 'user', content: 'Delete me'}}],
                    timestamp: new Date().toISOString()
                }})
            }});
            return await resp.json();
        }}""")
        assert save_result.get("success") is True

        # Delete the chat
        delete_result = page.evaluate(f"""async () => {{
            const resp = await fetch('{base_url}/delete_chat/e2e_delete_chat', {{
                method: 'DELETE'
            }});
            return {{ status: resp.status, body: await resp.json() }};
        }}""")
        assert delete_result["status"] == 200
        assert delete_result["body"].get("success") is True

        # Verify it's gone
        chats = page.evaluate(f"""async () => {{
            const resp = await fetch('{base_url}/get_chats');
            return await resp.json();
        }}""")
        chat_ids = [c.get("id") for c in chats.get("chats", [])]
        assert "e2e_delete_chat" not in chat_ids

    def test_delete_chat_not_found(self, page, base_url):
        """DELETE for non-existent chat returns 404."""
        result = page.evaluate(f"""async () => {{
            const resp = await fetch('{base_url}/delete_chat/nonexistent_e2e', {{
                method: 'DELETE'
            }});
            return {{ status: resp.status, body: await resp.json() }};
        }}""")
        assert result["status"] == 404
        assert "error" in result["body"]
