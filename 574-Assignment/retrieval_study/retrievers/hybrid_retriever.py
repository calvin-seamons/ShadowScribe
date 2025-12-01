"""
Hybrid retriever combining BM25 sparse retrieval with dense embeddings
"""
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
import pickle

from .base import BaseRetriever, RetrievalResult
from ..embedders import SentenceTransformerEmbedder
from ..config import EMBEDDINGS_CACHE_DIR, DEFAULT_ST_MODEL, BM25_K1, BM25_B, RRF_K


class HybridRetriever(BaseRetriever):
    """
    Hybrid retriever using BM25 + sentence transformer embeddings.
    Combines results using Reciprocal Rank Fusion (RRF).
    """
    
    def __init__(
        self, 
        model_name: str = DEFAULT_ST_MODEL,
        cache_dir: Optional[Path] = None,
        dense_weight: float = 0.5  # Weight for dense vs sparse (0-1)
    ):
        """
        Initialize the hybrid retriever.
        
        Args:
            model_name: Sentence transformer model for dense retrieval
            cache_dir: Directory to cache embeddings
            dense_weight: Weight for dense retrieval (1-dense_weight for BM25)
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir) if cache_dir else EMBEDDINGS_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.dense_weight = dense_weight
        
        self.embedder: Optional[SentenceTransformerEmbedder] = None
        self.bm25 = None
        
        self.sections: Dict[str, Dict] = {}
        self.section_ids: List[str] = []
        self.section_texts: List[str] = []
        self.embeddings: Optional[np.ndarray] = None
        self._loaded = False
    
    @property
    def name(self) -> str:
        model_short = self.model_name.split('/')[-1]
        return f"hybrid_bm25_{model_short}"
    
    def _get_embedder(self) -> SentenceTransformerEmbedder:
        """Lazy load the embedder"""
        if self.embedder is None:
            self.embedder = SentenceTransformerEmbedder(self.model_name)
        return self.embedder
    
    def _get_cache_path(self) -> Path:
        """Get path for cached embeddings"""
        model_safe = self.model_name.replace('/', '_')
        return self.cache_dir / f"hybrid_embeddings_{model_safe}.pkl"
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenization with lowercasing"""
        import re
        # Remove punctuation, lowercase, split on whitespace
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return text.split()
    
    def build_index(self, sections: Dict[str, Any]) -> None:
        """
        Build BM25 and dense indices.
        
        Args:
            sections: Dictionary of section_id -> section data
        """
        self.sections = sections
        self.section_ids = list(sections.keys())
        
        # Build texts
        self.section_texts = []
        for section_id in self.section_ids:
            section_data = sections[section_id]
            title = section_data.get('title', '')
            content = section_data.get('content', '')
            self.section_texts.append(f"{title}\n\n{content}" if content else title)
        
        # Build BM25 index
        self._build_bm25_index()
        
        # Build or load dense embeddings
        self._build_dense_index()
        
        self._loaded = True
    
    def _build_bm25_index(self) -> None:
        """Build BM25 index"""
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError(
                "rank-bm25 is required for hybrid retrieval. "
                "Install with: pip install rank-bm25"
            )
        
        # Tokenize all documents
        tokenized_docs = [self._tokenize(text) for text in self.section_texts]
        
        # Build BM25 index
        self.bm25 = BM25Okapi(tokenized_docs, k1=BM25_K1, b=BM25_B)
        print(f"Built BM25 index for {len(tokenized_docs)} documents")
    
    def _build_dense_index(self) -> None:
        """Build or load dense embeddings"""
        cache_path = self._get_cache_path()
        
        # Try to load from cache
        if cache_path.exists():
            print(f"Loading cached dense embeddings from {cache_path}")
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            cached_ids = cache_data.get('section_ids', [])
            if cached_ids == self.section_ids:
                self.embeddings = cache_data['embeddings']
                print(f"Loaded {len(self.section_ids)} cached embeddings")
                return
        
        # Build embeddings
        embedder = self._get_embedder()
        print(f"Embedding {len(self.section_texts)} sections with {self.model_name}...")
        self.embeddings = embedder.embed_batch(self.section_texts, show_progress=True)
        
        # Save to cache
        cache_data = {
            'section_ids': self.section_ids,
            'embeddings': self.embeddings,
            'model_name': self.model_name
        }
        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f)
        print(f"Saved embeddings to {cache_path}")
    
    def _bm25_retrieve(self, query: str, top_k: int) -> List[tuple]:
        """Get BM25 scores for query"""
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(idx, scores[idx]) for idx in top_indices]
    
    def _dense_retrieve(self, query: str, top_k: int) -> List[tuple]:
        """Get dense similarity scores for query"""
        embedder = self._get_embedder()
        query_embedding = embedder.embed(query)
        
        similarities = np.dot(self.embeddings, query_embedding)
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [(idx, similarities[idx]) for idx in top_indices]
    
    def _rrf_fusion(
        self, 
        bm25_results: List[tuple], 
        dense_results: List[tuple],
        k: int = RRF_K
    ) -> Dict[int, float]:
        """
        Reciprocal Rank Fusion to combine rankings.
        
        Args:
            bm25_results: List of (doc_idx, score) from BM25
            dense_results: List of (doc_idx, score) from dense
            k: RRF constant (default 60)
            
        Returns:
            Dict of doc_idx -> fused score
        """
        fused_scores = {}
        
        # Add BM25 scores
        for rank, (doc_idx, _) in enumerate(bm25_results):
            rrf_score = (1 - self.dense_weight) / (k + rank + 1)
            fused_scores[doc_idx] = fused_scores.get(doc_idx, 0) + rrf_score
        
        # Add dense scores
        for rank, (doc_idx, _) in enumerate(dense_results):
            rrf_score = self.dense_weight / (k + rank + 1)
            fused_scores[doc_idx] = fused_scores.get(doc_idx, 0) + rrf_score
        
        return fused_scores
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve using hybrid BM25 + dense with RRF fusion.
        
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
        
        # Get results from both retrievers (get more for fusion)
        n_candidates = top_k * 3
        bm25_results = self._bm25_retrieve(query, n_candidates)
        dense_results = self._dense_retrieve(query, n_candidates)
        
        # Fuse with RRF
        fused_scores = self._rrf_fusion(bm25_results, dense_results)
        
        # Sort by fused score and take top-k
        sorted_docs = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Build results
        results = []
        for doc_idx, score in sorted_docs:
            section_id = self.section_ids[doc_idx]
            section_data = self.sections[section_id]
            
            results.append(RetrievalResult(
                section_id=section_id,
                score=score,
                title=section_data.get('title', ''),
                content=section_data.get('content', ''),
                metadata={'level': section_data.get('level', 0)}
            ))
        
        return results
