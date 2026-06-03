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
Local Model Handler - LM Studio Integration

Handles communication with locally-hosted LLMs through LM Studio.
Supports OpenAI-compatible API format for models like Mistral, Llama, etc.
"""

import requests
import traceback
from typing import Optional

from config import (
    LM_STUDIO_API_URL, LOCAL_MODEL_MAX_CONTEXT, LOCAL_MODEL_TIMEOUT,
    LOCAL_MODEL_TEMPERATURE, LOCAL_MODEL_MAX_TOKENS
)


class LocalModelHandler:
    """Handler for local LLM models via LM Studio"""

    def __init__(self, api_url: str = LM_STUDIO_API_URL):
        """
        Initialize the local model handler.

        Args:
            api_url: LM Studio API endpoint URL
        """
        self.api_url = api_url
        self.max_context_length = LOCAL_MODEL_MAX_CONTEXT
        self.timeout = LOCAL_MODEL_TIMEOUT
        
    def query(self, query: str, context: str, model: str = "default") -> str:
        """
        Query the local model with context.
        
        Args:
            query: User's question
            context: Retrieved context from FAISS
            model: Model identifier (not used for LM Studio, but kept for compatibility)
            
        Returns:
            str: Model's response or error message
        """
        try:
            # Truncate context if too large
            truncated_context = self._truncate_context(context)
            
            # Build payload
            payload = self._build_payload(query, truncated_context)
            
            # Log request (truncated for readability)
            self._log_request(payload)
            
            # Make API call
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout
            )
            
            # Handle response
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            return "Error: Request to local model timed out. The context may be too large."
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to LM Studio. Please ensure it's running on port 1234."
        except Exception as e:
            print(f"Error with local model: {str(e)}")
            print(traceback.format_exc())
            return f"Error with local model: {str(e)}"
    
    def _truncate_context(self, context: str) -> str:
        """Truncate context if it exceeds max length."""
        if len(context) > self.max_context_length:
            return context[:self.max_context_length] + "... [context truncated for length]"
        return context
    
    def _build_payload(self, query: str, context: str) -> dict:
        """Build the API payload."""
        return {
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that answers questions based on the provided context."
                },
                {
                    "role": "user", 
                    "content": f"Context: {context}\n\nQuestion: {query}"
                }
            ],
            "temperature": LOCAL_MODEL_TEMPERATURE,
            "max_tokens": LOCAL_MODEL_MAX_TOKENS
        }
    
    def _log_request(self, payload: dict) -> None:
        """Log request for debugging (truncated if large)."""
        if len(str(payload)) > 500:
            print(f"Sending request to LM Studio (truncated for log)...")
        else:
            print(f"Sending request to LM Studio: {payload}")
    
    def _handle_response(self, response: requests.Response) -> str:
        """Handle API response and extract text."""
        if response.status_code == 200:
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"]
        else:
            # Build error message
            error_msg = f"LM Studio error: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text}"
            print(error_msg)
            return f"Error from local model: {error_msg}"
