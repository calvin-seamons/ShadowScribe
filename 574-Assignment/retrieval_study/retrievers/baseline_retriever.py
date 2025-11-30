"""
Baseline retriever using existing OpenAI embeddings from the rulebook storage
"""
from typing import List, Dict, Any
import numpy as np
import pickle

from .base import BaseRetriever, RetrievalResult
from ..config import RULEBOOK_STORAGE_PATH


class BaselineRetriever(BaseRetriever):
    """
    Baseline retriever using pre-computed OpenAI embeddings.
    This wraps the existing rulebook storage system.
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize from existing rulebook storage.
        
        Args:
            storage_path: Path to rulebook_storage.pkl (uses default if None)
        """
        self.storage_path = storage_path or RULEBOOK_STORAGE_PATH
        self.sections: Dict[str, Dict] = {}
        self.section_ids: List[str] = []
        self.embeddings: np.ndarray = None
        self._loaded = False
    
    @property
    def name(self) -> str:
        return "baseline_openai"
    
    def build_index(self, sections: Dict[str, Any] = None) -> None:
        """
        Build index from sections or load from storage.
        
        Args:
            sections: If provided, use these sections. Otherwise load from disk.
        """
        if sections is None:
            self._load_from_storage()
        else:
            self._build_from_sections(sections)
    
    def _load_from_storage(self) -> None:
        """Load sections and embeddings from existing storage"""
        with open(self.storage_path, 'rb') as f:
            data = pickle.load(f)
        
        self.sections = data['sections']
        
        # Extract embeddings into numpy array for fast similarity computation
        self.section_ids = []
        embeddings_list = []
        
        for section_id, section_data in self.sections.items():
            vector = section_data.get('vector')
            if vector is not None:
                self.section_ids.append(section_id)
                embeddings_list.append(vector)
        
        if embeddings_list:
            self.embeddings = np.array(embeddings_list)
        else:
            self.embeddings = np.array([])
        
        self._loaded = True
        print(f"Loaded {len(self.section_ids)} sections with embeddings")
    
    def _build_from_sections(self, sections: Dict[str, Any]) -> None:
        """Build index from provided sections dict"""
        self.sections = sections
        self.section_ids = []
        embeddings_list = []
        
        for section_id, section_data in sections.items():
            vector = section_data.get('vector')
            if vector is not None:
                self.section_ids.append(section_id)
                embeddings_list.append(vector)
        
        if embeddings_list:
            self.embeddings = np.array(embeddings_list)
        else:
            self.embeddings = np.array([])
        
        self._loaded = True
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve using cosine similarity against pre-computed embeddings.
        
        Note: For fair comparison, this method requires a query embedding to be passed
        or computed. Since we're comparing embedders, we use a simple approach here.
        """
        if not self._loaded:
            self.build_index()
        
        if len(self.section_ids) == 0:
            return []
        
        # For baseline, we need to get query embedding from OpenAI
        # To keep this simple and avoid API calls during evaluation,
        # we provide a method that takes a pre-computed query embedding
        raise NotImplementedError(
            "Use retrieve_with_embedding() for baseline retriever, "
            "or use the existing RulebookQueryRouter directly"
        )
    
    def retrieve_with_embedding(self, query_embedding: np.ndarray, top_k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve using a pre-computed query embedding.
        
        Args:
            query_embedding: Pre-computed embedding for the query
            top_k: Number of results to return
            
        Returns:
            List of RetrievalResult objects
        """
        if not self._loaded:
            self.build_index()
        
        if len(self.section_ids) == 0:
            return []
        
        # Normalize query embedding
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)
        
        # Compute cosine similarities (embeddings should already be normalized)
        similarities = np.dot(self.embeddings, query_norm)
        
        # Get top-k indices
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
    
    def get_section_texts(self) -> Dict[str, str]:
        """Get section ID to text mapping for other retrievers to use"""
        if not self._loaded:
            self.build_index()
        
        texts = {}
        for section_id, section_data in self.sections.items():
            title = section_data.get('title', '')
            content = section_data.get('content', '')
            texts[section_id] = f"{title}\n\n{content}" if content else title
        
        return texts
