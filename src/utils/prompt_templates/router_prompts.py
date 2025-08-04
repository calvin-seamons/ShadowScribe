"""
Router Prompts - Templates for Pass 1 and Pass 2 of the query routing system.
"""

from typing import Dict, Any, List


class RouterPrompts:
    """
    Contains prompt templates for the query router:
    - Pass 1: Source selection prompts
    - Pass 2: Content targeting prompts
    """
    
    def get_source_selection_prompt(self, user_query: str) -> str:
        """Generate prompt for Pass 1 - source selection."""
        return f"""You are an intelligent D&D assistant analyzing a user query to determine which knowledge sources are needed.

Available Sources:
- dnd_rulebook: D&D 5e System Reference Document (2,098 sections covering rules, spells, monsters, items, combat mechanics)
- character_data: Current character information (stats, equipment, abilities, background, objectives and contracts, actions, inventory, feats and traits, spell list)
- session_notes: Previous session summaries and campaign narrative (available dates with NPCs, events, story context)

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
        return f"""You are targeting specific sections within the D&D 5e SRD to answer this query.

Query: "{user_query}"

The D&D SRD contains 2,098 sections organized into categories like:
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
    
    def get_character_targeting_prompt(self, user_query: str) -> str:
        """Generate prompt for Pass 2B - character data targeting."""
        return f"""You are targeting specific character data to answer this query about Duskryn Nightwarden.

Query: "{user_query}"

Available character files and their contents:
- character.json: Basic stats (name, race, class, level, ability scores, combat stats, proficiencies)
  - Fields: character_base, characteristics, ability_scores, combat_stats, proficiencies
- inventory_list.json: Equipment (weapons, armor, consumables, magical items like Eldaryth of Regret)
  - Fields: inventory.equipped_items, inventory.weapons, inventory.armor, inventory.consumables
- feats_and_traits.json: Class features (Paladin 8/Warlock 5), racial traits, feats (Lucky, Fey Touched)
  - Fields: features_and_traits.class_features, features_and_traits.species_traits, features_and_traits.feats
- spell_list.json: Available spells by class (Paladin and Warlock spells, cantrips)
  - Fields: character_spells.paladin_spells, character_spells.warlock_spells, character_spells.cantrips
- action_list.json: Combat actions (attacks, spells, Channel Divinity, special abilities)
  - Fields: character_actions.action_economy, character_actions.attacks_per_action
- character_background.json: Backstory, personality, allies, enemies (includes Battle of Shadow's Edge)
  - Fields: background, personality, allies, enemies
- objectives_and_contracts.json: Active contracts, completed objectives, divine covenants (including The Covenant of Eternal Service with Ghul'Vor)
  - Fields: objectives_and_contracts.active_contracts, objectives_and_contracts.current_objectives, objectives_and_contracts.completed_objectives

Consider what specific data is needed:
- Combat questions: combat_stats, character_actions.action_economy, inventory.equipped_items, character_spells
- Character building: features_and_traits, ability_scores, progression options
- Roleplay: background, personality, allies, enemies, objectives_and_contracts
- Rules interactions: specific abilities and their mechanics
- Quest/story context: objectives_and_contracts.active_contracts, objectives_and_contracts.completed_objectives

You MUST respond with BOTH file_fields AND reasoning. The response MUST include:

1. file_fields: A dictionary mapping filenames to lists of field names (use dot notation for nested fields)
2. reasoning: A string explaining your choices

Example response format:
{{
  "file_fields": {{
    "inventory_list.json": ["inventory.weapons", "inventory.equipped_items"],
    "character.json": ["combat_stats"],
    "objectives_and_contracts.json": ["objectives_and_contracts.active_contracts"]
  }},
  "reasoning": "Need inventory for weapons list, character stats for combat calculations, and active contracts for quest context"
}}

CRITICAL: You must include BOTH file_fields and reasoning in your response."""
    
    def get_session_targeting_prompt(self, user_query: str) -> str:
        """Generate prompt for Pass 2C - session notes targeting."""
        return f"""You are targeting specific session notes to provide context for this query.

Query: "{user_query}"

Available sessions contain:
- Session summaries and key events
- NPCs encountered (including Ghul'Vor, High Acolyte Aldric, etc.)
- Locations visited
- Combat encounters and character decisions
- Story progression and cliffhangers

Recent notable events include:
- Duskryn's soul being trapped in a mirror during the Black Benediction ritual
- Interactions with Ghul'Vor (ex-god of darkness)
- The Theater of Blood incident
- Various NPCs and story developments

Consider:
- Recent events are usually more relevant
- Specific NPCs or locations mentioned in the query
- Story continuity and character development
- Combat or decision consequences

Return JSON specifying which sessions to retrieve:
{{
  "session_dates": ["06-30-25", "latest"],
  "keywords": ["ghul'vor", "ritual", "soul"],
  "reasoning": "Why these sessions provide relevant context for the query"
}}"""