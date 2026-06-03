# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Assertion helpers and file creation utilities for tests."""

import json
from pathlib import Path
from typing import Any


def create_test_file(directory: Path, filename: str, data: Any) -> Path:
    """Create a test data file containing JSON-encoded data."""
    filepath = directory / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    return filepath


def assert_valid_json_response(response, status_code=200):
    """Assert a Flask test-client response is JSON with expected status."""
    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}: {response.data}"
    )
    assert response.content_type.startswith("application/json")
    return response.get_json()


def assert_error_response(response, status_code, error_key="error"):
    """Assert a Flask error response has the expected shape."""
    data = assert_valid_json_response(response, status_code)
    assert error_key in data, f"Expected '{error_key}' in response: {data}"
    return data
