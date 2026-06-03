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
Index Routes Module

Handles knowledge base switching and configuration endpoints.
"""

from flask import Blueprint, request, jsonify


def create_index_blueprint(app_instance):
    """
    Create and configure the index routes blueprint.
    
    Args:
        app_instance: DocumentQAApp instance for accessing indices and models
        
    Returns:
        Flask Blueprint configured with index routes
    """
    bp = Blueprint('index', __name__)
    
    @bp.route('/get_available_indices', methods=['GET'])
    def get_available_indices():
        """API endpoint to get list of available FAISS indices"""
        try:
            return jsonify({
                'indices': app_instance.AVAILABLE_INDICES,
                'active': app_instance.ACTIVE_INDEX_KEY
            })
        except Exception as e:
            print(f"Error getting available indices: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @bp.route('/get_available_models', methods=['GET'])
    def get_available_models():
        """API endpoint to get list of available models"""
        try:
            return jsonify({
                'models': app_instance.AVAILABLE_MODELS
            })
        except Exception as e:
            print(f"Error getting available models: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @bp.route('/switch_index', methods=['POST'])
    def switch_index():
        """API endpoint to switch the active FAISS index"""
        try:
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
            
            data = request.get_json()
            index_key = data.get('index_key')
            
            if not index_key:
                return jsonify({'error': 'No index_key provided'}), 400
                
            if index_key not in app_instance.AVAILABLE_INDICES:
                return jsonify({
                    'error': f'Invalid index key: {index_key}',
                    'available': list(app_instance.AVAILABLE_INDICES.keys())
                }), 400
            
            # Load the index if not already loaded
            if index_key not in app_instance.vector_stores:
                app_instance._load_faiss_index(index_key)
            
            app_instance.ACTIVE_INDEX_KEY = index_key
            
            return jsonify({
                'success': True,
                'active_index': index_key,
                'name': app_instance.AVAILABLE_INDICES[index_key]['name']
            })
            
        except Exception as e:
            print(f"Error switching index: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return bp
