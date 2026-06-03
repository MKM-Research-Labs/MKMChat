# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# src/document_processor.py
# Version: 2.1
# Last Updated: Feb 2026
"""
Compatibility shim for document processing.
The actual implementation has been modularized into src/proc/

This file maintains backward compatibility for imports like:
    from src.document_processor import DocumentProcessor, get_processor
"""

# Re-export from the modular implementation
from .proc import DocumentProcessor, get_processor

__all__ = ['DocumentProcessor', 'get_processor']
