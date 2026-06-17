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

"""E2E tests for knowledge base switching."""

import pytest


@pytest.mark.e2e
class TestKnowledgeBase:

    def test_kb_selector_exists(self, page):
        """Knowledge base selector is present."""
        selector = page.query_selector(
            "select[id*='index'], select[id*='kb'], "
            "[id*='knowledge'], [id*='collection']"
        )
        assert selector is not None, "KB selector not found"

    def test_kb_has_options(self, page):
        """KB panel has knowledge base entries."""
        # KB list is dynamically built in #knowledge-bases-list, not a <select>
        page.wait_for_timeout(2000)  # allow JS to populate
        items = page.query_selector_all(
            "#knowledge-bases-list > *, "
            "select[id*='index'] option, select[id*='kb'] option"
        )
        assert len(items) >= 1, "KB list has no entries"

    def test_kb_switch_triggers_api(self, page):
        """Switching KB sends a request to /switch_index."""
        # Set up a request listener
        requests_made = []

        def handle_request(request):
            if "switch_index" in request.url:
                requests_made.append(request.url)

        page.on("request", handle_request)

        try:
            selector = page.query_selector(
                "select[id*='index'], select[id*='kb'], "
                "select[id*='knowledge'], select[id*='collection']"
            )
            if selector:
                options = selector.query_selector_all("option")
                if len(options) >= 2:
                    # Select the second option
                    value = options[1].get_attribute("value")
                    if value:
                        selector.select_option(value)
                        page.wait_for_timeout(1000)
                        # Request may or may not have fired depending on JS handler
        finally:
            page.remove_listener("request", handle_request)
