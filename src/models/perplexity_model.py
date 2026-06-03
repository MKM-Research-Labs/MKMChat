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
Perplexity Model Handler

Handles communication with Perplexity AI's API for models like Sonar.
Includes post-processing to replace specific terms.
"""

import requests
from typing import Optional
from src.utils.rep import replace_terms


class PerplexityHandler:
    """Handler for Perplexity AI models"""
    
    def __init__(self, api_key: str, api_url: str = "https://api.perplexity.ai/chat/completions"):
        """
        Initialize the Perplexity handler.
        
        Args:
            api_key: Perplexity API key
            api_url: Perplexity API endpoint URL
        """
        self.api_key = api_key
        self.api_url = api_url
        
    def query(self, query: str, context: str, model: str = "sonar") -> str:
        """
        Query Perplexity model with context.
        
        Args:
            query: User's question
            context: Retrieved context from FAISS
            model: Perplexity model name (sonar, sonar-pro, etc.)
            
        Returns:
            str: Model's response with term replacements or error message
        """
        try:
            payload = self._build_payload(query, context, model)
            
            response = requests.post(
                self.api_url,
                headers=self._build_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                response_text = response.json()["choices"][0]["message"]["content"]
                # Apply term replacements
                return replace_terms(response_text)
            else:
                return f"Error from Perplexity API: {response.text}"
                
        except Exception as e:
            return f"Error with Perplexity model: {str(e)}"
    
    def _build_headers(self) -> dict:
        """Build API request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _build_payload(self, query: str, context: str, model: str) -> dict:
        """Build the API payload."""
        return {
            "model": model,
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that answers questions based on the provided context."
                },
                {
                    "role": "user", 
                    "content": f"Context: {context}\n\nQuestion: {query}"
                }
            ]
        }
