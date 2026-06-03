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

# src/loaders/__init__.py
"""
Package for document loaders.
Provides a central registry of available loaders.
"""
from .base_loader import BaseLoader
from .pdf_loader import EnhancedPDFLoader
from .epub_loader import ImprovedEPubLoader
from .office_loaders import DocxLoader, DocLoader, PowerPointLoader, ExcelLoader

# Registry of loaders by file extension
LOADER_REGISTRY = {
    '.pdf': EnhancedPDFLoader,
    '.epub': ImprovedEPubLoader,
    '.docx': DocxLoader,
    '.doc': DocLoader,
    '.pptx': PowerPointLoader,
    '.ppt': PowerPointLoader,
    '.xlsx': ExcelLoader,
    '.xls': ExcelLoader
}

def get_loader_for_file(file_path):
    """
    Get appropriate loader instance for a file based on its extension.
    
    Args:
        file_path (str): Path to the document file
        
    Returns:
        BaseLoader: An instance of the appropriate loader
        
    Raises:
        ValueError: If the file extension is not supported
    """
    import os
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext not in LOADER_REGISTRY:
        raise ValueError(f"Unsupported file format: {ext}")
    
    loader_class = LOADER_REGISTRY[ext]
    
    # Handle Excel files with special mode parameter
    if ext in ['.xlsx', '.xls']:
        return loader_class(file_path, mode="elements")
    else:
        return loader_class(file_path)

# List of supported file extensions
SUPPORTED_EXTENSIONS = tuple(LOADER_REGISTRY.keys())