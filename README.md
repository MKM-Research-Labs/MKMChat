# MKMChat

**Version 7.2** | MKM Research Labs

A document Q&A application powered by Retrieval Augmented Generation (RAG). Query multiple document collections using AI-generated responses backed by vector-indexed documents.

## Features

- **Multi-Collection RAG** - Query across 7 configurable document knowledge bases
- **Deep Research** - Cross-collection research with real-time streaming progress
- **Multiple LLM Backends** - Anthropic Claude, Perplexity, and local models via LM Studio
- **Document Summarization** - Automated AI-powered summaries for indexed documents
- **Source Analysis** - Visualize and analyze retrieved source documents
- **Chat History** - Persistent conversation history with search and filtering
- **Wide Format Support** - PDF, EPUB, DOCX, DOC, PPTX, PPT, XLSX, XLS
- **96% Test Coverage** - Comprehensive pytest suite with E2E browser tests

## Prerequisites

- Python 3.11+
- An Anthropic API key (for Claude models)
- Optional: Perplexity API key, LM Studio running locally on port 1234
- Optional (for OCR on scanned PDFs): `tesseract` and `poppler` system binaries
  - macOS: `brew install tesseract poppler`
  - Ubuntu/Debian: `sudo apt install tesseract-ocr poppler-utils`

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd MKMChat
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Edit `config.py` (in the project root) and set your API keys:

```python
ANTHROPIC_API_KEY = "your-anthropic-api-key"
PERPLEXITY_API_KEY = "your-perplexity-api-key"   # optional
```

### 5. Set up the data directory

The `data/` directory holds your documents, FAISS indices, and runtime JSON files. It is **not tracked by git** — each user creates their own.

```bash
mkdir -p data/docs/{misc,phys,pops,hist,mods,corp,back}
```

Then place your documents into the appropriate collection folders:

| Folder | Collection | Description |
|--------|-----------|-------------|
| `data/docs/misc/` | Miscellaneous | General documents |
| `data/docs/phys/` | Physical | Physics / physical science |
| `data/docs/pops/` | Parenting | Parenting psychology |
| `data/docs/hist/` | History | History books |
| `data/docs/mods/` | Models | Modelling methodologies |
| `data/docs/corp/` | Corporate | Business documents |
| `data/docs/back/` | Backgammon | Backgammon research |

Supported file types: PDF, EPUB, DOCX, DOC, PPTX, PPT, XLSX, XLS.

The `data/faiss/` and `data/json/` directories are created automatically on first run.

### 6. Install JavaScript test dependencies (optional)

Only needed if you want to run frontend tests:

```bash
cd tests/js && npm install && cd ../..
```

## Usage

### Quick Start (web only)

Skip document processing and launch the web interface directly:

```bash
python chat.py -web-only
```

Then open **http://127.0.0.1:5000** in your browser.

### Full Pipeline

Process documents, build FAISS indices, then start the web server:

```bash
python chat.py
```

### Command-Line Options

```
Mode selection:
  -web-only              Skip processing, go directly to web interface
  -process-only          Process documents without starting the web server
  -summarize-only        Run summarization only
  -list-summaries        List summary status for all documents

Web server:
  --port PORT            Port number (default: 5000)
  --host HOST            Host to bind to (default: 127.0.0.1)
  --debug                Run Flask in debug mode (default: True)

Collection:
  --collection NAME      Process a specific collection (misc, phys, pops,
                         hist, mods, corp, back) or "all" (default: all)

Processing:
  --max-docs N           Maximum documents to process (default: 50)
  --force                Force reprocessing of all documents
  --no-progress          Disable progress bars
  --alt-embeddings       Use alternative embedding models
  --diagnose             Run diagnostics on problematic files

Summarization:
  --summarize            Summarize documents after processing
  --clean-summaries      Clear existing summaries before processing
```

### Examples

```bash
# Process only the history collection
python chat.py -process-only --collection hist

# Force-reprocess and summarize the corporate collection
python chat.py -process-only --collection corp --force --summarize

# List which documents have been summarized
python chat.py -list-summaries

# Start the web interface on a custom port
python chat.py -web-only --port 8080
```

## Running Tests

### Python unit tests (with coverage)

```bash
bash scripts/run_tests.sh
```

Or directly:

```bash
pytest tests/ --ignore=tests/e2e --ignore=tests/js -m "not integration" -q --cov=src
```

### E2E browser tests (Playwright)

```bash
bash scripts/run_e2e.sh
```

### JavaScript tests (Jest)

```bash
cd tests/js && npx jest --coverage
```

### All tests

```bash
bash scripts/run_all.sh
```

### Integration tests (live API calls)

```bash
pytest tests/ -m integration -v
```

Coverage reports are generated at `data/output/audit/coverage_html/index.html`.

## Project Structure

```
MKMChat/
├── chat.py                     # Main entry point
├── config.py                   # Centralised configuration
├── pyproject.toml              # pytest, coverage, ruff config
├── src/
│   ├── app.py                  # Flask application
│   ├── document_processor.py   # Document processing entry
│   ├── models/                 # LLM provider handlers
│   ├── routes/                 # Flask route blueprints
│   ├── services/               # Business logic (FAISS, chat)
│   ├── research/               # Deep research module
│   ├── summary/                # Document summarization
│   ├── proc/                   # Document processing pipeline
│   ├── loaders/                # File-type document loaders
│   └── utils/                  # Utility functions
├── data/                       # User data (git-ignored)
│   ├── docs/                   # Document collections (7 folders)
│   ├── faiss/                  # FAISS vector indices
│   ├── json/                   # Runtime metadata (chats, summaries)
│   └── output/audit/           # Test coverage & audit reports
├── templates/                  # Jinja2 HTML templates
├── static/
│   ├── js/modules/             # Frontend JavaScript modules
│   ├── css/                    # Stylesheets
│   └── images/                 # Static assets
├── tests/
│   ├── conftest.py             # Shared pytest fixtures
│   ├── _conftest/              # Fixture submodules
│   ├── test_*.py               # Python unit tests
│   ├── test_models/            # Model handler tests
│   ├── test_routes/            # Route tests
│   ├── test_services/          # Service tests
│   ├── test_research/          # Research module tests
│   ├── test_loaders/           # Document loader tests
│   ├── test_proc/              # Processing pipeline tests
│   ├── test_summary/           # Summarization tests
│   ├── e2e/                    # Playwright E2E tests
│   └── js/                     # Jest JavaScript tests
├── scripts/
│   ├── run_tests.sh            # Unit tests + coverage
│   ├── run_e2e.sh              # E2E tests
│   └── run_all.sh              # All test suites
└── .github/workflows/ci.yml   # CI/CD pipeline
```

## Technical Details

- **Embedding model**: `all-MiniLM-L6-v2` (Sentence Transformers)
- **Vector store**: FAISS (Facebook AI Similarity Search)
- **Chunk size**: 3000 characters with 500-character overlap
- **Top-k retrieval**: 5 chunks per query
- **Frontend**: Vanilla JavaScript with Tailwind CSS
- **Backend**: Flask with Jinja2 templates
- **Test coverage**: 96% (571+ tests)

## License

Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

This software is provided under license by MKM Research Labs. See the license agreement for terms and conditions.
