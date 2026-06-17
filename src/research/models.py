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
Research Data Models
--------------------

Data classes for research query results.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class KBQueryResult:
    """Result from querying a single knowledge base"""
    kb_key: str
    kb_name: str
    success: bool
    response: str = ""
    sources: List[Dict[str, str]] = field(default_factory=list)
    error: Optional[str] = None
    doc_count: int = 0
    query_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchResult:
    """Complete research result across all knowledge bases"""
    query: str
    model: str
    kb_results: List[KBQueryResult]
    synthesized_answer: str
    total_sources: int
    total_time_ms: int
    timestamp: str
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['kb_results'] = [kb.to_dict() if hasattr(kb, 'to_dict') else kb
                                for kb in self.kb_results]
        return result
