# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
"""
Summary Models

Data classes and type definitions for the summary module.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class SummaryResult:
    """Result of a document summarization operation."""
    document_name: str
    success: bool
    message: str
    status: str  # SUCCESS, SKIPPED, BASIC_FALLBACK, FAILED
    summary: Optional[str] = None
    num_chunks: int = 0


@dataclass
class ProcessingStats:
    """Statistics for a batch processing operation."""
    collection: str
    name: str
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    total_books: int = 0
    error: Optional[str] = None


@dataclass
class CleaningStats:
    """Statistics for a cleaning operation."""
    total_before: int = 0
    total_after: int = 0
    removed_count: int = 0
    error: Optional[str] = None


@dataclass
class DocumentChunk:
    """A chunk of document content from FAISS index."""
    content: str
    metadata: Dict[str, Any]
    doc_id: str
    page: int = 0


@dataclass
class SummaryEntry:
    """A summary entry for storage."""
    hash: str
    summarised_date: str
    summary: str
    summary_type: str  # FULL, BASIC_FALLBACK
    num_chunks: int = 0
    method: Optional[str] = None
    model: Optional[str] = None
    knowledge_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        result = {
            'hash': self.hash,
            'summarised_date': self.summarised_date,
            'summary': self.summary,
            'summary_type': self.summary_type,
        }
        if self.num_chunks:
            result['num_chunks'] = self.num_chunks
        if self.method:
            result['method'] = self.method
        if self.model:
            result['model'] = self.model
        if self.knowledge_type:
            result['knowledge_type'] = self.knowledge_type
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SummaryEntry':
        """Create from dictionary."""
        return cls(
            hash=data.get('hash', ''),
            summarised_date=data.get('summarised_date', ''),
            summary=data.get('summary', ''),
            summary_type=data.get('summary_type', 'FULL'),
            num_chunks=data.get('num_chunks', 0),
            method=data.get('method'),
            model=data.get('model'),
            knowledge_type=data.get('knowledge_type'),
        )
