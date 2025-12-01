"""
Sentence Transformer retriever at section level
"""
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
import pickle

from .base import BaseRetriever, RetrievalResult
from ..embedders import SentenceTransformerEmbedder
from ..config import EMBEDDINGS_CACHE_DIR, DEFAULT_ST_MODEL


class STSectionRetriever(BaseRetriever):
    """
    Retriever using sentence transformers at section level.
    Same chunking as baseline, different embedding model.
    """
    
    def __init__(self, model_name: str = DEFAULT_ST_MODEL, cache_dir: Optional[Path] = None):
        """
        Initialize the section-level sentence transformer retriever.
        
        Args:
            model_name: Sentence transformer model to use
            cache_dir: Directory to cache embeddings (uses default if None)
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir) if cache_dir else EMBEDDINGS_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.embedder: Optional[SentenceTransformerEmbedder] = None
        self.sections: Dict[str, Dict] = {}
        self.section_ids: List[str] = []
        self.embeddings: Optional[np.ndarray] = None
        self._loaded = False
    
    @property
    def name(self) -> str:
        model_short = self.model_name.split('/')[-1]
        return f"st_section_{model_short}"
    
    def _get_embedder(self) -> SentenceTransformerEmbedder:
        """Lazy load the embedder"""
        if self.embedder is None:
            self.embedder = SentenceTransformerEmbedder(self.model_name)
        return self.embedder
    
    def _get_cache_path(self) -> Path:
        """Get path for cached embeddings"""
        model_safe = self.model_name.replace('/', '_')
        return self.cache_dir / f"section_embeddings_{model_safe}.pkl"
    
    def build_index(self, sections: Dict[str, Any]) -> None:
        """
        Build index from sections, using cache if available.
        
        Args:
            sections: Dictionary of section_id -> section data
        """
        self.sections = sections
        cache_path = self._get_cache_path()
        
        # Try to load from cache
        if cache_path.exists():
            print(f"Loading cached embeddings from {cache_path}")
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Verify cache is valid for these sections
            cached_ids = set(cache_data.get('section_ids', []))
            current_ids = set(sections.keys())
            
            if cached_ids == current_ids:
                self.section_ids = cache_data['section_ids']
                self.embeddings = cache_data['embeddings']
                self._loaded = True
                print(f"Loaded {len(self.section_ids)} cached embeddings")
                return
            else:
                print("Cache invalid (sections changed), rebuilding...")
        
        # Build embeddings
        self._build_embeddings()
        
        # Save to cache
        cache_data = {
            'section_ids': self.section_ids,
            'embeddings': self.embeddings,
            'model_name': self.model_name
        }
        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f)
        print(f"Saved embeddings to {cache_path}")
    
    def _build_embeddings(self) -> None:
        """Build embeddings for all sections"""
        embedder = self._get_embedder()
        
        self.section_ids = list(self.sections.keys())
        texts = []
        
        for section_id in self.section_ids:
            section_data = self.sections[section_id]
            title = section_data.get('title', '')
            content = section_data.get('content', '')
            text = f"{title}\n\n{content}" if content else title
            texts.append(text)
        
        print(f"Embedding {len(texts)} sections with {self.model_name}...")
        self.embeddings = embedder.embed_batch(texts, show_progress=True)
        self._loaded = True
        print(f"Built embeddings: shape {self.embeddings.shape}")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve relevant sections for a query.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            List of RetrievalResult objects
        """
        if not self._loaded:
            raise RuntimeError("Index not built. Call build_index() first.")
        
        if len(self.section_ids) == 0:
            return []
        
        # Embed query
        embedder = self._get_embedder()
        query_embedding = embedder.embed(query)
        
        # Compute similarities (embeddings are normalized)
        similarities = np.dot(self.embeddings, query_embedding)
        
        # Get top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            section_id = self.section_ids[idx]
            section_data = self.sections[section_id]
            
            results.append(RetrievalResult(
                section_id=section_id,
                score=float(similarities[idx]),
                title=section_data.get('title', ''),
                content=section_data.get('content', ''),
                metadata={'level': section_data.get('level', 0)}
            ))
        
        return results
