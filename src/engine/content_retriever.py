"""
Content Retriever - Handles Pass 3 (Content Retrieval) from knowledge sources.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import os

from .query_router import ContentTarget, SourceType
from ..knowledge.knowledge_base import KnowledgeBase


@dataclass
class RetrievedContent:
    """Container for content retrieved from knowledge sources."""
    source_type: SourceType
    content: Dict[str, Any]
    metadata: Dict[str, Any]


class ContentRetriever:
    """
    Handles Pass 3 of the query routing system:
    - Retrieves specific content based on targeting from Pass 2
    - Optimizes retrieval to minimize data transfer
    - Caches frequently accessed content
    """
    
    def __init__(self, knowledge_base: KnowledgeBase):
        """Initialize content retriever with knowledge base access."""
        self.knowledge_base = knowledge_base
        self._cache = {}  # Simple in-memory cache
    
    async def fetch_content(self, targets: List[ContentTarget]) -> List[RetrievedContent]:
        """
        Retrieve content for all specified targets.
        
        Args:
            targets: List of ContentTarget objects from Pass 2
            
        Returns:
            List of RetrievedContent with the retrieved data
        """
        retrieved_content = []
        
        for target in targets:
            try:
                if target.source_type == SourceType.DND_RULEBOOK:
                    content = await self._fetch_rulebook_content(target)
                elif target.source_type == SourceType.CHARACTER_DATA:
                    content = await self._fetch_character_content(target)
                elif target.source_type == SourceType.SESSION_NOTES:
                    content = await self._fetch_session_content(target)
                else:
                    continue
                
                retrieved_content.append(content)
                
            except Exception as e:
                # Log error but continue with other targets
                print(f"Error retrieving content for {target.source_type}: {str(e)}")
                continue
        
        return retrieved_content
    
    async def _fetch_rulebook_content(self, target: ContentTarget) -> RetrievedContent:
        """Retrieve specific sections from the D&D rulebook."""
        cache_key = f"rulebook_{hash(str(target.specific_targets))}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        content = {}
        metadata = {"source": "dnd5e_srd", "sections_found": []}
        
        # Get section IDs if specified
        section_ids = target.specific_targets.get("section_ids", [])
        keywords = target.specific_targets.get("keywords", [])
        
        if section_ids:
            # Retrieve specific sections by ID
            sections = self.knowledge_base.get_sections_by_ids(section_ids)
            content["sections"] = sections
            metadata["sections_found"] = [s.get("id", "unknown") for s in sections]
        
        if keywords:
            # Search by keywords
            search_results = self.knowledge_base.search_by_keywords(keywords)
            content["search_results"] = search_results
            metadata["keywords_used"] = keywords
            metadata["results_count"] = len(search_results)
        
        result = RetrievedContent(
            source_type=SourceType.DND_RULEBOOK,
            content=content,
            metadata=metadata
        )
        
        # Cache the result
        self._cache[cache_key] = result
        return result
    
    async def _fetch_character_content(self, target: ContentTarget) -> RetrievedContent:
        """Retrieve specific data from character files."""
        cache_key = f"character_{hash(str(target.specific_targets))}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        content = {}
        metadata = {"source": "character_data", "files_accessed": []}
        
        file_fields = target.specific_targets.get("file_fields", {})
        
        for filename, fields in file_fields.items():
            try:
                file_data = self.knowledge_base.get_character_data(filename, fields)
                content[filename] = file_data
                metadata["files_accessed"].append(filename)
            except Exception as e:
                print(f"Error loading {filename}: {str(e)}")
                continue
        
        # If no specific files requested, get basic character info
        if not content:
            basic_data = self.knowledge_base.get_basic_character_info()
            content["basic_info"] = basic_data
            metadata["files_accessed"] = ["character.json"]
        
        result = RetrievedContent(
            source_type=SourceType.CHARACTER_DATA,
            content=content,
            metadata=metadata
        )
        
        # Cache the result
        self._cache[cache_key] = result
        return result
    
    async def _fetch_session_content(self, target: ContentTarget) -> RetrievedContent:
        """Retrieve specific session notes."""
        cache_key = f"sessions_{hash(str(target.specific_targets))}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        content = {}
        metadata = {"source": "session_notes", "sessions_loaded": []}
        
        session_dates = target.specific_targets.get("session_dates", [])
        keywords = target.specific_targets.get("keywords", [])
        
        if "latest" in session_dates:
            # Get the most recent session
            latest_session = self.knowledge_base.get_latest_session()
            if latest_session:
                content["latest_session"] = latest_session
                metadata["sessions_loaded"].append("latest")
        
        # Get specific sessions by date
        specific_dates = [date for date in session_dates if date != "latest"]
        for date in specific_dates:
            try:
                session_data = self.knowledge_base.get_session_by_date(date)
                if session_data:
                    content[f"session_{date}"] = session_data
                    metadata["sessions_loaded"].append(date)
            except Exception as e:
                print(f"Error loading session {date}: {str(e)}")
                continue
        
        # If keywords provided, search within sessions
        if keywords:
            search_results = self.knowledge_base.search_sessions_by_keywords(keywords)
            content["keyword_matches"] = search_results
            metadata["keywords_used"] = keywords
        
        result = RetrievedContent(
            source_type=SourceType.SESSION_NOTES,
            content=content,
            metadata=metadata
        )
        
        # Cache the result
        self._cache[cache_key] = result
        return result
    
    def clear_cache(self):
        """Clear the content cache."""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about cache usage."""
        return {
            "cache_size": len(self._cache),
            "cached_keys": list(self._cache.keys())
        }