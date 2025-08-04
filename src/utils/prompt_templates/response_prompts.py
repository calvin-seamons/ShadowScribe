"""
Response Prompts - Templates for Pass 4 response generation.
"""

from typing import Dict, Any, Optional
import json


class ResponsePrompts:
    """
    Contains prompt templates for Pass 4 response generation:
    - Synthesis prompts for combining retrieved content
    - Specialized prompts for combat, roleplay, etc.
    """
    
    def get_response_prompt(self, query: str, formatted_context: Dict[str, Any]) -> str:
        """
        Main entry point for generating response prompts.
        Routes to appropriate specialized prompt based on available context.
        """
        character_info = formatted_context.get("character_data", {}).get("content")
        rulebook_sections = formatted_context.get("dnd_rulebook", {}).get("content")
        session_context = formatted_context.get("session_notes", {}).get("content")
        
        return self.get_synthesis_prompt(
            query, character_info, rulebook_sections, session_context
        )
    
    def get_synthesis_prompt(self, query: str, character_info: Optional[Dict[str, Any]] = None, 
                           rulebook_sections: Optional[Dict[str, Any]] = None,
                           session_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate the main synthesis prompt for Pass 4."""
        
        prompt = f"""You are Duskryn Nightwarden's intelligent D&D assistant. Use the following information to answer the user's query accurately and helpfully.

User Query: "{query}"

"""
        
        # Add character information if available
        if character_info:
            prompt += "=== CHARACTER INFORMATION ===\n"
            prompt += self._format_character_info(character_info)
            prompt += "\n\n"
        
        # Add rulebook sections if available
        if rulebook_sections:
            prompt += "=== D&D RULES REFERENCE ===\n"
            prompt += self._format_rulebook_sections(rulebook_sections)
            prompt += "\n\n"
        
        # Add session context if available
        if session_context:
            prompt += "=== CAMPAIGN CONTEXT ===\n"
            prompt += self._format_session_context(session_context)
            prompt += "\n\n"
        
        prompt += """=== RESPONSE INSTRUCTIONS ===
Provide a comprehensive answer that:
1. Directly addresses the user's question
2. Includes relevant mechanical details (stats, DCs, damage, etc.) when applicable
3. Considers Duskryn's specific modifiers and abilities
4. References recent session events when relevant
5. Suggests tactical options or roleplay considerations when appropriate
6. Uses clear, helpful language that's easy to understand

Remember: You are specifically helping with Duskryn Nightwarden, a Level 13 Dwarf Warlock/Paladin multiclass character."""

        return prompt
    
    def get_quick_response_prompt(self, query: str, content_snippet: str) -> str:
        """Generate prompt for quick responses with minimal context."""
        return f"""You are a D&D assistant providing a quick answer to this query.

Query: "{query}"

Relevant Information:
{content_snippet}

Provide a concise, accurate answer based on the information provided. Focus on directly answering the question."""
    
    def get_combat_suggestion_prompt(self, query: str, character_info: Dict[str, Any], 
                                   rulebook_sections: Optional[Dict[str, Any]] = None) -> str:
        """Generate prompt for tactical combat suggestions."""
        prompt = f"""You are providing tactical combat advice for Duskryn Nightwarden in this D&D scenario.

Combat Scenario: "{query}"

=== CHARACTER COMBAT CAPABILITIES ===
{self._format_character_info(character_info)}

"""
        
        if rulebook_sections:
            prompt += "=== RELEVANT RULES ===\n"
            prompt += self._format_rulebook_sections(rulebook_sections)
            prompt += "\n\n"
        
        prompt += """=== TACTICAL ANALYSIS REQUESTED ===
Provide tactical suggestions considering:
1. Duskryn's available actions, spells, and abilities
2. Action economy optimization (action, bonus action, reaction)
3. Resource management (spell slots, Channel Divinity uses, etc.)
4. Positioning and battlefield control options
5. Risk/reward analysis of different approaches
6. Synergies between Warlock and Paladin abilities

Format your response with clear options and their expected outcomes."""

        return prompt
    
    def get_roleplay_suggestion_prompt(self, query: str, character_info: Dict[str, Any],
                                     session_context: Dict[str, Any]) -> str:
        """Generate prompt for roleplay suggestions."""
        prompt = f"""You are providing roleplay guidance for Duskryn Nightwarden in this D&D scenario.

Roleplay Situation: "{query}"

=== CHARACTER BACKGROUND ===
{self._format_character_background(character_info)}

=== RECENT CAMPAIGN EVENTS ===
{self._format_session_context(session_context)}

=== ROLEPLAY GUIDANCE REQUESTED ===
Provide suggestions considering:
1. Duskryn's personality traits, ideals, bonds, and flaws
2. His background as a Holy Knight of Kluntul and follower of Ethernea
3. Recent story developments and character growth
4. Relationships with NPCs and party members
5. Internal conflicts between his Paladin and Warlock nature
6. His obsession with balance between light and darkness

Suggest dialogue options, character motivations, and potential character development opportunities."""

        return prompt
    
    def _format_character_info(self, character_info: Dict[str, Any]) -> str:
        """Format character information for prompts."""
        formatted = ""
        
        # Basic info from different files
        for filename, data in character_info.items():
            if filename == "character.json" and data:
                basic = data.get("character_base", {})
                abilities = data.get("ability_scores", {})
                combat = data.get("combat_stats", {})
                
                formatted += f"Name: {basic.get('name', 'Unknown')}\n"
                formatted += f"Race: {basic.get('race', '')} {basic.get('subrace', '')}\n" 
                formatted += f"Class: {basic.get('class', '')} (Level {basic.get('total_level', 1)})\n"
                formatted += f"HP: {combat.get('current_hp', 0)}/{combat.get('max_hp', 0)}\n"
                formatted += f"AC: {combat.get('armor_class', 10)}\n"
                
                if abilities:
                    formatted += f"Ability Scores: STR {abilities.get('strength', 10)}, "
                    formatted += f"DEX {abilities.get('dexterity', 10)}, "
                    formatted += f"CON {abilities.get('constitution', 10)}, "
                    formatted += f"INT {abilities.get('intelligence', 10)}, "
                    formatted += f"WIS {abilities.get('wisdom', 10)}, "
                    formatted += f"CHA {abilities.get('charisma', 10)}\n"
            
            elif filename == "spell_list.json" and data:
                spellcasting = data.get("spellcasting", {})
                if spellcasting:
                    formatted += "Available Spells:\n"
                    for class_name, class_spells in spellcasting.items():
                        formatted += f"  {class_name.title()}: {len(class_spells.get('spells', {}))} spells\n"
            
            elif filename == "action_list.json" and data:
                actions = data.get("character_actions", {})
                if actions:
                    formatted += f"Attacks per Action: {actions.get('attacks_per_action', 1)}\n"
        
        return formatted
    
    def _format_character_background(self, character_info: Dict[str, Any]) -> str:
        """Format character background information."""
        formatted = ""
        
        background_data = character_info.get("character_background.json", {})
        if background_data:
            chars = background_data.get("characteristics", {})
            formatted += f"Alignment: {chars.get('alignment', 'Unknown')}\n"
            
            traits = chars.get("personality_traits", [])
            if traits:
                formatted += "Personality Traits:\n"
                for trait in traits:
                    formatted += f"  - {trait}\n"
            
            ideals = chars.get("ideals", [])
            if ideals:
                formatted += "Ideals:\n"
                for ideal in ideals:
                    formatted += f"  - {ideal}\n"
            
            bonds = chars.get("bonds", [])
            if bonds:
                formatted += "Bonds:\n"
                for bond in bonds:
                    formatted += f"  - {bond}\n"
            
            flaws = chars.get("flaws", [])
            if flaws:
                formatted += "Flaws:\n"
                for flaw in flaws:
                    formatted += f"  - {flaw}\n"
        
        return formatted
    
    def _format_rulebook_sections(self, rulebook_sections: Dict[str, Any]) -> str:
        """Format rulebook sections for prompts."""
        formatted = ""
        
        sections = rulebook_sections.get("sections", [])
        for section in sections:
            title = section.get("title", "Unknown Section")
            content = section.get("content", "")
            formatted += f"**{title}**:\n{content}\n\n"
        
        search_results = rulebook_sections.get("search_results", [])
        for result in search_results:
            title = result.get("title", "Unknown")
            path = result.get("path", "")
            formatted += f"**{title}** ({path})\n"
        
        return formatted
    
    def _format_session_context(self, session_context: Dict[str, Any]) -> str:
        """Format session context for prompts."""
        formatted = ""
        
        latest_session = session_context.get("latest_session")
        if latest_session:
            formatted += f"Latest Session: {latest_session.get('title', 'Untitled')}\n"
            formatted += f"Date: {latest_session.get('date', 'Unknown')}\n"
            summary = latest_session.get('summary', '')
            if summary:
                formatted += f"Summary: {summary}\n"
            
            key_events = latest_session.get('key_events', [])
            if key_events:
                formatted += "Key Events:\n"
                for event in key_events[:3]:  # Limit to top 3 events
                    formatted += f"  - {event}\n"
        
        # Add other sessions if present
        for key, session_data in session_context.items():
            if key.startswith("session_") and isinstance(session_data, dict):
                formatted += f"\nSession {session_data.get('date', 'Unknown')}:\n"
                formatted += f"Title: {session_data.get('title', 'Untitled')}\n"
                summary = session_data.get('summary', '')
                if summary:
                    formatted += f"Summary: {summary[:200]}...\n"
        
        return formatted