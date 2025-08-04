"""
Response Generator - Handles Pass 4 (Response Generation) using retrieved content.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

from .content_retriever import RetrievedContent
from ..utils.prompt_templates.response_prompts import ResponsePrompts
from ..utils.llm_client import LLMClient


@dataclass
class ResponseContext:
    """Context package for response generation."""
    user_query: str
    retrieved_content: List[RetrievedContent]
    character_info: Optional[Dict[str, Any]] = None
    rulebook_sections: Optional[Dict[str, Any]] = None
    session_context: Optional[Dict[str, Any]] = None


class ResponseGenerator:
    """
    Handles Pass 4 of the query routing system:
    - Synthesizes retrieved content into comprehensive responses
    - Maintains character-specific context
    - Provides tactical and roleplay suggestions
    """
    
    def __init__(self):
        """Initialize response generator with LLM client and prompt templates."""
        self.llm_client = LLMClient()
        self.response_prompts = ResponsePrompts()
    
    async def generate_response(self, user_query: str, retrieved_content: List[RetrievedContent]) -> str:
        """
        Generate a comprehensive response using retrieved content.
        
        Args:
            user_query: The original user question
            retrieved_content: Content retrieved in Pass 3
            
        Returns:
            Generated response addressing the user's query
        """
        try:
            # Organize retrieved content by type
            context = self._organize_content(user_query, retrieved_content)
            
            # Generate response using organized context
            response = await self._synthesize_response(context)
            
            # Post-process response for clarity and accuracy
            final_response = self._post_process_response(response, context)
            
            return final_response
            
        except Exception as e:
            return f"I encountered an error generating your response: {str(e)}. Please try rephrasing your question."
    
    def _organize_content(self, user_query: str, retrieved_content: List[RetrievedContent]) -> ResponseContext:
        """Organize retrieved content into structured context for response generation."""
        character_info = None
        rulebook_sections = None
        session_context = None
        
        for content in retrieved_content:
            if content.source_type.value == "character_data":
                character_info = content.content
            elif content.source_type.value == "dnd_rulebook":
                rulebook_sections = content.content
            elif content.source_type.value == "session_notes":
                session_context = content.content
        
        return ResponseContext(
            user_query=user_query,
            retrieved_content=retrieved_content,
            character_info=character_info,
            rulebook_sections=rulebook_sections,
            session_context=session_context
        )
    
    async def _synthesize_response(self, context: ResponseContext) -> str:
        """Generate response using LLM with organized context."""
        # Build the prompt with all available context
        prompt = self.response_prompts.get_synthesis_prompt(
            query=context.user_query,
            character_info=context.character_info,
            rulebook_sections=context.rulebook_sections,
            session_context=context.session_context
        )
        
        # Generate response
        response = await self.llm_client.generate_response(prompt)
        return response
    
    def _post_process_response(self, response: str, context: ResponseContext) -> str:
        """Post-process the response for accuracy and formatting."""
        # Add any necessary disclaimers or clarifications
        processed_response = response
        
        # Add character context note if relevant
        if context.character_info and "duskryn" not in response.lower():
            processed_response += "\n\n*Note: This information is specific to Duskryn Nightwarden, your Level 13 Dwarf Warlock/Paladin.*"
        
        # Add source attribution if multiple sources used
        sources_used = []
        for content in context.retrieved_content:
            source_name = content.metadata.get("source", content.source_type.value)
            if source_name not in sources_used:
                sources_used.append(source_name)
        
        if len(sources_used) > 1:
            processed_response += f"\n\n*Sources consulted: {', '.join(sources_used)}*"
        
        return processed_response
    
    async def generate_quick_response(self, user_query: str, content_snippet: str) -> str:
        """Generate a quick response for simple queries with minimal context."""
        prompt = self.response_prompts.get_quick_response_prompt(user_query, content_snippet)
        response = await self.llm_client.generate_response(prompt)
        return response
    
    async def generate_combat_suggestion(self, context: ResponseContext) -> str:
        """Generate tactical combat suggestions based on character abilities and situation."""
        if not context.character_info:
            return "I need character information to provide tactical suggestions."
        
        prompt = self.response_prompts.get_combat_suggestion_prompt(
            query=context.user_query,
            character_info=context.character_info,
            rulebook_sections=context.rulebook_sections
        )
        
        response = await self.llm_client.generate_response(prompt)
        return response
    
    async def generate_roleplay_suggestion(self, context: ResponseContext) -> str:
        """Generate roleplay suggestions based on character background and session context."""
        if not context.character_info or not context.session_context:
            return "I need character background and session context to provide roleplay suggestions."
        
        prompt = self.response_prompts.get_roleplay_suggestion_prompt(
            query=context.user_query,
            character_info=context.character_info,
            session_context=context.session_context
        )
        
        response = await self.llm_client.generate_response(prompt)
        return response