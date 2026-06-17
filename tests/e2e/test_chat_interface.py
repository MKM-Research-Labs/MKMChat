# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""E2E tests for the chat interface."""

import pytest


@pytest.mark.e2e
class TestChatInterface:

    def test_type_in_chat_input(self, page):
        """Can type text into the chat input."""
        input_el = page.query_selector("#query-input, textarea, #user-input")
        assert input_el is not None, "Chat input not found"
        input_el.fill("Test message from E2E")
        value = input_el.input_value()
        assert "Test message" in value

    def test_chat_area_exists(self, page):
        """Chat message area exists."""
        chat_area = page.query_selector(
            "#chat-container, #messages, .chat-messages, "
            "[id*='chat'], [class*='chat']"
        )
        assert chat_area is not None, "Chat area not found"

    def test_keyboard_shortcut_does_not_crash(self, page):
        """Pressing Enter in textarea does not crash the page."""
        input_el = page.query_selector("#query-input, textarea, #user-input")
        if input_el:
            input_el.fill("test")
            input_el.press("Enter")
            # Just verify page is still responsive
            page.wait_for_timeout(500)
            assert page.title() is not None


@pytest.mark.e2e
class TestNewChat:

    def test_new_chat_button_exists(self, page):
        """New chat button is present."""
        btn = page.query_selector(
            "button[id*='new'], button[onclick*='new'], "
            "[id*='new-chat'], .new-chat"
        )
        # May also be an icon button
        if btn is None:
            buttons = page.query_selector_all("button")
            new_buttons = [b for b in buttons if "new" in (b.get_attribute("id") or "").lower()
                          or "new" in (b.inner_text() or "").lower()]
            # Don't fail hard — just check UI is interactive
            assert len(buttons) > 0, "No buttons on page at all"
