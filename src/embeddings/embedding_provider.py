"""Unified embedding provider interface.

Supports both OpenAI API embeddings and local sentence-transformer models.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass
    
    @property
    def embedding_dim(self) -> int:
        """Alias for dimension for compatibility."""
        return self.dimension
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name."""
        pass
    
    @abstractmethod
    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str], show_progress: bool = False) -> List[np.ndarray]:
        """Embed a batch of text strings."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI API embedding provider."""
    
    # Model dimensions
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    def __init__(self, model: str = "text-embedding-3-small"):
        """Initialize OpenAI embedding provider.
        
        Args:
            model: OpenAI embedding model name
        """
        from openai import OpenAI
        from dotenv import load_dotenv
        
        load_dotenv()
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = OpenAI(api_key=api_key)
        self._model_name = model
        self._dimension = self.MODEL_DIMENSIONS.get(model, 1536)
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string using OpenAI API."""
        response = self.client.embeddings.create(
            input=text,
            model=self._model_name
        )
        return np.array(response.data[0].embedding)
    
    def embed_batch(self, texts: List[str], show_progress: bool = False) -> List[np.ndarray]:
        """Embed a batch of text strings using OpenAI API."""
        # OpenAI supports batch embedding
        response = self.client.embeddings.create(
            input=texts,
            model=self._model_name
        )
        return [np.array(item.embedding) for item in response.data]


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local sentence-transformer embedding provider.

    Uses sentence-transformers library for local inference.
    No API calls required.
    """

    # Map config model names to sentence-transformers model names
    MODEL_MAP = {
        "local-minilm-l6": "sentence-transformers/all-MiniLM-L6-v2",
        "local-mpnet-base": "sentence-transformers/all-mpnet-base-v2",
        "local-bge-small": "BAAI/bge-small-en-v1.5",
        "local-bge-base": "BAAI/bge-base-en-v1.5",
        "local-gte-small": "thenlper/gte-small",
        "local-gte-base": "thenlper/gte-base",
    }

    MODEL_DIMENSIONS = {
        "local-minilm-l6": 384,
        "local-mpnet-base": 768,
        "local-bge-small": 384,
        "local-bge-base": 768,
        "local-gte-small": 384,
        "local-gte-base": 768,
    }

    def __init__(self, model: str = "local-bge-base-en"):
        """Initialize local embedding provider.

        Args:
            model: Local model name (e.g., "local-bge-base-en")
        """
        from sentence_transformers import SentenceTransformer

        # Configure HuggingFace Hub to use HF_TOKEN if available (avoids rate limiting)
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            try:
                # Set the token in environment for huggingface_hub to pick up
                os.environ["HUGGING_FACE_HUB_TOKEN"] = hf_token
                os.environ["HF_TOKEN"] = hf_token
                print("HuggingFace Hub token configured")
            except Exception as e:
                print(f"Warning: Failed to configure HuggingFace Hub token: {e}")

        if model not in self.MODEL_MAP:
            raise ValueError(f"Unknown local model: {model}. Available: {list(self.MODEL_MAP.keys())}")

        self._model_name = model
        self.hf_model_name = self.MODEL_MAP[model]
        self._dimension = self.MODEL_DIMENSIONS[model]

        print(f"Loading local embedding model: {self.hf_model_name}")
        self.model = SentenceTransformer(self.hf_model_name)
        print(f"Model loaded. Embedding dimension: {self._dimension}")
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string locally."""
        # BGE models expect "query: " or "passage: " prefix for best results
        # For simplicity, we use the text as-is (still works well)
        embedding = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding
    
    def embed_batch(self, texts: List[str], show_progress: bool = False) -> List[np.ndarray]:
        """Embed a batch of text strings locally."""
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=show_progress)
        return [embeddings[i] for i in range(len(texts))]


def get_embedding_provider(model: Optional[str] = None) -> EmbeddingProvider:
    """Factory function to get the configured embedding provider.
    
    Uses the embedding_model setting from config to determine which provider to use,
    unless a specific model is provided.
    
    Args:
        model: Optional model name override. If not provided, uses config setting.
    
    Returns:
        EmbeddingProvider instance
    """
    from ..config import get_config
    
    if model is None:
        config = get_config()
        model = config.embedding_model
    
    if model.startswith("local-"):
        return LocalEmbeddingProvider(model)
    else:
        return OpenAIEmbeddingProvider(model)
