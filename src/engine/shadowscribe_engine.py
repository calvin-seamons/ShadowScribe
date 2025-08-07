"""
Main ShadowScribe Engine - Orchestrates the multi-pass query routing system.
IMPROVED VERSION with better async handling and progress updates
"""

from typing import Dict, Any, List, Callable, Optional
import asyncio
import traceback
import inspect
import time
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
    
    def __init__(self, knowledge_base_path: str = "./knowledge_base", model: str = "gpt-4o-mini"):
        """Initialize the ShadowScribe engine with all components."""
        self.current_model = model
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
                # For sync callbacks, create a task to run it without blocking
                loop = asyncio.get_event_loop()
                # Use run_in_executor to avoid blocking the event loop
                await loop.run_in_executor(None, self.debug_callback, stage, message, data)
                # Small delay to ensure message is sent
                await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Error in debug callback: {e}")
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a user query through the complete 4-pass system.
        
        Args:
            user_query: The user's question or request
            
        Returns:
            Dictionary containing response and source usage information
        """
        # Initialize tracking variables
        used_sources = []
        targets_info = []
        content_summary = {}
        
        try:
            # Pass 1: Source Selection
            await self._call_debug_callback("PASS_1_START", "Starting source selection", {"query": user_query})
            
            # Create task for source selection
            sources_task = asyncio.create_task(self.query_router.select_sources(user_query))
            sources = await sources_task
            
            # Track used sources
            used_sources = [s.value for s in sources.sources_needed] if hasattr(sources, 'sources_needed') else []
            
            await self._call_debug_callback("PASS_1_COMPLETE", "Source selection completed", {
                "selected_sources": used_sources,
                "reasoning": sources.reasoning if hasattr(sources, 'reasoning') else "No reasoning available"
            })
            
            # Pass 2: Content Targeting
            await self._call_debug_callback("PASS_2_START", "Starting content targeting", {
                "sources": used_sources
            })
                
            targets_task = asyncio.create_task(self.query_router.target_content(user_query, sources))
            targets = await targets_task
            
            # Format targets for debug output and tracking
            targets_info = []
            for target in targets:
                target_data = {
                    "source": target.source_type.value,
                    "targets": target.specific_targets
                }
                targets_info.append(target_data)
            
            await self._call_debug_callback("PASS_2_COMPLETE", "Content targeting completed", {
                "targets": targets_info
            })
            
            # Pass 3: Content Retrieval
            await self._call_debug_callback("PASS_3_START", "Starting content retrieval", {
                "num_targets": len(targets)
            })
            
            try:
                content_task = asyncio.create_task(self.content_retriever.fetch_content(targets))
                content = await content_task
                
                content_summary = {}
                if isinstance(content, list):
                    content_summary["retrieved_items"] = len(content)
                    content_summary["source_types"] = [item.source_type.value if hasattr(item, 'source_type') else str(type(item)) for item in content]
                    
                    # Add more detailed summary
                    for item in content:
                        if hasattr(item, 'source_type') and hasattr(item, 'content'):
                            source_name = item.source_type.value
                            if isinstance(item.content, dict):
                                content_summary[f"{source_name}_files"] = list(item.content.keys())
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
                
            except Exception as e:
                await self._call_debug_callback("PASS_3_ERROR", f"Content retrieval failed: {str(e)}", {"error": str(e)})
                # Use empty content as fallback
                content = []
            
            # Pass 4: Response Generation
            content_types = [item.source_type.value for item in content] if isinstance(content, list) else []
            await self._call_debug_callback("PASS_4_START", "Starting response generation", {
                "content_available": content_types,
                "content_count": len(content) if isinstance(content, list) else 0
            })
            
            try:
                response_task = asyncio.create_task(self.response_generator.generate_response(
                    user_query, content
                ))
                response = await response_task
                
                await self._call_debug_callback("PASS_4_COMPLETE", "Response generation completed", {
                    "response_length": len(response),
                    "response_preview": response[:200] + "..." if len(response) > 200 else response
                })
                
                # Return structured response with source usage
                return {
                    "response": response,
                    "sourceUsage": {
                        "sources": used_sources,
                        "targets": self._format_targets_for_frontend(targets_info),
                        "content": content_summary,
                        "retrievedAt": time.time()
                    }
                }
                
            except Exception as e:
                await self._call_debug_callback("PASS_4_ERROR", f"Response generation failed: {str(e)}", {"error": str(e)})
                # Return a fallback error message
                return {
                    "response": f"I encountered an error while generating the response. The query was processed but I couldn't formulate an answer: {str(e)}",
                    "sourceUsage": {
                        "sources": used_sources,
                        "targets": self._format_targets_for_frontend(targets_info),
                        "content": content_summary,
                        "retrievedAt": time.time()
                    }
                }
            
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
            
            await self._call_debug_callback("ERROR", f"Error in query processing: {str(e)}", error_details)
            
            # Return a user-friendly error message
            return {
                "response": f"I encountered an error while processing your query. Please try rephrasing your question or try again later.",
                "sourceUsage": {
                    "sources": used_sources,
                    "targets": self._format_targets_for_frontend(targets_info),
                    "content": content_summary,
                    "retrievedAt": time.time()
                }
            }
    
    def _format_targets_for_frontend(self, targets_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format targets data for frontend consumption."""
        formatted_targets = {}
        
        for target_data in targets_info:
            source = target_data["source"]
            targets = target_data["targets"]
            
            if source == "character_data":
                # Handle character data - remove file_fields wrapper if present
                if isinstance(targets, dict) and "file_fields" in targets:
                    formatted_targets[source] = targets["file_fields"]
                else:
                    formatted_targets[source] = targets
            else:
                # For other sources, use as-is
                formatted_targets[source] = targets
        
        return formatted_targets
    
    def get_available_sources(self) -> Dict[str, Any]:
        """Get information about available knowledge sources."""
        return self.knowledge_base.get_source_overview()
    
    async def validate_query(self, user_query: str) -> bool:
        """Validate if a query can be processed by the system."""
        return len(user_query.strip()) > 0
    
    def update_model(self, model: str):
        """Update the OpenAI model used by all components."""
        self.current_model = model
        self.query_router.update_model(model)
        self.response_generator.update_model(model)
    
    def get_current_model(self) -> str:
        """Get the currently configured OpenAI model."""
        return self.current_model
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Get list of available OpenAI models."""
        return [
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "gpt-4o",
            "gpt-4o-mini",
            "o4-mini"
        ]