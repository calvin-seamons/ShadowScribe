"""
Direct JSON Query Router - Uses direct JSON parsing for all LLM interactions
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from ..utils.schema_driven_client import SchemaDrivenClient
from ..utils.response_models import SourceTypeEnum


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
    Direct JSON router that uses direct JSON parsing for all LLM interactions.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize the query router with schema-driven client."""
        self.schema_client = SchemaDrivenClient(model=model)
    
    def set_debug_callback(self, callback):
        """Set debug callback for the schema client."""
        self.schema_client.set_debug_callback(callback)
    
    def update_model(self, model: str):
        """Update the OpenAI model used by the schema client."""
        old_callback = self.schema_client.debug_callback if hasattr(self.schema_client, 'debug_callback') else None
        self.schema_client = SchemaDrivenClient(model=model)
        if old_callback:
            self.schema_client.set_debug_callback(old_callback)
    
    async def _call_debug_callback(self, event_type: str, message: str, data: Dict[str, Any] = None):
        """Call debug callback if available."""
        if hasattr(self.schema_client, '_call_debug_callback'):
            try:
                await self.schema_client._call_debug_callback(event_type, message, data or {})
            except Exception as e:
                # Don't let debug callback errors break the main flow
                print(f"Debug callback error in query router: {e}")
    
    async def select_sources(self, user_query: str) -> SourceSelection:
        """
        Pass 1: Use direct JSON approach for source selection.
        Keywords provide hints to improve prompting.
        """
        await self._call_debug_callback("PASS_1_START", "Starting source selection", {"query": user_query})
        
        try:
            # Use the schema client's source selection
            result = await self.schema_client.select_sources(user_query)
            
            # Convert string source names to SourceType enums
            source_types = []
            for source_name in result["sources_needed"]:
                if source_name == "character_data":
                    source_types.append(SourceType.CHARACTER_DATA)
                elif source_name == "dnd_rulebook":
                    source_types.append(SourceType.DND_RULEBOOK)
                elif source_name == "session_notes":
                    source_types.append(SourceType.SESSION_NOTES)
            
            selection = SourceSelection(
                sources_needed=source_types,
                reasoning=result["reasoning"],
                confidence=0.8  # High confidence for direct client
            )
            
            await self._call_debug_callback("PASS_1_SUCCESS", 
                f"Selected {len(selection.sources_needed)} sources",
                {"sources": [s.value for s in selection.sources_needed],
                 "reasoning": selection.reasoning,
                 "confidence": selection.confidence})
            
            return selection
            
        except Exception as e:
            await self._call_debug_callback("PASS_1_ERROR", f"Source selection failed: {str(e)}", {"error": str(e)})
            # Use keyword-based fallback
            return self._create_keyword_fallback(user_query, str(e))
    
    async def target_content(self, user_query: str, sources: SourceSelection) -> List[ContentTarget]:
        """
        Pass 2: Use function calling for precise targeting.
        High confidence = more focused, low confidence = broader retrieval.
        """
        targets = []
        has_errors = False
        
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
                has_errors = True
                await self._call_debug_callback("PASS_2_ERROR", 
                    f"Targeting failed for {source_type.value}: {str(e)}", 
                    {"error": str(e), "source_type": source_type.value})
                # Create broad fallback target
                targets.append(self._create_broad_target(source_type, user_query))
        
        # If we had errors but still have targets (due to fallbacks), consider it a partial success
        if has_errors and targets:
            await self._call_debug_callback("PASS_2_ERROR", 
                "Content targeting completed with fallbacks", 
                {"error": "Some targeting failed, using fallbacks", "targets_count": len(targets)})
        
        return targets
    
    async def _target_rulebook_content(self, query: str, confidence: float) -> ContentTarget:
        """Target rulebook content using direct JSON approach."""
        try:
            # Use the direct client's rulebook targeting
            result = await self.direct_client.target_rulebook_content(query)
            
            return ContentTarget(
                source_type=SourceType.DND_RULEBOOK,
                specific_targets={
                    "section_ids": result.get("section_ids", []),
                    "keywords": result.get("keywords", [])
                },
                reasoning=f"Direct targeting found {len(result.get('keywords', []))} keywords and {len(result.get('section_ids', []))} section IDs"
            )
            
        except Exception as e:
            # Fallback to broad search
            words = query.split()
            keywords = [w.lower() for w in words if len(w) > 3][:10]
            
            return ContentTarget(
                source_type=SourceType.DND_RULEBOOK,
                specific_targets={"keywords": keywords, "section_ids": []},
                reasoning=f"Fallback: Using keyword extraction due to targeting error: {str(e)}"
            )
    
    async def _target_character_content(self, query: str, confidence: float) -> ContentTarget:
        """Target character data using direct JSON parsing - no function calling."""
        
        # Use the schema client for character targeting
        file_fields = await self.schema_client.target_character_files(query)
        
        # Create reasoning based on what was selected
        selected_files = list(file_fields.keys())
        reasoning = f"Schema-driven targeting selected {len(selected_files)} files: {', '.join(selected_files)}"
        
        return ContentTarget(
            source_type=SourceType.CHARACTER_DATA,
            specific_targets={"file_fields": file_fields},
            reasoning=reasoning
        )
    
    async def _target_session_content(self, query: str, confidence: float) -> ContentTarget:
        """Target session notes using direct JSON approach."""
        try:
            # Use the schema client's session targeting
            result = await self.schema_client.target_session_notes(query)
            
            return ContentTarget(
                source_type=SourceType.SESSION_NOTES,
                specific_targets={
                    "session_dates": result.get("session_dates", ["latest"]),
                    "keywords": result.get("keywords", [])
                },
                reasoning=f"Direct targeting found {len(result.get('keywords', []))} keywords for {len(result.get('session_dates', []))} sessions"
            )
            
        except Exception as e:
            # Fallback to latest session with query keywords
            words = query.split()
            keywords = [w.lower() for w in words if len(w) > 3][:5]
            
            return ContentTarget(
                source_type=SourceType.SESSION_NOTES,
                specific_targets={"session_dates": ["latest"], "keywords": keywords},
                reasoning=f"Fallback: Using latest session and keywords due to targeting error: {str(e)}"
            )
    
    def _create_broad_target(self, source_type: SourceType, query: str) -> ContentTarget:
        """
        Create broad target when specific targeting fails.
        FIXED: Now includes ALL 7 character files instead of just 4.
        """
        if source_type == SourceType.CHARACTER_DATA:
            # Get ALL character files - FIX for the backstory issue
            query_lower = query.lower()
            
            # Start with core files that are almost always needed
            targets = {
                "file_fields": {
                    "character.json": ["character_base", "combat_stats", "ability_scores"],
                    "inventory_list.json": ["inventory"],
                    "spell_list.json": ["character_spells"],
                    "action_list.json": ["character_actions"],
                    # ADD THE MISSING FILES HERE - THIS IS THE KEY FIX
                    "feats_and_traits.json": ["features_and_traits"],
                    "character_background.json": ["background", "characteristics", "backstory", "organizations", "allies", "enemies", "notes"],
                    "objectives_and_contracts.json": ["objectives_and_contracts"]
                }
            }
            
            # Add specific emphasis based on query keywords
            if any(word in query_lower for word in ['backstory', 'background', 'family', 'parents', 'father', 'mother', 'thaldrin', 'brenna', 'past', 'history']):
                # Emphasize backstory fields for family-related queries
                targets["file_fields"]["character_background.json"] = [
                    "background", 
                    "characteristics", 
                    "backstory",
                    "backstory.family_backstory",
                    "backstory.family_backstory.parents",
                    "organizations",
                    "allies",
                    "enemies",
                    "notes"
                ]
                
            if any(word in query_lower for word in ['objective', 'contract', 'quest', 'goal', 'covenant', 'ghul']):
                # Emphasize objectives for quest-related queries
                targets["file_fields"]["objectives_and_contracts.json"] = [
                    "objectives_and_contracts.active_contracts",
                    "objectives_and_contracts.current_objectives",
                    "objectives_and_contracts.completed_objectives"
                ]
                
            if any(word in query_lower for word in ['feat', 'trait', 'ability', 'feature', 'lucky', 'fey']):
                # Emphasize features for ability queries
                targets["file_fields"]["feats_and_traits.json"] = [
                    "features_and_traits.class_features",
                    "features_and_traits.species_traits",
                    "features_and_traits.feats"
                ]
                
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
            reasoning="Broad targeting fallback - including all available character files to ensure comprehensive data access"
        )
    
    def _create_keyword_fallback(self, user_query: str, error_msg: str) -> SourceSelection:
        """Create a comprehensive keyword-based fallback when direct client fails."""
        sources = []
        
        # Get keyword hints
        query_lower = user_query.lower()
        
        # Comprehensive character-related keywords
        character_keywords = [
            # Personal pronouns and references
            'my', 'i', 'me', 'character', 'pc', 'player character',
            
            # Character basics
            'stat', 'stats', 'statistics', 'level', 'class', 'race', 'background', 'alignment',
            'ability score', 'ability scores', 'strength', 'dexterity', 'constitution', 
            'intelligence', 'wisdom', 'charisma', 'modifier', 'modifiers',
            
            # Combat stats
            'hp', 'hit points', 'health', 'ac', 'armor class', 'initiative', 'speed',
            'proficiency', 'proficiency bonus', 'saving throw', 'saving throws',
            
            # Equipment and inventory
            'inventory', 'equipment', 'gear', 'weapon', 'weapons', 'armor', 'armour',
            'shield', 'item', 'items', 'magic item', 'magic items', 'carry', 'carrying',
            'gold', 'money', 'currency', 'treasure',
            
            # Spells and magic
            'spell', 'spells', 'magic', 'magical', 'cast', 'casting', 'spellcasting',
            'cantrip', 'cantrips', 'spell slot', 'spell slots', 'spell save', 'spell attack',
            
            # Abilities and features
            'ability', 'abilities', 'feature', 'features', 'feat', 'feats', 'trait', 'traits',
            'class feature', 'racial trait', 'special ability', 'power', 'powers',
            
            # Actions and combat
            'action', 'actions', 'attack', 'attacks', 'damage', 'combat', 'fight', 'fighting',
            'battle', 'maneuver', 'maneuvers', 'technique', 'techniques',
            
            # Background and story
            'backstory', 'background', 'history', 'past', 'family', 'parent', 'parents',
            'father', 'mother', 'sibling', 'siblings', 'ally', 'allies', 'enemy', 'enemies',
            'friend', 'friends', 'relationship', 'relationships', 'personality', 'trait',
            
            # Quests and objectives
            'quest', 'quests', 'objective', 'objectives', 'goal', 'goals', 'mission', 'missions',
            'contract', 'contracts', 'task', 'tasks', 'job', 'jobs', 'assignment', 'assignments',
            
            # Skills and proficiencies
            'skill', 'skills', 'proficient', 'expertise', 'acrobatics', 'animal handling',
            'arcana', 'athletics', 'deception', 'history', 'insight', 'intimidation',
            'investigation', 'medicine', 'nature', 'perception', 'performance', 'persuasion',
            'religion', 'sleight of hand', 'stealth', 'survival'
        ]
        
        if any(word in query_lower for word in character_keywords):
            sources.append(SourceType.CHARACTER_DATA)
        
        # Comprehensive rulebook keywords
        rulebook_keywords = [
            # Core mechanics
            'rule', 'rules', 'mechanic', 'mechanics', 'how do', 'how does', 'how to',
            'can i', 'can you', 'what is', 'what are', 'explain', 'definition', 'meaning',
            
            # Combat mechanics
            'combat', 'attack', 'attacks', 'damage', 'hit', 'miss', 'critical', 'crit',
            'armor class', 'ac', 'initiative', 'action', 'bonus action', 'reaction',
            'movement', 'move', 'opportunity attack', 'aoo', 'grapple', 'shove', 'trip',
            'disarm', 'sunder', 'charge', 'full attack', 'flurry', 'two weapon fighting',
            'dual wield', 'flanking', 'cover', 'concealment', 'prone', 'unconscious',
            
            # Spellcasting mechanics
            'spellcasting', 'spell', 'spells', 'cast', 'casting', 'concentration',
            'ritual', 'spell slot', 'spell slots', 'cantrip', 'cantrips', 'spell save',
            'spell attack', 'counterspell', 'dispel', 'metamagic', 'sorcery points',
            'spell components', 'verbal', 'somatic', 'material', 'focus', 'arcane focus',
            
            # Conditions and effects
            'condition', 'conditions', 'status', 'effect', 'effects', 'buff', 'debuff',
            'poisoned', 'charmed', 'frightened', 'paralyzed', 'stunned', 'unconscious',
            'prone', 'restrained', 'grappled', 'incapacitated', 'blinded', 'deafened',
            'exhaustion', 'petrified', 'invisible', 'hidden', 'surprised',
            
            # Saving throws and checks
            'save', 'saves', 'saving throw', 'saving throws', 'ability check', 'skill check',
            'proficiency', 'advantage', 'disadvantage', 'inspiration', 'luck', 'reroll',
            'natural 1', 'natural 20', 'critical success', 'critical failure',
            
            # Rest and recovery
            'rest', 'short rest', 'long rest', 'hit dice', 'recovery', 'heal', 'healing',
            'hit points', 'hp', 'temporary hit points', 'temp hp', 'death save',
            'death saves', 'dying', 'stabilize', 'unconscious',
            
            # Environment and exploration
            'travel', 'exploration', 'environment', 'weather', 'terrain', 'climbing',
            'swimming', 'flying', 'falling', 'suffocation', 'drowning', 'extreme cold',
            'extreme heat', 'vision', 'light', 'darkness', 'dim light', 'bright light',
            'darkvision', 'blindsight', 'tremorsense', 'truesight',
            
            # Equipment mechanics
            'weapon', 'weapons', 'armor', 'armour', 'shield', 'magic item', 'magic items',
            'attunement', 'curse', 'cursed', 'artifact', 'weapon property', 'weapon properties',
            'finesse', 'heavy', 'light', 'loading', 'range', 'reach', 'thrown', 'two-handed',
            'versatile', 'ammunition', 'silvered', 'adamantine', 'mithral'
        ]
        
        if any(word in query_lower for word in rulebook_keywords):
            sources.append(SourceType.DND_RULEBOOK)
        
        # Comprehensive session/story keywords
        session_keywords = [
            # Session references
            'session', 'sessions', 'last session', 'previous session', 'last time', 'before',
            'what happened', 'recap', 'summary', 'story so far', 'campaign', 'adventure',
            
            # Party and characters
            'party', 'party member', 'party members', 'group', 'team', 'companion', 'companions',
            'ally', 'allies', 'friend', 'friends', 'other character', 'other characters',
            'pc', 'pcs', 'player character', 'player characters', 'who', 'member', 'members',
            
            # NPCs and characters (generic terms, no specific names)
            'npc', 'npcs', 'non-player character', 'character', 'characters', 'person', 'people',
            'individual', 'someone', 'somebody', 'villain', 'villains', 'enemy', 'enemies',
            'boss', 'leader', 'captain', 'king', 'queen', 'lord', 'lady', 'sir', 'master',
            'merchant', 'trader', 'shopkeeper', 'innkeeper', 'bartender', 'guard', 'soldier',
            'priest', 'cleric', 'wizard', 'mage', 'rogue', 'thief', 'assassin', 'fighter',
            
            # Story elements
            'story', 'plot', 'narrative', 'lore', 'history', 'background', 'backstory',
            'tale', 'legend', 'myth', 'rumor', 'rumors', 'gossip', 'news', 'information',
            'secret', 'secrets', 'mystery', 'mysteries', 'clue', 'clues', 'evidence',
            'revelation', 'discovery', 'twist', 'surprise', 'shock', 'betrayal',
            
            # Events and encounters
            'event', 'events', 'encounter', 'encounters', 'meeting', 'meetings',
            'conversation', 'conversations', 'talk', 'discussion', 'negotiation', 'negotiations',
            'battle', 'battles', 'fight', 'fights', 'combat', 'skirmish', 'war', 'conflict',
            'investigation', 'search', 'exploration', 'journey', 'travel', 'trip',
            
            # Locations and world
            'location', 'locations', 'place', 'places', 'where', 'city', 'cities', 'town', 'towns',
            'village', 'villages', 'settlement', 'settlements', 'dungeon', 'dungeons', 'cave', 'caves',
            'castle', 'fortress', 'keep', 'tower', 'temple', 'church', 'shrine', 'tavern', 'inn',
            'shop', 'store', 'market', 'marketplace', 'guild', 'guildhall', 'palace', 'manor',
            'house', 'home', 'building', 'structure', 'ruins', 'ancient', 'old', 'abandoned',
            
            # Organizations and factions
            'organization', 'organizations', 'guild', 'guilds', 'faction', 'factions',
            'group', 'groups', 'society', 'societies', 'order', 'orders', 'cult', 'cults',
            'church', 'religion', 'religious', 'government', 'authority', 'council', 'court',
            
            # Relationships and politics
            'relationship', 'relationships', 'reputation', 'standing', 'politics', 'political',
            'diplomacy', 'diplomatic', 'war', 'peace', 'treaty', 'alliance', 'pact', 'agreement',
            'betrayal', 'loyalty', 'trust', 'distrust', 'rivalry', 'competition', 'cooperation',
            
            # Time references
            'when', 'time', 'date', 'day', 'week', 'month', 'year', 'ago', 'past', 'previous',
            'recent', 'recently', 'lately', 'earlier', 'before', 'after', 'during', 'while',
            'first', 'last', 'next', 'future', 'upcoming', 'planned', 'scheduled'
        ]
        
        if any(word in query_lower for word in session_keywords):
            sources.append(SourceType.SESSION_NOTES)
        
        # Default to all sources if none detected or if it's a complex query
        if not sources or len(user_query) > 100:
            sources = [SourceType.CHARACTER_DATA, SourceType.DND_RULEBOOK, SourceType.SESSION_NOTES]
        
        return SourceSelection(
            sources_needed=sources,
            reasoning=f"Keyword-based fallback after error: {error_msg}. Selected {len(sources)} sources based on query keywords.",
            confidence=0.3  # Low confidence for fallback
        )