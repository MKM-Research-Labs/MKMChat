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
Chat Routes Module

Handles query processing and response generation endpoints.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import traceback

from config import MODEL_ID, TOP_K_RESULTS


def create_chat_blueprint(app_instance):
    """
    Create and configure the chat routes blueprint.
    
    Args:
        app_instance: DocumentQAApp instance for accessing services and handlers
        
    Returns:
        Flask Blueprint configured with chat routes
    """
    bp = Blueprint('chat', __name__)
    
    @bp.route('/query', methods=['POST'])
    def query():
        """Main query endpoint for processing user questions"""
        try:
            # Validate request
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
            
            data = request.get_json()
            user_query = data.get('query', '').strip()
            model = data.get('model', MODEL_ID)
            
            if not user_query:
                return jsonify({'error': 'Query cannot be empty'}), 400
            
            print(f"\n{'='*60}")
            print(f"Processing query: {user_query}")
            print(f"Model: {model}")
            print(f"Active index: {app_instance.ACTIVE_INDEX_KEY}")
            print(f"{'='*60}\n")
            
            # Get the active vector store
            if app_instance.ACTIVE_INDEX_KEY not in app_instance.vector_stores:
                return jsonify({
                    'error': f'Index not loaded: {app_instance.ACTIVE_INDEX_KEY}',
                    'details': 'Please switch to a valid knowledge base'
                }), 500
            
            vector_store = app_instance.vector_stores[app_instance.ACTIVE_INDEX_KEY]
            
            # Perform similarity search
            print(f"Searching for relevant documents...")
            docs = vector_store.similarity_search(user_query, k=TOP_K_RESULTS)
            print(f"Found {len(docs)} relevant documents")
            
            # Build context from retrieved documents
            context_parts = []
            sources = []
            
            for i, doc in enumerate(docs, 1):
                content = doc.page_content
                metadata = doc.metadata
                
                source_info = f"Source {i}: {metadata.get('source', 'Unknown')}"
                if 'page' in metadata:
                    source_info += f", Page {metadata.get('page')}"
                
                context_parts.append(f"{source_info}\n{content}")
                
                # Store source information for response
                sources.append({
                    'file': metadata.get('source', 'Unknown'),
                    'page': metadata.get('page', 'N/A'),
                    'chunk': i
                })
            
            context = "\n\n---\n\n".join(context_parts)
            
            print(f"Context length: {len(context)} characters")
            print(f"Calling model: {model}")
            
            # Route to appropriate model handler
            if model in ['sonar', 'sonar-pro', 'sonar-reasoning', 'sonar-reasoning-pro']:
                response_text = app_instance._handle_perplexity_model(user_query, context, model)
            elif model in ['claude-sonnet-4.5', 'claude-3-opus']:
                response_text = app_instance._handle_anthropic_model(user_query, context, model)
            else:
                response_text = app_instance._handle_local_model(user_query, context, model)
            
            if not response_text:
                return jsonify({
                    'error': 'Failed to generate response',
                    'details': 'The model did not return a valid response'
                }), 500
            
            print(f"Response generated: {len(response_text)} characters")
            
            # Format response
            response = {
                'response': response_text,
                'sources': sources,
                'model': model,
                'knowledge_base': app_instance.ACTIVE_INDEX_KEY,
                'knowledge_base_name': app_instance.AVAILABLE_INDICES[app_instance.ACTIVE_INDEX_KEY]['name'],
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(response)
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            print(f"\n{error_msg}")
            print(traceback.format_exc())
            
            return jsonify({
                'error': error_msg,
                'details': traceback.format_exc()
            }), 500
    
    return bp
