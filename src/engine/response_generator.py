"""
Simplified Response Generator - Cleaner Pass 4 implementation
"""

from typing import Dict, Any, List, Optional
import json
from ..utils.llm_client import LLMClient
from .content_retriever import RetrievedContent


class ResponseGenerator:
    """
    Simplified response generator that provides clear context to the LLM.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize response generator."""
        self.llm_client = LLMClient(model=model)
        self.debug_callback = None
    
    def set_debug_callback(self, callback):
        """Set debug callback."""
        self.debug_callback = callback
        if self.llm_client:
            self.llm_client.set_debug_callback(callback)
    
    async def generate_response(self, user_query: str, content: List[RetrievedContent]) -> str:
        """
        Generate response with retrieved content.
        Simplified approach with clear data presentation.
        """
        # Organize content by type
        organized_content = self._organize_content(content)
        
        # Create a clear, structured prompt
        prompt = self._create_response_prompt(user_query, organized_content)
        
        # Generate response
        response = await self.llm_client.generate_response(
            prompt,
            temperature=0.7,  # Slightly higher for more natural responses
            max_tokens=1500
        )
        
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
        """Extract and flatten character data for easier LLM consumption."""
        extracted = {}
        
        for filename, data in content.items():
            if not data or filename == "basic_info":
                continue
            
            # Flatten nested structures
            if isinstance(data, dict):
                # Handle different file structures
                if "character_base" in data:
                    extracted["character_info"] = data
                elif "inventory" in data:
                    extracted["equipment"] = data["inventory"]
                elif "character_spells" in data:
                    extracted["spells"] = data["character_spells"]
                elif "character_actions" in data:
                    extracted["actions"] = data["character_actions"]
                elif "features_and_traits" in data:
                    extracted["abilities"] = data["features_and_traits"]
                elif "objectives_and_contracts" in data:
                    extracted["quests"] = data["objectives_and_contracts"]
                else:
                    # Generic handling
                    key = filename.replace(".json", "").replace("_", " ")
                    extracted[key] = data
        
        return extracted
    
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
        prompt = f"""You are Duskryn Nightwarden's D&D assistant. Answer the following query using the provided data.

QUERY: {query}

"""
        
        # Add character data if available
        if "character" in content and content["character"]:
            prompt += "=== CHARACTER DATA ===\n"
            for section, data in content["character"].items():
                prompt += f"\n{section.upper()}:\n"
                if isinstance(data, dict):
                    # Format nested data nicely
                    prompt += self._format_dict(data, indent=1)
                elif isinstance(data, list):
                    prompt += self._format_list(data, indent=1)
                else:
                    prompt += f"  {data}\n"
            prompt += "\n"
        
        # Add rules data if available
        if "rules" in content and content["rules"]:
            prompt += "=== D&D RULES ===\n"
            if "relevant_rules" in content["rules"]:
                for rule in content["rules"]["relevant_rules"][:3]:  # Limit to top 3
                    if isinstance(rule, dict):
                        prompt += f"\n{rule.get('title', 'Rule')}:\n"
                        prompt += f"  {rule.get('content', rule.get('text', str(rule)))}\n"
                    else:
                        prompt += f"  {rule}\n"
            prompt += "\n"
        
        # Add session data if available
        if "sessions" in content and content["sessions"]:
            prompt += "=== CAMPAIGN CONTEXT ===\n"
            if "recent_session" in content["sessions"]:
                session = content["sessions"]["recent_session"]
                if isinstance(session, dict):
                    prompt += f"Recent Events: {session.get('summary', str(session))}\n"
                else:
                    prompt += f"Recent Events: {session}\n"
            
            # Add party member information if available
            if "party_members" in content["sessions"]:
                party_info = content["sessions"]["party_members"]
                if party_info:
                    prompt += "\nKnown Party Members:\n"
                    for member, actions in party_info.items():
                        prompt += f"  {member}:\n"
                        for action in actions[:3]:  # Limit to 3 most recent
                            prompt += f"    - {action}\n"
            
            prompt += "\n"
        
        prompt += """=== INSTRUCTIONS ===
1. Answer the query directly and accurately using the data provided
2. Include specific numbers, modifiers, and mechanics when relevant
3. Reference character abilities, items, or spells by name
4. Be helpful and concise
5. If data is missing, work with what's available

Character Summary: Duskryn is a Level 13 Hill Dwarf (Warlock 5/Paladin 8) with divine obligations to Ghul'Vor."""
        
        return prompt
    
    def _format_dict(self, data: dict, indent: int = 0) -> str:
        """Format dictionary data for readable output."""
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
                lines.append(f"{indent_str}{key}: {value}")
        
        return "\n".join(lines)
    
    def _format_list(self, data: list, indent: int = 0) -> str:
        """Format list data for readable output."""
        lines = []
        indent_str = "  " * indent
        
        for item in data[:5]:  # Limit lists to 5 items
            if isinstance(item, dict):
                # Extract key info from dict
                if "name" in item:
                    lines.append(f"{indent_str}- {item['name']}")
                elif "title" in item:
                    lines.append(f"{indent_str}- {item['title']}")
                else:
                    lines.append(f"{indent_str}- {str(item)[:100]}")
            else:
                lines.append(f"{indent_str}- {item}")
        
        if len(data) > 5:
            lines.append(f"{indent_str}... and {len(data) - 5} more")
        
        return "\n".join(lines)