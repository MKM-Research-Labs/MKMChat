# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

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
