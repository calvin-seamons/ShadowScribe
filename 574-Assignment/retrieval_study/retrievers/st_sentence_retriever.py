"""
Sentence Transformer retriever at sentence level with parent expansion
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path
import pickle
import re

from .base import BaseRetriever, RetrievalResult
from ..embedders import SentenceTransformerEmbedder
from ..config import EMBEDDINGS_CACHE_DIR, DEFAULT_ST_MODEL


class STSentenceRetriever(BaseRetriever):
    """
    Retriever using sentence transformers at sentence/paragraph level.
    Retrieves fine-grained chunks then expands to parent sections.
    """
    
    def __init__(
        self, 
        model_name: str = DEFAULT_ST_MODEL, 
        cache_dir: Optional[Path] = None,
        chunk_size: int = 2,  # Number of sentences per chunk
        expand_to_section: bool = True  # Whether to return full section
    ):
        """
        Initialize the sentence-level retriever.
        
        Args:
            model_name: Sentence transformer model to use
            cache_dir: Directory to cache embeddings
            chunk_size: Number of sentences per chunk (1-3 recommended)
            expand_to_section: If True, return full parent section instead of chunk
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir) if cache_dir else EMBEDDINGS_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.chunk_size = chunk_size
        self.expand_to_section = expand_to_section
        
        self.embedder: Optional[SentenceTransformerEmbedder] = None
        self.sections: Dict[str, Dict] = {}
        
        # Chunk storage
        self.chunks: List[Dict] = []  # List of {text, section_id, start_idx}
        self.chunk_embeddings: Optional[np.ndarray] = None
        self._loaded = False
    
    @property
    def name(self) -> str:
        model_short = self.model_name.split('/')[-1]
        return f"st_sentence_{model_short}_chunk{self.chunk_size}"
    
    def _get_embedder(self) -> SentenceTransformerEmbedder:
        """Lazy load the embedder"""
        if self.embedder is None:
            self.embedder = SentenceTransformerEmbedder(self.model_name)
        return self.embedder
    
    def _get_cache_path(self) -> Path:
        """Get path for cached embeddings"""
        model_safe = self.model_name.replace('/', '_')
        return self.cache_dir / f"sentence_embeddings_{model_safe}_chunk{self.chunk_size}.pkl"
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - could use nltk for better results
        # Split on . ! ? followed by space or end
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Filter out empty strings and very short sentences
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _create_chunks(self, text: str, section_id: str) -> List[Dict]:
        """Create overlapping chunks from text"""
        sentences = self._split_into_sentences(text)
        if not sentences:
            # If no sentences, use the whole text as one chunk
            return [{'text': text, 'section_id': section_id, 'start_idx': 0}]
        
        chunks = []
        for i in range(0, len(sentences), max(1, self.chunk_size - 1)):  # Slight overlap
            chunk_sentences = sentences[i:i + self.chunk_size]
            if chunk_sentences:
                chunks.append({
                    'text': ' '.join(chunk_sentences),
                    'section_id': section_id,
                    'start_idx': i
                })
        
        return chunks
    
    def build_index(self, sections: Dict[str, Any]) -> None:
        """
        Build index from sections, chunking each section into sentences.
        
        Args:
            sections: Dictionary of section_id -> section data
        """
        self.sections = sections
        cache_path = self._get_cache_path()
        
        # Try to load from cache
        if cache_path.exists():
            print(f"Loading cached sentence embeddings from {cache_path}")
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Verify cache is valid
            cached_section_ids = set(c['section_id'] for c in cache_data.get('chunks', []))
            current_ids = set(sections.keys())
            
            if cached_section_ids == current_ids:
                self.chunks = cache_data['chunks']
                self.chunk_embeddings = cache_data['embeddings']
                self._loaded = True
                print(f"Loaded {len(self.chunks)} cached chunks")
                return
            else:
                print("Cache invalid (sections changed), rebuilding...")
        
        # Build chunks and embeddings
        self._build_chunks_and_embeddings()
        
        # Save to cache
        cache_data = {
            'chunks': self.chunks,
            'embeddings': self.chunk_embeddings,
            'model_name': self.model_name,
            'chunk_size': self.chunk_size
        }
        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f)
        print(f"Saved embeddings to {cache_path}")
    
    def _build_chunks_and_embeddings(self) -> None:
        """Build chunks and their embeddings"""
        embedder = self._get_embedder()
        
        # Create chunks for all sections
        self.chunks = []
        for section_id, section_data in self.sections.items():
            title = section_data.get('title', '')
            content = section_data.get('content', '')
            
            # Include title as first chunk
            if title:
                self.chunks.append({
                    'text': title,
                    'section_id': section_id,
                    'start_idx': -1,  # -1 indicates title
                    'is_title': True
                })
            
            # Chunk content
            if content:
                content_chunks = self._create_chunks(content, section_id)
                self.chunks.extend(content_chunks)
        
        # Embed all chunks
        texts = [c['text'] for c in self.chunks]
        print(f"Embedding {len(texts)} chunks with {self.model_name}...")
        self.chunk_embeddings = embedder.embed_batch(texts, show_progress=True)
        self._loaded = True
        print(f"Built embeddings: shape {self.chunk_embeddings.shape}")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve relevant sections by finding best matching chunks.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            List of RetrievalResult objects (deduplicated by section)
        """
        if not self._loaded:
            raise RuntimeError("Index not built. Call build_index() first.")
        
        if len(self.chunks) == 0:
            return []
        
        # Embed query
        embedder = self._get_embedder()
        query_embedding = embedder.embed(query)
        
        # Compute similarities
        similarities = np.dot(self.chunk_embeddings, query_embedding)
        
        # Get top chunks (retrieve more than k since we deduplicate)
        top_indices = np.argsort(similarities)[::-1][:top_k * 3]
        
        # Deduplicate by section, keeping best score per section
        seen_sections: Dict[str, Tuple[float, int]] = {}  # section_id -> (score, chunk_idx)
        
        for idx in top_indices:
            chunk = self.chunks[idx]
            section_id = chunk['section_id']
            score = float(similarities[idx])
            
            if section_id not in seen_sections or score > seen_sections[section_id][0]:
                seen_sections[section_id] = (score, idx)
        
        # Sort by score and take top-k
        sorted_sections = sorted(seen_sections.items(), key=lambda x: x[1][0], reverse=True)[:top_k]
        
        # Build results
        results = []
        for section_id, (score, chunk_idx) in sorted_sections:
            section_data = self.sections[section_id]
            chunk = self.chunks[chunk_idx]
            
            # Decide whether to return full section or just the chunk
            if self.expand_to_section:
                content = section_data.get('content', '')
            else:
                content = chunk['text']
            
            results.append(RetrievalResult(
                section_id=section_id,
                score=score,
                title=section_data.get('title', ''),
                content=content,
                metadata={
                    'level': section_data.get('level', 0),
                    'matched_chunk': chunk['text'][:200],  # Include matched chunk for debugging
                    'chunk_idx': chunk_idx
                }
            ))
        
        return results
