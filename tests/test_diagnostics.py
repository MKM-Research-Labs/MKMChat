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
Diagnostic Tests
================

These tests help diagnose 500 errors and other issues.
Run with: pytest tests/test_diagnostics.py -v
"""

import json
import os

import pytest


class TestDiagnose500Errors:
    """
    Diagnostic tests to identify sources of 500 errors.
    These tests print detailed information about what's working and what's not.
    """

    def test_01_check_config_files(self):
        """Check if required config files exist."""
        from config import paths, get_all_collections

        print("\n" + "=" * 60)
        print("CHECKING CONFIGURATION FILES")
        print("=" * 60)

        # Check paths
        checks = [
            ("Static directory", paths.static_dir),
            ("Templates directory", paths.templates_dir),
            ("Chats file", paths.chats_file),
        ]

        for name, path in checks:
            exists = os.path.exists(path)
            status = "" if exists else ""
            print(f"{status} {name}: {path}")

        # Check collection summary files
        print("\nCollection Summary Files:")
        collections = get_all_collections()
        for key, config in collections.items():
            summary_file = config.get('summary_file', '')
            exists = os.path.exists(summary_file)
            status = "" if exists else ""
            print(f"  {status} {key}: {summary_file}")

    def test_02_check_faiss_indices(self):
        """Check if FAISS index files exist."""
        from src.services import FAISSService

        print("\n" + "=" * 60)
        print("CHECKING FAISS INDICES")
        print("=" * 60)

        service = FAISSService()
        indices = service.get_available_indices()

        for key, info in indices.items():
            path = info.get('path', '')
            index_file = os.path.join(path, 'index.faiss')
            pkl_file = os.path.join(path, 'index.pkl')

            index_exists = os.path.exists(index_file)
            pkl_exists = os.path.exists(pkl_file)

            if index_exists and pkl_exists:
                status = ""
                detail = "ready"
            elif os.path.exists(path):
                status = ""
                detail = "directory exists but index files missing"
            else:
                status = ""
                detail = "directory missing"

            print(f"{status} {key} ({info.get('name', 'Unknown')}): {detail}")
            print(f"    Path: {path}")

    def test_03_check_api_keys(self):
        """Check if API keys are configured."""
        from config import ANTHROPIC_API_KEY, PERPLEXITY_API_KEY

        print("\n" + "=" * 60)
        print("CHECKING API KEYS")
        print("=" * 60)

        if ANTHROPIC_API_KEY:
            print(f" Anthropic API key set (length: {len(ANTHROPIC_API_KEY)})")
        else:
            print(" Anthropic API key NOT set")

        if PERPLEXITY_API_KEY:
            print(f" Perplexity API key set (length: {len(PERPLEXITY_API_KEY)})")
        else:
            print(" Perplexity API key NOT set")

    def test_04_check_lm_studio(self):
        """Check if LM Studio is running."""
        import requests
        from config import LM_STUDIO_API_URL

        print("\n" + "=" * 60)
        print("CHECKING LM STUDIO CONNECTION")
        print("=" * 60)

        print(f"URL: {LM_STUDIO_API_URL}")

        try:
            models_url = LM_STUDIO_API_URL.replace('/chat/completions', '/models')
            response = requests.get(models_url, timeout=3)

            if response.status_code == 200:
                print(" LM Studio is running and reachable")
                try:
                    data = response.json()
                    models = data.get('data', [])
                    if models:
                        print(f"   Available models: {len(models)}")
                        for model in models[:3]:
                            print(f"     - {model.get('id', 'Unknown')}")
                except Exception:
                    pass
            else:
                print(f" LM Studio returned status {response.status_code}")

        except requests.exceptions.ConnectionError:
            print(" LM Studio NOT reachable")
            print("   To use local models, start LM Studio and load a model")
        except Exception as e:
            print(f" Error: {e}")

    def test_05_test_vector_store_query(self):
        """Test querying the vector store."""
        from src.services import FAISSService

        print("\n" + "=" * 60)
        print("TESTING VECTOR STORE QUERY")
        print("=" * 60)

        service = FAISSService()

        try:
            # Load the default index
            vector_store = service.load_default_index("misc")

            if not vector_store:
                print(" Failed to load vector store")
                print("   Run: python run.py -process-only")
                return

            print(" Vector store loaded")

            # Try a test query
            test_query = "test"
            docs = vector_store.similarity_search(test_query, k=2)

            print(f" Query returned {len(docs)} documents")

            if docs:
                print(f"   First result source: {docs[0].metadata.get('source', 'Unknown')}")

        except FileNotFoundError as e:
            print(f" Index files not found: {e}")
            print("   Run: python run.py -process-only")
        except Exception as e:
            print(f" Error: {e}")

    def test_06_full_query_simulation(self, flask_app):
        """Simulate a full query to identify where 500 errors occur.

        Uses the flask_app conftest fixture instead of manually creating
        DocumentQAApp with stdout suppression.
        """
        print("\n" + "=" * 60)
        print("SIMULATING FULL QUERY FLOW")
        print("=" * 60)

        steps_passed = []
        steps_failed = []

        # Step 1: App already instantiated via flask_app fixture
        try:
            assert flask_app is not None
            assert flask_app.app is not None
            steps_passed.append("App instantiation")
        except Exception as e:
            steps_failed.append(f"App instantiation: {e}")
            print(" FAILED at app instantiation")
            return

        # Step 2: Check vector store
        try:
            if 'misc' in flask_app.vector_stores and flask_app.vector_stores['misc']:
                steps_passed.append("Vector store loaded")
            else:
                steps_failed.append("Vector store not loaded")
        except Exception as e:
            steps_failed.append(f"Vector store check: {e}")

        # Step 3: Test similarity search
        if 'misc' in flask_app.vector_stores:
            try:
                docs = flask_app.vector_stores['misc'].similarity_search("test", k=2)
                steps_passed.append(f"Similarity search ({len(docs)} results)")
            except Exception as e:
                steps_failed.append(f"Similarity search: {e}")

        # Step 4: Check model handlers
        try:
            if flask_app.local_model:
                steps_passed.append("Local model handler ready")
        except Exception as e:
            steps_failed.append(f"Local model handler: {e}")

        # Print results
        print("\nSteps passed:")
        for step in steps_passed:
            print(f"  {step}")

        if steps_failed:
            print("\nSteps failed:")
            for step in steps_failed:
                print(f"  {step}")
        else:
            print("\n All steps passed!")
            print("   If you still get 500 errors, the issue is likely:")
            print("   - LM Studio not running (for local models)")
            print("   - API key invalid (for cloud models)")
            print("   - Network connectivity issues")


class TestEndpointDiagnostics:
    """Test each endpoint and report detailed errors.

    Uses the client conftest fixture instead of manually creating
    DocumentQAApp with stdout suppression.
    """

    def test_endpoint_diagnostics(self, client):
        """Test all endpoints and report status."""
        print("\n" + "=" * 60)
        print("ENDPOINT DIAGNOSTICS")
        print("=" * 60)

        endpoints = [
            ('GET', '/', None),
            ('GET', '/get_available_indices', None),
            ('GET', '/get_available_models', None),
            ('GET', '/get_chat_history', None),
            ('GET', '/get_summaries?docs_type=misc', None),
            ('POST', '/query', {'query': 'test', 'model': 'mistral-7b-instruct-v0.2'}),
            ('POST', '/switch_index', {'index_key': 'misc'}),
            ('POST', '/analyze_sources', {'sources': [{'file': 'test.pdf', 'page': '1'}], 'query': 'test'}),
        ]

        for method, endpoint, data in endpoints:
            try:
                if method == 'GET':
                    response = client.get(endpoint)
                else:
                    response = client.post(
                        endpoint,
                        json=data,
                        content_type='application/json'
                    )

                status = "" if response.status_code == 200 else ""
                print(f"{status} {method} {endpoint}: {response.status_code}")

                if response.status_code >= 400:
                    try:
                        error_data = response.get_json()
                        if error_data and 'error' in error_data:
                            print(f"     Error: {error_data['error'][:100]}")
                    except Exception:
                        pass

            except Exception as e:
                print(f" {method} {endpoint}: Exception - {e}")
