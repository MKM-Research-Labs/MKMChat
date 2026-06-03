# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
# ... (license header unchanged)
"""
MKM Research Document Q&A Application (v7.2)
--------------------------------------------

CHANGELOG:
v7.2 - Cleaned imports; added WSGI factory; patched langchain_core paths
v7.1 - Server config (host, port, debug) moved to config.py
v7.0 - Research routes now properly registered with Flask

Description:
This application provides a document query interface using Retrieval Augmented Generation (RAG).
Users can interact with locally hosted LLMs through LM Studio or cloud-based APIs (Perplexity, Anthropic).
The system retrieves relevant document chunks using FAISS vector indexing and generates responses
based on the provided context.
"""

from flask import Flask, render_template, send_from_directory
from langchain_community.vectorstores import FAISS  # noqa: F401 (used in services)
from langchain_huggingface import HuggingFaceEmbeddings
import os
import argparse
from typing import List

from config import (
    CONFIG,
    paths,
    get_collection_config,
    get_all_collections,
    ANTHROPIC_API_KEY,
    PERPLEXITY_API_KEY,
    PERPLEXITY_API_URL,
    ANTHROPIC_API_URL,
    LM_STUDIO_API_URL,
    MODEL_ID,
    EMBEDDING_MODEL,
    AVAILABLE_MODELS,
    DEFAULT_COLLECTION,
)

from src.research import create_research_route, create_research_stream_route
from src.models import LocalModelHandler, PerplexityHandler, AnthropicHandler
from src.services import FAISSService, ChatService
from src.routes import (
    create_summary_blueprint,
    create_chat_blueprint,
    create_index_blueprint,
    create_analysis_blueprint,
)


class DocumentQAApp:
    """Main application class for the Document Q&A system"""

    def __init__(self):
        # API Keys (from config.py)
        self.ANTHROPIC_API_KEY = ANTHROPIC_API_KEY
        self.PERPLEXITY_API_KEY = PERPLEXITY_API_KEY

        # API URLs (from config.py)
        self.PERPLEXITY_API_URL = PERPLEXITY_API_URL
        self.ANTHROPIC_API_URL = ANTHROPIC_API_URL

        # Initialize Flask app
        self.app = Flask(
            __name__,
            static_folder=str(paths.static_dir),
            template_folder=str(paths.templates_dir),
        )

        # Initialize services
        self.CHATS_FILE = str(paths.chats_file)
        self.chat_service = ChatService(self.CHATS_FILE)
        self.faiss_service = FAISSService()

        self.AVAILABLE_INDICES = self.faiss_service.get_available_indices()
        self.ACTIVE_INDEX_KEY = DEFAULT_COLLECTION

        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

        # Backward-compatible vector store cache
        self.vector_stores = {}

        self.AVAILABLE_MODELS = AVAILABLE_MODELS

        # Initialize model handlers
        self.local_model = LocalModelHandler(LM_STUDIO_API_URL)
        self.perplexity_model = PerplexityHandler(self.PERPLEXITY_API_KEY, self.PERPLEXITY_API_URL)
        self.anthropic_model = AnthropicHandler(self.ANTHROPIC_API_KEY, self.ANTHROPIC_API_URL)

        self._load_default_index()
        self._setup_routes()

    def _load_default_index(self):
        """Load the default index on startup using FAISS service"""
        try:
            vector_store = self.faiss_service.load_default_index(DEFAULT_COLLECTION)
            if vector_store:
                self.vector_stores[DEFAULT_COLLECTION] = vector_store
        except Exception as e:
            print(f"Warning: Failed to load default index: {e}")

    def _load_faiss_index(self, index_key):
        """Load a FAISS index by key using FAISS service"""
        vector_store = self.faiss_service.load_index(index_key)
        self.vector_stores[index_key] = vector_store
        return vector_store

    def _handle_local_model(self, query: str, context: str, model: str) -> str:
        return self.local_model.query(query, context, model)

    def _handle_perplexity_model(self, query: str, context: str, model: str) -> str:
        return self.perplexity_model.query(query, context, model)

    def _handle_anthropic_model(self, query: str, context: str, model: str) -> str:
        return self.anthropic_model.query(query, context, model)

    def _setup_routes(self):
        """Set up Flask routes using blueprints"""

        @self.app.route("/")
        def index():
            return render_template(
                "chat.html",
                available_models=self.AVAILABLE_MODELS,
                available_indices=self.AVAILABLE_INDICES,
                active_index=self.ACTIVE_INDEX_KEY,
                lm_studio_url=LM_STUDIO_API_URL,
            )

        @self.app.route("/favicon.ico")
        def favicon():
            return send_from_directory(
                os.path.join(self.app.static_folder, "images"),
                "favicon.svg",
                mimetype="image/svg+xml",
            )

        @self.app.route("/apple-touch-icon.png")
        @self.app.route("/apple-touch-icon-precomposed.png")
        def apple_touch_icon():
            return send_from_directory(
                os.path.join(self.app.static_folder, "images"),
                "favicon.svg",
                mimetype="image/svg+xml",
            )

        summary_bp = create_summary_blueprint(self.chat_service)
        chat_bp = create_chat_blueprint(self)
        index_bp = create_index_blueprint(self)
        analysis_bp = create_analysis_blueprint()

        self.app.register_blueprint(summary_bp)
        self.app.register_blueprint(chat_bp)
        self.app.register_blueprint(index_bp)
        self.app.register_blueprint(analysis_bp)

        research_handler = create_research_route(self)
        research_stream_handler = create_research_stream_route(self)

        self.app.add_url_rule("/research_query", "research_query", research_handler, methods=["POST"])
        self.app.add_url_rule(
            "/research_query_stream",
            "research_query_stream",
            research_stream_handler,
            methods=["GET", "POST"],
        )
        print("✓ Research routes registered")

    def run(self, debug=None, port=None, host=None):
        debug = CONFIG.get("server_debug", True) if debug is None else debug
        port = CONFIG.get("server_port") if port is None else port
        host = CONFIG.get("server_host") if host is None else host

        print(f"Starting server -> host={host}, port={port}, debug={debug}")
        print("Available FAISS indices:")
        for key, info in self.AVAILABLE_INDICES.items():
            print(f"  - {key}: {info['name']} ({info['path']})")

        print(f"Default active index: {self.ACTIVE_INDEX_KEY}")
        print("Template directory:", paths.templates_dir)
        print("Static directory:", paths.static_dir)
        print(f"Chat history file: {self.CHATS_FILE}")
        print("Available models:", list(self.AVAILABLE_MODELS.keys()))

        print("\nRegistered routes:")
        for rule in self.app.url_map.iter_rules():
            methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
            print(f"  {rule.endpoint}: {rule.rule} [{methods}]")

        self.app.run(debug=debug, port=port, host=host)


def create_app() -> Flask:
    """WSGI factory — use with: gunicorn 'app:create_app()'"""
    return DocumentQAApp().app


def parse_arguments():
    parser = argparse.ArgumentParser(description="MKM Research Document Q&A Application")
    parser.add_argument("--host", type=str, help="Server host (overrides config)")
    parser.add_argument("--port", type=int, help="Server port (overrides config)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-debug", action="store_true", help="Disable debug mode")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    app = DocumentQAApp()

    debug = None
    if args.debug:
        debug = True
    elif args.no_debug:
        debug = False

    app.run(debug=debug, port=args.port, host=args.host)
