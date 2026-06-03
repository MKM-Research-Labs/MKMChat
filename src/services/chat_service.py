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
Chat Storage Service

Manages persistent storage of chat conversations in JSON format.
Handles loading, saving, and updating chat history.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class ChatService:
    """Service for managing chat history storage"""
    
    def __init__(self, chats_file: str):
        """
        Initialize the chat service.
        
        Args:
            chats_file: Path to the JSON file for storing chats
        """
        self.chats_file = Path(chats_file)
        self._init_storage()
    
    def _init_storage(self) -> None:
        """Initialize chat storage file if it doesn't exist"""
        # Ensure directory exists
        self.chats_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file with empty structure if it doesn't exist
        if not self.chats_file.exists():
            self._write_chats({"chats": []})
            print(f"Initialized chat storage at: {self.chats_file}")
    
    def _read_chats(self) -> Dict[str, List[Dict]]:
        """
        Read chats from storage file.
        
        Returns:
            Dictionary with 'chats' key containing list of chats
        """
        try:
            with open(self.chats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Validate structure
                if not isinstance(data, dict) or 'chats' not in data:
                    print("Warning: Invalid chat file structure, resetting")
                    return {"chats": []}
                
                return data
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not read chats file: {e}")
            return {"chats": []}
    
    def _write_chats(self, data: Dict[str, List[Dict]]) -> None:
        """
        Write chats to storage file.
        
        Args:
            data: Dictionary with 'chats' key
            
        Raises:
            Exception: If writing fails
        """
        with open(self.chats_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_all_chats(self) -> Dict[str, List[Dict]]:
        """
        Get all chats from storage.
        
        Returns:
            Dictionary containing all chats
        """
        return self._read_chats()
    
    def save_chat(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save or update a chat conversation.
        
        Args:
            chat_data: Chat data to save (must include messages, title, etc.)
            
        Returns:
            Dictionary with success status and chat ID
            
        Raises:
            ValueError: If chat_data is invalid
            Exception: If saving fails
        """
        if not chat_data:
            raise ValueError("Chat data cannot be empty")
        
        # Ensure chat has an ID
        if 'id' not in chat_data:
            chat_data['id'] = datetime.now().strftime('%Y%m%d%H%M%S%f')
        
        # Load existing chats
        all_chats = self._read_chats()
        
        # Find and update existing chat, or append new one
        chat_found = False
        for i, existing_chat in enumerate(all_chats['chats']):
            if existing_chat.get('id') == chat_data['id']:
                all_chats['chats'][i] = chat_data
                chat_found = True
                break
        
        if not chat_found:
            all_chats['chats'].append(chat_data)
        
        # Save back to file
        self._write_chats(all_chats)
        
        action = "updated" if chat_found else "created"
        print(f"Chat {action}: {chat_data['id']}")
        
        return {
            'success': True,
            'message': f'Chat {action} successfully',
            'id': chat_data['id']
        }
    
    def get_chat_by_id(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific chat by ID.
        
        Args:
            chat_id: ID of the chat to retrieve
            
        Returns:
            Chat data or None if not found
        """
        all_chats = self._read_chats()
        
        for chat in all_chats['chats']:
            if chat.get('id') == chat_id:
                return chat
        
        return None
    
    def delete_chat(self, chat_id: str) -> bool:
        """
        Delete a chat by ID.
        
        Args:
            chat_id: ID of the chat to delete
            
        Returns:
            True if deleted, False if not found
        """
        all_chats = self._read_chats()
        
        # Find and remove the chat
        original_length = len(all_chats['chats'])
        all_chats['chats'] = [
            chat for chat in all_chats['chats'] 
            if chat.get('id') != chat_id
        ]
        
        if len(all_chats['chats']) < original_length:
            self._write_chats(all_chats)
            print(f"Chat deleted: {chat_id}")
            return True
        
        return False
    
    def clear_all_chats(self) -> None:
        """Clear all chats from storage"""
        self._write_chats({"chats": []})
        print("All chats cleared")
    
    def get_chat_count(self) -> int:
        """
        Get the total number of chats.
        
        Returns:
            Number of chats in storage
        """
        all_chats = self._read_chats()
        return len(all_chats['chats'])
    
    def get_recent_chats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent chats.
        
        Args:
            limit: Maximum number of chats to return
            
        Returns:
            List of recent chats (newest first)
        """
        all_chats = self._read_chats()
        chats = all_chats['chats']
        
        # Sort by timestamp if available, otherwise by ID
        try:
            sorted_chats = sorted(
                chats,
                key=lambda x: x.get('timestamp', x.get('id', '')),
                reverse=True
            )
        except:
            sorted_chats = chats[::-1]  # Just reverse if sorting fails
        
        return sorted_chats[:limit]
