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
Summary Package

Document summarization functionality for MKMChat.
Provides batch processing, document summarization, and summary management.
"""

# Models
from .models import (
    SummaryResult,
    ProcessingStats,
    CleaningStats,
    DocumentChunk,
    SummaryEntry,
)

# Storage utilities
from .storage import (
    get_paths,
    load_json_file,
    save_json_file,
    get_summary_files,
)

# FAISS operations
from .faiss_reader import (
    load_faiss_index,
    search_book_content,
    get_document_chunks_from_faiss,
)

# LLM client
from .llm_client import (
    call_llm_for_summary,
    generate_basic_summary,
    clean_summary_text,
)

# Main classes
from .summariser import DocumentSummariser, get_summariser
from .cleaner import SummaryCleaner, run_cleaner, CLEANING_MODES

# Batch processing
from .batch import (
    run_batch_processor,
    process_single_collection,
    initialize_embedding_model,
)

__all__ = [
    # Models
    'SummaryResult',
    'ProcessingStats',
    'CleaningStats',
    'DocumentChunk',
    'SummaryEntry',
    # Storage
    'get_paths',
    'load_json_file',
    'save_json_file',
    'get_summary_files',
    # FAISS
    'load_faiss_index',
    'search_book_content',
    'get_document_chunks_from_faiss',
    # LLM
    'call_llm_for_summary',
    'generate_basic_summary',
    'clean_summary_text',
    # Classes
    'DocumentSummariser',
    'get_summariser',
    'SummaryCleaner',
    'run_cleaner',
    'CLEANING_MODES',
    # Batch
    'run_batch_processor',
    'process_single_collection',
    'initialize_embedding_model',
]
