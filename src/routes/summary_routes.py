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
Summary Routes Module

Handles document summary retrieval and chat history management endpoints.
"""

from flask import Blueprint, request, jsonify
import json
import threading
from datetime import datetime
import traceback
import requests
from config import get_all_collections, DEFAULT_COLLECTION, LM_STUDIO_MODELS_URL

# Track generation job status
_generation_status = {}


def create_summary_blueprint(chat_service):
    """
    Create and configure the summary routes blueprint.
    
    Args:
        chat_service: ChatService instance for managing chat history
        
    Returns:
        Flask Blueprint configured with summary routes
    """
    bp = Blueprint('summary', __name__)
    
    @bp.route('/get_summaries', methods=['GET'])
    @bp.route('/get_summarised_files', methods=['GET'])  # Legacy endpoint name
    def get_summaries():
        """API endpoint to retrieve document summaries from the summarised_files.json file"""
        try:
            # Get the optional docs_type parameter from query string
            # Try both 'docs_type' and 'knowledge_base' for compatibility
            docs_type = request.args.get('docs_type') or request.args.get('knowledge_base') or DEFAULT_COLLECTION
            print(f"[DEBUG] get_summaries called with docs_type: {docs_type}")
            print(f"[DEBUG] All query params: {dict(request.args)}")
            
            # Validate that docs_type exists in collections
            available_collections = get_all_collections()
            print(f"[DEBUG] Available collections: {list(available_collections.keys())}")
            
            if docs_type not in available_collections:
                error_msg = f'Invalid knowledge base: {docs_type}'
                print(f"[ERROR] {error_msg}")
                return jsonify({
                    'error': error_msg,
                    'available_collections': list(available_collections.keys())
                }), 400
            
            # Get the summary file path for this collection
            collection_config = available_collections[docs_type]
            summary_file_path = collection_config['summary_file']
            
            print(f"[DEBUG] Loading summaries from: {summary_file_path}")
            
            try:
                with open(summary_file_path, 'r') as f:
                    summaries = json.load(f)
                print(f"[SUCCESS] Loaded {len(summaries)} summaries for {docs_type}")
                return jsonify(summaries)
            except FileNotFoundError:
                error_msg = f'Summary file not found for {docs_type}: {summary_file_path}'
                print(f"[ERROR] {error_msg}")
                return jsonify({'error': error_msg}), 404
            except json.JSONDecodeError as e:
                error_msg = f'Invalid JSON in summary file for {docs_type}: {str(e)}'
                print(f"[ERROR] {error_msg}")
                return jsonify({'error': error_msg}), 500
                
        except Exception as e:
            error_msg = f'Error loading summaries: {str(e)}'
            print(f"[ERROR] {error_msg}")
            import traceback
            print(traceback.format_exc())
            return jsonify({'error': error_msg}), 500
    
    @bp.route('/get_chat_history', methods=['GET'])
    @bp.route('/get_chats', methods=['GET'])  # Legacy endpoint name
    def get_chat_history():
        """API endpoint to retrieve chat history"""
        try:
            # Get all chats from service (returns {"chats": [...]})
            data = chat_service.get_all_chats()
            chats = data.get('chats', [])
            
            # Sort chats by timestamp (most recent first)
            sorted_chats = sorted(
                chats,
                key=lambda x: x.get('timestamp', '') if isinstance(x, dict) else '',
                reverse=True
            )
            
            # Return as {"chats": [...]} for consistency
            return jsonify({'chats': sorted_chats})
            
        except Exception as e:
            print(f"Error loading chat history: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Error loading chat history: {str(e)}'}), 500
    
    @bp.route('/save_chat', methods=['POST'])
    def save_chat():
        """API endpoint to save a chat session"""
        try:
            # Log the incoming request
            print(f"\n{'='*60}")
            print("SAVE CHAT REQUEST RECEIVED")
            print(f"Content-Type: {request.content_type}")
            print(f"{'='*60}")
            
            if not request.is_json:
                print("ERROR: Request is not JSON")
                return jsonify({'error': 'Request must be JSON'}), 400
            
            chat_data = request.get_json()
            
            if not chat_data:
                print("ERROR: No JSON data received")
                return jsonify({'error': 'No data received'}), 400
            
            print(f"Received chat data: {list(chat_data.keys())}")
            
            # Auto-generate ID if not provided
            if 'id' not in chat_data:
                chat_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                chat_data['id'] = chat_id
                print(f"Auto-generated chat ID: {chat_id}")
            
            # Add timestamp if not present
            if 'timestamp' not in chat_data:
                chat_data['timestamp'] = datetime.now().isoformat()
            
            # Save the chat
            print(f"Attempting to save chat with ID: {chat_data['id']}")
            result = chat_service.save_chat(chat_data)
            
            if result.get('success'):
                print(f"Successfully saved chat: {chat_data['id']}")
                return jsonify({'success': True, 'id': chat_data['id']})
            else:
                print(f"Failed to save chat: {chat_data['id']}")
                return jsonify({'error': 'Failed to save chat'}), 500
                
        except Exception as e:
            error_msg = f"Error saving chat: {str(e)}"
            print(f"\n{error_msg}")
            print(traceback.format_exc())
            return jsonify({'error': error_msg}), 500
    
    @bp.route('/delete_chat/<chat_id>', methods=['DELETE'])
    def delete_chat(chat_id):
        """API endpoint to delete a chat session"""
        try:
            success = chat_service.delete_chat(chat_id)

            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Chat not found'}), 404

        except Exception as e:
            print(f"Error deleting chat: {str(e)}")
            return jsonify({'error': f'Error deleting chat: {str(e)}'}), 500

    @bp.route('/api/generate_summaries', methods=['POST'])
    def generate_summaries():
        """API endpoint to trigger book summary generation"""
        try:
            data = request.get_json() or {}
            collection = data.get('collection', DEFAULT_COLLECTION)

            print(f"[INFO] Generate summaries requested for collection: {collection}")

            # Validate collection
            available_collections = get_all_collections()
            if collection not in available_collections:
                return jsonify({
                    'error': f'Invalid collection: {collection}',
                    'available_collections': list(available_collections.keys())
                }), 400

            # Check if LM Studio is available
            try:
                health_check = requests.get(
                    LM_STUDIO_MODELS_URL,
                    timeout=5
                )
                if health_check.status_code != 200:
                    return jsonify({
                        'error': 'LM Studio is not responding. Please ensure it is running with DeepSeek loaded.'
                    }), 503
            except requests.exceptions.ConnectionError:
                return jsonify({
                    'error': f'Cannot connect to LM Studio at {LM_STUDIO_MODELS_URL}. Please ensure it is running.'
                }), 503
            except requests.exceptions.Timeout:
                return jsonify({
                    'error': 'LM Studio connection timed out. Please check if it is responding.'
                }), 503

            # Import and run the batch processor in a background thread
            from ..summary import run_batch_processor

            # Initialize status tracking
            _generation_status[collection] = {
                'status': 'running',
                'started_at': datetime.now().isoformat(),
                'completed_at': None,
                'result': None
            }

            def run_in_background():
                try:
                    print(f"[INFO] Starting background summary generation for {collection}")
                    result = run_batch_processor(collections=[collection])
                    _generation_status[collection]['status'] = 'completed'
                    _generation_status[collection]['completed_at'] = datetime.now().isoformat()
                    _generation_status[collection]['result'] = 'success' if result == 0 else 'failed'
                    print(f"[INFO] Background summary generation completed for {collection}")
                except Exception as e:
                    _generation_status[collection]['status'] = 'error'
                    _generation_status[collection]['completed_at'] = datetime.now().isoformat()
                    _generation_status[collection]['result'] = str(e)
                    print(f"[ERROR] Background summary generation failed: {str(e)}")

            thread = threading.Thread(target=run_in_background, daemon=True)
            thread.start()

            return jsonify({
                'status': 'started',
                'message': f'Summary generation started for {collection}. This process runs in the background.',
                'collection': collection
            })

        except Exception as e:
            error_msg = f"Error starting summary generation: {str(e)}"
            print(f"[ERROR] {error_msg}")
            print(traceback.format_exc())
            return jsonify({'error': error_msg}), 500

    @bp.route('/api/generate_summaries/status/<collection>', methods=['GET'])
    def get_generation_status(collection):
        """API endpoint to check summary generation status"""
        if collection in _generation_status:
            return jsonify(_generation_status[collection])
        else:
            return jsonify({'status': 'not_started'})

    return bp
