"""Embedding providers for the RAG system.

Supports both OpenAI API embeddings and local sentence-transformer models.
"""

from .embedding_provider import (
    EmbeddingProvider,
    OpenAIEmbeddingProvider,
    LocalEmbeddingProvider,
    get_embedding_provider,
)

__all__ = [
    "EmbeddingProvider",
    "OpenAIEmbeddingProvider", 
    "LocalEmbeddingProvider",
    "get_embedding_provider",
]
