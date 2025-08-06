"""
Main ShadowScribe Engine - Orchestrates the multi-pass query routing system.
"""

from typing import Dict, Any, List, Callable
import asyncio
import traceback
import inspect
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
    
    def __init__(self, knowledge_base_path: str = "./knowledge_base", model: str = "gpt-4.1-nano"):
        """Initialize the ShadowScribe engine with all components."""
        self.knowledge_base = KnowledgeBase(knowledge_base_path)
        self.query_router = QueryRouter(model=model)
        self.content_retriever = ContentRetriever(self.knowledge_base)
        self.response_generator = ResponseGenerator(model=model)
        self.debug_callback = None  # Optional callback for debug logging
        
    def set_debug_callback(self, callback):
        """Set a callback function for debug logging."""
        self.debug_callback = callback
        # Pass the callback to all components that use LLM clients
        self.query_router.set_debug_callback(callback)
        self.response_generator.set_debug_callback(callback)
    
    async def _call_debug_callback(self, stage: str, message: str, data: dict = None):
        """Helper method to call debug callback, handling both sync and async callbacks."""
        if not self.debug_callback:
            return
            
        try:
            if inspect.iscoroutinefunction(self.debug_callback):
                await self.debug_callback(stage, message, data)
            else:
                self.debug_callback(stage, message, data)
        except Exception as e:
            print(f"Error in debug callback: {e}")
    
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
            await self._call_debug_callback("PASS_1_START", "Starting source selection", {"query": user_query})
            
            sources = await self.query_router.select_sources(user_query)
            
            await self._call_debug_callback("PASS_1_COMPLETE", "Source selection completed", {
                "selected_sources": sources.sources_needed if hasattr(sources, 'sources_needed') else str(sources),
                "reasoning": sources.reasoning if hasattr(sources, 'reasoning') else "No reasoning available"
            })
            
            # Pass 2: Content Targeting
            await self._call_debug_callback("PASS_2_START", "Starting content targeting", {"sources": str(sources)})
                
            targets = await self.query_router.target_content(user_query, sources)
            
            await self._call_debug_callback("PASS_2_COMPLETE", "Content targeting completed", {
                "targets": str(targets)
            })
            
            # Pass 3: Content Retrieval
            await self._call_debug_callback("PASS_3_START", "Starting content retrieval", {"targets": str(targets)})
                
            content = await self.content_retriever.fetch_content(targets)
            
            content_summary = {}
            if isinstance(content, list):
                content_summary["retrieved_items"] = len(content)
                content_summary["source_types"] = [item.source_type.value if hasattr(item, 'source_type') else str(type(item)) for item in content]
            else:
                # Fallback for dictionary-style content
                for key, value in content.items():
                    if isinstance(value, str):
                        content_summary[key] = f"{len(value)} characters" if value else "empty"
                    else:
                        content_summary[key] = f"{type(value).__name__} object"
            
            await self._call_debug_callback("PASS_3_COMPLETE", "Content retrieval completed", {
                "content_summary": content_summary
            })
            
            # Pass 4: Response Generation
            # Fix: Handle list of RetrievedContent objects
            content_types = [item.source_type.value for item in content] if isinstance(content, list) else []
            await self._call_debug_callback("PASS_4_START", "Starting response generation", {
                "content_available": content_types
            })
                
            response = await self.response_generator.generate_response(
                user_query, content
            )
            
            await self._call_debug_callback("PASS_4_COMPLETE", "Response generation completed", {
                "response_length": len(response),
                "response_preview": response[:200] + "..." if len(response) > 200 else response
            })
            
            return response
            
        except Exception as e:
            await self._call_debug_callback("ERROR", f"Error in query processing: {str(e)}", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            })
            return f"Error processing query: {str(e)}"
    
    def get_available_sources(self) -> Dict[str, Any]:
        """Get information about available knowledge sources."""
        return self.knowledge_base.get_source_overview()
    
    async def validate_query(self, user_query: str) -> bool:
        """Validate if a query can be processed by the system."""
        # TODO: Implement query validation logic
        return len(user_query.strip()) > 0