# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""
Pytest configuration for MKMChat.

Submodules are in tests/_conftest/:
  data.py             — SAMPLE_* test data constants
  fixtures_files.py   — temp dir and sample file fixtures
  fixtures_flask.py   — Flask app and test client fixtures
  fixtures_mocks.py   — mock objects for external dependencies
  helpers.py          — assertion helpers and file utilities
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
_TESTS_DIR = Path(__file__).parent

# Ensure project root and conftest subpackage are importable
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(_TESTS_DIR / "_conftest"))

# Re-export everything so pytest discovers fixtures in this namespace.
from data import (  # noqa: F401, E402
    SAMPLE_CHAT,
    SAMPLE_CHAT_2,
    SAMPLE_CHAT_MESSAGE,
    SAMPLE_CHAT_MESSAGE_RESPONSE,
    SAMPLE_COLLECTION_CONFIG,
    SAMPLE_DOCUMENT_CHUNK,
    SAMPLE_DOCUMENT_CHUNKS,
    SAMPLE_LLM_RESPONSE_ANTHROPIC,
    SAMPLE_LLM_RESPONSE_LOCAL,
    SAMPLE_LLM_RESPONSE_PERPLEXITY,
    SAMPLE_QUERY_REQUEST,
    SAMPLE_RESEARCH_REQUEST,
    SAMPLE_SUMMARY,
)

from fixtures_files import (  # noqa: F401, E402
    temp_data_dir,
    temp_chats_file,
    sample_pdf_file,
    sample_text_file,
)

from fixtures_flask import (  # noqa: F401, E402
    flask_app,
    client,
    mock_llm_responses,
)

from fixtures_mocks import (  # noqa: F401, E402
    mock_embeddings,
    mock_faiss_service,
    mock_anthropic_api,
    mock_perplexity_api,
    mock_lm_studio_api,
)

from helpers import (  # noqa: F401, E402
    create_test_file,
    assert_valid_json_response,
    assert_error_response,
)
