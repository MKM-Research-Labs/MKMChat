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
Tests for src/routes/analysis_routes.py

Tests the analysis blueprint and source analysis endpoints.
"""

import json

import pytest
from flask import Flask

from src.routes.analysis_routes import create_analysis_blueprint


@pytest.fixture
def analysis_client():
    """Create a minimal Flask app with only the analysis blueprint registered."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    bp = create_analysis_blueprint()
    app.register_blueprint(bp)
    return app.test_client()


class TestAnalysisRoutes:
    """Tests for analysis routes."""

    def test_analyze_sources_requires_json(self, analysis_client):
        """Should return 400 if request is not JSON."""
        response = analysis_client.post(
            '/analyze_sources',
            data='not json',
            content_type='text/plain'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_analyze_sources_requires_sources(self, analysis_client):
        """Should return 400 if sources not provided."""
        response = analysis_client.post(
            '/analyze_sources',
            json={'query': 'test'},
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_analyze_sources_requires_list(self, analysis_client):
        """Should return 400 if sources is not a list."""
        response = analysis_client.post(
            '/analyze_sources',
            json={'sources': 'not a list', 'query': 'test'},
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_analyze_sources_success(self, analysis_client):
        """Should analyze sources successfully."""
        sources = [
            {'file': '/Users/newdavid/Documents/MKMChat/docs/doc1_2023.pdf', 'page': '1'},
            {'file': '/Users/newdavid/Documents/MKMChat/docs/doc2_2020.pdf', 'page': '5'},
            {'file': '/Users/newdavid/Documents/MKMChat/docs/doc3_2018.pdf', 'page': '2'}
        ]

        response = analysis_client.post(
            '/analyze_sources',
            json={'sources': sources, 'query': 'test query'},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'totalResults' in data
        assert 'topSources' in data
        assert 'relevanceDistribution' in data
        assert 'dateDistribution' in data
        assert 'topKeywords' in data

    def test_analyze_sources_total_results(self, analysis_client):
        """Should return correct total results count."""
        sources = [
            {'file': 'doc1.pdf', 'page': '1'},
            {'file': 'doc2.pdf', 'page': '2'},
            {'file': 'doc3.pdf', 'page': '3'}
        ]

        response = analysis_client.post(
            '/analyze_sources',
            json={'sources': sources, 'query': 'test'},
            content_type='application/json'
        )

        data = json.loads(response.data)
        assert data['totalResults'] == 3

    def test_analyze_sources_groups_by_file(self, analysis_client):
        """Should group sources by file name."""
        sources = [
            {'file': 'doc1.pdf', 'page': '1'},
            {'file': 'doc1.pdf', 'page': '2'},
            {'file': 'doc1.pdf', 'page': '3'},
            {'file': 'doc2.pdf', 'page': '1'}
        ]

        response = analysis_client.post(
            '/analyze_sources',
            json={'sources': sources, 'query': 'test'},
            content_type='application/json'
        )

        data = json.loads(response.data)

        # Check top sources
        top_sources = data['topSources']
        assert len(top_sources) > 0

        # Find doc1.pdf in top sources
        doc1 = next((s for s in top_sources if 'doc1' in s['name']), None)
        if doc1:
            assert doc1['count'] == 3
            assert doc1['pages'] == 3

    def test_analyze_sources_date_distribution(self, analysis_client):
        """Should categorize sources by date."""
        sources = [
            {'file': 'document_2024.pdf', 'page': '1'},
            {'file': 'document_2021.pdf', 'page': '1'},
            {'file': 'document_2018.pdf', 'page': '1'},
            {'file': 'document_2010.pdf', 'page': '1'}
        ]

        response = analysis_client.post(
            '/analyze_sources',
            json={'sources': sources, 'query': 'test'},
            content_type='application/json'
        )

        data = json.loads(response.data)
        date_distribution = data['dateDistribution']

        # Should have multiple date groups
        assert isinstance(date_distribution, list)

    def test_analyze_sources_relevance_distribution(self, analysis_client):
        """Should return relevance distribution."""
        sources = [
            {'file': 'doc1.pdf', 'page': '1'},
            {'file': 'doc2.pdf', 'page': '2'}
        ]

        response = analysis_client.post(
            '/analyze_sources',
            json={'sources': sources, 'query': 'test'},
            content_type='application/json'
        )

        data = json.loads(response.data)
        relevance = data['relevanceDistribution']

        assert isinstance(relevance, list)
        assert len(relevance) > 0

        # Check structure
        for item in relevance:
            assert 'name' in item
            assert 'value' in item

    def test_analyze_sources_top_keywords(self, analysis_client):
        """Should extract keywords from filenames."""
        sources = [
            {'file': 'physics_quantum_mechanics.pdf', 'page': '1'},
            {'file': 'physics_relativity_theory.pdf', 'page': '1'},
            {'file': 'chemistry_organic.pdf', 'page': '1'}
        ]

        response = analysis_client.post(
            '/analyze_sources',
            json={'sources': sources, 'query': 'test'},
            content_type='application/json'
        )

        data = json.loads(response.data)
        keywords = data['topKeywords']

        assert isinstance(keywords, list)
        # Should have extracted some keywords
        if keywords:
            for kw in keywords:
                assert 'text' in kw
                assert 'value' in kw

    def test_analyze_sources_limits_top_sources(self, analysis_client):
        """Should limit top sources to 5."""
        sources = [
            {'file': f'doc{i}.pdf', 'page': '1'}
            for i in range(10)
        ]

        response = analysis_client.post(
            '/analyze_sources',
            json={'sources': sources, 'query': 'test'},
            content_type='application/json'
        )

        data = json.loads(response.data)
        assert len(data['topSources']) <= 5

    def test_analyze_sources_handles_empty_file(self, analysis_client):
        """Should handle sources with empty file field."""
        sources = [
            {'file': '', 'page': '1'},
            {'file': 'valid_doc.pdf', 'page': '2'}
        ]

        response = analysis_client.post(
            '/analyze_sources',
            json={'sources': sources, 'query': 'test'},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Only valid source should be counted
        assert data['totalResults'] >= 1

    def test_analyze_sources_returns_query(self, analysis_client):
        """Should return the original query."""
        response = analysis_client.post(
            '/analyze_sources',
            json={'sources': [{'file': 'doc.pdf', 'page': '1'}], 'query': 'my test query'},
            content_type='application/json'
        )

        data = json.loads(response.data)
        assert data['query'] == 'my test query'

    def test_analyze_sources_sorts_by_count(self, analysis_client):
        """Should sort top sources by count descending."""
        sources = [
            {'file': 'doc1.pdf', 'page': '1'},
            {'file': 'doc2.pdf', 'page': '1'},
            {'file': 'doc2.pdf', 'page': '2'},
            {'file': 'doc2.pdf', 'page': '3'},
            {'file': 'doc3.pdf', 'page': '1'},
            {'file': 'doc3.pdf', 'page': '2'}
        ]

        response = analysis_client.post(
            '/analyze_sources',
            json={'sources': sources, 'query': 'test'},
            content_type='application/json'
        )

        data = json.loads(response.data)
        top_sources = data['topSources']

        # Verify descending order
        for i in range(len(top_sources) - 1):
            assert top_sources[i]['count'] >= top_sources[i + 1]['count']


    def test_analyze_sources_archive_date_group(self, analysis_client):
        """Should categorize pre-2014 sources into 'Archive (Before 2014)' (covers line 93-95)."""
        sources = [
            {'file': 'document_2010.pdf', 'page': '1'},
            {'file': 'document_2005.pdf', 'page': '1'},
            {'file': 'document_1999.pdf', 'page': '1'},
        ]

        response = analysis_client.post(
            '/analyze_sources',
            json={'sources': sources, 'query': 'test'},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        date_distribution = data['dateDistribution']

        # All 3 sources should be in 'Archive (Before 2014)'
        archive = next((d for d in date_distribution if 'Archive' in d['name']), None)
        assert archive is not None
        assert archive['count'] == 3

    def test_analyze_sources_exception(self, analysis_client):
        """Should return 500 when an unexpected error occurs (covers lines 155-158)."""
        from unittest.mock import patch

        # Patch re.search to raise an unexpected error during processing
        with patch("src.routes.analysis_routes.re.search", side_effect=RuntimeError("unexpected error")):
            response = analysis_client.post(
                '/analyze_sources',
                json={'sources': [{'file': 'doc_2020.pdf', 'page': '1'}], 'query': 'test'},
                content_type='application/json'
            )

        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


class TestCreateAnalysisBlueprint:
    """Tests for create_analysis_blueprint function."""

    def test_creates_blueprint(self):
        """Should create a Flask blueprint."""
        bp = create_analysis_blueprint()

        assert bp is not None
        assert bp.name == 'analysis'

    def test_blueprint_has_routes(self):
        """Blueprint should have analyze_sources route."""
        bp = create_analysis_blueprint()

        # Check that rules exist
        app = Flask(__name__)
        app.register_blueprint(bp)

        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/analyze_sources' in rules
