# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
"""
Summary LLM Client

Handles local LLM API calls and text post-processing for summaries.
"""

import re
import os
import requests
from datetime import datetime
from typing import Optional, List

from .models import DocumentChunk
from config import (
    LM_STUDIO_API_URL, LOCAL_SUMMARY_MODEL,
    SUMMARY_MAX_TOKENS, SUMMARY_TEMPERATURE, SUMMARY_TIMEOUT,
    SUMMARY_FALLBACK_TEMPERATURE, SUMMARY_FALLBACK_MAX_TOKENS,
    SUMMARY_FALLBACK_TIMEOUT, SUMMARY_MAX_CHUNKS,
    SUMMARY_CHUNK_CONTENT_LENGTH, SUMMARY_CHUNK_CONTENT_LENGTH_RETRY,
    SUMMARY_CONTEXT_TRUNCATION
)


def clean_summary_text(text: str) -> str:
    """
    Remove thinking process and other unwanted elements from LLM output.

    Args:
        text: Raw LLM output text

    Returns:
        Cleaned summary text
    """
    # Remove <think>...</think> blocks
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

    # Remove common preamble phrases
    preamble_patterns = [
        r'^.*?(?=###|\*\*|1\.|Main themes|Key concepts|Important takeaways)',
        r'^.*?(?=The book)',
        r'^.*?(?=This book)'
    ]

    for pattern in preamble_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    text = text.strip()

    return text


def call_llm_for_summary(
    book_name: str,
    context: str,
    url: str = LM_STUDIO_API_URL,
    model: str = LOCAL_SUMMARY_MODEL,
    max_tokens: int = SUMMARY_MAX_TOKENS,
    temperature: float = SUMMARY_TEMPERATURE
) -> Optional[str]:
    """
    Call the local LLM to generate a book summary.

    Args:
        book_name: Name of the book
        context: Context text from FAISS search
        url: LLM API URL
        model: Model name
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature

    Returns:
        Generated summary or None if failed
    """
    try:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that creates comprehensive "
                        "book summaries. Analyze the provided content and create "
                        "detailed, structured summaries. Do not include any "
                        "thinking process or preamble - provide only the final summary."
                    )
                },
                {
                    "role": "user",
                    "content": f"""Please provide a comprehensive summary of the book "{book_name}" based on the following content:

{context}

Please structure your summary to include:
1. Main themes and topics
2. Key concepts and ideas
3. Important takeaways
4. Target audience and relevance

Provide a detailed, well-organized summary."""
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }

        response = requests.post(url, json=payload, timeout=SUMMARY_TIMEOUT)

        if response.status_code == 200:
            result = response.json()
            raw_summary = result["choices"][0]["message"]["content"].strip()
            return clean_summary_text(raw_summary)
        else:
            return None

    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return None


def query_local_model_with_chunks(
    document_name: str,
    document_chunks: List[DocumentChunk],
    url: str = LM_STUDIO_API_URL,
    max_retries: int = 3
) -> Optional[str]:
    """
    Query local model for document summary using FAISS-extracted chunks.

    Args:
        document_name: The name of the document
        document_chunks: List of document chunks from FAISS
        url: LLM API URL
        max_retries: Number of retry attempts

    Returns:
        Generated summary or None if all attempts fail
    """
    if not document_chunks:
        return None

    max_chunks = min(SUMMARY_MAX_CHUNKS, len(document_chunks))

    for attempt in range(max_retries):
        try:
            # Reduce chunks on retry
            num_chunks = max(2, max_chunks // (attempt + 1))
            selected_chunks = document_chunks[:num_chunks]

            print(f"Attempt {attempt+1}: Using {num_chunks} chunks for local model...")

            # Build context from FAISS chunks
            context_parts = []
            content_length = SUMMARY_CHUNK_CONTENT_LENGTH if attempt == 0 else SUMMARY_CHUNK_CONTENT_LENGTH_RETRY

            for chunk in selected_chunks:
                page_info = f"Page {chunk.metadata.get('page', 'N/A')}"
                content = chunk.content[:content_length]
                context_parts.append(f"[{page_info}] {content}")

            context = "\n\n".join(context_parts)

            prompt = f"""Document: {document_name}

Content from FAISS index:
{context[:SUMMARY_CONTEXT_TRUNCATION]}

Write a comprehensive summary of this document in 2-3 paragraphs."""

            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "temperature": SUMMARY_FALLBACK_TEMPERATURE,
                "max_tokens": SUMMARY_FALLBACK_MAX_TOKENS
            }

            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=SUMMARY_FALLBACK_TIMEOUT
            )

            response.raise_for_status()
            response_data = response.json()

            if ("choices" in response_data and
                len(response_data["choices"]) > 0 and
                "message" in response_data["choices"][0]):

                print("Successfully received response from local model")
                return response_data["choices"][0]["message"].get("content", "")
            else:
                raise ValueError("Unexpected API response format")

        except Exception as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
            if attempt == max_retries - 1:
                return None

    return None


def generate_basic_summary(document_name: str) -> str:
    """
    Generate a basic placeholder summary when other methods fail.

    Args:
        document_name: The name of the document

    Returns:
        Basic placeholder summary text
    """
    base_name = os.path.splitext(document_name)[0]
    clean_name = base_name.replace('_', ' ').replace('-', ' ')

    return f"""# Summary of {clean_name}

This document appears to be about {clean_name}.

The automatic summarization using the local model was not successful due to technical limitations. This is a placeholder summary generated based on the document filename.

## Key Information:
- Document name: {document_name}
- Summary generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Method: Automated filename-based placeholder (API summarization failed)

To get a better summary of this document, you may want to:
1. Try running the summarizer again later
2. Adjust the model parameters
3. Process this document manually

## Note:
This is a fallback summary created because the API-based summarization was unsuccessful.
"""
