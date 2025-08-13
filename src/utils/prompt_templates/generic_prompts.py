"""
Generic Prompt Templates - Schema-driven prompts without character-specific content.
"""

from typing import Dict, Any, List


class GenericPrompts:
    """
    Contains generic prompt templates for the query router:
    - Pass 1: Source selection prompts
    - Pass 2: Content targeting prompts
    - Response generation prompts
    """
    
    def get_source_selection_prompt(self, user_query: str) -> str:
        """Generate prompt for Pass 1 - source selection."""
        return f"""You are an intelligent assistant analyzing a user query to determine which knowledge sources are needed.

Available Sources:
- dnd_rulebook: Game system reference document (rules, spells, monsters, items, combat mechanics)
- character_data: Character information files (stats, equipment, abilities, background, objectives, actions, inventory, features, spells)
- session_notes: Previous session summaries and campaign narrative (events, NPCs, story context)

User Query: "{user_query}"

Analyze this query and determine which sources you need. Consider:
- Rules questions need dnd_rulebook
- Character-specific questions need character_data
- Story/narrative questions need session_notes
- Combat planning often needs both rules and character data
- Complex questions may need multiple sources

Return a JSON response:
{{
  "sources_needed": ["dnd_rulebook", "character_data", "session_notes"],
  "reasoning": "Detailed explanation of why each source is needed for this specific query"
}}"""
    
    def get_rulebook_targeting_prompt(self, user_query: str) -> str:
        """Generate prompt for Pass 2A - rulebook content targeting."""
        return f"""You are targeting specific sections within the game system reference document to answer this query.

Query: "{user_query}"

The system reference document contains organized sections covering:
- Rules (combat, spellcasting, conditions, etc.)
- Spells (organized by level and class)
- Equipment (weapons, armor, magic items)
- Character options (races, classes, backgrounds)
- Monsters and NPCs
- Adventure content

You have access to a searchable index with section IDs and keywords. Target the most relevant sections.

Common keywords for different topics:
- Spells: spell names, "spellcasting", "concentration", "verbal", "somatic"
- Combat: "attack", "damage", "armor class", "initiative", "action", "reaction"
- Character mechanics: race names, class names, "ability scores", "proficiency"

Return JSON with specific sections to retrieve:
{{
  "section_ids": ["abc123", "def456"],
  "keywords": ["counterspell", "reaction", "spellcasting"],
  "reasoning": "Why these specific sections will answer the query"
}}"""
    
    def get_character_targeting_prompt(self, user_query: str, available_files: List[str]) -> str:
        """Generate prompt for Pass 2B - character data targeting."""
        
        # Generate file descriptions
        file_descriptions = []
        for filename in available_files:
            # Create generic descriptions based on filename patterns
            if "character" in filename and "background" not in filename:
                file_descriptions.append(f"- {filename}: Basic character information (stats, abilities, combat data, proficiencies)")
            elif "background" in filename:
                file_descriptions.append(f"- {filename}: Character backstory, personality, relationships, history")
            elif "inventory" in filename:
                file_descriptions.append(f"- {filename}: Equipment, weapons, armor, items, currency")
            elif "spell" in filename:
                file_descriptions.append(f"- {filename}: Known spells, spell slots, spellcasting abilities")
            elif "action" in filename:
                file_descriptions.append(f"- {filename}: Combat actions, attacks, special abilities")
            elif "feat" in filename or "trait" in filename:
                file_descriptions.append(f"- {filename}: Class features, racial traits, feats, abilities")
            elif "objective" in filename or "contract" in filename:
                file_descriptions.append(f"- {filename}: Active quests, objectives, contracts, goals")
            else:
                file_descriptions.append(f"- {filename}: Character data file")
        
        files_text = "\n".join(file_descriptions)
        
        return f"""You are targeting specific character data to answer this query.

Query: "{user_query}"

Available character files:
{files_text}

Consider what specific data is needed:
- Combat questions: combat stats, actions, equipment, spells
- Character building: features, abilities, progression options
- Roleplay: background, personality, relationships, objectives
- Rules interactions: specific abilities and their mechanics
- Quest/story context: objectives, contracts, background information

You MUST respond with BOTH file_fields AND reasoning. The response MUST include:

1. file_fields: A dictionary mapping filenames to lists of field names (use "*" for all data or specific field paths)
2. reasoning: A string explaining your choices

Example response format:
{{
  "file_fields": {{
    "inventory_list.json": ["*"],
    "character.json": ["*"],
    "objectives_and_contracts.json": ["*"]
  }},
  "reasoning": "Need inventory for equipment info, character data for stats, and objectives for quest context"
}}

CRITICAL: You must include BOTH file_fields and reasoning in your response."""
    
    def get_session_targeting_prompt(self, user_query: str) -> str:
        """Generate prompt for Pass 2C - session notes targeting."""
        return f"""You are targeting specific session notes to provide context for this query.

Query: "{user_query}"

Available sessions contain:
- Session summaries and key events
- NPCs encountered and interactions
- Locations visited
- Combat encounters and character decisions
- Story progression and developments

Consider:
- Recent events are usually more relevant
- Specific NPCs or locations mentioned in the query
- Story continuity and character development
- Combat or decision consequences

Return JSON specifying which sessions to retrieve:
{{
  "session_dates": ["06-30-25", "latest"],
  "keywords": ["npc_name", "location", "event"],
  "reasoning": "Why these sessions provide relevant context for the query"
}}"""
    
    def get_response_generation_prompt(self, user_query: str, content: Dict[str, Any]) -> str:
        """Generate prompt for final response generation."""
        
        prompt = f"""You are a helpful assistant providing information based on the available data.

User Query: "{user_query}"

Available Information:
"""
        
        # Add character data if available
        if "character" in content and content["character"]:
            prompt += "=== CHARACTER DATA ===\n"
            for section, data in content["character"].items():
                prompt += f"\n{section.upper()}:\n"
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, (str, int, float, bool)):
                            prompt += f"  {key}: {value}\n"
                        elif isinstance(value, list) and value:
                            prompt += f"  {key}: {len(value)} items\n"
                        elif isinstance(value, dict) and value:
                            prompt += f"  {key}: {len(value)} entries\n"
                elif isinstance(data, list):
                    prompt += f"  {len(data)} items available\n"
                else:
                    prompt += f"  {data}\n"
        
        # Add rules data if available
        if "rules" in content and content["rules"]:
            prompt += "\n=== RULES REFERENCE ===\n"
            rules_data = content["rules"]
            if isinstance(rules_data, dict):
                for section, data in rules_data.items():
                    prompt += f"\n{section.upper()}:\n"
                    if isinstance(data, str):
                        prompt += f"{data[:500]}...\n" if len(data) > 500 else f"{data}\n"
                    elif isinstance(data, list):
                        for item in data[:3]:  # Show first 3 items
                            if isinstance(item, dict) and "content" in item:
                                content_text = item["content"]
                                prompt += f"- {content_text[:200]}...\n" if len(content_text) > 200 else f"- {content_text}\n"
        
        # Add session data if available
        if "sessions" in content and content["sessions"]:
            prompt += "\n=== SESSION CONTEXT ===\n"
            sessions_data = content["sessions"]
            if isinstance(sessions_data, dict):
                for session, data in sessions_data.items():
                    prompt += f"\n{session.upper()}:\n"
                    if isinstance(data, str):
                        prompt += f"{data[:300]}...\n" if len(data) > 300 else f"{data}\n"
        
        prompt += f"""

Instructions:
1. Answer the user's query using the available information
2. Be specific and reference actual data when possible
3. Use clear formatting with headers, lists, and emphasis where appropriate
4. Include specific numbers, modifiers, and mechanics when relevant
5. When presenting multiple options or comparisons, use organized lists
6. For complex information, use step-by-step formatting
7. Always include a brief summary if the response is long
8. If information is missing or incomplete, acknowledge this clearly

Remember: Your response will be rendered as Markdown, so use formatting to make it clear and visually appealing."""

        return prompt