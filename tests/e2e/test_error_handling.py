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

"""E2E tests for error handling."""

import pytest


@pytest.mark.e2e
class TestErrorHandling:

    def test_invalid_endpoint_returns_404(self, page, base_url):
        """Requesting a non-existent endpoint returns 404."""
        status = page.evaluate(f"""async () => {{
            const resp = await fetch('{base_url}/nonexistent_endpoint');
            return resp.status;
        }}""")
        assert status == 404

    def test_invalid_json_to_query(self, page, base_url):
        """Sending non-JSON to /query returns 400."""
        status = page.evaluate(f"""async () => {{
            const resp = await fetch('{base_url}/query', {{
                method: 'POST',
                headers: {{'Content-Type': 'text/plain'}},
                body: 'not json'
            }});
            return resp.status;
        }}""")
        assert status == 400

    def test_empty_query_returns_400(self, page, base_url):
        """Sending empty query to /query returns 400."""
        status = page.evaluate(f"""async () => {{
            const resp = await fetch('{base_url}/query', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{query: '', model: 'test'}})
            }});
            return resp.status;
        }}""")
        assert status == 400

    def test_invalid_kb_switch_returns_400(self, page, base_url):
        """Switching to invalid KB returns 400."""
        result = page.evaluate(f"""async () => {{
            const resp = await fetch('{base_url}/switch_index', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{index_key: 'nonexistent_kb'}})
            }});
            return {{status: resp.status, data: await resp.json()}};
        }}""")
        assert result["status"] == 400
        assert "error" in result["data"]
