"""
Abstract base class for embedders
"""
from abc import ABC, abstractmethod
from typing import List
import numpy as np


class BaseEmbedder(ABC):
    """Abstract base class for text embedders"""
    
    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Return the dimensionality of embeddings"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name/identifier"""
        pass
    
    @abstractmethod
    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string"""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embed a batch of text strings"""
        pass
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
