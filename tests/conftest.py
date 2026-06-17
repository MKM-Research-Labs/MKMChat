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
