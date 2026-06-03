# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
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
