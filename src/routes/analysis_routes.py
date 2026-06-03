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
Analysis Routes Module

Handles source analysis and visualization endpoints.
"""

from flask import Blueprint, request, jsonify
import traceback
import re

from config import paths


def create_analysis_blueprint():
    """
    Create and configure the analysis routes blueprint.
    
    Returns:
        Flask Blueprint configured with analysis routes
    """
    bp = Blueprint('analysis', __name__)
    
    @bp.route('/analyze_sources', methods=['POST'])
    def analyze_sources():
        """API endpoint to analyze query sources for visualization"""
        try:
            # Validate request data
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
                
            request_data = request.get_json()
            sources = request_data.get('sources')
            query = request_data.get('query')
            
            if not sources or not isinstance(sources, list):
                return jsonify({'error': 'Invalid sources data'}), 400
            
            # Group sources by file name
            source_counts = {}
            for source in sources:
                file_name = source.get('file', '').replace(str(paths.docs_root) + '/', '')
                if not file_name:
                    continue
                    
                if file_name not in source_counts:
                    source_counts[file_name] = {
                        'count': 0,
                        'pages': set()
                    }
                    
                source_counts[file_name]['count'] += 1
                source_counts[file_name]['pages'].add(source.get('page', '1'))
            
            # Extract year from filename if possible
            def extract_year(filename):
                year_match = re.search(r'(19|20)\d{2}', filename)
                return int(year_match.group(0)) if year_match else None
            
            # Date grouping
            date_groups = {
                'Recent (2023-2026)': 0,
                'Newer (2020-2022)': 0,
                'Recent (2017-2019)': 0,
                'Older (2014-2016)': 0,
                'Archive (Before 2014)': 0
            }
            
            # Process each source for date categorization
            for file_name in source_counts:
                year = extract_year(file_name)
                if year:
                    if year >= 2023:
                        date_groups['Recent (2023-2026)'] += source_counts[file_name]['count']
                    elif year >= 2020:
                        date_groups['Newer (2020-2022)'] += source_counts[file_name]['count']
                    elif year >= 2017:
                        date_groups['Recent (2017-2019)'] += source_counts[file_name]['count']
                    elif year >= 2014:
                        date_groups['Older (2014-2016)'] += source_counts[file_name]['count']
                    else:
                        date_groups['Archive (Before 2014)'] += source_counts[file_name]['count']
            
            # Format response
            top_sources = []
            for file_name, data in source_counts.items():
                top_sources.append({
                    'name': file_name[:20] + ('...' if len(file_name) > 20 else ''),
                    'count': data['count'],
                    'pages': len(data['pages'])
                })
            
            # Sort by count, descending
            top_sources.sort(key=lambda x: x['count'], reverse=True)
            top_sources = top_sources[:5]  # Take top 5
            
            # Format date distribution
            date_distribution = []
            for date_range, count in date_groups.items():
                if count > 0:
                    date_distribution.append({
                        'name': date_range,
                        'count': count
                    })
            
            # Generate estimated relevance distribution (in a real implementation,
            # this would use embeddings to calculate actual relevance)
            total_sources = len(sources)
            relevance_distribution = [
                {'name': 'Very High', 'value': int(total_sources * 0.3) or 1},
                {'name': 'High', 'value': int(total_sources * 0.4) or 1},
                {'name': 'Medium', 'value': int(total_sources * 0.2) or 1},
                {'name': 'Low', 'value': int(total_sources * 0.1) or 1}
            ]
            
            # Extract keywords from filenames
            terms = {}
            for filename in source_counts:
                words = re.sub(r'\.\w+$', '', filename)  # Remove file extension
                words = re.sub(r'[^a-zA-Z0-9 ]', ' ', words)  # Remove special chars
                words = [w for w in words.split() if len(w) > 3]  # Split and filter short words
                
                for word in words:
                    if word not in terms:
                        terms[word] = 0
                    terms[word] += source_counts[filename]['count']
            
            # Get top keywords
            top_keywords = []
            for text, value in sorted(terms.items(), key=lambda x: x[1], reverse=True)[:10]:
                top_keywords.append({'text': text, 'value': value})
            
            return jsonify({
                'totalResults': len(sources),
                'topSources': top_sources,
                'relevanceDistribution': relevance_distribution,
                'dateDistribution': date_distribution,
                'topKeywords': top_keywords,
                'query': query
            })
            
        except Exception as e:
            print(f"Error analyzing sources: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': f'Error analyzing sources: {str(e)}'}), 500
    
    return bp
