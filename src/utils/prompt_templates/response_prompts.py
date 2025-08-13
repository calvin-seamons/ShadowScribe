"""
Response Prompts - Templates for Pass 4 response generation.
Uses minimal processing to provide raw JSON data to the LLM.
"""

from typing import Dict, Any, Optional
import json


class ResponsePrompts:
    """
    Contains prompt templates for Pass 4 response generation.
    Provides raw JSON data with minimal formatting to preserve accuracy.
    """
    
    def get_response_prompt(self, query: str, formatted_context: Dict[str, Any]) -> str:
        """
        Main entry point for generating response prompts.
        Uses minimal processing approach with raw JSON data.
        """
        return self.get_synthesis_prompt(query, formatted_context)
    
    def get_synthesis_prompt(self, query: str, formatted_context: Dict[str, Any]) -> str:
        """Generate the main synthesis prompt with minimal processing of raw JSON data."""
        
        prompt = f"""You are an intelligent D&D assistant. Use the following JSON data to answer the user's query accurately and helpfully.

User Query: "{query}"

"""
        
        # Add character data if available (raw JSON with minimal processing)
        character_data = formatted_context.get("character_data")
        if character_data and character_data.get("content"):
            prompt += "=== CHARACTER DATA (JSON) ===\n"
            prompt += json.dumps(character_data["content"], indent=2)
            prompt += "\n\n"
        
        # Add rulebook data if available (raw JSON with minimal processing)
        rulebook_data = formatted_context.get("dnd_rulebook")
        if rulebook_data and rulebook_data.get("content"):
            prompt += "=== D&D RULES REFERENCE (JSON) ===\n"
            prompt += json.dumps(rulebook_data["content"], indent=2)
            prompt += "\n\n"
        
        # Add session data if available (raw JSON with minimal processing)
        session_data = formatted_context.get("session_notes")
        if session_data and session_data.get("content"):
            prompt += "=== CAMPAIGN CONTEXT (JSON) ===\n"
            prompt += json.dumps(session_data["content"], indent=2)
            prompt += "\n\n"
        
        prompt += """=== RESPONSE INSTRUCTIONS ===
Using the JSON data above, provide a comprehensive answer that:
1. Directly addresses the user's question
2. Extracts relevant stats, modifiers, and mechanical details from the JSON
3. References specific abilities, spells, or equipment from the data
4. Uses campaign context when relevant
5. Provides clear, helpful guidance based on the character data

Important notes:
- Character data may include class levels, multiclass information, and progression
- Extract actual values from the JSON rather than making assumptions
- Calculate modifiers and bonuses based on the provided data
- Reference specific spell names, weapon stats, and abilities from the JSON
- Consider any character objectives, contracts, or goals when providing guidance
- Use the character's name from the JSON data when referencing them"""

        return prompt
    
    def get_quick_response_prompt(self, query: str, content_snippet: str) -> str:
        """Generate prompt for quick responses with minimal context."""
        return f"""You are a D&D assistant providing a quick answer to this query.

Query: "{query}"

Relevant Information (JSON):
{content_snippet}

Provide a concise, accurate answer based on the JSON data provided. Extract specific values and calculations as needed."""