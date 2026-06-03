# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.

"""Sample test data constants for MKMChat tests."""


SAMPLE_CHAT_MESSAGE = {
    "role": "user",
    "content": "What is the Nelson-Siegel model?",
    "timestamp": "2026-03-25T10:00:00",
}

SAMPLE_CHAT_MESSAGE_RESPONSE = {
    "role": "assistant",
    "content": "The Nelson-Siegel model is a parsimonious yield curve model.",
    "timestamp": "2026-03-25T10:00:01",
}

SAMPLE_CHAT = {
    "id": "test_chat_001",
    "title": "Test Chat",
    "timestamp": "2026-03-25T10:00:00",
    "messages": [SAMPLE_CHAT_MESSAGE, SAMPLE_CHAT_MESSAGE_RESPONSE],
    "knowledge_base": "misc",
    "model": "claude-sonnet-4-5-20250929",
}

SAMPLE_CHAT_2 = {
    "id": "test_chat_002",
    "title": "Second Test Chat",
    "timestamp": "2026-03-25T11:00:00",
    "messages": [
        {"role": "user", "content": "Hello", "timestamp": "2026-03-25T11:00:00"},
    ],
    "knowledge_base": "phys",
    "model": "sonar-pro",
}

SAMPLE_QUERY_REQUEST = {
    "query": "What is flood risk modelling?",
    "model": "claude-sonnet-4-5-20250929",
}

SAMPLE_RESEARCH_REQUEST = {
    "query": "Compare the Nelson-Siegel and Svensson yield curve models",
    "knowledge_bases": ["mods", "misc"],
    "model": "claude-sonnet-4-5-20250929",
}

SAMPLE_LLM_RESPONSE_ANTHROPIC = {
    "content": [{"text": "This is a test response from Claude."}],
    "model": "claude-sonnet-4-5-20250929",
    "stop_reason": "end_turn",
}

SAMPLE_LLM_RESPONSE_PERPLEXITY = {
    "choices": [{"message": {"content": "This is a test response from Perplexity."}}],
    "model": "sonar-pro",
}

SAMPLE_LLM_RESPONSE_LOCAL = {
    "choices": [{"message": {"content": "This is a test response from LM Studio."}}],
    "model": "local-model",
}

SAMPLE_DOCUMENT_CHUNK = {
    "page_content": "The Nelson-Siegel-Svensson model extends the Nelson-Siegel model by adding a second hump term.",
    "metadata": {
        "source": "test_document.pdf",
        "page": 1,
    },
}

SAMPLE_DOCUMENT_CHUNKS = [
    {
        "page_content": f"Test document chunk {i}. This contains sample text for testing purposes.",
        "metadata": {"source": f"test_doc_{i}.pdf", "page": i},
    }
    for i in range(5)
]

SAMPLE_COLLECTION_CONFIG = {
    "name": "Test Collection",
    "description": "A test document collection",
    "docs_folder": "/tmp/mkm_test/docs",
    "faiss_index": "/tmp/mkm_test/faiss",
    "summary_file": "/tmp/mkm_test/summaries.json",
    "processed_file": "/tmp/mkm_test/processed.json",
    "cleanup_module": None,
}

SAMPLE_SUMMARY = {
    "test_document.pdf": {
        "hash": "abc123def456",
        "summary": "This document discusses yield curve modelling approaches.",
        "summary_type": "FULL",
        "timestamp": "2026-03-25T10:00:00",
    }
}
