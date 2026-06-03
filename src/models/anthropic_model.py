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
Anthropic Model Handler

Handles communication with Anthropic's Claude API.
Includes post-processing to replace specific terms.
"""

import requests
from typing import Optional
from src.utils.rep import replace_terms
from config import (
    ANTHROPIC_API_URL, ANTHROPIC_MAX_TOKENS, ANTHROPIC_API_VERSION, MODEL_ID,
    ANTHROPIC_MODEL_IDS
)


class AnthropicHandler:
    """Handler for Anthropic's Claude models"""

    # Model ID mapping (centralised in config.py)
    MODEL_IDS = ANTHROPIC_MODEL_IDS

    def __init__(self, api_key: str, api_url: str = ANTHROPIC_API_URL):
        """
        Initialize the Anthropic handler.

        Args:
            api_key: Anthropic API key
            api_url: Anthropic API endpoint URL
        """
        self.api_key = api_key
        self.api_url = api_url
        self.max_tokens = ANTHROPIC_MAX_TOKENS
        
    def query(self, query: str, context: str, model: str = "claude-sonnet-4.5") -> str:
        """
        Query Anthropic model with context.
        
        Args:
            query: User's question
            context: Retrieved context from FAISS
            model: Model identifier (claude-sonnet-4.5 or claude-3-opus)
            
        Returns:
            str: Model's response with term replacements or error message
        """
        try:
            # Get the actual model ID
            model_id = self._get_model_id(model)
            
            payload = self._build_payload(query, context, model_id)
            
            response = requests.post(
                self.api_url,
                headers=self._build_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                response_text = response.json()["content"][0]["text"]
                # Apply term replacements
                return replace_terms(response_text)
            else:
                return f"Error from Anthropic API: {response.text}"
                
        except Exception as e:
            return f"Error with Anthropic model: {str(e)}"
    
    def _get_model_id(self, model: str) -> str:
        """Get the actual model ID from the friendly name."""
        return self.MODEL_IDS.get(model, self.MODEL_IDS["claude-sonnet-4.5"])
    
    def _build_headers(self) -> dict:
        """Build API request headers."""
        return {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "Content-Type": "application/json"
        }
    
    def _build_payload(self, query: str, context: str, model_id: str) -> dict:
        """Build the API payload."""
        return {
            "model": model_id,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user", 
                    "content": f"Context: {context}\n\nQuestion: {query}"
                }
            ]
        }
