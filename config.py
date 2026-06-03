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

# config.py
"""
Centralized configuration management for MKM Research Document Q&A Application.

Provides consistent path handling and configuration across all modules.
"""

import os
import importlib.util
from pathlib import Path
from typing import Dict, Any

# =============================================================================
# API KEYS
# =============================================================================
# Secrets are never committed. They live in data/config_key.py, which sits on
# the external SSD (data/ is a symlink whose contents git never tracks). If the
# SSD is not mounted, fall back to environment variables.
def _load_api_keys():
    key_file = Path(__file__).parent / "data" / "config_key.py"
    if key_file.exists():
        spec = importlib.util.spec_from_file_location("config_key", key_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return (
            getattr(module, "ANTHROPIC_API_KEY", ""),
            getattr(module, "PERPLEXITY_API_KEY", ""),
        )
    return (
        os.environ.get("ANTHROPIC_API_KEY", ""),
        os.environ.get("PERPLEXITY_API_KEY", ""),
    )

ANTHROPIC_API_KEY, PERPLEXITY_API_KEY = _load_api_keys()

# =============================================================================
# API URLs
# =============================================================================
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================
MODEL_ID = "claude-sonnet-4-5-20250929"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Anthropic model ID mapping
ANTHROPIC_MODEL_IDS = {
    "claude-sonnet-4.5": MODEL_ID,
    "claude-3-opus": "claude-3-opus-20240229"
}

# Available models menu
AVAILABLE_MODELS = {
    "cogito-v1-preview-llama-3b": "Cogito v1 3B",
    "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M": "Deepseek Qwen 1.5B",
    "sonar-pro": "Perplexity Sonar Pro",
    "sonar-reasoning-pro": "Perplexity Sonar Reasoning Pro",
    "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5"
}

# Derived URL for LM Studio model listing
LM_STUDIO_MODELS_URL = LM_STUDIO_API_URL.replace("/chat/completions", "/models")

# Default collection loaded on startup
DEFAULT_COLLECTION = "misc"

# =============================================================================
# SUMMARY CLEANING
# =============================================================================
CLEANING_MODES = ['fallback_only', 'force_all', 'clean_all']

# =============================================================================
# MKM BRAND COLOURS (hex strings – converted to ReportLab objects in pdf_builder)
# =============================================================================
MKM_DARK_HEX = "#1e293b"
MKM_BLUE_HEX = "#3b82f6"
MKM_LIGHT_BLUE_HEX = "#dbeafe"
MKM_GREEN_HEX = "#22c55e"
MKM_RED_HEX = "#ef4444"
MKM_AMBER_HEX = "#f59e0b"
MKM_GREY_HEX = "#64748b"
MKM_LIGHT_GREY_HEX = "#f1f5f9"

# =============================================================================
# ANTHROPIC MODEL SETTINGS
# =============================================================================
ANTHROPIC_MAX_TOKENS = 4096
ANTHROPIC_API_VERSION = "2023-06-01"

# =============================================================================
# LOCAL MODEL SETTINGS (LM Studio)
# =============================================================================
LOCAL_MODEL_MAX_CONTEXT = 4000
LOCAL_MODEL_TIMEOUT = 120
LOCAL_MODEL_TEMPERATURE = 0.7
LOCAL_MODEL_MAX_TOKENS = 1000
LOCAL_SUMMARY_MODEL = "deepseek-r1-distill-qwen-1.5b"

# =============================================================================
# RETRIEVAL SETTINGS
# =============================================================================
TOP_K_RESULTS = 5
RESEARCH_MAX_DOCS_PER_KB = 20
EMBEDDING_BATCH_SIZE = 5

# =============================================================================
# SUMMARIZATION SETTINGS
# =============================================================================
SUMMARY_MAX_TOKENS = 2000
SUMMARY_TEMPERATURE = 0.7
SUMMARY_TIMEOUT = 300
SUMMARY_FALLBACK_TEMPERATURE = 0.4
SUMMARY_FALLBACK_MAX_TOKENS = 600
SUMMARY_FALLBACK_TIMEOUT = 120
SUMMARY_MAX_CHUNKS = 25
SUMMARY_CHUNK_CONTENT_LENGTH = 500
SUMMARY_CHUNK_CONTENT_LENGTH_RETRY = 300
SUMMARY_CONTEXT_TRUNCATION = 6000

# =============================================================================


class PathManager:
    """Centralized path management for the application."""

    def __init__(self) -> None:
        # Get the project root directory (config.py lives at project root)
        self.project_root = Path(__file__).parent.absolute()

        # Core directories
        self.src_dir = self.project_root / "src"
        self.data_dir = self.project_root / "data"
        self.json_dir = self.data_dir / "json"

        # Root folders for docs and indices (under data/)
        self.docs_root = self.data_dir / "docs"
        self.faiss_root = self.data_dir / "faiss"

        # Document collections
        self.docs_misc_dir = self.docs_root / "misc"
        self.docs_phys_dir = self.docs_root / "phys"
        self.docs_pops_dir = self.docs_root / "pops"
        self.docs_hist_dir = self.docs_root / "hist"
        self.docs_mods_dir = self.docs_root / "mods"
        self.docs_corp_dir = self.docs_root / "corp"
        self.docs_back_dir = self.docs_root / "back"

        # FAISS indices
        self.faiss_misc_dir = self.faiss_root / "misc"
        self.faiss_phys_dir = self.faiss_root / "phys"
        self.faiss_pops_dir = self.faiss_root / "pops"
        self.faiss_hist_dir = self.faiss_root / "hist"
        self.faiss_mods_dir = self.faiss_root / "mods"
        self.faiss_corp_dir = self.faiss_root / "corp"
        self.faiss_back_dir = self.faiss_root / "back"

        # Templates and static files
        self.templates_dir = self.project_root / "templates"
        self.static_dir = self.project_root / "static"

        # Chat and summary files (now in json subdirectory)
        self.chats_file = self.json_dir / "all_chats.json"
        self.summarised_files_misc = self.json_dir / "summarised_files_misc.json"
        self.summarised_files_phys = self.json_dir / "summarised_files_phys.json"
        self.summarised_files_pops = self.json_dir / "summarised_files_pops.json"
        self.summarised_files_mods = self.json_dir / "summarised_files_mods.json"
        self.summarised_files_hist = self.json_dir / "summarised_files_hist.json"
        self.summarised_files_corp = self.json_dir / "summarised_files_corp.json"
        self.summarised_files_back = self.json_dir / "summarised_files_back.json"
        self.summarised_files_main = self.json_dir / "summarised_files.json"

        # Processing files (now in json subdirectory)
        self.processed_files_misc = self.json_dir / "proc_files_misc.json"
        self.processed_files_phys = self.json_dir / "proc_files_phys.json"
        self.processed_files_pops = self.json_dir / "proc_files_pops.json"
        self.processed_files_hist = self.json_dir / "proc_files_hist.json"
        self.processed_files_mods = self.json_dir / "proc_files_mods.json"
        self.processed_files_corp = self.json_dir / "proc_files_corp.json"
        self.processed_files_back = self.json_dir / "proc_files_back.json"
        
        # Ensure critical directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create all critical directories if they do not exist."""
        critical_dirs = [
            self.data_dir,
            self.json_dir,  # Ensure json directory is created
            self.docs_root,
            self.faiss_root,
            self.docs_misc_dir,
            self.docs_phys_dir,
            self.docs_pops_dir,
            self.docs_hist_dir,
            self.docs_mods_dir,
            self.docs_corp_dir,
            self.docs_back_dir,
            self.faiss_misc_dir,
            self.faiss_phys_dir,
            self.faiss_pops_dir,
            self.faiss_hist_dir,
            self.faiss_mods_dir,
            self.faiss_corp_dir,
            self.faiss_back_dir,
            self.templates_dir,
            self.static_dir,
        ]
        for directory in critical_dirs:
            directory.mkdir(parents=True, exist_ok=True)

    def get_docs_dir(self, collection_type: str) -> Path:
        """Get the documents directory for a specific collection."""
        if collection_type == "misc":
            return self.docs_misc_dir
        elif collection_type == "phys":
            return self.docs_phys_dir
        elif collection_type == "pops":
            return self.docs_pops_dir
        elif collection_type == "hist":
            return self.docs_hist_dir
        elif collection_type == "mods":
            return self.docs_mods_dir
        elif collection_type == "corp":
            return self.docs_corp_dir
        elif collection_type == "back":
            return self.docs_back_dir
        else:
            raise ValueError(f"Unknown collection type: {collection_type}")

    def get_faiss_dir(self, collection_type: str) -> Path:
        """Get the FAISS index directory for a specific collection."""
        if collection_type == "misc":
            return self.faiss_misc_dir
        elif collection_type == "phys":
            return self.faiss_phys_dir
        elif collection_type == "pops":
            return self.faiss_pops_dir
        elif collection_type == "hist":
            return self.faiss_hist_dir
        elif collection_type == "mods":
            return self.faiss_mods_dir
        elif collection_type == "corp":
            return self.faiss_corp_dir
        elif collection_type == "back":
            return self.faiss_back_dir
        else:
            raise ValueError(f"Unknown collection type: {collection_type}")

    def get_summary_file(self, collection_type: str) -> Path:
        """Get the summary file path for a specific collection."""
        if collection_type == "misc":
            return self.summarised_files_misc
        elif collection_type == "phys":
            return self.summarised_files_phys
        elif collection_type == "pops":
            return self.summarised_files_pops
        elif collection_type == "hist":
            return self.summarised_files_hist
        elif collection_type == "mods":
            return self.summarised_files_mods
        elif collection_type == "corp":
            return self.summarised_files_corp
        elif collection_type == "back":
            return self.summarised_files_back
        else:
            raise ValueError(f"Unknown collection type: {collection_type}")

    def get_processed_file(self, collection_type: str) -> Path:
        """Get the processed files tracking file for a specific collection."""
        if collection_type == "misc":
            return self.processed_files_misc
        elif collection_type == "phys":
            return self.processed_files_phys
        elif collection_type == "pops":
            return self.processed_files_pops
        elif collection_type == "hist":
            return self.processed_files_hist
        elif collection_type == "mods":
            return self.processed_files_mods
        elif collection_type == "corp":
            return self.processed_files_corp
        elif collection_type == "back":
            return self.processed_files_back
        else:
            raise ValueError(f"Unknown collection type: {collection_type}")


# Initialize the path manager
paths = PathManager()

# Central CONFIG dictionary
CONFIG: Dict[str, Any] = {
    # Document processing settings
    "chunk_size": 3000,
    "chunk_overlap": 500,
    "default_max_docs": 50,
    # Model settings
    "embedding_model": "all-MiniLM-L6-v2",
    "alternative_embedding_models": [
        "sentence-transformers/all-mpnet-base-v2",
        "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
    ],
    "fallback_embedding_model": "sentence-transformers/all-mpnet-base-v2",
    "last_resort_model": "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
    # File extensions
    "supported_extensions": [
        ".pdf",
        ".epub",
        ".docx",
        ".doc",
        ".pptx",
        ".ppt",
        ".xlsx",
        ".xls",
    ],
    # Collections configuration
    "collections": {
        "misc": {
            "name": "Miscellaneous",
            "description": "General documents and miscellaneous content",
            "docs_folder": str(paths.docs_misc_dir),
            "faiss_index": str(paths.faiss_misc_dir),
            "summary_file": str(paths.summarised_files_misc),
            "processed_file": str(paths.processed_files_misc),
            "cleanup_module": "data.docs.misc.cleanup_misc",
        },
        "phys": {
            "name": "Physical",
            "description": "Physics and physical science documents",
            "docs_folder": str(paths.docs_phys_dir),
            "faiss_index": str(paths.faiss_phys_dir),
            "summary_file": str(paths.summarised_files_phys),
            "processed_file": str(paths.processed_files_phys),
            "cleanup_module": "data.docs.phys.cleanup_phys",
        },
        "pops": {
            "name": "Parenting",
            "description": "Popular books on the psycholology of parenting",
            "docs_folder": str(paths.docs_pops_dir),
            "faiss_index": str(paths.faiss_pops_dir),
            "summary_file": str(paths.summarised_files_pops),
            "processed_file": str(paths.processed_files_pops),
            "cleanup_module": "data.docs.pops.cleanup_pops",
        },
        "hist": {
            "name": "History",
            "description": "Popular books on History",
            "docs_folder": str(paths.docs_hist_dir),
            "faiss_index": str(paths.faiss_hist_dir),
            "summary_file": str(paths.summarised_files_hist),
            "processed_file": str(paths.processed_files_hist),
            "cleanup_module": "data.docs.hist.cleanup_hist",
        },
        "mods": {
            "name": "Models",
            "description": "Modeling methodologies, frameworks, and tools",
            "docs_folder": str(paths.docs_mods_dir),
            "faiss_index": str(paths.faiss_mods_dir),
            "summary_file": str(paths.summarised_files_mods),
            "processed_file": str(paths.processed_files_mods),
            "cleanup_module": "data.docs.mods.cleanup_mods",
        },
        "corp": {
            "name": "Corporate",
            "description": "Corporate strategy, business analysis, and financial documents",
            "docs_folder": str(paths.docs_corp_dir),
            "faiss_index": str(paths.faiss_corp_dir),
            "summary_file": str(paths.summarised_files_corp),
            "processed_file": str(paths.processed_files_corp),
            "cleanup_module": "data.docs.corp.cleanup_corp",
        },
        "back": {
            "name": "backgammon",
            "description": "Backgammon research and practical books",
            "docs_folder": str(paths.docs_back_dir),
            "faiss_index": str(paths.faiss_back_dir),
            "summary_file": str(paths.summarised_files_back),
            "processed_file": str(paths.processed_files_back),
            "cleanup_module": "data.docs.back.cleanup_back",
        },
    },
    # Legacy path fields for backward compatibility (misc/phys only)
    "docs_misc_folder": str(paths.docs_misc_dir),
    "docs_phys_folder": str(paths.docs_phys_dir),
    "faiss_misc_path": str(paths.faiss_misc_dir),
    "faiss_phys_path": str(paths.faiss_phys_dir),
    "summarised_files_misc_path": str(paths.summarised_files_misc),
    "summarised_files_phys_path": str(paths.summarised_files_phys),
    "all_chats_path": str(paths.chats_file),
    # App settings
    "templates_folder": str(paths.templates_dir),
    "static_folder": str(paths.static_dir),
    "project_root": str(paths.project_root),
    # Server settings
    "server_host": "127.0.0.1",
    "server_port": 5000,
    "server_debug": True,
    
}


def get_collection_config(collection_type: str) -> Dict[str, Any]:
    """Get configuration for a specific collection."""
    if collection_type not in CONFIG["collections"]:
        raise ValueError(
            f"Unknown collection type: {collection_type}. "
            f"Available: {list(CONFIG['collections'].keys())}"
        )
    return CONFIG["collections"][collection_type]


def get_all_collections() -> Dict[str, Dict[str, Any]]:
    """Get configuration for all collections."""
    return CONFIG["collections"]


def validate_paths() -> None:
    """Validate that all configured paths exist and are accessible."""
    issues = []

    # Check critical directories
    critical_paths = [
        ("Project Root", paths.project_root),
        ("Source Directory", paths.src_dir),
        ("JSON Directory", paths.json_dir),
        ("Templates Directory", paths.templates_dir),
        ("Static Directory", paths.static_dir),
    ]

    for name, path in critical_paths:
        if not path.exists():
            issues.append(f"{name} does not exist: {path}")
        elif not path.is_dir():
            issues.append(f"{name} is not a directory: {path}")

    # Check collection directories
    for collection_type, config in CONFIG["collections"].items():
        docs_dir = Path(config["docs_folder"])
        faiss_dir = Path(config["faiss_index"])

        if not docs_dir.exists():
            issues.append(
                f"Documents directory for {collection_type} does not exist: {docs_dir}"
            )

        # FAISS directories are created as needed, so just warn if missing
        if not faiss_dir.exists():
            print(
                f"Warning: FAISS index directory for {collection_type} "
                f"does not exist: {faiss_dir}"
            )

    if issues:
        raise RuntimeError(
            "Path validation failed:\n" + "\n".join(f" - {issue}" for issue in issues)
        )

    print("âœ“ All critical paths validated successfully")


def print_configuration() -> None:
    """Print the current configuration for debugging."""
    print("=" * 60)
    print("MKM RESEARCH DOCUMENT Q&A - CONFIGURATION")
    print("=" * 60)
    print(f"Project Root: {paths.project_root}")
    print(f"Source Directory: {paths.src_dir}")
    print(f"JSON Directory: {paths.json_dir}")
    print()
    print("COLLECTIONS:")
    for collection_type, config in CONFIG["collections"].items():
        print(f"  {collection_type.upper()} - {config['name']}")
        print(f"    Documents: {config['docs_folder']}")
        print(f"    FAISS Index: {config['faiss_index']}")
        print(f"    Summaries: {config['summary_file']}")
        print(f"    Processed: {config['processed_file']}")
        print()
    print("FILES:")
    print(f"  Chat History: {paths.chats_file}")
    print(f"  Templates:   {paths.templates_dir}")
    print(f"  Static:      {paths.static_dir}")
    print()
    print("SETTINGS:")
    print(f"  Chunk Size:       {CONFIG['chunk_size']}")
    print(f"  Chunk Overlap:    {CONFIG['chunk_overlap']}")
    print(f"  Default Max Docs: {CONFIG['default_max_docs']}")
    print(f"  Embedding Model:  {CONFIG['embedding_model']}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        validate_paths()
        print_configuration()
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        exit(1)
else:
    # Only validate that project root exists during normal import
    try:
        if not paths.project_root.exists():
            raise RuntimeError(f"Project root does not exist: {paths.project_root}")
    except Exception as e:
        print(f"Warning: Configuration issue detected: {e}")