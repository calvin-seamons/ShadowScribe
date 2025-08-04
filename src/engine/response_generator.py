"""
Response Generator - Handles Pass 4 (Response Generation) using retrieved context.
"""

from typing import Dict, Any, List, Optional
from ..utils.llm_client import LLMClient
from ..utils.prompt_templates.response_prompts import ResponsePrompts
from .content_retriever import RetrievedContent


class ResponseGenerator:
    """
    Handles Pass 4 of the query routing system:
    - Takes retrieved content and user query
    - Generates appropriate response using LLM
    - Formats response for user consumption
    """
    
    def __init__(self):
        """Initialize response generator with LLM client."""
        self.llm_client = LLMClient()
        self.response_prompts = ResponsePrompts()
        self.debug_callback = None
    
    def set_debug_callback(self, callback):
        """Set a callback function for debug logging."""
        self.debug_callback = callback
        if self.llm_client:
            self.llm_client.set_debug_callback(callback)
    
    async def generate_response(self, user_query: str, content: List[RetrievedContent]) -> str:
        """
        Generate final response based on query and retrieved content.
        
        Args:
            user_query: The original user question
            content: List of RetrievedContent objects from Pass 3
            
        Returns:
            Generated response string
        """
        # Convert list of RetrievedContent to formatted context
        formatted_context = self._format_content(content)
        
        # Generate appropriate prompt based on content type
        prompt = self.response_prompts.get_response_prompt(
            user_query, 
            formatted_context
        )
        
        # Generate response using LLM
        response = await self.llm_client.generate_response(prompt)
        
        return response
    
    def _format_content(self, content: List[RetrievedContent]) -> Dict[str, Any]:
        """Format retrieved content for prompt generation."""
        formatted = {}
        
        for item in content:
            source_type = item.source_type.value
            formatted[source_type] = {
                "content": item.content,
                "metadata": item.metadata
            }
        
        return formatted