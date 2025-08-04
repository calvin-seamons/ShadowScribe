"""
Main ShadowScribe Engine - Orchestrates the multi-pass query routing system.
"""

from typing import Dict, Any, List
import asyncio
from ..knowledge.knowledge_base import KnowledgeBase
from .query_router import QueryRouter
from .content_retriever import ContentRetriever
from .response_generator import ResponseGenerator


class ShadowScribeEngine:
    """
    Main engine class that orchestrates the 4-pass query processing system:
    1. Source Selection
    2. Content Targeting
    3. Content Retrieval
    4. Response Generation
    """
    
    def __init__(self, knowledge_base_path: str = "./knowledge_base"):
        """Initialize the ShadowScribe engine with all components."""
        self.knowledge_base = KnowledgeBase(knowledge_base_path)
        self.query_router = QueryRouter()
        self.content_retriever = ContentRetriever(self.knowledge_base)
        self.response_generator = ResponseGenerator()
        
    async def process_query(self, user_query: str) -> str:
        """
        Process a user query through the complete 4-pass system.
        
        Args:
            user_query: The user's question or request
            
        Returns:
            Generated response based on retrieved context
        """
        try:
            # Pass 1: Source Selection
            sources = await self.query_router.select_sources(user_query)
            
            # Pass 2: Content Targeting
            targets = await self.query_router.target_content(user_query, sources)
            
            # Pass 3: Content Retrieval
            content = await self.content_retriever.fetch_content(targets)
            
            # Pass 4: Response Generation
            response = await self.response_generator.generate_response(
                user_query, content
            )
            
            return response
            
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    def get_available_sources(self) -> Dict[str, Any]:
        """Get information about available knowledge sources."""
        return self.knowledge_base.get_source_overview()
    
    async def validate_query(self, user_query: str) -> bool:
        """Validate if a query can be processed by the system."""
        # TODO: Implement query validation logic
        return len(user_query.strip()) > 0