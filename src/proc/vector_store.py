# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""
Vector store management for document embeddings.
Handles FAISS operations: create, merge, save, verify, and fallback embeddings.
"""

import os
from tqdm import tqdm
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from config import CONFIG, EMBEDDING_BATCH_SIZE
from ..utils.text_utils import sanitize_text


class VectorStoreManager:
    """Manages FAISS vector store operations."""

    def __init__(self, faiss_path, embeddings, show_progress=True):
        """
        Initialize the vector store manager.

        Args:
            faiss_path (str): Path to FAISS index directory
            embeddings: HuggingFace embeddings model
            show_progress (bool): Whether to show progress bars
        """
        self.faiss_path = faiss_path
        self.embeddings = embeddings
        self.show_progress = show_progress

    def prepare_texts(self, chunks):
        """
        Prepare and validate texts for embedding.

        Args:
            chunks (list): List of Document chunks

        Returns:
            tuple: (texts, metadatas) lists
        """
        texts = []
        metadatas = []

        with tqdm(total=len(chunks), desc="Preparing text data",
                  disable=not self.show_progress) as pbar:
            for chunk in chunks:
                clean_text = sanitize_text(chunk.page_content)
                if clean_text and len(clean_text.strip()) > 10:
                    texts.append(clean_text)
                    metadatas.append(chunk.metadata)
                pbar.update(1)

        return texts, metadatas

    def load_existing(self):
        """
        Load existing FAISS index.

        Returns:
            FAISS or None: Loaded vector store or None if not found
        """
        if not os.path.exists(self.faiss_path):
            return None

        try:
            return FAISS.load_local(
                self.faiss_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        except Exception as e:
            print(f"Error loading existing index: {str(e)}")
            return None

    def add_to_existing(self, existing_store, texts, metadatas):
        """
        Add new texts to existing vector store.

        Args:
            existing_store: Existing FAISS store
            texts (list): Texts to add
            metadatas (list): Metadata for each text

        Returns:
            FAISS: Updated vector store
        """
        batch_size = EMBEDDING_BATCH_SIZE
        with tqdm(total=len(texts), desc="Adding to vector store",
                  disable=not self.show_progress) as pbar:
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]

                try:
                    existing_store.add_texts(
                        texts=batch_texts,
                        metadatas=batch_metadatas
                    )
                except Exception as e:
                    print(f"Batch failed, trying one by one: {str(e)}")
                    for j in range(len(batch_texts)):
                        try:
                            existing_store.add_texts(
                                texts=[batch_texts[j]],
                                metadatas=[batch_metadatas[j]]
                            )
                        except Exception as e2:
                            print(f"Skipping problematic text: {str(e2)[:100]}...")

                pbar.update(len(batch_texts))

        return existing_store

    def create_new(self, texts, metadatas):
        """
        Create a new vector store from texts.

        Args:
            texts (list): Texts to embed
            metadatas (list): Metadata for each text

        Returns:
            FAISS or None: New vector store or None on failure
        """
        try:
            print(f"Creating vector store from {len(texts)} documents...")
            return FAISS.from_texts(texts, self.embeddings, metadatas)
        except Exception as e:
            print(f"Error creating index: {str(e)}")
            return None

    def save(self, vector_store):
        """
        Save vector store to disk.

        Args:
            vector_store: FAISS vector store to save

        Returns:
            bool: True if successful
        """
        try:
            with tqdm(total=1, desc="Saving index",
                      disable=not self.show_progress) as pbar:
                vector_store.save_local(self.faiss_path)
                pbar.update(1)
            return True
        except Exception as e:
            print(f"Error saving index: {str(e)}")
            return False

    def verify(self):
        """
        Verify the saved index works correctly.

        Returns:
            bool: True if verification passed
        """
        try:
            print("\nVerifying index...")
            with tqdm(total=1, desc="Verification",
                      disable=not self.show_progress) as pbar:
                store = FAISS.load_local(
                    self.faiss_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                if store:
                    _ = store.similarity_search("test", k=1)
                    pbar.update(1)
                    print("Index verification successful")
                    return True
                else:
                    print("Index verification skipped: could not load index")
                    return False
        except Exception as e:
            print(f"Index verification failed: {str(e)}")
            return False

    def try_alternative_embeddings(self, texts, metadatas):
        """
        Try creating index with alternative embedding models.

        Args:
            texts (list): Texts to embed
            metadatas (list): Metadata for each text

        Returns:
            tuple: (success, embeddings) - bool and embeddings model used
        """
        try:
            print("Attempting with alternative embedding model...")
            alt_embeddings = HuggingFaceEmbeddings(
                model_name=CONFIG['fallback_embedding_model'],
                encode_kwargs={'normalize_embeddings': True}
            )
            vector_store = FAISS.from_texts(texts, alt_embeddings, metadatas)
            vector_store.save_local(self.faiss_path)
            print("Successfully created index with alternative embedding model")
            return True, alt_embeddings
        except Exception as e:
            print(f"Alternative model failed: {str(e)}")

        try:
            print("Trying last resort embedding model...")
            last_resort = HuggingFaceEmbeddings(
                model_name=CONFIG['last_resort_model'],
                encode_kwargs={'normalize_embeddings': True}
            )
            vector_store = FAISS.from_texts(texts, last_resort, metadatas)
            vector_store.save_local(self.faiss_path)
            print("Successfully created index with last resort embedding model")
            return True, last_resort
        except Exception as e:
            print(f"All embedding attempts failed: {str(e)}")
            return False, None

    def setup_alternative_embeddings(self):
        """
        Set up alternative embeddings when default model fails.

        Returns:
            tuple: (success, embeddings) - bool and new embeddings model
        """
        try:
            print("Setting up alternative embedding model...")
            embeddings = HuggingFaceEmbeddings(
                model_name=CONFIG['fallback_embedding_model'],
                encode_kwargs={'normalize_embeddings': True}
            )
            print("Successfully set up alternative embeddings")
            return True, embeddings
        except Exception as e:
            print(f"Error setting up alternative embeddings: {str(e)}")

        try:
            print("Trying MPNet base model as fallback...")
            embeddings = HuggingFaceEmbeddings(
                model_name=CONFIG['last_resort_model'],
                encode_kwargs={'normalize_embeddings': True}
            )
            print("Successfully set up MPNet embeddings")
            return True, embeddings
        except Exception as e:
            print(f"Error setting up fallback embeddings: {str(e)}")
            return False, None
