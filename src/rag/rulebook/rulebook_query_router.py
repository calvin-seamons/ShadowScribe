"""
D&D 5e Rulebook Query Router
Intelligent semantic search with intention-based filtering and multi-stage scoring.
Now includes hybrid BM25 + semantic search for better keyword matching.
Supports cross-encoder reranking for improved precision.
"""

import re
import time
import numpy as np
from typing import List, Dict, Tuple, Optional
import hashlib

from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from .rulebook_types import (
    RulebookQueryIntent, RulebookSection, SearchResult,
    RulebookCategory, INTENTION_CATEGORY_MAP, QueryPerformanceMetrics
)
from ...config import get_config
from ...embeddings import get_embedding_provider, EmbeddingProvider

# Note: dotenv is loaded in config.py

# Module-level singleton for cross-encoder reranker
_reranker_instance: Optional[CrossEncoder] = None


def get_reranker() -> Optional[CrossEncoder]:
    """
    Get or initialize the cross-encoder reranker (singleton).

    Returns None if reranking is disabled in config.
    """
    global _reranker_instance

    config = get_config()
    if not config.rulebook_rerank_enabled:
        return None

    if _reranker_instance is None:
        print(f"Loading cross-encoder reranker: {config.rulebook_reranker_model}")
        _reranker_instance = CrossEncoder(
            config.rulebook_reranker_model,
            max_length=512,
            device=config.local_model_device
        )

    return _reranker_instance


class EmbeddingCache:
    """LRU cache for embeddings to avoid repeated API calls"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.access_order = []
        self.max_size = max_size
    
    def _hash_text(self, text: str) -> str:
        """Create hash key for text"""
        return hashlib.md5(text.encode('utf-8'), usedforsecurity=False).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache"""
        key = self._hash_text(text)
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def put(self, text: str, embedding: List[float]) -> None:
        """Store embedding in cache"""
        key = self._hash_text(text)
        
        # Remove if already exists
        if key in self.cache:
            self.access_order.remove(key)
        
        # Evict oldest if at capacity
        while len(self.cache) >= self.max_size:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
        
        # Add new embedding
        self.cache[key] = embedding
        self.access_order.append(key)


class RulebookQueryRouter:
    """
    Intelligent query router for D&D 5e rulebook sections.
    Combines BM25 keyword search with semantic search using RRF fusion,
    plus entity matching and context hints.
    """
    
    # BM25 parameters
    BM25_K1 = 1.5
    BM25_B = 0.75
    RRF_K = 60  # Reciprocal Rank Fusion constant
    
    def __init__(self, storage):
        """Initialize with RulebookStorage instance"""
        from .rulebook_storage import RulebookStorage  # Import here to avoid circular import
        
        if not isinstance(storage, RulebookStorage):
            raise TypeError("storage must be a RulebookStorage instance")
            
        self.storage = storage
        self.config = get_config()
        self.embedding_model = self.config.embedding_model
        self.embedding_cache = EmbeddingCache(max_size=self.config.embedding_cache_size)
        
        # Initialize embedding provider (supports both OpenAI and local models)
        self._embedding_provider: Optional[EmbeddingProvider] = None
        
        # Initialize cross-encoder reranker (lazy loading)
        self._reranker: Optional[CrossEncoder] = None
        self._reranker_model = self.config.rulebook_reranker_model
        
        # Build BM25 index for all sections
        self._build_bm25_index()
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenization with lowercasing for BM25"""
        # Remove punctuation, lowercase, split on whitespace
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return text.split()
    
    def _build_bm25_index(self) -> None:
        """Build BM25 index for all sections"""
        self._section_ids = list(self.storage.sections.keys())
        self._section_texts = []
        
        for section_id in self._section_ids:
            section = self.storage.sections[section_id]
            # Combine title and content for BM25 indexing
            # Weight title more by repeating it
            text = f"{section.title} {section.title} {section.id} {section.content}"
            self._section_texts.append(text)
        
        # Tokenize all documents
        tokenized_docs = [self._tokenize(text) for text in self._section_texts]
        
        # Build BM25 index
        self._bm25 = BM25Okapi(tokenized_docs, k1=self.BM25_K1, b=self.BM25_B)
        print(f"Built BM25 index for {len(tokenized_docs)} rulebook sections")
    
    def query(
        self,
        intention: RulebookQueryIntent,
        user_query: str,
        entities: List[str],
        context_hints: List[str] = None,
        k: int = 5
    ) -> Tuple[List[SearchResult], QueryPerformanceMetrics]:
        """
        Perform intelligent query against rulebook sections using hybrid search.
        
        Combines:
        1. BM25 keyword search on raw query
        2. Semantic embedding search
        3. Entity ID/title boosting from gazetteer entities
        4. RRF fusion to combine BM25 and semantic results
        
        Args:
            intention: Query intent to determine search categories
            user_query: Original user query string
            entities: Normalized entities extracted from query (from gazetteer)
            context_hints: Additional phrases to enhance search
            k: Number of results to return
            
        Returns:
            Tuple of (SearchResult list, QueryPerformanceMetrics)
        """
        start_time = time.perf_counter()
        
        # Initialize performance tracking
        performance = QueryPerformanceMetrics()
        performance.total_sections_available = len(self.storage.sections)
        
        if context_hints is None:
            context_hints = []
            
        # 1. Filter sections by intention
        filter_start = time.perf_counter()
        candidate_sections = self._filter_sections_by_intention(intention)
        candidate_ids = set(s.id for s in candidate_sections)
        filter_end = time.perf_counter()
        
        performance.intention_filtering_ms = (filter_end - filter_start) * 1000
        performance.sections_after_filtering = len(candidate_sections)
        
        if not candidate_sections:
            performance.total_time_ms = (time.perf_counter() - start_time) * 1000
            return [], performance
        
        # 2. Perform HYBRID search (BM25 + Semantic with RRF fusion)
        hybrid_start = time.perf_counter()
        hybrid_results = self._hybrid_search(user_query, candidate_sections, candidate_ids, performance)
        hybrid_end = time.perf_counter()
        
        performance.semantic_search_ms = (hybrid_end - hybrid_start) * 1000
        
        # 3. Apply entity boosting (using gazetteer-resolved entities)
        entity_start = time.perf_counter()
        entity_boosted_results = self._boost_entity_matches(hybrid_results, entities)
        entity_end = time.perf_counter()
        
        performance.entity_boosting_ms = (entity_end - entity_start) * 1000
        
        # 4. Enhance with context hints
        context_start = time.perf_counter()
        enhanced_results = self._enhance_with_context_hints(entity_boosted_results, context_hints, performance)
        context_end = time.perf_counter()
        
        performance.context_enhancement_ms = (context_end - context_start) * 1000
        
        # 5. Force-include entity-matching sections (guarantees entity sections in results)
        final_results = self._force_include_entity_sections(enhanced_results, entities, candidate_sections)
        
        # 6. Take top-k and create SearchResult objects
        assembly_start = time.perf_counter()
        top_results = final_results[:k]
        search_results = []
        
        for section, score in top_results:
            # Find matched entities and context for this section
            matched_entities = self._find_matched_entities(section, entities)
            matched_context = self._find_matched_context(section, context_hints)
            
            search_result = SearchResult(
                section=section,
                score=score,
                matched_entities=matched_entities,
                matched_context=matched_context,
                includes_children=True  # We'll include children content
            )
            search_results.append(search_result)
        
        assembly_end = time.perf_counter()
        performance.result_assembly_ms = (assembly_end - assembly_start) * 1000
        performance.results_returned = len(search_results)
        
        # 6. Include children content for complete context
        children_start = time.perf_counter()
        self._include_children_content(search_results)
        children_end = time.perf_counter()
        
        performance.children_inclusion_ms = (children_end - children_start) * 1000
        
        # Finalize performance metrics
        end_time = time.perf_counter()
        performance.total_time_ms = (end_time - start_time) * 1000
        
        return search_results, performance
    
    def _filter_sections_by_intention(self, intention: RulebookQueryIntent) -> List[RulebookSection]:
        """Filter sections to only those relevant to the query intention"""
        target_categories = INTENTION_CATEGORY_MAP.get(intention, [])
        
        if not target_categories:
            # If no specific mapping, return all sections
            return list(self.storage.sections.values())
        
        candidate_sections = []
        for section in self.storage.sections.values():
            # Check if section has any of the target categories
            section_category_values = [cat.value if hasattr(cat, 'value') else cat for cat in section.categories]
            target_category_values = [cat.value if hasattr(cat, 'value') else cat for cat in target_categories]
            
            if any(cat in target_category_values for cat in section_category_values):
                candidate_sections.append(section)
        
        return candidate_sections
    
    def _bm25_search(self, query: str, candidate_ids: set) -> List[Tuple[str, float]]:
        """
        Perform BM25 keyword search on the raw query.
        
        Args:
            query: Raw user query string
            candidate_ids: Set of section IDs to consider (from intention filtering)
            
        Returns:
            List of (section_id, bm25_score) tuples, sorted by score descending
        """
        tokenized_query = self._tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)
        
        # Pair scores with section IDs and filter to candidates
        results = []
        for idx, section_id in enumerate(self._section_ids):
            if section_id in candidate_ids:
                results.append((section_id, scores[idx]))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def _hybrid_search(
        self, 
        query: str, 
        candidate_sections: List[RulebookSection],
        candidate_ids: set,
        performance: QueryPerformanceMetrics
    ) -> List[Tuple[RulebookSection, float]]:
        """
        Perform hybrid BM25 + semantic search with RRF fusion and optional reranking.
        
        Args:
            query: Raw user query string
            candidate_sections: List of sections to search (from intention filtering)
            candidate_ids: Set of candidate section IDs for fast lookup
            performance: Performance metrics object to update
            
        Returns:
            List of (RulebookSection, fused_score) tuples, sorted by score descending
        """
        if not candidate_sections:
            return []
        
        # Track sections with embeddings
        performance.sections_with_embeddings = sum(1 for s in candidate_sections if s.vector is not None)
        
        # Get top-N candidates from each method (use config value)
        n_candidates = min(len(candidate_sections), self.config.rulebook_candidate_pool_size)
        
        # 1. BM25 keyword search on raw query
        bm25_results = self._bm25_search(query, candidate_ids)[:n_candidates]
        
        # 2. Semantic search
        embed_start = time.perf_counter()
        query_embedding = self._get_embedding(query, performance)
        embed_end = time.perf_counter()
        performance.embedding_total_ms += (embed_end - embed_start) * 1000
        
        semantic_results = []
        for section in candidate_sections:
            if section.vector is None:
                continue
            similarity = self._cosine_similarity(query_embedding, section.vector)
            semantic_results.append((section.id, similarity))
        
        semantic_results.sort(key=lambda x: x[1], reverse=True)
        semantic_results = semantic_results[:n_candidates]
        
        # 3. RRF fusion - combine rankings using config weights
        bm25_weight = self.config.rulebook_bm25_weight
        semantic_weight = self.config.rulebook_semantic_weight
        fused_scores: Dict[str, float] = {}
        
        # BM25 contribution
        for rank, (section_id, _) in enumerate(bm25_results):
            rrf_score = bm25_weight / (self.RRF_K + rank + 1)
            fused_scores[section_id] = fused_scores.get(section_id, 0) + rrf_score
        
        # Semantic contribution
        for rank, (section_id, _) in enumerate(semantic_results):
            rrf_score = semantic_weight / (self.RRF_K + rank + 1)
            fused_scores[section_id] = fused_scores.get(section_id, 0) + rrf_score
        
        # 4. Convert back to (section, score) format
        section_lookup = {s.id: s for s in candidate_sections}
        results = []
        for section_id, score in fused_scores.items():
            if section_id in section_lookup:
                results.append((section_lookup[section_id], score))
        
        # Sort by fused score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 5. Apply cross-encoder reranking if enabled
        if self.config.rulebook_rerank_enabled and len(results) > 0:
            rerank_start = time.perf_counter()
            results = self._rerank_results(query, results, performance)
            rerank_end = time.perf_counter()
            performance.reranking_ms = (rerank_end - rerank_start) * 1000
        
        return results

    def _semantic_search(self, query: str, candidate_sections: List[RulebookSection], performance: QueryPerformanceMetrics) -> List[Tuple[RulebookSection, float]]:
        """Perform semantic search using embeddings"""
        if not candidate_sections:
            return []
        
        # Track sections with embeddings
        performance.sections_with_embeddings = sum(1 for s in candidate_sections if s.vector is not None)
        
        # Embed the query
        embed_start = time.perf_counter()
        query_embedding = self._get_embedding(query, performance)
        embed_end = time.perf_counter()
        
        performance.embedding_total_ms += (embed_end - embed_start) * 1000
        
        results = []
        for section in candidate_sections:
            if section.vector is None:
                # Skip sections without embeddings
                continue
                
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, section.vector)
            results.append((section, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def _get_reranker(self) -> Optional[CrossEncoder]:
        """Get the cross-encoder reranker (uses module-level singleton)"""
        if self._reranker is None:
            self._reranker = get_reranker()
        return self._reranker
    
    def _rerank_results(
        self,
        query: str,
        results: List[Tuple[RulebookSection, float]],
        performance: QueryPerformanceMetrics
    ) -> List[Tuple[RulebookSection, float]]:
        """
        Rerank results using a cross-encoder model for improved precision.
        
        Cross-encoders jointly encode query and document, providing more accurate
        relevance scores than bi-encoder similarity. This is slower but more accurate.
        
        Args:
            query: The user query string
            results: Initial results from hybrid search [(section, score), ...]
            performance: Performance metrics to update
            
        Returns:
            Reranked results [(section, rerank_score), ...]
        """
        if not results:
            return results
        
        # Limit to top candidates for reranking (cross-encoder is slower)
        max_rerank_candidates = min(len(results), self.config.rulebook_candidate_pool_size)
        candidates = results[:max_rerank_candidates]
        
        # Prepare query-document pairs for cross-encoder
        # Use title + first 400 chars of content to stay within token limits
        pairs = []
        for section, _ in candidates:
            # Construct document text: title + content preview
            doc_text = f"{section.title}\n{section.content[:400]}"
            pairs.append([query, doc_text])
        
        try:
            reranker = self._get_reranker()
            
            # Get relevance scores from cross-encoder
            scores = reranker.predict(pairs, show_progress_bar=False)
            
            # Pair sections with new scores
            reranked = []
            for i, (section, _) in enumerate(candidates):
                reranked.append((section, float(scores[i])))
            
            # Sort by reranker score descending
            reranked.sort(key=lambda x: x[1], reverse=True)
            
            # Return top-k after reranking
            return reranked[:self.config.rulebook_rerank_top_k]
            
        except Exception as e:
            print(f"Warning: Reranking failed, falling back to original results: {e}")
            # Fall back to original results without reranking
            return results[:self.config.rulebook_rerank_top_k]
    
    def _boost_entity_matches(self, results: List[Tuple[RulebookSection, float]], entities: List[str]) -> List[Tuple[RulebookSection, float]]:
        """Boost scores based on entity matches in section content"""
        if not entities:
            return results
        
        boosted_results = []
        for section, base_score in results:
            entity_boost = 0.0
            
            for entity in entities:
                entity_lower = entity.lower()
                
                # Check title (high weight)
                if entity_lower in section.title.lower():
                    entity_boost += 0.3
                
                # Check ID (medium weight)
                if entity_lower in section.id.lower():
                    entity_boost += 0.2
                
                # Check content (medium weight, scaled by frequency)
                content_lower = section.content.lower()
                entity_count = content_lower.count(entity_lower)
                if entity_count > 0:
                    # Diminishing returns for multiple mentions
                    entity_boost += min(0.25 * entity_count, 0.5)
            
            # Apply entity boost (25% of total score)
            boosted_score = base_score * 0.75 + entity_boost * 0.25
            boosted_results.append((section, boosted_score))
        
        # Re-sort by boosted scores
        boosted_results.sort(key=lambda x: x[1], reverse=True)
        return boosted_results
    
    def _force_include_entity_sections(
        self, 
        results: List[Tuple[RulebookSection, float]], 
        entities: List[str],
        candidate_sections: List[RulebookSection]
    ) -> List[Tuple[RulebookSection, float]]:
        """
        Force-include sections that directly match extracted entity names.
        
        This ensures that when entities like "Fireball" or "Lightning Bolt" are extracted,
        the corresponding sections are ALWAYS in the final results, regardless of how 
        the reranker scored them. This fixes the issue where cross-encoder reranking
        would push out exact entity matches in favor of sections that merely mention
        the entities (like spell lists).
        
        Args:
            results: Current ranked results after boosting/enhancement
            entities: List of entity names extracted from the query
            candidate_sections: All candidate sections from intention filtering
            
        Returns:
            Results with entity-matching sections force-included at appropriate positions
        """
        if not entities:
            return results
        
        # Build lookup of current results
        result_ids = {section.id for section, _ in results}
        
        # Find entity-matching sections not already in results
        entity_sections_to_add = []
        
        for entity in entities:
            entity_normalized = self._normalize_entity_to_id(entity)
            entity_lower = entity.lower()
            
            for section in candidate_sections:
                # Skip if already in results
                if section.id in result_ids:
                    continue
                
                # Check for exact ID match (highest priority)
                if section.id == entity_normalized:
                    # Give a high score to ensure good placement
                    entity_sections_to_add.append((section, 0.95, "id_match"))
                    result_ids.add(section.id)
                    continue
                
                # Check for exact title match
                if section.title.lower() == entity_lower:
                    entity_sections_to_add.append((section, 0.90, "title_match"))
                    result_ids.add(section.id)
                    continue
                
                # Check for title containing entity (for multi-word entities)
                if entity_lower in section.title.lower() and len(entity_lower) > 3:
                    # Only if the entity is a significant part of the title
                    title_words = section.title.lower().split()
                    if any(entity_lower == word or entity_lower in word for word in title_words):
                        entity_sections_to_add.append((section, 0.85, "title_contains"))
                        result_ids.add(section.id)
        
        if not entity_sections_to_add:
            return results
        
        # Merge entity sections into results at appropriate positions
        # Strategy: Insert based on score, but ensure entity sections are in top portion
        merged_results = list(results)
        
        for section, priority_score, match_type in entity_sections_to_add:
            # Find insertion point based on priority score
            insert_idx = 0
            for i, (_, score) in enumerate(merged_results):
                if priority_score > score:
                    insert_idx = i
                    break
                insert_idx = i + 1
            
            merged_results.insert(insert_idx, (section, priority_score))
        
        return merged_results
    
    def _normalize_entity_to_id(self, entity: str) -> str:
        """Convert entity name to expected section ID format (lowercase, hyphenated)."""
        # Convert to lowercase and replace spaces with hyphens
        normalized = entity.lower().strip()
        normalized = re.sub(r'\s+', '-', normalized)
        # Remove any special characters except hyphens
        normalized = re.sub(r'[^a-z0-9\-]', '', normalized)
        return normalized

    def _enhance_with_context_hints(self, results: List[Tuple[RulebookSection, float]], hints: List[str], performance: QueryPerformanceMetrics) -> List[Tuple[RulebookSection, float]]:
        """Enhance scores using context hints"""
        if not hints:
            return results
        
        # Get embeddings for all context hints using batch processing
        embed_start = time.perf_counter()
        hint_embeddings = self._get_embeddings_batch(hints, performance)
        embed_end = time.perf_counter()
        
        performance.embedding_total_ms += (embed_end - embed_start) * 1000
        
        enhanced_results = []
        for section, base_score in results:
            if section.vector is None:
                enhanced_results.append((section, base_score))
                continue
            
            context_boost = 0.0
            
            # Check similarity with each context hint
            for hint_embedding in hint_embeddings:
                similarity = self._cosine_similarity(hint_embedding, section.vector)
                context_boost += similarity
            
            # Average the context hint similarities
            if hint_embeddings:
                context_boost /= len(hint_embeddings)
            
            # Apply context boost (15% of total score)
            enhanced_score = base_score * 0.85 + context_boost * 0.15
            enhanced_results.append((section, enhanced_score))
        
        # Re-sort by enhanced scores
        enhanced_results.sort(key=lambda x: x[1], reverse=True)
        return enhanced_results
    
    def _include_children_content(self, search_results: List[SearchResult]) -> None:
        """Include children content for hierarchical completeness"""
        for result in search_results:
            # Get full content including children
            full_content = result.section.get_full_content(
                include_children=True, 
                storage=self.storage
            )
            
            # Update the section content with hierarchical content
            # Note: We modify the content but keep the original section structure
            if full_content != result.section.content:
                # Create a copy of the section with full content
                result.section.content = full_content
                result.includes_children = True
    
    def _find_matched_entities(self, section: RulebookSection, entities: List[str]) -> List[str]:
        """Find which entities match in this section"""
        matched = []
        section_text = f"{section.title} {section.id} {section.content}".lower()
        
        for entity in entities:
            if entity.lower() in section_text:
                matched.append(entity)
        
        return matched
    
    def _find_matched_context(self, section: RulebookSection, context_hints: List[str]) -> List[str]:
        """Find which context hints are relevant to this section"""
        if not context_hints:
            return []
        
        matched = []
        section_text = f"{section.title} {section.content}".lower()
        
        for hint in context_hints:
            # Simple word overlap check for context relevance
            hint_words = set(hint.lower().split())
            section_words = set(section_text.split())
            
            # If hint has significant word overlap with section, consider it matched
            overlap = len(hint_words & section_words)
            if overlap >= min(2, len(hint_words) // 2):  # At least 2 words or half the hint words
                matched.append(hint)
        
        return matched
    
    def _get_embedding_provider(self) -> EmbeddingProvider:
        """Get or initialize the embedding provider (lazy loading)"""
        if self._embedding_provider is None:
            self._embedding_provider = get_embedding_provider(self.embedding_model)
        return self._embedding_provider
    
    def _get_embedding(self, text: str, performance: QueryPerformanceMetrics) -> List[float]:
        """Get embedding for text using the embedding provider with caching"""
        # Check cache first
        cached_embedding = self.embedding_cache.get(text)
        if cached_embedding is not None:
            performance.embedding_cache_hits += 1
            return cached_embedding
        
        performance.embedding_cache_misses += 1
        performance.embedding_api_calls += 1
        
        try:
            provider = self._get_embedding_provider()
            embedding = provider.embed(text)
            
            # Store in cache
            self.embedding_cache.put(text, embedding)
            return embedding
            
        except Exception as e:
            print(f"Error getting embedding: {e}")
            # Return zero vector as fallback (use provider's dimension)
            provider = self._get_embedding_provider()
            fallback = [0.0] * provider.embedding_dim
            self.embedding_cache.put(text, fallback)
            return fallback
    
    def _get_embeddings_batch(self, texts: List[str], performance: QueryPerformanceMetrics) -> List[List[float]]:
        """Get embeddings for multiple texts, using cache where possible"""
        embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            cached_embedding = self.embedding_cache.get(text)
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
                performance.embedding_cache_hits += 1
            else:
                embeddings.append(None)  # Placeholder
                texts_to_embed.append(text)
                indices_to_embed.append(i)
                performance.embedding_cache_misses += 1
        
        # Batch embed uncached texts
        if texts_to_embed:
            performance.embedding_api_calls += 1  # One batch call
                
            try:
                provider = self._get_embedding_provider()
                batch_embeddings = provider.embed_batch(texts_to_embed)
                
                # Fill in the embeddings and cache them
                for j, embedding in enumerate(batch_embeddings):
                    text = texts_to_embed[j]
                    index = indices_to_embed[j]
                    
                    embeddings[index] = embedding
                    self.embedding_cache.put(text, embedding)
                    
            except Exception as e:
                print(f"Error getting batch embeddings: {e}")
                # Fill with zero vectors as fallback
                provider = self._get_embedding_provider()
                fallback = [0.0] * provider.embedding_dim
                for i in indices_to_embed:
                    embeddings[i] = fallback
                    self.embedding_cache.put(texts[i], fallback)
        
        return embeddings
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            print(f"Error calculating cosine similarity: {e}")
            return 0.0
