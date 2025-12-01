"""
Sentence Transformer embedder using the sentence-transformers library
"""
from typing import List, Optional
import numpy as np

from .base import BaseEmbedder


class SentenceTransformerEmbedder(BaseEmbedder):
    """Embedder using sentence-transformers models"""
    
    def __init__(self, model_name: str = "all-mpnet-base-v2", device: Optional[str] = None):
        """
        Initialize the sentence transformer embedder.
        
        Args:
            model_name: Name of the sentence-transformers model to use
            device: Device to use ('cuda', 'cpu', or None for auto)
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is required. Install with: pip install sentence-transformers"
            )
        
        self._model_name = model_name
        self._model = SentenceTransformer(model_name, device=device)
        self._embedding_dim = self._model.get_sentence_embedding_dimension()
    
    @property
    def embedding_dim(self) -> int:
        return self._embedding_dim
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string"""
        return self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32, show_progress: bool = False) -> np.ndarray:
        """
        Embed a batch of text strings.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding
            show_progress: Whether to show progress bar
            
        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        return self._model.encode(
            texts, 
            batch_size=batch_size,
            convert_to_numpy=True, 
            normalize_embeddings=True,
            show_progress_bar=show_progress
        )
