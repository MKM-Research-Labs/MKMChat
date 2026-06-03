# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# src/utils/__init__.py
"""
Utility functions package for document processing.
"""
from .text_utils import sanitize_text, standardize_metadata
from .file_utils import (
    get_file_hash, 
    load_json_file, 
    save_json_file, 
    get_supported_files,
    ensure_directory_exists,
    create_processed_record
)
from .diagnostics import diagnose_pdf, evaluate_diagnostics, generate_recommendation
from .rep import replace_terms  # Added: rep module now lives in utils

# Export commonly used functions at package level
__all__ = [
    'sanitize_text',
    'standardize_metadata',
    'get_file_hash',
    'load_json_file',
    'save_json_file',
    'get_supported_files',
    'ensure_directory_exists',
    'create_processed_record',
    'diagnose_pdf',
    'evaluate_diagnostics',
    'generate_recommendation',
    'replace_terms'  # Added export
]