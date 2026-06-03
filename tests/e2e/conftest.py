# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""
Playwright E2E test fixtures.

Starts a Flask dev server on a free port, provides a Playwright page
pre-navigated to the chat UI, and tears everything down after the session.
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _free_port() -> int:
    """Find an available TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 30.0) -> bool:
    """Block until the server accepts TCP connections or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


# ---------------------------------------------------------------------------
# Session-scoped: one server + one browser for the entire test session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def server_port():
    """Start Flask server on a free port; yield the port; kill on teardown."""
    port = _free_port()
    env = os.environ.copy()
    env.update({
        "MKM_SERVER_PORT": str(port),
        "MKM_SERVER_HOST": "127.0.0.1",
        "PYTHONUNBUFFERED": "1",
        "MKM_TEST_MODE": "1",
    })

    proc = subprocess.Popen(
        [sys.executable, "chat.py", "-web-only",
         "--port", str(port), "--host", "127.0.0.1"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if not _wait_for_server(port, timeout=60):
        proc.kill()
        out, _ = proc.communicate(timeout=5)
        pytest.fail(
            f"Flask server did not start on port {port} within 60s.\n"
            f"Server output:\n{out.decode(errors='replace')[:3000]}"
        )

    yield port

    proc.kill()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def base_url(server_port):
    return f"http://127.0.0.1:{server_port}"


@pytest.fixture(scope="session")
def _browser_page(browser, base_url):
    """Create a single browser page for the entire test session."""
    context = browser.new_context(viewport={"width": 1400, "height": 900})
    page = context.new_page()
    page.set_default_timeout(30_000)

    page.goto(base_url, wait_until="networkidle", timeout=60_000)

    yield page

    context.close()


@pytest.fixture
def page(_browser_page, base_url):
    """Provide the shared page to each test, with cleanup between tests."""
    pg = _browser_page

    # Navigate back to home if we drifted
    if base_url not in pg.url:
        pg.goto(base_url, wait_until="networkidle", timeout=30_000)

    # Clean up: dismiss any open modals/panels
    pg.evaluate("""() => {
        // Close modals
        document.querySelectorAll('.modal, .overlay').forEach(el => {
            el.style.display = 'none';
        });
        // Clear chat input
        const input = document.querySelector('#user-input, textarea');
        if (input) input.value = '';
    }""")

    return pg
