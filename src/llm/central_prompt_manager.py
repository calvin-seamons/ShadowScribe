"""
Central Prompt Manager

Builds all prompts and coordinates between components. No LLM calls - just prompt generation 
and component coordination.
"""

from typing import Dict, Any, Optional
from src.rag.character.character_query_types import CharacterPromptHelper
from src.rag.rulebook.rulebook_types import RulebookPromptHelper
from src.rag.session_notes.session_types import SessionNotesPromptHelper


class CentralPromptManager:
    """Builds prompts and coordinates components - no LLM calls."""
    
    def __init__(self, context_assembler):
        """Initialize with context assembler."""
        self.context_assembler = context_assembler
    
    def get_tool_and_intention_selector_prompt(self, user_query: str, character_name: str, character=None, conversation_history=None) -> str:
        """
        Build prompt for Tool & Intention Selector LLM call (NEW ARCHITECTURE).
        
        This is the first of 2 parallel LLM calls that replace the old 3 sequential router calls.
        Returns which RAG tools are needed and what intention to use for each.
        
        Args:
            user_query: The user's question about their character
            character_name: Name of the character being queried
            character: Optional Character object for additional context
            conversation_history: Previous conversation turns for context
            
        Returns:
            Prompt string for the tool selector LLM
        """
        # Get intention definitions from each helper
        character_intents = CharacterPromptHelper.get_intent_definitions()
        session_intents = SessionNotesPromptHelper.get_intent_definitions()
        rulebook_intents = RulebookPromptHelper.get_intent_definitions()
        
        # Format intentions for prompt
        character_intentions_text = "\n".join([f"- {intent}: {definition}" for intent, definition in character_intents.items()])
        session_intentions_text = "\n".join([f"- {intent}: {definition}" for intent, definition in session_intents.items()])
        rulebook_intentions_text = "\n".join([f"- {intent}: {definition}" for intent, definition in rulebook_intents.items()])
        
        # Build inventory context if character is provided
        inventory_context = ""
        if character and hasattr(character, 'inventory') and character.inventory:
            inventory_items = []
            
            # Add equipped items
            if character.inventory.equipped_items:
                for slot, items in character.inventory.equipped_items.items():
                    for item in items:
                        if hasattr(item, 'definition') and hasattr(item.definition, 'name'):
                            item_type = getattr(item.definition, 'type', 'unknown')
                            inventory_items.append(f"  - {item.definition.name} ({item_type}) [equipped]")
            
            # Add backpack items
            if character.inventory.backpack:
                for item in character.inventory.backpack:
                    if hasattr(item, 'definition') and hasattr(item.definition, 'name'):
                        item_type = getattr(item.definition, 'type', 'unknown')
                        quantity = getattr(item, 'quantity', 1)
                        qty_str = f" x{quantity}" if quantity > 1 else ""
                        inventory_items.append(f"  - {item.definition.name} ({item_type}){qty_str}")
            
            if inventory_items:
                inventory_context = f"\n\n--- CONTEXT: {character_name}'s Inventory ---\n" + "\n".join(inventory_items)
                inventory_context += "\n--- END CONTEXT ---"
        
        history_context = ""
        if conversation_history and len(conversation_history) > 0:
            history_context = "\n\n--- CONVERSATION HISTORY ---\n"
            for turn in conversation_history[-5:]:
                role = turn.get('role', 'unknown').upper()
                content = turn.get('content', '')
                history_context += f"{role}: {content}\n"
            history_context += "--- END HISTORY ---\n"
        
        return f'''You are an expert D&D assistant analyzing what information sources are needed to answer a query.{history_context}

Current Query: "{user_query}"
Character: "{character_name}"

TASK: Determine which RAG tools are needed and what intention to use for each tool.

⚠️ CRITICAL: Select ONLY ONE intention per tool unless the query explicitly asks multiple distinct questions.
Most queries need just ONE tool with ONE intention. Multi-tool responses should be rare.

AVAILABLE TOOLS:
1. character_data - Character stats, inventory, spells, abilities, features
2. session_notes - Campaign history, past events, NPCs, decisions
3. rulebook - D&D rules, mechanics, spell descriptions, combat rules

TOOL SELECTION GUIDELINES:
- Select ONLY the tools actually needed to answer the query
- Most queries need 1-2 tools, rarely 3
- For specific items, weapons, or inventory: ALWAYS use character_data
- For NPCs or story characters: Use session_notes
- For general D&D rules: Use rulebook
- Queries use placeholders like {{CHARACTER}}, {{NPC}}, {{ITEM}}, {{SPELL}}, {{PARTY_MEMBER}}, {{LOCATION}}
- Examples:
  * "What's my AC?" → character_data only
  * "Tell me about {{NPC}}" → session_notes + character_data
  * "Tell me about {{ITEM}}" → character_data only
  * "How does grappling work?" → rulebook only
  * "What persuasion abilities do I have?" → character_data only
  * "Remind me about {{NPC}} and my persuasion abilities" → session_notes + character_data
  * "Tell me about {{ITEM}}" → character_data (inventory_info)

CHARACTER_DATA INTENTIONS (choose ONE per tool):
{character_intentions_text}

SESSION_NOTES INTENTIONS (choose ONE per tool):
{session_intentions_text}

RULEBOOK INTENTIONS (choose ONE per tool):
{rulebook_intentions_text}

EXAMPLES:

Query: "What combat abilities do I have tied to {{ITEM}}?"
Response: {{
  "tools_needed": [
    {{"tool": "character_data", "intention": "combat_info", "confidence": 0.95}}
  ]
}}

Query: "Remind me who {{NPC}} is and what persuasion abilities I have"
Response: {{
  "tools_needed": [
    {{"tool": "session_notes", "intention": "npc_history", "confidence": 0.95}},
    {{"tool": "character_data", "intention": "abilities_info", "confidence": 0.95}}
  ]
}}

Query: "How does grappling work and what's my athletics bonus?"
Response: {{
  "tools_needed": [
    {{"tool": "rulebook", "intention": "rule_mechanics", "confidence": 0.95}},
    {{"tool": "character_data", "intention": "abilities_info", "confidence": 0.90}}
  ]
}}

Query: "What spells can I cast?"
Response: {{
  "tools_needed": [
    {{"tool": "character_data", "intention": "magic_info", "confidence": 1.0}}
  ]
}}

Query: "Tell me about my weapon"
Response: {{
  "tools_needed": [
    {{"tool": "character_data", "intention": "inventory_info", "confidence": 0.95}}
  ]
}}

Query: "Tell me about {{ITEM}}"
Response: {{
  "tools_needed": [
    {{"tool": "character_data", "intention": "inventory_info", "confidence": 0.9}}
  ]
}}

Query: "What can you tell me about the {{ITEM}}?"
Response: {{
  "tools_needed": [
    {{"tool": "character_data", "intention": "inventory_info", "confidence": 0.8}},
    {{"tool": "rulebook", "intention": "item_details", "confidence": 0.7}}
  ]
}}

Query: "Tell me about {{CHARACTER}}'s backstory and his parents"
Response: {{
  "tools_needed": [
    {{"tool": "character_data", "intention": "backstory_info", "confidence": 1.0}}
  ]
}}

Query: "List all the actions {{CHARACTER}} can take"
Response: {{
  "tools_needed": [
    {{"tool": "character_data", "intention": "combat_info", "confidence": 0.95}}
  ]
}}

Return ONLY valid JSON:
{{
  "tools_needed": [
    {{
      "tool": "tool_name",
      "intention": "intention_name",
      "confidence": 0.0-1.0
    }}
  ]
}}

IMPORTANT: Return valid JSON only. No explanations.{inventory_context}'''

    def get_final_response_prompt(self, raw_results: Dict[str, Any], user_query: str) -> str:
        """
        Build the final response prompt using assembled context data.
        Creates a professional prompt that makes the AI act as an authoritative knowledge source.
        """
        import json
        
        context_sections = []
        
        # Process character data
        if "character" in raw_results and raw_results["character"]:
            char_result = raw_results["character"]
            
            if hasattr(char_result, 'character_data') and char_result.character_data:
                try:
                    def custom_serializer(obj):
                        """Custom serializer for complex objects"""
                        if hasattr(obj, '__dict__'):
                            return obj.__dict__
                        elif hasattr(obj, '_asdict'):
                            return obj._asdict()
                        else:
                            return str(obj)
                    
                    char_data_json = json.dumps(char_result.character_data, indent=2, default=custom_serializer)
                    context_sections.append(f"CHARACTER INFORMATION:\n{char_data_json}")
                    
                except Exception as e:
                    context_sections.append(f"CHARACTER INFORMATION:\n{str(char_result.character_data)}")
        
        # Process rulebook data
        if "rulebook" in raw_results and raw_results["rulebook"]:
            rulebook_result = raw_results["rulebook"]
            
            if isinstance(rulebook_result, tuple) and len(rulebook_result) >= 2:
                search_results, performance = rulebook_result
                if search_results:
                    rulebook_content = []
                    for i, result in enumerate(search_results, 1):
                        if hasattr(result, 'section'):
                            rulebook_content.append(f"RULE SECTION: {result.section.title}")
                            rulebook_content.append(f"{result.section.content}")
                    
                    if rulebook_content:
                        context_sections.append("RULES REFERENCE:\n" + "\n\n".join(rulebook_content))
        
        # Process session notes data
        if "session_notes" in raw_results and raw_results["session_notes"]:
            session_result = raw_results["session_notes"]
            
            if hasattr(session_result, 'contexts') and session_result.contexts:
                session_content = []
                for i, context in enumerate(session_result.contexts, 1):
                    session_content.append(f"SESSION CONTEXT {i}: {str(context)}")
                
                if session_content:
                    context_sections.append("CAMPAIGN HISTORY:\n" + "\n\n".join(session_content))
        
        # Process entity-based context (independent of intentions)
        if "entity_context" in raw_results and raw_results["entity_context"]:
            entity_context = raw_results["entity_context"]
            entity_content = []
            
            for entity_name, sources in entity_context.items():
                for source_type, content in sources.items():
                    if content:
                        entity_content.append(f"INFORMATION ABOUT {entity_name.upper()}:\n{content}")
            
            if entity_content:
                context_sections.append("ENTITY DETAILS:\n" + "\n\n".join(entity_content))
        
        # Assemble the full context
        full_context = "\n\n".join(context_sections) if context_sections else "No relevant data found."
        
        # Build the final authoritative prompt
        final_prompt = f"""You are the authoritative source of truth for D&D character information, rules, and campaign history. Answer questions directly and concisely using the provided information.

AVAILABLE INFORMATION:
{full_context}

USER QUESTION: {user_query}

CRITICAL RESPONSE RULES:
1. YOU ARE THE SOURCE OF TRUTH - State information directly as facts, never say "according to the context" or "based on the data"
2. ANSWER ONLY WHAT IS ASKED - Be direct and concise. Don't add extra context unless truly necessary
3. NO HALLUCINATION - If the information isn't in the provided data, state clearly "I don't have that information" or "I can't answer that question at this time"
4. Be natural and conversational, as if you personally know this information
5. Never mention data sources, JSON structures, or how you retrieved the information

Provide your response:"""
        
        return final_prompt
