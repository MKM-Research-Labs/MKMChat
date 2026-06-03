# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
"""
Summary FAISS Reader

Handles FAISS index loading, chunk extraction, and vector search for summaries.
"""

import os
import pickle
import shutil
from typing import Optional, Tuple, List, Any, Dict

import faiss
import numpy as np

from .models import DocumentChunk
from config import TOP_K_RESULTS


def load_faiss_index(paths: Dict[str, str]) -> Tuple[Optional[Any], Optional[Any]]:
    """
    Load FAISS index and metadata.

    Args:
        paths: Dictionary with 'faiss_index' and 'faiss_pkl' paths

    Returns:
        Tuple of (index, metadata) or (None, None) if failed
    """
    print(f"  Loading FAISS index from {paths['faiss_index']}...")
    try:
        if not os.path.exists(paths['faiss_index']):
            print(f"  FAISS index file not found: {paths['faiss_index']}")
            return None, None

        index = faiss.read_index(paths['faiss_index'])
        with open(paths['faiss_pkl'], 'rb') as f:
            metadata = pickle.load(f)

        print(f"  Loaded FAISS index with {index.ntotal} vectors")

        # Handle LangChain tuple structure
        if isinstance(metadata, tuple) and len(metadata) >= 2:
            docstore, index_to_docstore_id = metadata
            print(f"  Using LangChain structure with {len(index_to_docstore_id)} mappings")
            return index, (docstore, index_to_docstore_id)

        return index, metadata
    except Exception as e:
        print(f"  Error loading FAISS: {e}")
        return None, None


def search_book_content(
    book_name: str,
    embedding_model: Any,
    index: Any,
    metadata: Any,
    top_k: int = TOP_K_RESULTS
) -> str:
    """
    Search for relevant content about a specific book.

    Args:
        book_name: Name of the book to search for
        embedding_model: SentenceTransformer model instance
        index: FAISS index
        metadata: Index metadata (docstore, index_to_docstore_id)
        top_k: Number of results to return

    Returns:
        Combined text of relevant chunks or empty string
    """
    try:
        # Handle LangChain structure
        if isinstance(metadata, tuple) and len(metadata) == 2:
            docstore, index_to_docstore_id = metadata

            query = f"provide a summary of the book {book_name}"

            query_embedding = embedding_model.encode([query])
            query_embedding = np.array(query_embedding, dtype=np.float32)

            distances, indices = index.search(query_embedding, top_k)

            relevant_chunks = []

            for i, idx in enumerate(indices[0]):
                try:
                    if idx in index_to_docstore_id:
                        doc_id = index_to_docstore_id[idx]
                        document = docstore.search(doc_id)
                        if document and hasattr(document, 'page_content'):
                            content = document.page_content
                            relevant_chunks.append(content)

                except Exception:
                    continue

            if relevant_chunks:
                return "\n\n".join(relevant_chunks[:3])
            else:
                return ""

        else:
            return ""

    except Exception:
        return ""


def create_safe_faiss_copy(
    faiss_path: str,
    temp_dir: str,
    embeddings: Any
) -> Tuple[Optional[str], Optional[Any]]:
    """
    Create a temporary read-only copy of the FAISS index for safe access.

    Args:
        faiss_path: Path to the original FAISS index
        temp_dir: Path for temporary copy
        embeddings: Embeddings model for loading

    Returns:
        Tuple of (temp_path, vector_store) or (None, None) if failed
    """
    from langchain_community.vectorstores import FAISS

    if not os.path.exists(faiss_path):
        print(f"FAISS index not found at {faiss_path}")
        return None, None

    try:
        # Remove existing temp directory if it exists
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        # Copy the FAISS index files
        print(f"Creating safe copy of FAISS index...")
        shutil.copytree(faiss_path, temp_dir)

        # Load the copied index
        print(f"Loading FAISS copy...")
        vector_store = FAISS.load_local(
            temp_dir,
            embeddings,
            allow_dangerous_deserialization=True
        )

        print(f"Successfully loaded FAISS copy with {vector_store.index.ntotal} vectors")
        return temp_dir, vector_store

    except Exception as e:
        print(f"Error creating FAISS copy: {str(e)}")
        return None, None


def cleanup_faiss_copy(temp_path: Optional[str]) -> None:
    """
    Clean up temporary FAISS copy.

    Args:
        temp_path: Path to temporary directory to remove
    """
    if temp_path and os.path.exists(temp_path):
        try:
            shutil.rmtree(temp_path)
            print("Cleaned up temporary FAISS copy")
        except Exception as e:
            print(f"Warning: Could not clean up temporary FAISS copy: {str(e)}")


def get_document_chunks_from_faiss(
    vector_store: Any,
    document_name: str
) -> List[DocumentChunk]:
    """
    Extract all chunks belonging to a specific document from FAISS index.

    Args:
        vector_store: The FAISS vector store
        document_name: Name of the document to extract chunks for

    Returns:
        List of DocumentChunk objects sorted by page number
    """
    try:
        document_chunks = []

        # Get all document IDs from the vector store
        all_doc_ids = list(vector_store.docstore._dict.keys())

        # Filter chunks by document source
        for doc_id in all_doc_ids:
            try:
                doc = vector_store.docstore._dict[doc_id]
                doc_source = doc.metadata.get('source', '')

                # Match document by various source formats
                if (document_name in doc_source or
                    os.path.basename(doc_source) == document_name or
                    os.path.splitext(os.path.basename(doc_source))[0] ==
                    os.path.splitext(document_name)[0]):

                    document_chunks.append(DocumentChunk(
                        content=doc.page_content,
                        metadata=doc.metadata,
                        doc_id=doc_id,
                        page=doc.metadata.get('page', 0)
                    ))

            except Exception:
                # Skip problematic chunks
                continue

        if document_chunks:
            # Sort by page number for better context
            document_chunks.sort(key=lambda x: x.page)
            print(f"Found {len(document_chunks)} chunks for {document_name}")
            return document_chunks
        else:
            print(f"No chunks found for {document_name} in FAISS index")
            return []

    except Exception as e:
        print(f"Error extracting chunks for {document_name}: {str(e)}")
        return []
