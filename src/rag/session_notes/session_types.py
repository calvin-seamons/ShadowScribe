"""
Session Notes Query Types

Types used for session notes query routing and results.
Session data itself is stored in SessionDocument (api/database/firestore_models.py).
"""

from typing import List, Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass, field


class UserIntention(Enum):
    """Categories of user queries about session notes"""
    CHARACTER_STATUS = "character_status"
    EVENT_SEQUENCE = "event_sequence"
    NPC_INFO = "npc_info"
    LOCATION_DETAILS = "location_details"
    ITEM_TRACKING = "item_tracking"
    COMBAT_RECAP = "combat_recap"
    SPELL_ABILITY_USAGE = "spell_ability_usage"
    CHARACTER_DECISIONS = "character_decisions"
    PARTY_DYNAMICS = "party_dynamics"
    QUEST_TRACKING = "quest_tracking"
    PUZZLE_SOLUTIONS = "puzzle_solutions"
    LOOT_REWARDS = "loot_rewards"
    DEATH_REVIVAL = "death_revival"
    DIVINE_RELIGIOUS = "divine_religious"
    MEMORY_VISION = "memory_vision"
    RULES_MECHANICS = "rules_mechanics"
    HUMOR_MOMENTS = "humor_moments"
    UNRESOLVED_MYSTERIES = "unresolved_mysteries"
    FUTURE_IMPLICATIONS = "future_implications"
    CROSS_SESSION = "cross_session"


@dataclass
class SessionNotesContext:
    """Context from a specific session relevant to a query"""
    session_number: int
    session_summary: str
    relevant_sections: Dict[str, Any] = field(default_factory=dict)
    entities_found: List[str] = field(default_factory=list)
    relevance_score: float = 0.0


@dataclass
class QueryEngineResult:
    """Result from the query engine"""
    contexts: List[SessionNotesContext] = field(default_factory=list)
    total_sessions_searched: int = 0
    entities_resolved: List[str] = field(default_factory=list)
    query_summary: str = ""
    performance_metrics: Optional['SessionNotesQueryPerformanceMetrics'] = None


@dataclass
class SessionNotesQueryPerformanceMetrics:
    """Detailed timing performance information for session notes query operations"""
    total_time_ms: float = 0.0
    entity_resolution_ms: float = 0.0
    session_filtering_ms: float = 0.0
    context_building_ms: float = 0.0
    scoring_sorting_ms: float = 0.0
    result_limiting_ms: float = 0.0

    # Entity processing metrics
    entities_input: int = 0
    entities_resolved: int = 0
    fuzzy_matches_performed: int = 0

    # Search scope metrics
    total_sessions_available: int = 0
    sessions_searched: int = 0
    contexts_built: int = 0
    results_returned: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for analysis"""
        return {
            'total_time_ms': self.total_time_ms,
            'timing_breakdown': {
                'entity_resolution_ms': self.entity_resolution_ms,
                'session_filtering_ms': self.session_filtering_ms,
                'context_building_ms': self.context_building_ms,
                'scoring_sorting_ms': self.scoring_sorting_ms,
                'result_limiting_ms': self.result_limiting_ms
            },
            'entity_processing': {
                'entities_input': self.entities_input,
                'entities_resolved': self.entities_resolved,
                'fuzzy_matches_performed': self.fuzzy_matches_performed
            },
            'search_scope': {
                'total_sessions_available': self.total_sessions_available,
                'sessions_searched': self.sessions_searched,
                'contexts_built': self.contexts_built,
                'results_returned': self.results_returned
            }
        }


class SessionNotesPromptHelper:
    """Provides prompt-ready information for session notes intents and entity types."""

    @staticmethod
    def get_intent_definitions() -> Dict[str, str]:
        """Returns all session notes intentions with their definitions for prompts."""
        return {
            "character_status": "Current character status and conditions",
            "event_sequence": "What happened when - chronological events",
            "npc_info": "NPC interactions, relationships, and information",
            "location_details": "Information about places visited and explored",
            "item_tracking": "Items found, lost, used, or traded",
            "combat_recap": "Details of past combat encounters",
            "spell_ability_usage": "Spells and abilities used during sessions",
            "character_decisions": "Important character choices and their outcomes",
            "party_dynamics": "Group interactions and relationships",
            "quest_tracking": "Quest progress, objectives, and completion status",
            "puzzle_solutions": "Puzzles encountered and how they were solved",
            "loot_rewards": "Treasure, rewards, and items obtained",
            "death_revival": "Character deaths, revivals, and soul-related events",
            "divine_religious": "Interactions with deities and religious events",
            "memory_vision": "Memories recovered, visions seen, dreams experienced",
            "rules_mechanics": "Rule interpretations and mechanical decisions made",
            "humor_moments": "Funny moments and memorable jokes",
            "unresolved_mysteries": "Ongoing mysteries and unanswered questions",
            "future_implications": "Events that might affect future sessions",
            "cross_session": "Connections and patterns across multiple sessions"
        }

    @staticmethod
    def get_entity_type_definitions() -> Dict[str, str]:
        """Returns all session notes entity types with examples for prompts."""
        return {
            "player_character": "Player characters (e.g., 'Duskryn', 'party members')",
            "non_player_character": "NPCs (e.g., 'tavern keeper', 'quest giver', 'villain')",
            "location": "Places (e.g., 'tavern', 'dungeon', 'city', 'forest')",
            "item": "Items and objects (e.g., 'magic sword', 'treasure chest', 'key')",
            "artifact": "Powerful magical items (e.g., 'staff of power', 'ancient relic')",
            "spell": "Spells cast (e.g., 'fireball', 'healing word', 'teleport')",
            "ability": "Special abilities used (e.g., 'rage', 'sneak attack', 'turn undead')",
            "organization": "Groups and factions (e.g., 'thieves guild', 'royal court')",
            "deity": "Gods and divine beings (e.g., 'Tyr', 'Shar', 'patron deity')",
            "creature": "Monsters and creatures (e.g., 'dragon', 'goblin', 'undead')",
            "event": "Significant occurrences (e.g., 'battle', 'discovery', 'betrayal')",
            "quest": "Missions and objectives (e.g., 'rescue mission', 'fetch quest')",
            "puzzle": "Puzzles and challenges (e.g., 'riddle', 'trap', 'maze')"
        }

    @staticmethod
    def get_all_intents() -> List[str]:
        """Returns list of all session notes intention names."""
        return [intent.value for intent in UserIntention]

    @staticmethod
    def get_all_entity_types() -> List[str]:
        """Returns list of all session notes entity type names."""
        return [
            "player_character", "non_player_character", "location", "item",
            "artifact", "spell", "ability", "organization", "deity",
            "creature", "event", "quest", "puzzle"
        ]
