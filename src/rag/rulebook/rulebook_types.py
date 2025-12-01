"""
D&D 5e Rulebook Storage System - Core Data Models
"""

from typing import List, Dict, Optional, Set, Any, TYPE_CHECKING
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import hashlib

if TYPE_CHECKING:
    from .rulebook_storage import RulebookStorage


class RulebookCategory(Enum):
    """The 10 main content categories"""
    CHARACTER_CREATION = 1
    CLASS_FEATURES = 2
    SPELLCASTING = 3
    COMBAT = 4
    CONDITIONS = 5
    EQUIPMENT = 6
    CORE_MECHANICS = 7
    EXPLORATION = 8
    CREATURES = 9
    WORLD_LORE = 10


class RulebookQueryIntent(Enum):
    """All supported D&D 5e rulebook query intentions"""
    DESCRIBE_ENTITY = "describe_entity"  # Find exact section for single entity - "What are the traits of a dwarf?"
    COMPARE_ENTITIES = "compare_entities"  # Compare multiple entities - "What's the difference between a wizard and a sorcerer?"
    LEVEL_PROGRESSION = "level_progression"  # Class level features - "What does a fighter get at level 5?"
    ACTION_OPTIONS = "action_options"  # Combat actions available - "What can I do on my turn in combat?"
    RULE_MECHANICS = "rule_mechanics"  # Specific rule explanations - "How does concentration work?"
    CALCULATE_VALUES = "calculate_values"  # Math and calculations - "What's my AC with chain mail and a shield?"
    SPELL_DETAILS = "spell_details"  # Individual spell descriptions - "What does fireball do?"
    CLASS_SPELL_ACCESS = "class_spell_access"  # Class spell lists - "What spells can a ranger learn?"
    MONSTER_STATS = "monster_stats"  # Creature stat blocks - "What are the stats for a red dragon?"
    CONDITION_EFFECTS = "condition_effects"  # Status effects - "What does being poisoned do?"
    CHARACTER_CREATION = "character_creation"  # Character building overview - "How do I create a character?"
    MULTICLASS_RULES = "multiclass_rules"  # Multi-classing requirements - "Can I multiclass barbarian and wizard?"
    EQUIPMENT_PROPERTIES = "equipment_properties"  # Item properties - "What does the finesse property mean?"
    DAMAGE_TYPES = "damage_types"  # Damage mechanics - "How does fire damage work?"
    REST_MECHANICS = "rest_mechanics"  # Rest rules - "What happens during a long rest?"
    SKILL_USAGE = "skill_usage"  # Skill applications - "When do I use Investigation vs Perception?"
    FIND_BY_CRITERIA = "find_by_criteria"  # Search by properties - "What spells deal thunder damage?"
    PREREQUISITE_CHECK = "prerequisite_check"  # Requirements - "What do I need to take the Grappler feat?"
    INTERACTION_RULES = "interaction_rules"  # Rule interactions - "How does invisibility interact with opportunity attacks?"
    TACTICAL_USAGE = "tactical_usage"  # Combat tactics - "How do I effectively use grappling?"
    ENVIRONMENTAL_RULES = "environmental_rules"  # Environment effects - "How does underwater combat work?"
    CREATURE_ABILITIES = "creature_abilities"  # Monster special abilities - "What special abilities does a lich have?"
    SAVING_THROWS = "saving_throws"  # Save mechanics - "When do I make a Wisdom saving throw?"
    MAGIC_ITEM_USAGE = "magic_item_usage"  # Magic item mechanics - "How does a Bag of Holding work?"
    PLANAR_PROPERTIES = "planar_properties"  # Plane characteristics - "What are the properties of the Feywild?"
    DOWNTIME_ACTIVITIES = "downtime_activities"  # Non-adventure activities - "What can I do during downtime?"
    SUBCLASS_FEATURES = "subclass_features"  # Subclass abilities - "What does a Circle of the Moon druid get?"
    COST_LOOKUP = "cost_lookup"  # Item pricing - "How much does plate armor cost?"
    LEGENDARY_MECHANICS = "legendary_mechanics"  # Legendary creature rules - "How do legendary actions work?"
    OPTIMIZATION_ADVICE = "optimization_advice"  # Character build advice - "What's the best build for a tank?"


@dataclass
class RulebookSection:
    """Represents a hierarchical section of the D&D 5e rulebook"""
    id: str
    title: str
    level: int  # 1 for chapter (#), 2 for section (##), etc.
    content: str  # Content until next header (any level)
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    categories: List[RulebookCategory] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    vector: Optional[List[float]] = None  # Embedding vector
    
    def get_full_content(self, include_children: bool = False, storage: Optional['RulebookStorage'] = None) -> str:
        """Get content including optional children sections"""
        if not include_children:
            return self.content
        
        # Recursively include children content
        if not storage:
            return self.content
        
        content_parts = [self.content]
        
        # Add all children sections recursively
        for child_id in self.children_ids:
            if child_id in storage.sections:
                child_section = storage.sections[child_id]
                child_content = child_section.get_full_content(include_children=True, storage=storage)
                content_parts.append(child_content)
        
        return '\n\n'.join(content_parts)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'level': self.level,
            'content': self.content,
            'parent_id': self.parent_id,
            'children_ids': self.children_ids,
            'categories': [cat.value for cat in self.categories],
            'metadata': self.metadata,
            'vector': self.vector
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RulebookSection':
        """Create from dictionary for deserialization"""
        return cls(
            id=data['id'],
            title=data['title'],
            level=data['level'],
            content=data['content'],
            parent_id=data.get('parent_id'),
            children_ids=data.get('children_ids', []),
            categories=[RulebookCategory(cat) for cat in data.get('categories', [])],
            metadata=data.get('metadata', {}),
            vector=data.get('vector')
        )
    
    def generate_id(self) -> str:
        """Generate a unique ID based on title and parent"""
        text = f"{self.parent_id or 'root'}_{self.title}"
        return hashlib.md5(text.encode()).hexdigest()[:12]


@dataclass
class SearchResult:
    """Represents a search result with relevance scoring"""
    section: RulebookSection
    score: float
    matched_entities: List[str] = field(default_factory=list)
    matched_context: List[str] = field(default_factory=list)
    includes_children: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            'id': self.section.id,
            'title': self.section.title,
            'level': self.section.level,
            'content': self.section.content,
            'score': self.score,
            'matched_entities': self.matched_entities,
            'matched_context': self.matched_context,
            'includes_children': self.includes_children,
            'categories': [cat.name for cat in self.section.categories]
        }


@dataclass 
class QueryRequest:
    """Request structure for querying the rulebook"""
    intention: RulebookQueryIntent
    entities: List[str]  # Already normalized
    context_hints: Optional[List[str]] = None
    max_tokens: int = 8000
    include_children_for_top: bool = True
    
    def validate(self) -> bool:
        """Validate the query request"""
        if not self.intention:
            return False
        if not isinstance(self.entities, list):
            return False
        if self.max_tokens < 100 or self.max_tokens > 50000:
            return False
        return True


@dataclass
class QueryPerformanceMetrics:
    """Detailed timing performance information for query operations"""
    total_time_ms: float = 0.0
    intention_filtering_ms: float = 0.0
    semantic_search_ms: float = 0.0
    entity_boosting_ms: float = 0.0
    context_enhancement_ms: float = 0.0
    result_assembly_ms: float = 0.0
    children_inclusion_ms: float = 0.0
    
    # Detailed embedding performance
    embedding_cache_hits: int = 0
    embedding_cache_misses: int = 0
    embedding_api_calls: int = 0
    embedding_total_ms: float = 0.0
    
    # Search scope metrics
    total_sections_available: int = 0
    sections_after_filtering: int = 0
    sections_with_embeddings: int = 0
    results_returned: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for analysis"""
        return {
            'total_time_ms': self.total_time_ms,
            'timing_breakdown': {
                'intention_filtering_ms': self.intention_filtering_ms,
                'semantic_search_ms': self.semantic_search_ms,
                'entity_boosting_ms': self.entity_boosting_ms,
                'context_enhancement_ms': self.context_enhancement_ms,
                'result_assembly_ms': self.result_assembly_ms,
                'children_inclusion_ms': self.children_inclusion_ms
            },
            'embedding_performance': {
                'cache_hits': self.embedding_cache_hits,
                'cache_misses': self.embedding_cache_misses,
                'api_calls': self.embedding_api_calls,
                'total_embedding_time_ms': self.embedding_total_ms
            },
            'search_scope': {
                'total_sections_available': self.total_sections_available,
                'sections_after_filtering': self.sections_after_filtering,
                'sections_with_embeddings': self.sections_with_embeddings,
                'results_returned': self.results_returned
            }
        }


@dataclass
class QueryResponse:
    """Response structure from rulebook queries"""
    request: QueryRequest
    results: List[SearchResult]
    total_tokens: int
    categories_searched: List[RulebookCategory]
    processing_time_ms: float = 0.0
    performance_metrics: Optional['QueryPerformanceMetrics'] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        result = {
            'intention': self.request.intention.value,
            'entities': self.request.entities,
            'context_hints': self.request.context_hints,
            'results': [r.to_dict() for r in self.results],
            'total_tokens': self.total_tokens,
            'categories_searched': [cat.name for cat in self.categories_searched],
            'processing_time_ms': self.processing_time_ms
        }
        
        if self.performance_metrics:
            result['performance_metrics'] = self.performance_metrics.to_dict()
            
        return result


# Intention to Category Mapping
# NOTE: Mappings are intentionally broad to avoid missing relevant sections.
# It's better to search more sections and let ranking sort out relevance
# than to filter out relevant content too aggressively.
INTENTION_CATEGORY_MAP: Dict[RulebookQueryIntent, List[RulebookCategory]] = {
    # DESCRIBE_ENTITY: Expanded to include CONDITIONS (for describing conditions like "poisoned"),
    # CORE_MECHANICS (for core rules), and EXPLORATION (for resting, travel, etc.)
    RulebookQueryIntent.DESCRIBE_ENTITY: [
        RulebookCategory.CHARACTER_CREATION,
        RulebookCategory.CLASS_FEATURES,
        RulebookCategory.SPELLCASTING,
        RulebookCategory.EQUIPMENT,
        RulebookCategory.CREATURES,
        RulebookCategory.CONDITIONS,
        RulebookCategory.CORE_MECHANICS,
        RulebookCategory.EXPLORATION,
    ],
    # COMPARE_ENTITIES: Same expansion as DESCRIBE_ENTITY
    RulebookQueryIntent.COMPARE_ENTITIES: [
        RulebookCategory.CHARACTER_CREATION,
        RulebookCategory.CLASS_FEATURES,
        RulebookCategory.SPELLCASTING,
        RulebookCategory.EQUIPMENT,
        RulebookCategory.CREATURES,
        RulebookCategory.CONDITIONS,
        RulebookCategory.CORE_MECHANICS,
        RulebookCategory.EXPLORATION,
    ],
    RulebookQueryIntent.LEVEL_PROGRESSION: [
        RulebookCategory.CLASS_FEATURES
    ],
    RulebookQueryIntent.ACTION_OPTIONS: [
        RulebookCategory.COMBAT,
        RulebookCategory.CORE_MECHANICS
    ],
    # RULE_MECHANICS: Expanded to include SPELLCASTING for concentration, ritual rules, etc.
    # and COMBAT for attack/damage rules, CONDITIONS for rule interactions
    RulebookQueryIntent.RULE_MECHANICS: [
        RulebookCategory.CORE_MECHANICS,
        RulebookCategory.SPELLCASTING,
        RulebookCategory.COMBAT,
        RulebookCategory.CONDITIONS,
        RulebookCategory.EXPLORATION,
    ],
    # CALCULATE_VALUES: Expanded to include EQUIPMENT for AC calculations (armor, shields)
    # and COMBAT for attack/damage calculations
    RulebookQueryIntent.CALCULATE_VALUES: [
        RulebookCategory.CHARACTER_CREATION,
        RulebookCategory.CLASS_FEATURES,
        RulebookCategory.CORE_MECHANICS,
        RulebookCategory.EQUIPMENT,
        RulebookCategory.COMBAT,
    ],
    RulebookQueryIntent.SPELL_DETAILS: [
        RulebookCategory.SPELLCASTING
    ],
    RulebookQueryIntent.CLASS_SPELL_ACCESS: [
        RulebookCategory.CLASS_FEATURES,
        RulebookCategory.SPELLCASTING
    ],
    RulebookQueryIntent.MONSTER_STATS: [
        RulebookCategory.CREATURES
    ],
    RulebookQueryIntent.CONDITION_EFFECTS: [
        RulebookCategory.CONDITIONS
    ],
    RulebookQueryIntent.CHARACTER_CREATION: [
        RulebookCategory.CHARACTER_CREATION
    ],
    RulebookQueryIntent.MULTICLASS_RULES: [
        RulebookCategory.CHARACTER_CREATION,
        RulebookCategory.CLASS_FEATURES
    ],
    RulebookQueryIntent.EQUIPMENT_PROPERTIES: [
        RulebookCategory.EQUIPMENT
    ],
    RulebookQueryIntent.DAMAGE_TYPES: [
        RulebookCategory.COMBAT,
        RulebookCategory.CORE_MECHANICS
    ],
    RulebookQueryIntent.REST_MECHANICS: [
        RulebookCategory.CORE_MECHANICS,
        RulebookCategory.EXPLORATION
    ],
    RulebookQueryIntent.SKILL_USAGE: [
        RulebookCategory.CORE_MECHANICS
    ],
    RulebookQueryIntent.FIND_BY_CRITERIA: [
        RulebookCategory.CHARACTER_CREATION,
        RulebookCategory.CLASS_FEATURES,
        RulebookCategory.SPELLCASTING,
        RulebookCategory.EQUIPMENT,
        RulebookCategory.CREATURES
    ],
    RulebookQueryIntent.PREREQUISITE_CHECK: [
        RulebookCategory.CHARACTER_CREATION,
        RulebookCategory.CLASS_FEATURES,
        RulebookCategory.EQUIPMENT
    ],
    RulebookQueryIntent.INTERACTION_RULES: [
        RulebookCategory.CORE_MECHANICS,
        RulebookCategory.EXPLORATION
    ],
    RulebookQueryIntent.TACTICAL_USAGE: [
        RulebookCategory.COMBAT
    ],
    RulebookQueryIntent.ENVIRONMENTAL_RULES: [
        RulebookCategory.EXPLORATION
    ],
    RulebookQueryIntent.CREATURE_ABILITIES: [
        RulebookCategory.CREATURES
    ],
    RulebookQueryIntent.SAVING_THROWS: [
        RulebookCategory.COMBAT,
        RulebookCategory.CORE_MECHANICS
    ],
    RulebookQueryIntent.MAGIC_ITEM_USAGE: [
        RulebookCategory.EQUIPMENT
    ],
    RulebookQueryIntent.PLANAR_PROPERTIES: [
        RulebookCategory.WORLD_LORE
    ],
    RulebookQueryIntent.DOWNTIME_ACTIVITIES: [
        RulebookCategory.EXPLORATION
    ],
    RulebookQueryIntent.SUBCLASS_FEATURES: [
        RulebookCategory.CLASS_FEATURES
    ],
    RulebookQueryIntent.COST_LOOKUP: [
        RulebookCategory.EQUIPMENT,
        RulebookCategory.EXPLORATION
    ],
    RulebookQueryIntent.LEGENDARY_MECHANICS: [
        RulebookCategory.CREATURES
    ],
    RulebookQueryIntent.OPTIMIZATION_ADVICE: [
        RulebookCategory.CHARACTER_CREATION,
        RulebookCategory.CLASS_FEATURES
    ]
}


# Complete Category Mapping for D&D 5e Rulebook Sections
# Legend for Categories:
# CHARACTER_CREATION - Races, base classes, ability scores, backgrounds
# CLASS_FEATURES - All class abilities and specializations
# SPELLCASTING - Magic rules, spell lists, descriptions
# COMBAT - Combat mechanics and tactical rules
# CONDITIONS - All temporary effects and ailments
# EQUIPMENT - Gear, weapons, magical equipment
# CORE_MECHANICS - Fundamental rules like advantage, proficiency
# EXPLORATION - Non-combat adventuring and travel
# CREATURES - All creature stats and abilities
# WORLD_LORE - Planes, deities, campaign setting info


RULEBOOK_CATEGORY_ASSIGNMENTS = {
    # Legal Information
    "Legal Information": [],  # Skip - not game content
    
    # RACES CHAPTER
    "chapter-races": [1],  # CHARACTER_CREATION
    "section-racial-traits": [1],
    "section-dragonborn": [1],
    "section-dwarf": [1],
    "section-elf": [1],
    "section-gnome": [1],
    "section-half-elf": [1],
    "section-half-orc": [1],
    "section-halfling": [1],
    "section-human": [1],
    "section-tiefling": [1],
    
    # CLASSES CHAPTER - Most sections need dual categorization
    "chapter-classes": [1, 2],  # CHARACTER_CREATION, CLASS_FEATURES
    
    # Barbarian and features
    "section-barbarian": [1, 2],
    "section-barbarian-paths": [2],
    # All barbarian features (Rage, Unarmored Defense, etc.)
    "*barbarian*": [2],  # All barbarian-specific features
    
    # Bard and features
    "section-bard": [1, 2],
    "section-bard-colleges": [2],
    "*bard*": [2],  # All bard-specific features
    
    # Cleric and features
    "section-cleric": [1, 2],
    "section-domains": [2],
    "*cleric*": [2],
    
    # Druid and features
    "section-druid": [1, 2],
    "section-druid-circles": [2],
    "*druid*": [2],
    
    # Fighter and features
    "section-fighter": [1, 2],
    "section-martial-archetypes": [2],
    "*fighter*": [2],
    
    # Monk and features
    "section-monk": [1, 2],
    "section-monastic-traditions": [2],
    "*monk*": [2],
    
    # Paladin and features
    "section-paladin": [1, 2],
    "section-sacred-oaths": [2],
    "*paladin*": [2],
    
    # Ranger and features
    "section-ranger": [1, 2],
    "section-ranger-archetypes": [2],
    "*ranger*": [2],
    
    # Rogue and features
    "section-rogue": [1, 2],
    "section-roguish-archetypes": [2],
    "*rogue*": [2],
    
    # Sorcerer and features
    "section-sorcerer": [1, 2],
    "section-sorcerous-origins": [2],
    "*sorcerer*": [2],
    
    # Warlock and features
    "section-warlock": [1, 2],
    "section-eldritch-invocations": [2],
    "section-otherworldly-patrons": [2],
    "*warlock*": [2],
    
    # Wizard and features
    "section-wizard": [1, 2],
    "section-arcane-traditions": [2],
    "*wizard*": [2],
    
    # USING ABILITY SCORES CHAPTER
    "chapter-using-ability-scores": [7],  # CORE_MECHANICS
    "section-ability-scores-and-modifiers": [7],
    "section-advantage-and-disadvantage": [7],
    "section-proficiency-bonus": [7],
    "section-ability-checks": [7],
    "section-using-each-ability": [7],
    "section-saving-throws": [4, 7],  # COMBAT, CORE_MECHANICS
    
    # BEYOND 1ST LEVEL CHAPTER
    "chapter-beyond-1st-level": [1],  # CHARACTER_CREATION
    "section-character-advancement": [1, 7],  # CHARACTER_CREATION, CORE_MECHANICS
    "section-multiclassing": [1, 2],  # CHARACTER_CREATION, CLASS_FEATURES
    "section-alignment": [1],
    "section-languages": [1],
    "section-backgrounds": [1],
    
    # FEATS CHAPTER
    "chapter-feats": [1, 2],  # CHARACTER_CREATION, CLASS_FEATURES
    "section-grappler": [1, 2, 4],  # Also COMBAT for grappling
    "section-inspiration": [7],  # CORE_MECHANICS
    
    # THE PLANES OF EXISTENCE CHAPTER
    "chapter-the-planes-of-existence": [10],  # WORLD_LORE
    "section-the-material-plane": [10],
    "section-beyond-the-material": [10],
    
    # PANTHEONS CHAPTER
    "chapter-pantheons": [10],  # WORLD_LORE
    "section-the-celtic-pantheon": [10],
    "section-the-egyptian-pantheon": [10],
    "section-the-greek-pantheon": [10],
    "section-the-norse-pantheon": [10],
    
    # ADVENTURING CHAPTER
    "chapter-adventuring": [8],  # EXPLORATION
    "section-time": [8],
    "section-movement": [8],
    "section-environment": [8],
    "section-objects": [7, 8],  # CORE_MECHANICS, EXPLORATION
    "section-resting": [7, 8],  # CORE_MECHANICS, EXPLORATION
    "section-between-adventures": [8],
    "section-conditions": [5],  # CONDITIONS
    "section-poisons": [5],  # CONDITIONS
    "section-diseases": [5],  # CONDITIONS
    "section-madness": [5],  # CONDITIONS
    "section-traps": [8, 4],  # EXPLORATION, COMBAT
    
    # Individual conditions should only be CONDITIONS (override parent inheritance)
    "blinded": [5],  # CONDITIONS
    "charmed": [5],  # CONDITIONS
    "deafened": [5],  # CONDITIONS
    "exhaustion": [5],  # CONDITIONS
    "frightened": [5],  # CONDITIONS
    "grappled": [5],  # CONDITIONS
    "incapacitated": [5],  # CONDITIONS
    "invisible": [5],  # CONDITIONS
    "paralyzed": [5],  # CONDITIONS
    "petrified": [5],  # CONDITIONS
    "poisoned": [5],  # CONDITIONS
    "prone": [5],  # CONDITIONS
    "restrained": [5],  # CONDITIONS
    "stunned": [5],  # CONDITIONS
    "unconscious": [5],  # CONDITIONS
    
    # Restoration spells should only be SPELLCASTING (override parent inheritance)
    "greater-restoration": [3],  # SPELLCASTING
    "lesser-restoration": [3],  # SPELLCASTING
    
    # Restorative items should only be EQUIPMENT (override parent inheritance)
    "restorative-ointment": [6],  # EQUIPMENT
    
    # MONSTER STAT BLOCK SECTIONS - Need dual categorization for core mechanics + creatures
    # These appear in monster stat blocks but explain core game mechanics
    "hit-points": [7, 9],  # CORE_MECHANICS, CREATURES - HP rules are core mechanics
    "armor-class": [4, 7, 9],  # COMBAT, CORE_MECHANICS, CREATURES - AC is combat/core
    "speed": [7, 9],  # CORE_MECHANICS, CREATURES - Speed rules
    "skills": [7, 9],  # CORE_MECHANICS, CREATURES - Skills overview
    "experience-points": [1, 7, 9],  # CHARACTER_CREATION, CORE_MECHANICS, CREATURES
    
    # COMBAT CHAPTER
    "chapter-combat": [4],  # COMBAT
    "section-the-order-of-combat": [4],
    "section-movement-and-position": [4],
    "section-actions-in-combat": [4],
    "section-making-an-attack": [4],
    "section-cover": [4],
    "section-damage-and-healing": [4, 7],  # COMBAT, CORE_MECHANICS
    "section-mounted-combat": [4],
    "section-underwater-combat": [4, 8],  # COMBAT, EXPLORATION
    
    # SPELLCASTING CHAPTER
    "chapter-spellcasting": [3],  # SPELLCASTING
    "section-what-is-a-spell": [3],
    "section-casting-a-spell": [3],
    
    # SPELL LISTS CHAPTER
    "chapter-spell-lists": [3],  # SPELLCASTING
    "section-bard-spells": [2, 3],  # CLASS_FEATURES, SPELLCASTING
    "section-cleric-spells": [2, 3],
    "section-druid-spells": [2, 3],
    "section-paladin-spells": [2, 3],
    "section-ranger-spells": [2, 3],
    "section-sorcerer-spells": [2, 3],
    "section-warlock-spells": [2, 3],
    "section-wizard-spells": [2, 3],
    "section-spell-descriptions": [3],
    # All individual spells
    "*spell-*": [3],  # Pattern for all spell entries
    
    # EQUIPMENT CHAPTER
    "chapter-equipment": [6],  # EQUIPMENT
    "section-currency": [6],
    "section-selling-treasure": [6],
    "section-adventuring-gear": [6],
    "section-tools": [6],
    "section-mounts-and-vehicles": [6, 8],  # EQUIPMENT, EXPLORATION
    "section-trade-goods": [6],
    "section-expenses": [6, 8],  # EQUIPMENT, EXPLORATION
    "section-services": [6, 8],  # EQUIPMENT, EXPLORATION
    "section-armor": [6],
    "section-weapons": [6],
    
    # MAGIC ITEMS CHAPTER
    "chapter-magic-items": [6],  # EQUIPMENT
    "section-attunement": [6],
    "section-wearing-and-wielding-items": [6],
    "section-activating-an-item": [6],
    "section-magic-item-descriptions": [6],
    # All individual magic items
    "*magic-item-*": [6],  # Pattern for all magic item entries
    "section-sentient-magic-items": [6],
    "section-artifacts": [6],
    
    # MONSTERS CHAPTER
    "chapter-monsters": [9],  # CREATURES
    "section-monster-construction": [9],
    "section-legendary-creatures": [9],
    "section-monster-descriptions": [9],
    # All individual monsters/creature types
    "*monster-*": [9],  # Pattern for all monster entries
    
    # MISCELLANEOUS CREATURES CHAPTER
    "chapter-miscellaneous-creatures": [9],  # CREATURES
    "section-creature-descriptions": [9],
    # All miscellaneous creatures
    "*creature-*": [9],
    
    # NONPLAYER CHARACTERS CHAPTER
    "chapter-nonplayer-characters": [9],  # CREATURES (NPCs are statblocks)
    "section-customizing-npcs": [9],
    "section-nonplayer-character-descriptions": [9],
    # All NPC stat blocks
    "*npc-*": [9],
}

# Special handling patterns for subsections
PATTERN_RULES = {
    # Any section with "spell" in the ID that's not already categorized
    "contains:spell": [3],  # SPELLCASTING
    
    # Any section with class names should be in CLASS_FEATURES
    "contains:barbarian|bard|cleric|druid|fighter|monk|paladin|ranger|rogue|sorcerer|warlock|wizard": [2],
    
    # Specific condition names
    "contains:blinded|charmed|deafened|exhaustion|frightened|grappled|incapacitated|invisible|paralyzed|petrified|poisoned|prone|restrained|stunned|unconscious": [5],
    
    # Combat-related keywords
    "contains:attack|damage|initiative|reaction|bonus-action": [4],
    
    # Exploration keywords
    "contains:travel|rest|downtime|lifestyle": [8],
}

# Sections that need MULTIPLE categories (duplicates)
MULTI_CATEGORY_SECTIONS = {
    # Class spell lists appear in both categories
    "section-bard-spells": [2, 3],
    "section-cleric-spells": [2, 3],
    "section-druid-spells": [2, 3],
    "section-paladin-spells": [2, 3],
    "section-ranger-spells": [2, 3],
    "section-sorcerer-spells": [2, 3],
    "section-warlock-spells": [2, 3],
    "section-wizard-spells": [2, 3],
    
    # Multiclassing is both character creation and class features
    "section-multiclassing": [1, 2],
    
    # Saving throws are both combat and core mechanics
    "section-saving-throws": [4, 7],
    
    # Damage and healing span combat and core mechanics
    "section-damage-and-healing": [4, 7],
    
    # Underwater combat is both combat and exploration
    "section-underwater-combat": [4, 8],
    
    # Traps can be combat encounters or exploration hazards
    "section-traps": [4, 8],
    
    # Mounts are both equipment and exploration
    "section-mounts-and-vehicles": [6, 8],
}


# ===== PROMPT GENERATION HELPERS =====

class RulebookPromptHelper:
    """Provides prompt-ready information for rulebook intents and entity types."""
    
    @staticmethod
    def get_intent_definitions() -> Dict[str, str]:
        """Returns all rulebook query intentions with their definitions for prompts."""
        return {
            "describe_entity": "Find exact section for single entity - 'What are the traits of a dwarf?'",
            "compare_entities": "Compare multiple entities - 'What's the difference between a wizard and a sorcerer?'",
            "level_progression": "Class level features - 'What does a fighter get at level 5?'",
            "action_options": "Combat actions available - 'What can I do on my turn in combat?'",
            "rule_mechanics": "Specific rule explanations - 'How does concentration work?'",
            "calculate_values": "Math and calculations - 'What's my AC with chain mail and a shield?'",
            "spell_details": "Individual spell descriptions - 'What does fireball do?'",
            "class_spell_access": "Class spell lists - 'What spells can a ranger learn?'",
            "monster_stats": "Creature stat blocks - 'What are the stats for a red dragon?'",
            "condition_effects": "Status effects - 'What does being poisoned do?'",
            "character_creation": "Character building overview - 'How do I create a character?'",
            "multiclass_rules": "Multi-classing requirements - 'Can I multiclass barbarian and wizard?'",
            "equipment_properties": "Item properties - 'What does the finesse property mean?'",
            "damage_types": "Damage mechanics - 'How does fire damage work?'",
            "rest_mechanics": "Rest rules - 'What happens during a long rest?'",
            "skill_usage": "Skill applications - 'When do I use Investigation vs Perception?'",
            "find_by_criteria": "Search by properties - 'What spells deal thunder damage?'",
            "prerequisite_check": "Requirements - 'What do I need to take the Grappler feat?'",
            "interaction_rules": "Rule interactions - 'How does invisibility interact with opportunity attacks?'",
            "tactical_usage": "Combat tactics - 'How do I effectively use grappling?'",
            "environmental_rules": "Environment effects - 'How does underwater combat work?'",
            "creature_abilities": "Monster special abilities - 'What special abilities does a lich have?'",
            "saving_throws": "Save mechanics - 'When do I make a Wisdom saving throw?'",
            "magic_item_usage": "Magic item mechanics - 'How does a Bag of Holding work?'",
            "planar_properties": "Plane characteristics - 'What are the properties of the Feywild?'",
            "downtime_activities": "Non-adventure activities - 'What can I do during downtime?'",
            "subclass_features": "Subclass abilities - 'What does a Circle of the Moon druid get?'",
            "cost_lookup": "Item pricing - 'How much does plate armor cost?'",
            "legendary_mechanics": "Legendary creature rules - 'How do legendary actions work?'",
            "optimization_advice": "Character build advice - 'What's the best build for a tank?'"
        }
    
    @staticmethod
    def get_entity_type_definitions() -> Dict[str, str]:
        """Returns entity types relevant to rulebook queries with examples."""
        return {
            "spell": "Magic spells (e.g., 'fireball', 'healing word', 'counterspell')",
            "item": "Equipment and items (e.g., 'longsword', 'healing potion', 'rope')",
            "creature": "Monsters and NPCs (e.g., 'dragon', 'goblin', 'lich')",
            "condition": "Status effects (e.g., 'poisoned', 'stunned', 'charmed')",
            "rule": "Game mechanics (e.g., 'concentration', 'opportunity attacks', 'advantage')",
            "mechanic": "System mechanics (e.g., 'saving throws', 'ability checks', 'combat')",
            "action": "Combat actions (e.g., 'attack', 'dash', 'dodge', 'help')",
            "class": "Character classes (e.g., 'wizard', 'fighter', 'rogue')",
            "race": "Character races (e.g., 'elf', 'dwarf', 'tiefling')",
            "feat": "Character feats (e.g., 'great weapon master', 'lucky', 'alert')",
            "equipment": "Weapons, armor, tools (e.g., 'plate armor', 'thieves' tools')",
            "plane": "Planes of existence (e.g., 'feywild', 'shadowfell', 'nine hells')"
        }
    
    @staticmethod
    def get_all_intents() -> List[str]:
        """Returns list of all rulebook query intention names."""
        return [intent.value for intent in RulebookQueryIntent]