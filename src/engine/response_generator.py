"""
Simplified Response Generator - Uses direct JSON parsing for all LLM interactions
"""

from typing import Dict, Any, List, Optional
import json
from ..utils.schema_driven_client import SchemaDrivenClient
from .content_retriever import RetrievedContent


class ResponseGenerator:
    """
    Simplified response generator that provides clear context to the LLM using direct JSON parsing.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize response generator."""
        self.schema_client = SchemaDrivenClient(model=model)
        self.debug_callback = None
    
    def set_debug_callback(self, callback):
        """Set debug callback."""
        self.debug_callback = callback
        if self.schema_client:
            self.schema_client.set_debug_callback(callback)
    
    def update_model(self, model: str):
        """Update the OpenAI model used by the schema client."""
        old_callback = self.schema_client.debug_callback if hasattr(self.schema_client, 'debug_callback') else None
        self.schema_client = SchemaDrivenClient(model=model)
        if old_callback:
            self.schema_client.set_debug_callback(old_callback)
    
    async def generate_response(self, user_query: str, content: List[RetrievedContent]) -> str:
        """
        Generate response with retrieved content.
        Simplified approach with clear data presentation.
        """
        print(f"[RESPONSE_GEN DEBUG] Starting response generation")
        print(f"[RESPONSE_GEN DEBUG] User query: {user_query}")
        print(f"[RESPONSE_GEN DEBUG] Content type: {type(content)}")
        print(f"[RESPONSE_GEN DEBUG] Content length: {len(content) if content else 0}")
        
        if content:
            for i, item in enumerate(content):
                print(f"[RESPONSE_GEN DEBUG] Content[{i}]: source_type={item.source_type}, content_keys={list(item.content.keys()) if hasattr(item, 'content') and isinstance(item.content, dict) else 'not dict'}")
        else:
            print(f"[RESPONSE_GEN DEBUG] No content provided!")
        
        # Organize content by type
        organized_content = self._organize_content(content)
        print(f"[RESPONSE_GEN DEBUG] Organized content keys: {list(organized_content.keys())}")
        
        # Create a clear, structured prompt
        prompt = self._create_response_prompt(user_query, organized_content)
        print(f"[RESPONSE_GEN DEBUG] Prompt length: {len(prompt)} characters")
        print(f"[RESPONSE_GEN DEBUG] Prompt preview: {prompt[:200]}...")
        
        # Generate response using schema client - NO TOKEN LIMITS FOR TESTING
        print(f"[RESPONSE_GEN DEBUG] Calling generate_natural_response with NO token limits")
        response = await self.schema_client.generate_natural_response(
            prompt,
            temperature=0.7  # No max_tokens limit for testing
        )
        
        print(f"[RESPONSE_GEN DEBUG] Generated response length: {len(response) if response else 0}")
        print(f"[RESPONSE_GEN DEBUG] Response preview: {response[:100] if response else 'None or empty'}...")
        
        return response
    
    def _organize_content(self, content: List[RetrievedContent]) -> Dict[str, Any]:
        """Organize retrieved content by type for clarity."""
        organized = {}
        
        for item in content:
            source_type = item.source_type.value
            
            # Extract the most relevant data
            if source_type == "character_data":
                organized["character"] = self._extract_character_data(item.content)
            elif source_type == "dnd_rulebook":
                organized["rules"] = self._extract_rulebook_data(item.content)
            elif source_type == "session_notes":
                organized["sessions"] = self._extract_session_data(item.content)
        
        return organized
    
    def _extract_character_data(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract character data - pass through the full JSON structure."""
        # Don't try to flatten or extract - just pass through the full data
        # The response_prompts will handle the JSON serialization
        return content
    
    def _extract_rulebook_data(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract rulebook sections and search results."""
        extracted = {}
        
        if "sections" in content:
            extracted["sections"] = content["sections"]
        
        if "search_results" in content:
            # Limit to top 5 most relevant results
            results = content["search_results"][:5] if isinstance(content["search_results"], list) else content["search_results"]
            extracted["relevant_rules"] = results
        
        return extracted
    
    def _extract_session_data(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract session notes."""
        extracted = {}
        
        for key, value in content.items():
            if value:
                if "latest" in key:
                    extracted["recent_session"] = value
                elif "keyword" in key:
                    extracted["relevant_events"] = value
                else:
                    extracted[key] = value
        
        return extracted
    
    def _create_response_prompt(self, query: str, content: Dict[str, Any]) -> str:
        """Create a clear, well-structured prompt for response generation."""
        # Import the response prompts that handle JSON properly
        from ..utils.prompt_templates.response_prompts import ResponsePrompts
        
        response_prompts = ResponsePrompts()
        
        # Format content for the response prompts
        formatted_context = {}
        
        # Add character data if available
        if "character" in content and content["character"]:
            formatted_context["character_data"] = {
                "content": content["character"]
            }
        
        # Add rules data if available
        if "rules" in content and content["rules"]:
            formatted_context["dnd_rulebook"] = {
                "content": content["rules"]
            }
        
        # Add session data if available  
        if "sessions" in content and content["sessions"]:
            formatted_context["session_notes"] = {
                "content": content["sessions"]
            }
        
        return response_prompts.get_response_prompt(query, formatted_context)
        

    
    def _format_dict(self, data: dict, indent: int = 0) -> str:
        """Format dictionary data for readable output - include ALL information."""
        lines = []
        indent_str = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{indent_str}{key}:")
                lines.append(self._format_dict(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{indent_str}{key}:")
                lines.append(self._format_list(value, indent + 1))
            else:
                # Include the full value, no truncation
                lines.append(f"{indent_str}{key}: {value}")
        
        return "\n".join(lines)
    
    def _format_list(self, data: list, indent: int = 0) -> str:
        """Format list data for readable output - include ALL information."""
        lines = []
        indent_str = "  " * indent
        
        # Include ALL items, not just first 5
        for i, item in enumerate(data):
            if isinstance(item, dict):
                # Include ALL dictionary content for each item
                if "name" in item:
                    lines.append(f"{indent_str}- {item['name']}:")
                    # Include ALL fields from the dictionary
                    for key, value in item.items():
                        if key != "name":  # Skip name since we already used it
                            if isinstance(value, dict):
                                lines.append(f"{indent_str}  {key}:")
                                lines.append(self._format_dict(value, indent + 2))
                            elif isinstance(value, list):
                                lines.append(f"{indent_str}  {key}:")
                                lines.append(self._format_list(value, indent + 2))
                            else:
                                lines.append(f"{indent_str}  {key}: {value}")
                else:
                    # For dictionaries without a name field, format the entire dict
                    lines.append(f"{indent_str}- Item {i + 1}:")
                    lines.append(self._format_dict(item, indent + 1))
            else:
                lines.append(f"{indent_str}- {item}")
        
        return "\n".join(lines)