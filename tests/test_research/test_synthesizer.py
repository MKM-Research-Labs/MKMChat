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

"""Tests for src/research/synthesizer.py (ResponseSynthesizer)."""

from unittest.mock import MagicMock, patch

from src.research.models import KBQueryResult


def test_synthesize_results():
    """synthesize should combine successful KB results into a single response."""
    from src.research.synthesizer import ResponseSynthesizer

    app = MagicMock()
    synth = ResponseSynthesizer(app)

    kb_results = [
        KBQueryResult(
            kb_key="misc",
            kb_name="Miscellaneous",
            success=True,
            response="Floods cause significant damage.",
            doc_count=3,
            query_time_ms=100,
        ),
        KBQueryResult(
            kb_key="phys",
            kb_name="Physical",
            success=True,
            response="Physical models predict water flow.",
            doc_count=2,
            query_time_ms=80,
        ),
    ]

    with patch(
        "src.research.synthesizer.route_to_model_handler",
        return_value="Combined: floods cause damage and physical models predict flow.",
    ):
        result = synth.synthesize("What is flood risk?", kb_results, "claude-sonnet-4-5-20250929")

    assert isinstance(result, str)
    assert len(result) > 0
    assert "Combined" in result


def test_synthesize_empty_results():
    """synthesize should return a 'no relevant information' message when all results are empty."""
    from src.research.synthesizer import ResponseSynthesizer

    app = MagicMock()
    synth = ResponseSynthesizer(app)

    kb_results = [
        KBQueryResult(
            kb_key="misc",
            kb_name="Miscellaneous",
            success=True,
            response="No relevant documents found in this knowledge base.",
            doc_count=0,
            query_time_ms=50,
        ),
        KBQueryResult(
            kb_key="phys",
            kb_name="Physical",
            success=False,
            error="Index not loaded",
            doc_count=0,
            query_time_ms=10,
        ),
    ]

    result = synth.synthesize("Obscure question", kb_results, "claude-sonnet-4-5-20250929")

    assert isinstance(result, str)
    assert "no relevant information" in result.lower()


def test_synthesize_fallback_on_llm_error():
    """When the LLM synthesis call raises, the fallback concatenation should be used."""
    from src.research.synthesizer import ResponseSynthesizer

    app = MagicMock()
    synth = ResponseSynthesizer(app)

    kb_results = [
        KBQueryResult(
            kb_key="misc",
            kb_name="Miscellaneous",
            success=True,
            response="Useful information here.",
            doc_count=2,
            query_time_ms=100,
        ),
    ]

    with patch(
        "src.research.synthesizer.route_to_model_handler",
        side_effect=RuntimeError("LLM unavailable"),
    ):
        result = synth.synthesize("test query", kb_results, "claude-sonnet-4-5-20250929")

    assert isinstance(result, str)
    # Fallback synthesis should contain the individual response
    assert "Useful information here." in result
    assert "Miscellaneous" in result
