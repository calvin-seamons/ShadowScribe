"""
Balanced Query Router - Uses function calling with keyword hints for optimization
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import re

from ..utils.llm_client import LLMClient
from ..utils.response_models import (
    SourceSelectionResponse, 
    RulebookTargetResponse,
    CharacterTargetResponse, 
    SessionTargetResponse,
    SourceTypeEnum
)


class SourceType(Enum):
    """Available knowledge source types."""
    DND_RULEBOOK = "dnd_rulebook"
    CHARACTER_DATA = "character_data"
    SESSION_NOTES = "session_notes"


@dataclass
class SourceSelection:
    """Result of Pass 1 - which sources are needed."""
    sources_needed: List[SourceType]
    reasoning: str
    confidence: float  # 0.0 to 1.0


@dataclass
class ContentTarget:
    """Specific content to retrieve from a source."""
    source_type: SourceType
    specific_targets: Dict[str, Any]
    reasoning: str


class QueryRouter:
    """
    Balanced router that uses function calling as primary method,
    with keyword hints for optimization and better prompting.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize the query router."""
        self.llm_client = LLMClient(model=model)
        
        # Keyword patterns used as HINTS, not decisions
        self.hint_patterns = {
            'rules': re.compile(r'\b(rule|spell|action|attack|damage|save|dc|ac|hp|concentration|ritual)\b', re.I),
            'character': re.compile(r'\b(my|i|character|stats|equipment|inventory|eldaryth)\b', re.I),
            'session': re.compile(r'\b(last session|previous session|story|npc|quest|ghul\'?vor|mirror)\b', re.I),
            'combat': re.compile(r'\b(attack|damage|initiative|combat|fight|smite|hex)\b', re.I),
            'complex': re.compile(r'\b(how can i|what if|combination|together with|and also)\b', re.I)
        }
    
    def set_debug_callback(self, callback):
        """Set debug callback."""
        self.llm_client.set_debug_callback(callback)
    
    async def select_sources(self, user_query: str) -> SourceSelection:
        """
        Pass 1: Use function calling to determine sources.
        Keywords provide hints to improve prompting, not replace LLM judgment.
        """
        # Get keyword hints (but don't rely on them exclusively)
        keyword_hints = self._get_keyword_hints(user_query)
        
        # Always use function calling for accurate source selection
        prompt = self._create_enhanced_source_prompt(user_query, keyword_hints)
        
        try:
            response = await self.llm_client.generate_structured_response(
                prompt, 
                SourceSelectionResponse,
                max_retries=2  # Reasonable retries
            )
            
            sources = [SourceType(s.value) for s in response.sources_needed]
            
            # Calculate confidence based on alignment with hints
            confidence = self._calculate_confidence(sources, keyword_hints)
            
            return SourceSelection(
                sources_needed=sources,
                reasoning=response.reasoning,
                confidence=confidence
            )
            
        except Exception as e:
            # Fallback uses keyword hints + safe defaults
            return self._create_fallback_selection(user_query, keyword_hints, str(e))
    
    def _get_keyword_hints(self, query: str) -> Set[str]:
        """Get keyword hints without making decisions."""
        hints = set()
        
        for hint_type, pattern in self.hint_patterns.items():
            if pattern.search(query):
                hints.add(hint_type)
        
        # Complex queries likely need multiple sources
        if self.hint_patterns['complex'].search(query) or len(query) > 100:
            hints.add('complex')
        
        return hints
    
    def _create_enhanced_source_prompt(self, query: str, hints: Set[str]) -> str:
        """Create an enhanced prompt with keyword hints to guide the LLM."""
        
        # Add hints to help the LLM
        hint_text = ""
        if hints:
            hint_text = f"\nQuery characteristics detected: {', '.join(hints)}"
            if 'complex' in hints:
                hint_text += "\nThis appears to be a complex query that may need multiple sources."
        
        return f"""Analyze this D&D query to determine which knowledge sources are needed.

User Query: "{query}"{hint_text}

Available Sources:
1. dnd_rulebook: Complete D&D 5e rules, spells, mechanics, conditions, combat rules
   - Use for: game mechanics, spell descriptions, rule clarifications, general D&D knowledge
   
2. character_data: Duskryn Nightwarden (Level 13 Hill Dwarf Paladin 8/Warlock 5)
   - Files: stats, inventory (including Eldaryth), spells, actions, feats, background, objectives
   - Use for: character-specific questions, build optimization, equipment, personal abilities
   
3. session_notes: Campaign history and narrative
   - Contains: NPCs (Ghul'Vor, etc.), story events, quest progress, past decisions
   - Use for: story context, NPC information, campaign-specific events

Important considerations:
- "My" or "I" in the query usually refers to Duskryn's character
- Combat optimization often needs both rules AND character data
- Story questions need session notes even if they mention character actions
- Spell questions may need rules (general) AND character data (specific spells known)
- Always include all sources that could contribute to a complete answer

Return a JSON response with sources_needed and detailed reasoning."""
    
    async def target_content(self, user_query: str, sources: SourceSelection) -> List[ContentTarget]:
        """
        Pass 2: Use function calling for precise targeting.
        High confidence = more focused, low confidence = broader retrieval.
        """
        targets = []
        
        for source_type in sources.sources_needed:
            try:
                if source_type == SourceType.DND_RULEBOOK:
                    target = await self._target_rulebook_content(user_query, sources.confidence)
                elif source_type == SourceType.CHARACTER_DATA:
                    target = await self._target_character_content(user_query, sources.confidence)
                elif source_type == SourceType.SESSION_NOTES:
                    target = await self._target_session_content(user_query, sources.confidence)
                else:
                    continue
                    
                targets.append(target)
                
            except Exception as e:
                # Create broad fallback target
                targets.append(self._create_broad_target(source_type, user_query))
        
        return targets
    
    async def _target_rulebook_content(self, query: str, confidence: float) -> ContentTarget:
        """Target rulebook with function calling."""
        prompt = f"""Target specific D&D 5e rulebook sections for this query.

Query: "{query}"

The rulebook has 2,098 sections covering:
- Combat mechanics (actions, attacks, damage, conditions)
- Spellcasting (spell descriptions, components, concentration)
- Character creation and advancement
- Equipment and magic items
- Monsters and NPCs

Based on the query, identify:
1. Specific section IDs if you know them
2. Keywords to search for (spell names, rule terms, mechanics)

Be {'precise' if confidence > 0.7 else 'comprehensive'} in your targeting.

Return section_ids (if known) and keywords for searching."""
        
        response = await self.llm_client.generate_structured_response(
            prompt, RulebookTargetResponse, max_retries=1
        )
        
        return ContentTarget(
            source_type=SourceType.DND_RULEBOOK,
            specific_targets={
                "section_ids": response.section_ids,
                "keywords": response.keywords
            },
            reasoning=response.reasoning
        )
    
    async def _target_character_content(self, query: str, confidence: float) -> ContentTarget:
        """Target character data with function calling."""
        # Build comprehensive prompt with ALL available files
        prompt = f"""Target specific character data files for Duskryn Nightwarden.

Query: "{query}"

Available character files and their contents:
1. character.json - Core stats
   - character_base (name, race, classes, level)
   - ability_scores (STR, DEX, CON, INT, WIS, CHA)
   - combat_stats (AC, HP, initiative, speed, proficiency)
   - proficiencies (saves, skills, tools, languages)

2. inventory_list.json - All equipment
   - inventory.equipped_items (currently worn/wielded)
   - inventory.weapons (including Eldaryth of Regret)
   - inventory.armor (plate mail, etc.)
   - inventory.consumables (potions, scrolls)
   - inventory.other_items (general equipment)

3. spell_list.json - All known spells
   - character_spells.paladin_spells (by level)
   - character_spells.warlock_spells (by level)
   - character_spells.cantrips
   - character_spells.spell_slots

4. action_list.json - Combat actions
   - character_actions.action_economy (what can be done when)
   - character_actions.attacks_per_action
   - character_actions.special_abilities (Divine Smite, Hex, etc.)

5. feats_and_traits.json - Abilities
   - features_and_traits.class_features (Paladin/Warlock abilities)
   - features_and_traits.species_traits (Hill Dwarf traits)
   - features_and_traits.feats (Lucky, Fey Touched)

6. character_background.json - Roleplay info
   - background (history, story)
   - personality (traits, ideals, bonds, flaws)
   - allies (friendly NPCs)
   - enemies (hostile NPCs)

7. objectives_and_contracts.json - Quests
   - objectives_and_contracts.active_contracts
   - objectives_and_contracts.current_objectives
   - objectives_and_contracts.completed_objectives
   - objectives_and_contracts.divine_covenants (Ghul'Vor pact)

Select the files and specific fields needed. Use dot notation for nested fields.
Be {'selective' if confidence > 0.7 else 'inclusive'} - when in doubt, include more data.

Return file_fields as a dict mapping filenames to field lists."""
        
        response = await self.llm_client.generate_structured_response(
            prompt, CharacterTargetResponse, max_retries=2
        )
        
        return ContentTarget(
            source_type=SourceType.CHARACTER_DATA,
            specific_targets={"file_fields": response.file_fields},
            reasoning=response.reasoning
        )
    
    async def _target_session_content(self, query: str, confidence: float) -> ContentTarget:
        """Target session notes with function calling."""
        prompt = f"""Target specific session notes for this query.

Query: "{query}"

Session notes contain:
- Campaign events and story progression
- NPC interactions (Ghul'Vor, Aldric, etc.)
- Combat encounters and outcomes
- Player decisions and consequences
- Location descriptions
- Quest updates

Specify:
1. Session dates (or "latest" for most recent)
2. Keywords to search for (NPC names, locations, events)

Be {'specific' if confidence > 0.7 else 'broad'} in your targeting."""
        
        response = await self.llm_client.generate_structured_response(
            prompt, SessionTargetResponse, max_retries=1
        )
        
        return ContentTarget(
            source_type=SourceType.SESSION_NOTES,
            specific_targets={
                "session_dates": response.session_dates,
                "keywords": response.keywords
            },
            reasoning=response.reasoning
        )
    
    def _calculate_confidence(self, sources: List[SourceType], hints: Set[str]) -> float:
        """Calculate confidence based on hint alignment."""
        if not hints:
            return 0.5  # Neutral confidence
        
        expected_sources = set()
        if 'rules' in hints:
            expected_sources.add(SourceType.DND_RULEBOOK)
        if 'character' in hints:
            expected_sources.add(SourceType.CHARACTER_DATA)
        if 'session' in hints:
            expected_sources.add(SourceType.SESSION_NOTES)
        
        if not expected_sources:
            return 0.5
        
        actual_sources = set(sources)
        overlap = len(expected_sources & actual_sources)
        total = len(expected_sources | actual_sources)
        
        return overlap / total if total > 0 else 0.5
    
    def _create_fallback_selection(self, query: str, hints: Set[str], error: str) -> SourceSelection:
        """Create intelligent fallback when function calling fails."""
        sources = []
        
        # Use hints as guidance, but be inclusive
        if 'rules' in hints or 'complex' in hints:
            sources.append(SourceType.DND_RULEBOOK)
        
        if 'character' in hints or 'combat' in hints or not hints:
            # Default to including character data
            sources.append(SourceType.CHARACTER_DATA)
        
        if 'session' in hints:
            sources.append(SourceType.SESSION_NOTES)
        
        # Ensure we have at least one source
        if not sources:
            sources = [SourceType.CHARACTER_DATA]
        
        return SourceSelection(
            sources_needed=sources,
            reasoning=f"Fallback selection based on query analysis. Error: {error}",
            confidence=0.3  # Low confidence for fallback
        )
    
    def _create_broad_target(self, source_type: SourceType, query: str) -> ContentTarget:
        """Create broad target when specific targeting fails."""
        if source_type == SourceType.CHARACTER_DATA:
            # Get most commonly needed files
            targets = {
                "file_fields": {
                    "character.json": ["character_base", "combat_stats", "ability_scores"],
                    "inventory_list.json": ["inventory"],
                    "spell_list.json": ["character_spells"],
                    "action_list.json": ["character_actions"]
                }
            }
        elif source_type == SourceType.DND_RULEBOOK:
            # Extract any potential keywords
            words = query.split()
            keywords = [w.lower() for w in words if len(w) > 3][:10]
            targets = {"keywords": keywords, "section_ids": []}
        else:  # SESSION_NOTES
            targets = {"session_dates": ["latest"], "keywords": []}
        
        return ContentTarget(
            source_type=source_type,
            specific_targets=targets,
            reasoning="Broad targeting fallback"
        )