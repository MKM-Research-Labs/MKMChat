# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""
Document processing module.
Provides modular document processing with vector embeddings.
"""

from .processor import DocumentProcessor, get_processor

__all__ = ['DocumentProcessor', 'get_processor']
