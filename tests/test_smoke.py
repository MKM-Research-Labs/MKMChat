#!/usr/bin/env python3
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

"""
Smoke Tests
===========

Quick tests to verify basic application functionality.
These tests should run fast and catch obvious issues.
"""

import pytest


class TestImports:
    """Test that all core modules can be imported."""

    def test_import_config(self):
        """Config module should import without errors."""
        from config import CONFIG, paths, get_all_collections
        assert CONFIG is not None
        assert paths is not None

    def test_import_app(self):
        """App module should import without errors."""
        from src.app import DocumentQAApp
        assert DocumentQAApp is not None

    def test_import_routes(self):
        """Route modules should import without errors."""
        from src.routes import (
            create_summary_blueprint,
            create_chat_blueprint,
            create_index_blueprint,
            create_analysis_blueprint
        )
        assert create_summary_blueprint is not None
        assert create_chat_blueprint is not None
        assert create_index_blueprint is not None
        assert create_analysis_blueprint is not None

    def test_import_services(self):
        """Service modules should import without errors."""
        from src.services import FAISSService, ChatService
        assert FAISSService is not None
        assert ChatService is not None

    def test_import_models(self):
        """Model handler modules should import without errors."""
        from src.models import LocalModelHandler, PerplexityHandler, AnthropicHandler
        assert LocalModelHandler is not None
        assert PerplexityHandler is not None
        assert AnthropicHandler is not None


class TestConfiguration:
    """Test configuration is valid."""

    def test_collections_exist(self):
        """At least one collection should be configured."""
        from config import get_all_collections
        collections = get_all_collections()
        assert isinstance(collections, dict)
        assert len(collections) > 0, "No collections configured"

    def test_paths_configured(self):
        """Required paths should be configured."""
        from config import paths
        assert hasattr(paths, 'static_dir')
        assert hasattr(paths, 'templates_dir')

    def test_embedding_model_configured(self):
        """Embedding model should be configured."""
        from config import EMBEDDING_MODEL
        assert EMBEDDING_MODEL is not None
        assert isinstance(EMBEDDING_MODEL, str)


class TestAppInitialization:
    """Test that the application can be initialized.

    Uses the flask_app conftest fixture which handles mocking of heavy
    dependencies (FAISS, embeddings, etc.).
    """

    def test_app_instantiation(self, flask_app):
        """DocumentQAApp should instantiate without errors."""
        assert flask_app is not None
        assert flask_app.app is not None  # Flask app

    def test_flask_app_exists(self, flask_app):
        """Flask app should be created."""
        assert flask_app.app is not None
        assert flask_app.app.name == 'src.app'

    def test_routes_registered(self, flask_app):
        """All expected routes should be registered."""
        # Get all registered routes
        routes = [rule.rule for rule in flask_app.app.url_map.iter_rules()]

        # Check critical routes exist
        expected_routes = [
            '/',
            '/query',
            '/get_available_indices',
            '/get_available_models',
            '/switch_index',
            '/get_summaries',
            '/get_chat_history',
            '/save_chat',
            '/analyze_sources',
            '/research_query',
        ]

        for route in expected_routes:
            assert route in routes, f"Missing route: {route}"


class TestFlaskTestClient:
    """Test routes using Flask test client.

    Uses the client conftest fixture (which depends on flask_app).
    """

    def test_index_page(self, client):
        """GET / should return 200."""
        response = client.get('/')
        assert response.status_code == 200

    def test_get_available_indices(self, client):
        """GET /get_available_indices should return JSON."""
        response = client.get('/get_available_indices')
        assert response.status_code == 200
        data = response.get_json()
        assert 'indices' in data
        assert 'active' in data

    def test_get_available_models(self, client):
        """GET /get_available_models should return JSON."""
        response = client.get('/get_available_models')
        assert response.status_code == 200
        data = response.get_json()
        assert 'models' in data

    def test_get_chat_history(self, client):
        """GET /get_chat_history should return JSON."""
        response = client.get('/get_chat_history')
        assert response.status_code == 200
        data = response.get_json()
        assert 'chats' in data

    def test_query_requires_json(self, client):
        """POST /query without JSON should return 400."""
        response = client.post('/query', data='not json')
        assert response.status_code == 400

    def test_query_requires_query_field(self, client):
        """POST /query without query field should return 400."""
        response = client.post(
            '/query',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_switch_index_requires_json(self, client):
        """POST /switch_index without JSON should return 400."""
        response = client.post('/switch_index', data='not json')
        assert response.status_code == 400

    def test_switch_index_requires_index_key(self, client):
        """POST /switch_index without index_key should return 400."""
        response = client.post(
            '/switch_index',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_analyze_sources_requires_json(self, client):
        """POST /analyze_sources without JSON should return 400."""
        response = client.post('/analyze_sources', data='not json')
        assert response.status_code == 400

    def test_save_chat_requires_json(self, client):
        """POST /save_chat without JSON should return 400."""
        response = client.post('/save_chat', data='not json')
        assert response.status_code == 400
