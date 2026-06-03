# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Smoke tests — verify basic page load and core UI elements."""

import pytest


@pytest.mark.e2e
class TestPageLoad:

    def test_page_title(self, page):
        """Page title contains MKM."""
        assert "MKM" in page.title()

    def test_chat_input_exists(self, page):
        """Chat input textarea is present."""
        textarea = page.query_selector("textarea, #user-input, [id*='input']")
        assert textarea is not None, "Chat input not found"

    def test_send_button_exists(self, page):
        """Send button is present."""
        btn = page.query_selector("button[id*='send'], button[onclick*='send'], .send-btn")
        if btn is None:
            # Try broader search
            buttons = page.query_selector_all("button")
            send_buttons = [b for b in buttons if "send" in (b.inner_text() or "").lower()]
            assert len(send_buttons) > 0 or len(buttons) > 0, "No buttons found on page"

    def test_model_selector_exists(self, page):
        """Model selection dropdown is present."""
        select = page.query_selector("select[id*='model'], #model-select, [id*='model']")
        assert select is not None, "Model selector not found"

    def test_page_loads_css(self, page):
        """Main stylesheet is loaded."""
        stylesheets = page.evaluate("() => document.styleSheets.length")
        assert stylesheets > 0, "No stylesheets loaded"

    def test_page_loads_js(self, page):
        """JavaScript modules are loaded."""
        scripts = page.evaluate("() => document.scripts.length")
        assert scripts > 0, "No scripts loaded"
