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
FAISS Index Service

Manages loading, caching, and retrieval from FAISS vector stores for
different document collections.
"""

import traceback
from typing import Dict, Optional, List
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from config import get_all_collections, EMBEDDING_MODEL, DEFAULT_COLLECTION, TOP_K_RESULTS


class FAISSService:
    """Service for managing FAISS vector stores"""
    
    def __init__(self):
        """Initialize the FAISS service with embeddings model"""
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Cache for loaded vector stores
        self.vector_stores: Dict[str, FAISS] = {}
        
        # Get available indices from config
        self.available_indices = self._build_available_indices()
        
    def _build_available_indices(self) -> Dict[str, Dict[str, str]]:
        """Build available indices dictionary from config"""
        collections = get_all_collections()
        indices = {}
        
        for key, config in collections.items():
            indices[key] = {
                "name": config["name"],
                "path": config["faiss_index"]
            }
        
        return indices
    
    def get_available_indices(self) -> Dict[str, Dict[str, str]]:
        """Get dictionary of available FAISS indices"""
        return self.available_indices
    
    def load_default_index(self, default_key: str = DEFAULT_COLLECTION) -> Optional[FAISS]:
        """
        Load the default index on startup.
        
        Args:
            default_key: Key of the default index to load
            
        Returns:
            The loaded FAISS vector store or None if failed
        """
        try:
            return self.load_index(default_key)
        except Exception as e:
            print(f"Warning: Failed to load default index '{default_key}': {str(e)}")
            return None
    
    def load_index(self, index_key: str) -> FAISS:
        """
        Load a FAISS index by key. Uses caching to avoid reloading.
        
        Args:
            index_key: Key of the index to load (e.g., 'misc', 'phys')
            
        Returns:
            The loaded FAISS vector store
            
        Raises:
            ValueError: If index_key is not valid
            Exception: If loading fails
        """
        # Validate index key
        if index_key not in self.available_indices:
            raise ValueError(
                f"Invalid index key: {index_key}. "
                f"Available: {list(self.available_indices.keys())}"
            )
        
        # Return cached version if already loaded
        if index_key in self.vector_stores:
            print(f"Using cached index: {index_key}")
            return self.vector_stores[index_key]
        
        # Load the index
        index_path = self.available_indices[index_key]["path"]
        print(f"Loading FAISS index from: {index_path}")
        
        try:
            vector_store = FAISS.load_local(
                index_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # Cache the loaded index
            self.vector_stores[index_key] = vector_store
            print(f"Successfully loaded and cached index: {index_key}")
            
            return vector_store
            
        except Exception as e:
            print(f"Error loading index {index_key}: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def get_cached_index(self, index_key: str) -> Optional[FAISS]:
        """
        Get a cached index without loading if not present.
        
        Args:
            index_key: Key of the index to retrieve
            
        Returns:
            The cached FAISS vector store or None if not cached
        """
        return self.vector_stores.get(index_key)
    
    def search(
        self, 
        index_key: str, 
        query: str, 
        k: int = TOP_K_RESULTS
    ) -> List[tuple]:
        """
        Search a FAISS index for similar documents.
        
        Args:
            index_key: Key of the index to search
            query: Search query text
            k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
            
        Raises:
            ValueError: If index_key is not valid
            Exception: If search fails
        """
        # Load index if not cached
        vector_store = self.load_index(index_key)
        
        # Perform similarity search with scores
        results = vector_store.similarity_search_with_score(query, k=k)
        
        return results
    
    def clear_cache(self, index_key: Optional[str] = None) -> None:
        """
        Clear cached vector stores.
        
        Args:
            index_key: Specific index to clear, or None to clear all
        """
        if index_key:
            if index_key in self.vector_stores:
                del self.vector_stores[index_key]
                print(f"Cleared cache for index: {index_key}")
        else:
            self.vector_stores.clear()
            print("Cleared all cached indices")
    
    def is_loaded(self, index_key: str) -> bool:
        """
        Check if an index is currently loaded in cache.
        
        Args:
            index_key: Key of the index to check
            
        Returns:
            True if loaded, False otherwise
        """
        return index_key in self.vector_stores
    
    def get_loaded_indices(self) -> List[str]:
        """
        Get list of currently loaded index keys.
        
        Returns:
            List of loaded index keys
        """
        return list(self.vector_stores.keys())
