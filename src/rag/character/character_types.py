"""
Character Types Module

This module defines Python type definitions for creating and managing RPG characters.
These types are designed to be generalizable across different character concepts
while maintaining flexibility for various game systems and settings.

The types are organized by functional areas:
- Core character information
- Background and personality
- Combat and actions
- Abilities and features
- Inventory and equipment
- Spells and spellcasting
- Objectives and contracts
"""

from typing import Dict, List, Optional, Union, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime


# ===== CORE CHARACTER TYPES =====

@dataclass
class AbilityScores:
    """Represents the six core ability scores.
    
    EXTRACTION PATHS:
    - stats[0].value (id=1 = strength)
    - stats[1].value (id=2 = dexterity) 
    - stats[2].value (id=3 = constitution)
    - stats[3].value (id=4 = intelligence)
    - stats[4].value (id=5 = wisdom)
    - stats[5].value (id=6 = charisma)
    - overrideStats can override base values if not null
    """
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int


@dataclass
class CombatStats:
    """Core combat statistics.
    
    EXTRACTION PATHS:
    - max_hp: overrideHitPoints (if not null) or baseHitPoints + bonusHitPoints
    - armor_class: calculated from equipped armor items in inventory[].definition.armorClass
    - initiative_bonus: calculated from dex modifier + modifiers
    - speed: race.weightSpeeds.normal.walk (base walking speed)
    - hit_dice: classes[].definition.hitDice (per class level)
    """
    max_hp: int
    armor_class: int
    initiative_bonus: int
    speed: int
    hit_dice: Optional[Dict[str, str]] = None


@dataclass
class CharacterBase:
    """Basic character information.
    
    EXTRACTION PATHS:
    - name: data.name
    - race: race.fullName (e.g., "Hill Dwarf") or race.baseName for base race
    - character_class: classes[0].definition.name (primary/starting class)
    - total_level: sum of all classes[].level
    - alignment: lookup alignmentId in alignment reference table
    - background: background.definition.name
    - subrace: race.subRaceShortName (if race.isSubRace is true)
    - multiclass_levels: {classes[].definition.name: classes[].level} for each class
    - lifestyle: lookup lifestyleId in lifestyle reference table
    """
    name: str
    race: str
    character_class: str  # Primary class
    total_level: int
    alignment: str
    background: str
    subrace: Optional[str] = None
    multiclass_levels: Optional[Dict[str, int]] = None
    lifestyle: Optional[str] = None


@dataclass
class PhysicalCharacteristics:
    """Physical appearance and traits.
    
    EXTRACTION PATHS:
    - alignment: lookup data.alignmentId in alignment reference table
    - gender: data.gender
    - eyes: data.eyes
    - size: lookup data.race.sizeId in size reference table (4 = Medium)
    - height: data.height
    - hair: data.hair
    - skin: data.skin
    - age: data.age
    - weight: data.weight (may need to add unit like "lb")
    - faith: data.faith
    """
    alignment: str
    gender: str
    eyes: str
    size: str
    height: str
    hair: str
    skin: str
    age: int
    weight: str  # Include unit (e.g., "180 lb")
    faith: Optional[str] = None


@dataclass
class Proficiency:
    """Represents a skill, tool, language, or armor proficiency.
    
    EXTRACTION PATHS:
    - Extract from data.modifiers[category] where category in ["race", "class", "background", "item", "feat"]
    - Filter modifiers where modifier.type == "proficiency"
    - type: map modifier.subType to appropriate category:
      * weapon subtypes (e.g., "warhammer", "battleaxe") -> "weapon"
      * tool subtypes (e.g., "smiths-tools", "poisoners-kit") -> "tool" 
      * skill subtypes (e.g., "insight", "religion") -> "skill"
      * armor subtypes -> "armor"
      * language subtypes -> "language"
      * saving throw subtypes -> "saving_throw"
    - name: modifier.friendlySubtypeName (e.g., "Smith's Tools", "Warhammer")
    """
    type: Literal["armor", "weapon", "tool", "language", "skill", "saving_throw"]
    name: str


@dataclass
class DamageModifier:
    """Damage resistance, immunity, or vulnerability.
    
    EXTRACTION PATHS:
    - Extract from data.modifiers[category] where category in ["race", "class", "background", "item", "feat"]
    - Filter modifiers where modifier.type in ["resistance", "immunity", "vulnerability"]
    - damage_type: modifier.subType (e.g., "poison", "acid", "fire")
    - modifier_type: modifier.type ("resistance", "immunity", or "vulnerability")
    """
    damage_type: str
    modifier_type: Literal["resistance", "immunity", "vulnerability"]


@dataclass
class PassiveScores:
    """Passive perception and other passive abilities.
    
    EXTRACTION PATHS:
    NOTE: D&D Beyond does not store pre-calculated passive scores in the JSON.
    These must be calculated from ability scores and proficiencies:
    - perception: 10 + WIS modifier + proficiency bonus (if proficient in Perception)
    - investigation: 10 + INT modifier + proficiency bonus (if proficient in Investigation)
    - insight: 10 + WIS modifier + proficiency bonus (if proficient in Insight) 
    - stealth: 10 + DEX modifier + proficiency bonus (if proficient in Stealth)
    
    Base ability scores from data.stats[] and overrideStats[]
    Proficiencies from data.modifiers[category] where type="proficiency" and subType matches skill name
    """
    perception: int
    investigation: Optional[int] = None
    insight: Optional[int] = None
    stealth: Optional[int] = None


@dataclass
class Senses:
    """
    Special senses in D&D 5e.

    EXTRACTION PATHS:
    - Extract from data.modifiers[category] where category in ["race", "class", "background", "item", "feat"]
    - Filter modifiers where modifier.type == "set-base" and modifier.subType contains sense names:
      * "darkvision": modifier.value (range in feet, e.g., 60)
      * "blindsight": modifier.value (range in feet)
      * "tremorsense": modifier.value (range in feet) 
      * "truesight": modifier.value (range in feet)
      * Other special senses as they appear
    - Some senses may also be found in class features or spell descriptions
    
    NOTE: Not all characters will have special senses beyond normal vision.

    A flexible dictionary to store any type of sense with its range or description.
    Common examples:
    - "darkvision": 60 (feet)
    - "blindsight": 30
    - "tremorsense": 20
    - "truesight": 120
    - "devils_sight": 120
    - "ethereal_sight": 60
    - "see_invisibility": 10
    
    - "superior_darkvision": 120

    Values can be integers (ranges in feet) or strings (descriptive values).
    """
    senses: Dict[str, Union[int, str]] = field(default_factory=dict)


# ===== BACKGROUND AND PERSONALITY TYPES =====

@dataclass
class BackgroundFeature:
    """A background feature with name and description.
    
    EXTRACTION PATHS:
    - name: data.background.definition.featureName
    - description: data.background.definition.featureDescription (HTML content, may need cleaning)
    
    Example from Acolyte background:
    - name: "Shelter of the Faithful"
    - description: HTML description of the feature's mechanics and benefits
    """
    name: str
    description: str


@dataclass
class BackgroundInfo:
    """Character background information.
    
    EXTRACTION PATHS:
    - name: data.background.definition.name
    - feature: Create BackgroundFeature from data.background.definition.featureName and featureDescription
    - skill_proficiencies: Parse from data.background.definition.skillProficienciesDescription (comma-separated list)
    - tool_proficiencies: Parse from data.background.definition.toolProficienciesDescription (comma-separated list, may be empty)
    - language_proficiencies: Parse from data.background.definition.languagesDescription (descriptive text, may need interpretation)
    - equipment: Parse from data.background.definition.equipmentDescription (descriptive text listing items)
    - feature_description: Same as data.background.definition.featureDescription (duplicate of feature.description)
    
    NOTE: Proficiency descriptions are text that need parsing, not structured arrays.
    Language descriptions may be vague (e.g., "Two of your choice").
    """
    name: str
    feature: BackgroundFeature
    skill_proficiencies: List[str] = field(default_factory=list)
    tool_proficiencies: List[str] = field(default_factory=list)
    language_proficiencies: List[str] = field(default_factory=list)
    equipment: List[str] = field(default_factory=list)
    feature_description: Optional[str] = None


@dataclass
class PersonalityTraits:
    """Personality traits, ideals, bonds, and flaws.
    
    EXTRACTION PATHS:
    - personality_traits: Split data.traits.personalityTraits on newlines (\n)
    - ideals: Split data.traits.ideals on newlines (\n)
    - bonds: Split data.traits.bonds on newlines (\n) 
    - flaws: Split data.traits.flaws on newlines (\n)
    
    NOTE: These are stored as single strings with newline separators, not arrays.
    May contain multiple entries per field separated by \n characters.
    Probably will need to ask LLM to parse into lists.
    """
    personality_traits: List[str] = field(default_factory=list)
    ideals: List[str] = field(default_factory=list)
    bonds: List[str] = field(default_factory=list)
    flaws: List[str] = field(default_factory=list)


@dataclass
class BackstorySection:
    """A section of the character's backstory.
    
    EXTRACTION PATHS:
    WARNING: D&D Beyond does NOT store backstory as structured sections.
    
    - Backstory is stored as single markdown text: data.notes.backstory
    - Contains markdown formatting (**, \n\n for sections)
    - Must parse markdown headers (** text **) to extract section headings
    - Must split content between headers to create sections
    
    ALTERNATIVE EXTRACTION:
    - heading: Extract from markdown headers in data.notes.backstory
    - content: Extract content between headers
    
    NOTE: This requires custom parsing of markdown-formatted text.
    Example structure in JSON: "**Header**\n\nContent text\n\n**Next Header**\n\nMore content"
    Might need to ask LLM to parse into structured sections.
    """
    heading: str
    content: str


@dataclass
class FamilyBackstory:
    """Family background information.
    
    EXTRACTION PATHS:
    WARNING: D&D Beyond does NOT store family backstory as a separate structured field.
    
    - parents: Must be extracted from the main backstory text (data.notes.backstory)
    - sections: Must parse markdown sections from data.notes.backstory
    
    NOTE: This entire dataclass represents data that must be extracted using an LLM
    to parse unstructured backstory text and identify family-related information.
    The backstory is stored as free-form markdown text, not structured data.
    """
    parents: str
    sections: List[BackstorySection] = field(default_factory=list)


@dataclass
class Backstory:
    """Complete character backstory.
    
    EXTRACTION PATHS:
    - title: Extract first markdown header from data.notes.backstory
    - family_backstory: Must be parsed from data.notes.backstory using LLM
    - sections: Parse all markdown sections from data.notes.backstory
    
    Example structure in JSON:
    data.notes.backstory: "**The Battle of Shadow's Edge**\n\nUnder the tutelage..."
    
    NOTE: Requires LLM parsing of markdown-formatted free text to extract:
    - Section headers (** Header **)
    - Section content (text between headers)
    - Family information (parents, relationships)
    - Story structure and organization
    """
    title: str
    family_backstory: FamilyBackstory
    sections: List[BackstorySection] = field(default_factory=list)


@dataclass
class Organization:
    """An organization the character belongs to.
    
    EXTRACTION PATHS:
    - Parse from data.notes.organizations (free text with organization descriptions)
    
    Example structure:
    "The Holy Knights of Kluntul: As a high-ranking officer, Duskryn plays a significant role..."
    
    NOTE: Requires LLM parsing of free text to extract:
    - name: Organization name (e.g., "The Holy Knights of Kluntul")
    - role: Character's role/position in the organization
    - description: Organization's purpose and character's involvement
    
    The JSON stores this as unstructured descriptive text, not separate fields.
    """
    name: str
    role: str
    description: str


@dataclass
class Ally:
    """An ally or contact.
    
    EXTRACTION PATHS:
    - Parse from data.notes.allies (numbered list with markdown formatting)
    
    Example structure:
    "1. **High Acolyte Aldric**: His mentor and leader of the Holy Knights of Kluntul..."
    
    NOTE: Requires LLM parsing of markdown-formatted text to extract:
    - name: Extract from markdown bold text (e.g., "High Acolyte Aldric")
    - description: Extract descriptive text after the colon
    - title: May be part of the name or description (e.g., "High Acolyte")
    
    The JSON stores allies as a formatted string with numbered entries,
    not as an array of structured objects.
    """
    name: str
    description: str
    title: Optional[str] = None


@dataclass
class Enemy:
    """An enemy or rival.
    
    EXTRACTION PATHS:
    - Parse from data.notes.enemies (simple text list)
    
    Example structure:
    "Xurmurrin, The Voiceless One\nAnyone who is an enemy of Etherena"
    
    NOTE: Requires LLM parsing of free text to extract:
    - name: Extract enemy names from newline-separated text
    - description: May need to infer from context or backstory
    
    The JSON stores enemies as simple newline-separated text,
    not structured data with separate name/description fields.
    Enemy descriptions may need to be extracted from the backstory text.
    """
    name: str
    description: str


# ===== COMBAT AND ACTION TYPES =====
# Action models from parse_actions.py - single source of truth

@dataclass
class ActionActivation:
    """How an action is activated.
    
    EXTRACTION PATHS:
    - activationType: Map from actions[].actionType using ACTION_TYPE_MAP
    - activationTime: actions[].activation.activationTime
    - activationCondition: Parse from action description or activation data
    """
    activationType: Optional[str] = None  # "action", "bonus_action", "reaction", etc.
    activationTime: Optional[int] = None  # Number of time units
    activationCondition: Optional[str] = None  # Special conditions for activation


@dataclass
class ActionUsage:
    """Usage limitations for an action.
    
    EXTRACTION PATHS:
    - maxUses: actions[].limitedUse.maxUses
    - resetType: Map from actions[].limitedUse.resetType using RESET_TYPE_MAP
    - usesPerActivation: actions[].limitedUse.minNumberConsumed (default 1)
    """
    maxUses: Optional[int] = None
    resetType: Optional[str] = None  # "short_rest", "long_rest", "dawn", etc.
    usesPerActivation: Optional[int] = None


@dataclass
class ActionRange:
    """Range information for an action.
    
    EXTRACTION PATHS:
    - range: actions[].range.range or inventory[].definition.range
    - longRange: actions[].range.longRange or inventory[].definition.longRange
    - aoeType: Map from actions[].range.aoeType (1=sphere, 2=cube, 3=cone, 4=line)
    - aoeSize: actions[].range.aoeSize
    - rangeDescription: Generated from range/longRange/aoe data
    """
    range: Optional[int] = None  # Range in feet
    longRange: Optional[int] = None  # Long range in feet
    aoeType: Optional[str] = None  # Area of effect type
    aoeSize: Optional[int] = None  # AOE size in feet
    rangeDescription: Optional[str] = None  # Human-readable range


@dataclass
class ActionDamage:
    """Damage information for an action.
    
    EXTRACTION PATHS:
    - diceNotation: actions[].dice.diceString or inventory[].definition.damage.diceString
    - damageType: Map from actions[].damageTypeId or inventory[].definition.damageType
    - fixedDamage: actions[].value (if no dice)
    - bonusDamage: Additional damage from modifiers
    - criticalHitDice: Special crit dice if applicable
    """
    diceNotation: Optional[str] = None  # e.g., "1d8+3"
    damageType: Optional[str] = None  # "slashing", "fire", etc.
    fixedDamage: Optional[int] = None
    bonusDamage: Optional[str] = None
    criticalHitDice: Optional[str] = None


@dataclass
class ActionSave:
    """Saving throw information.
    
    EXTRACTION PATHS:
    - saveDC: actions[].fixedSaveDc
    - saveAbility: Map from actions[].saveStatId using ABILITY_MAP
    - onSuccess: actions[].saveSuccessDescription (clean HTML)
    - onFailure: actions[].saveFailDescription (clean HTML)
    """
    saveDC: Optional[int] = None
    saveAbility: Optional[str] = None  # "Dexterity", "Wisdom", etc.
    onSuccess: Optional[str] = None
    onFailure: Optional[str] = None


@dataclass
class CharacterAction:
    """A complete character action with all relevant information.
    
    This unified model represents all types of actions: attacks, features, spells, etc.
    
    EXTRACTION PATHS:
    - name: actions[category][].name or inventory[].definition.name (for weapons)
    - description: Clean HTML from actions[].description or inventory[].definition.description
    - shortDescription: actions[].snippet or generated summary
    - activation: Parse using ActionActivation from actions[].activation and actionType
    - usage: Parse using ActionUsage from actions[].limitedUse
    - actionRange: Parse using ActionRange from actions[].range
    - damage: Parse using ActionDamage from actions[].dice or inventory damage
    - save: Parse using ActionSave from actions[] save data
    - actionCategory: "attack", "feature", "spell", "unequipped_weapon", "item"
    - source: "class", "race", "feat", "item", "background"
    - sourceFeature: Name of feature/item granting this action
    - attackBonus: actions[].fixedToHit
    - isWeaponAttack: True if actions[].attackType in [1, 2] (melee/ranged)
    - requiresAmmo: True if weapon has "ammunition" or "thrown" property
    - duration: Parse from spell/ability duration data
    - materials: Parse from spell components or item requirements
    
    ACTION TYPE MAPPINGS:
    - actionType: 1="action", 2="no_action", 3="bonus_action", 4="reaction", etc.
    - resetType: 1="short_rest", 2="long_rest", 3="dawn", 4="dusk", etc.
    - damageTypeId: 1="bludgeoning", 2="piercing", 3="slashing", 4="necrotic", etc.
    - saveStatId: 1="Strength", 2="Dexterity", 3="Constitution", 4="Intelligence", 5="Wisdom", 6="Charisma"
    """
    name: str
    description: Optional[str] = None
    shortDescription: Optional[str] = None  # Snippet or summary
    
    # Action mechanics
    activation: Optional[ActionActivation] = None
    usage: Optional[ActionUsage] = None
    actionRange: Optional[ActionRange] = None
    damage: Optional[ActionDamage] = None
    save: Optional[ActionSave] = None
    
    # Classification
    actionCategory: Optional[str] = None  # "attack", "feature", "item", "spell"
    source: Optional[str] = None  # "class", "race", "feat", "item", "background"
    sourceFeature: Optional[str] = None  # Name of the feature/item granting this action
    
    # Combat details
    attackBonus: Optional[int] = None
    isWeaponAttack: bool = False
    requiresAmmo: bool = False
    
    # Special properties
    duration: Optional[str] = None
    materials: Optional[str] = None  # Required items or materials


@dataclass
class ActionEconomy:
    """Character's action economy information.
    
    EXTRACTION PATHS:
    - attacks_per_action: NOT DIRECTLY AVAILABLE - Must be calculated from class features
      * Look for "Extra Attack" features in classes[].classFeatures[]
      * Default is 1, increases based on fighter/ranger/paladin levels
      * Some subclasses grant additional attacks
    - actions: Aggregate from multiple sources:
      * actions.class[] (class features that are actions)
      * actions.race[] (racial abilities)
      * actions.feat[] (feat-granted actions)
      * actions.item[] (item-granted actions)
      * inventory[] (weapon attacks)
      * Convert each to CharacterAction objects
    
    MISSING INFORMATION:
    - No explicit "attacks per action" field in JSON
    - Must derive from class features and levels
    
    LLM ASSISTANCE NEEDED:
    - Parse class features to identify "Extra Attack" or similar abilities
    - Calculate attacks per action based on class levels and features
    - Convert various action sources into unified CharacterAction format
    - Identify passive vs active abilities
    """
    attacks_per_action: int = 1
    actions: List[CharacterAction] = field(default_factory=list)


# ===== FEATURES AND TRAITS TYPES =====

@dataclass
class FeatureActivation:
    """Activation information for features and actions.
    
    EXTRACTION PATHS:
    - activationTime: actions[].activation.activationTime or feature activation time
    - activationType: Map from actions[].actionType using ACTION_TYPE_MAP
      * 1="action", 2="no_action", 3="bonus_action", 4="reaction", etc.
    """
    activationTime: Optional[int] = None
    activationType: Optional[str] = None  # Converted to human-readable string


@dataclass
class FeatureRange:
    """Range information for feature actions.
    
    EXTRACTION PATHS:
    - range: actions[].range.range
    - longRange: actions[].range.longRange
    - aoeType: actions[].range.aoeType (1=sphere, 2=cube, 3=cone, 4=line)
    - aoeSize: actions[].range.aoeSize
    - hasAoeSpecialDescription: actions[].range.hasAoeSpecialDescription
    - minimumRange: actions[].range.minimumRange
    """
    range: Optional[int] = None
    longRange: Optional[int] = None
    aoeType: Optional[int] = None
    aoeSize: Optional[int] = None
    hasAoeSpecialDescription: Optional[bool] = None
    minimumRange: Optional[int] = None


@dataclass
class RacialTrait:
    """A racial trait from race or subrace.
    
    EXTRACTION PATHS:
    - name: race.racialTraits[].definition.name
    - description: race.racialTraits[].definition.description (HTML, needs cleaning)
    - creatureRules: race.racialTraits[].definition.creatureRules
    - featureType: Map from race.racialTraits[].definition.featureType
      * 1="trait", 2="action", 3="bonus_action", 4="reaction", etc.
    """
    name: str
    description: Optional[str] = None
    creatureRules: Optional[List[Dict[str, Any]]] = None
    featureType: Optional[str] = None  # Converted to human-readable string


@dataclass
class ClassFeature:
    """A class or subclass feature.
    
    EXTRACTION PATHS:
    - name: classes[].classFeatures[].definition.name or
            classes[].subclassDefinition.classFeatures[].definition.name
    - description: Corresponding .definition.description (HTML, needs cleaning)
    """
    name: str
    description: Optional[str] = None


@dataclass
class Feat:
    """A character feat.
    
    EXTRACTION PATHS:
    - name: feats[].definition.name
    - description: feats[].definition.description (HTML, needs cleaning)
    - activation: Parse from feats[].definition.activation
    - creatureRules: feats[].definition.creatureRules
    - isRepeatable: feats[].definition.isRepeatable
    """
    name: str
    description: Optional[str] = None
    activation: Optional[FeatureActivation] = None
    creatureRules: Optional[List[Dict[str, Any]]] = None
    isRepeatable: Optional[bool] = None


@dataclass
class FeatureAction:
    """An action granted by a feature (from actions data).
    
    EXTRACTION PATHS:
    - limitedUse: Parse from actions[category][].limitedUse
    - name: actions[category][].name
    - description: actions[category][].description (HTML, needs cleaning)
    - abilityModifierStatName: Map from actions[category][].abilityModifierStatId
      * 1="Strength", 2="Dexterity", 3="Constitution", 4="Intelligence", 5="Wisdom", 6="Charisma"
    - onMissDescription: actions[category][].onMissDescription
    - saveFailDescription: actions[category][].saveFailDescription
    - saveSuccessDescription: actions[category][].saveSuccessDescription
    - saveStatId: actions[category][].saveStatId
    - fixedSaveDc: actions[category][].fixedSaveDc
    - attackTypeRange: actions[category][].attackTypeRange
    - actionType: Map from actions[category][].actionType
    - attackSubtype: actions[category][].attackSubtype
    - dice: actions[category][].dice
    - value: actions[category][].value
    - damageTypeId: actions[category][].damageTypeId
    - isMartialArts: actions[category][].isMartialArts
    - isProficient: actions[category][].isProficient
    - spellRangeType: actions[category][].spellRangeType
    - range: Parse from actions[category][].range as FeatureRange
    - activation: Parse from actions[category][].activation as FeatureActivation
    """
    limitedUse: Optional['LimitedUse'] = None
    name: Optional[str] = None
    description: Optional[str] = None
    abilityModifierStatName: Optional[str] = None  # Human readable name
    onMissDescription: Optional[str] = None
    saveFailDescription: Optional[str] = None
    saveSuccessDescription: Optional[str] = None
    saveStatId: Optional[int] = None
    fixedSaveDc: Optional[int] = None
    attackTypeRange: Optional[int] = None
    actionType: Optional[str] = None  # Converted to human-readable string
    attackSubtype: Optional[int] = None
    dice: Optional[Dict[str, Any]] = None
    value: Optional[int] = None
    damageTypeId: Optional[int] = None
    isMartialArts: Optional[bool] = None
    isProficient: Optional[bool] = None
    spellRangeType: Optional[int] = None
    range: Optional[FeatureRange] = None
    activation: Optional[FeatureActivation] = None


@dataclass
class FeatureModifier:
    """A modifier granted by a feature.
    
    EXTRACTION PATHS:
    - type: modifiers[category][].type
    - subType: modifiers[category][].subType
    - dice: modifiers[category][].dice
    - restriction: modifiers[category][].restriction
    - statId: modifiers[category][].statId
    - requiresAttunement: modifiers[category][].requiresAttunement
    - duration: modifiers[category][].duration
    - friendlyTypeName: modifiers[category][].friendlyTypeName
    - friendlySubtypeName: modifiers[category][].friendlySubtypeName
    - bonusTypes: modifiers[category][].bonusTypes
    - value: modifiers[category][].value
    """
    type: Optional[str] = None
    subType: Optional[str] = None
    dice: Optional[Dict[str, Any]] = None
    restriction: Optional[str] = None
    statId: Optional[int] = None
    requiresAttunement: Optional[bool] = None
    duration: Optional[Dict[str, Any]] = None
    friendlyTypeName: Optional[str] = None
    friendlySubtypeName: Optional[str] = None
    bonusTypes: Optional[List[str]] = None
    value: Optional[int] = None


@dataclass
class FeaturesAndTraits:
    """Container for all character features and traits.
    
    EXTRACTION PATHS:
    - racial_traits: Parse from race.racialTraits[] as RacialTrait objects
    - class_features: Parse from classes[].classFeatures[] organized by class name and level
      * Key format: class name (e.g., "Warlock", "Cleric")
      * Value format: Dict[int, List[ClassFeature]] - features grouped by required level
    - feats: Parse from feats[] as Feat objects
    - modifiers: Parse from modifiers[category][] organized by category
      * Categories: "race", "class", "background", "item", "feat", "condition"
      * Each category contains List[FeatureModifier]
    
    ORGANIZATION:
    - racial_traits: Flat list of all racial traits (base race + subrace)
    - class_features: Nested dict by class name, then by level
    - feats: Flat list of all feats
    - modifiers: Dict by source category
    
    NOTE: Character actions are parsed separately by parse_actions.py into CharacterAction objects.
          See ActionEconomy dataclass for the complete action system.
    """
    racial_traits: List[RacialTrait] = field(default_factory=list)
    class_features: Dict[str, Dict[int, List[ClassFeature]]] = field(default_factory=dict)
    feats: List[Feat] = field(default_factory=list)
    modifiers: Dict[str, List[FeatureModifier]] = field(default_factory=dict)


# ===== INVENTORY TYPES =====

@dataclass
class ItemModifier:
    """A modifier granted by an inventory item.
    
    EXTRACTION PATHS:
    - type: inventory[].definition.grantedModifiers[].type
    - subType: inventory[].definition.grantedModifiers[].subType
    - restriction: inventory[].definition.grantedModifiers[].restriction
    - friendlyTypeName: inventory[].definition.grantedModifiers[].friendlyTypeName
    - friendlySubtypeName: inventory[].definition.grantedModifiers[].friendlySubtypeName
    - duration: inventory[].definition.grantedModifiers[].duration
    - fixedValue: inventory[].definition.grantedModifiers[].fixedValue
    - diceString: inventory[].definition.grantedModifiers[].dice.diceString
    """
    type: Optional[str] = None
    subType: Optional[str] = None
    restriction: Optional[str] = None
    friendlyTypeName: Optional[str] = None
    friendlySubtypeName: Optional[str] = None
    duration: Optional[Dict[str, Any]] = None
    fixedValue: Optional[int] = None
    diceString: Optional[str] = None


@dataclass
class LimitedUse:
    """Limited use information for items and features.
    
    EXTRACTION PATHS:
    - maxUses: inventory[].limitedUse.maxUses or actions[].limitedUse.maxUses
    - numberUsed: inventory[].limitedUse.numberUsed (for items)
    - resetType: inventory[].limitedUse.resetType or actions[].limitedUse.resetType
      * Map: 1="short_rest", 2="long_rest", 3="dawn", 4="dusk", 5="recharge", 6="turn"
    - resetTypeDescription: inventory[].limitedUse.resetTypeDescription
    """
    maxUses: Optional[int] = None
    numberUsed: Optional[int] = None
    resetType: Optional[str] = None  # Human-readable string
    resetTypeDescription: Optional[str] = None


@dataclass
class InventoryItemDefinition:
    """Definition of an inventory item with all properties.
    
    EXTRACTION PATHS:
    - name: inventory[].definition.name
    - type: inventory[].definition.type
    - description: inventory[].definition.description (HTML, needs cleaning)
    - canAttune: inventory[].definition.canAttune
    - attunementDescription: inventory[].definition.attunementDescription
    - rarity: inventory[].definition.rarity
    - weight: inventory[].definition.weight
    - capacity: inventory[].definition.capacity
    - capacityWeight: inventory[].definition.capacityWeight
    - canEquip: inventory[].definition.canEquip
    - magic: inventory[].definition.magic
    - tags: inventory[].definition.tags
    - grantedModifiers: Parse inventory[].definition.grantedModifiers[] as ItemModifier objects
    - damage: inventory[].definition.damage
    - damageType: inventory[].definition.damageType
    - attackType: inventory[].definition.attackType
    - range: inventory[].definition.range
    - longRange: inventory[].definition.longRange
    - isContainer: inventory[].definition.isContainer
    - isCustomItem: inventory[].definition.isCustomItem
    """
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    canAttune: Optional[bool] = None
    attunementDescription: Optional[str] = None
    rarity: Optional[str] = None
    weight: Optional[Union[int, float]] = None
    capacity: Optional[str] = None
    capacityWeight: Optional[int] = None
    canEquip: Optional[bool] = None
    magic: Optional[bool] = None
    tags: Optional[List[str]] = None
    grantedModifiers: Optional[List[ItemModifier]] = None
    damage: Optional[Dict[str, Any]] = None
    damageType: Optional[str] = None
    attackType: Optional[int] = None
    range: Optional[int] = None
    longRange: Optional[int] = None
    isContainer: Optional[bool] = None
    isCustomItem: Optional[bool] = None


@dataclass
class InventoryItem:
    """An inventory item with quantity and equipped status.
    
    EXTRACTION PATHS:
    - definition: Parse inventory[].definition as InventoryItemDefinition
    - quantity: inventory[].quantity
    - isAttuned: inventory[].isAttuned
    - equipped: inventory[].equipped
    - limitedUse: Parse inventory[].limitedUse as LimitedUse (if present)
    """
    definition: InventoryItemDefinition
    quantity: int
    isAttuned: bool
    equipped: bool
    limitedUse: Optional[LimitedUse] = None


@dataclass
class Inventory:
    """Character's complete inventory.
    
    EXTRACTION PATHS:
    - total_weight: CALCULATED - sum all inventory[].definition.weight * inventory[].quantity
      * Consider inventory[].definition.weightMultiplier (usually 1 or 0)
      * Some items like Bag of Holding have weightMultiplier = 0
    - weight_unit: NOT EXPLICIT - assume "lb" (pounds) as D&D standard
    - equipped_items: All inventory[] items where inventory[].equipped == true
    - backpack: All inventory[] items where inventory[].equipped == false
    - valuables: NOT AVAILABLE - no separate valuables tracking in D&D Beyond
    
    INVENTORY ORGANIZATION:
    - Simple equipped/backpack split based on equipped status
    - No slot-based categorization
    
    CURRENCY TRACKING:
    - Separate currencies object: {"cp": int, "sp": int, "gp": int, "ep": int, "pp": int}
    - Not included in regular inventory weight calculations
    """
    total_weight: float
    weight_unit: str = "lb"
    equipped_items: List[InventoryItem] = field(default_factory=list)
    backpack: List[InventoryItem] = field(default_factory=list)
    valuables: List[Dict[str, Any]] = field(default_factory=list)


# ===== SPELL TYPES =====

@dataclass
class SpellComponents:
    """Components required for spellcasting.
    
    EXTRACTION PATHS:
    - verbal: NOT DIRECTLY AVAILABLE - must parse from spell definitions
    - somatic: NOT DIRECTLY AVAILABLE - must parse from spell definitions
    - material: NOT DIRECTLY AVAILABLE - must parse from spell definitions
    
    SPELL COMPONENT SOURCES:
    - D&D Beyond doesn't store spell components in character JSON
    - Spell definitions would need to be fetched from separate API/database
    - Character JSON only contains spell references, not full spell data
    
    MISSING INFORMATION:
    - No spell component data in character JSON
    - Would need external spell database lookup
    - Components typically stored as text strings in spell descriptions
    
    LLM ASSISTANCE NEEDED:
    - Parse spell descriptions to identify V/S/M components
    - Extract material component details from spell text
    - Convert component text to boolean/string format
    """
    verbal: bool = False
    somatic: bool = False
    material: Union[bool, str] = False


@dataclass
class SpellRite:
    """A rite option for certain spells.
    
    EXTRACTION PATHS:
    - name: NOT AVAILABLE - D&D Beyond doesn't use rite system
    - effect: NOT AVAILABLE - D&D Beyond doesn't use rite system
    
    RITE SYSTEM:
    - This appears to be a custom system not used by D&D Beyond
    - D&D Beyond doesn't have spell "rites" as separate options
    - May be specific to your campaign/system
    
    MISSING INFORMATION:
    - No rite data in D&D Beyond JSON
    - Would need custom implementation or campaign-specific data
    
    LLM ASSISTANCE NEEDED:
    - Identify if any spells have variant options that could be considered "rites"
    - Extract spell options from descriptions if present
    - Create rite structures from spell variant text
    """
    name: str
    effect: str


@dataclass
class Spell:
    """A spell definition.
    
    EXTRACTION PATHS:
    - name: spells.*.*.definition.name (from character's known spells)
    - level: spells.*.*.definition.level
    - school: spells.*.*.definition.school (may need lookup)
    - casting_time: spells.*.*.activation.activationTime + activationType
    - range: spells.*.*.range.range
    - components: Create SpellComponents from spell definition (limited data)
    - duration: spells.*.*.duration (may need parsing)
    - description: spells.*.*.definition.description (HTML, needs cleaning)
    - concentration: spells.*.*.concentration
    - ritual: spells.*.*.castOnlyAsRitual or ritualCastingType
    - tags: spells.*.*.definition.tags (if available)
    - area: spells.*.*.range.aoeType + aoeSize
    - rites: NOT AVAILABLE - see SpellRite comments
    - charges: spells.*.*.charges (for item spells)
    
    SPELL SOURCES IN JSON:
    - spells.race[] - racial spells
    - spells.class[] - class spells
    - spells.background[] - background spells (rare)
    - spells.item[] - item-granted spells
    - spells.feat[] - feat-granted spells
    
    SPELL STRUCTURE:
    - Each spell has definition object with basic info
    - Range object with range/aoe data
    - Activation object with casting time info
    - Limited use tracking for charged spells
    
    MISSING INFORMATION:
    - Spell components not fully detailed in character JSON
    - School might be ID that needs lookup
    - Duration often needs parsing from description
    - Tags may not be present for all spells
    
    LLM ASSISTANCE NEEDED:
    - Parse HTML descriptions to clean text
    - Extract spell components from description text
    - Convert activation data to readable casting time
    - Parse duration information from various formats
    - Map school IDs to school names if needed
    - Extract area information from range data
    """
    name: str
    level: int
    school: str
    casting_time: str
    range: str
    components: SpellComponents
    duration: str
    description: str
    concentration: bool = False
    ritual: bool = False
    tags: List[str] = field(default_factory=list)
    area: Optional[str] = None
    rites: Optional[List[SpellRite]] = None
    charges: Optional[int] = None


@dataclass
class SpellcastingInfo:
    """Spellcasting ability information.
    
    EXTRACTION PATHS:
    - ability: classes[].definition.spellCastingAbilityId (requires lookup to ability name)
    - spell_save_dc: CALCULATED - 8 + proficiency bonus + ability modifier
    - spell_attack_bonus: CALCULATED - proficiency bonus + ability modifier
    - cantrips_known: Filter spells where level == 0
    - spells_known: Filter spells where level > 0
    - spell_slots: spellSlots[] array with level/available/used
    
    SPELLCASTING ABILITY MAPPING:
    - spellCastingAbilityId to ability name:
      * 1 = "strength", 2 = "dexterity", 3 = "constitution"
      * 4 = "intelligence", 5 = "wisdom", 6 = "charisma"
    
    SPELL SLOT STRUCTURE:
    - spellSlots[] array with objects: {level, used, available}
    - Separate pactMagic[] array for warlock slots
    
    SPELL ORGANIZATION:
    - Spells organized by source: spells.class[], spells.race[], etc.
    - Each source contains spells for that category
    - prepared/known status tracked per spell
    
    MISSING INFORMATION:
    - Save DC and attack bonus not pre-calculated
    - Must derive ability name from ID
    - Need to filter and organize spells by level
    
    LLM ASSISTANCE NEEDED:
    - Map spellCastingAbilityId to ability names
    - Calculate save DC and attack bonus from ability scores
    - Filter and organize spells by level (cantrips vs leveled)
    - Handle multiclass spellcasting scenarios
    - Convert spell slot structure to level:count format
    """
    ability: str
    spell_save_dc: int
    spell_attack_bonus: int
    cantrips_known: List[str] = field(default_factory=list)
    spells_known: List[str] = field(default_factory=list)
    spell_slots: Dict[int, int] = field(default_factory=dict)


@dataclass
class SpellList:
    """Complete spell list organized by class.
    
    EXTRACTION PATHS:
    - spellcasting: Create SpellcastingInfo for each spellcasting class
      * Key: class name from classes[].definition.name
      * Value: SpellcastingInfo with that class's spellcasting data
    - spells: Organize all character spells by class and level
      * Outer key: class name
      * Inner key: spell level ("cantrip", "1st_level", etc.)
      * Value: List of Spell objects
    
    SPELLCASTING CLASSES:
    - Only classes with canCastSpells == true have spellcasting
    - Each class has spellCastingAbilityId for their casting ability
    - Spell preparation varies by class (spellPrepareType)
    
    SPELL ORGANIZATION IN JSON:
    - spells object contains arrays by source:
      * spells.class[] - spells from class features
      * spells.race[] - racial spells
      * spells.item[] - item-granted spells
      * spells.feat[] - feat-granted spells
      * spells.background[] - background spells
    
    MULTICLASS SPELLCASTING:
    - Each class tracked separately in classSpells[]
    - Different classes may have different spell lists
    - Some classes share spell slots, others don't
    
    MISSING INFORMATION:
    - No pre-organized structure by class and level
    - Must manually group spells by source class
    - Spell level organization needs custom logic
    
    LLM ASSISTANCE NEEDED:
    - Identify which classes are spellcasting classes
    - Group spells by their source class
    - Organize spells by level within each class
    - Handle multiclass spellcasting rules
    - Convert spell level numbers to string format
    - Create SpellcastingInfo for each casting class
    - Handle different spell preparation types
    """
    spellcasting: Dict[str, SpellcastingInfo] = field(default_factory=dict)
    spells: Dict[str, Dict[str, List[Spell]]] = field(default_factory=dict)


# ===== OBJECTIVES AND CONTRACTS TYPES =====

@dataclass
class BaseObjective:
    """Base for all objectives"""
    id: str
    name: str
    type: str
    status: Literal["Active", "In Progress", "Completed", "Failed", "Suspended", "Abandoned"]
    description: str
    priority: Optional[Literal["Absolute", "Critical", "High", "Medium", "Low"]] = None
    objectives: List[str] = field(default_factory=list)
    rewards: List[str] = field(default_factory=list)
    deadline: Optional[str] = None
    notes: Optional[str] = None
    completion_date: Optional[str] = None
    parties: Optional[str] = None
    outcome: Optional[str] = None
    obligations_accepted: List[str] = field(default_factory=list)
    lasting_effects: List[str] = field(default_factory=list)


@dataclass
class Quest(BaseObjective):
    """Quest-specific fields"""
    quest_giver: Optional[str] = None
    location: Optional[str] = None
    deity: Optional[str] = None
    purpose: Optional[str] = None
    signs_received: List[str] = field(default_factory=list)
    divine_favor: Optional[str] = None
    consequences_of_failure: List[str] = field(default_factory=list)
    motivation: Optional[str] = None
    steps: List[str] = field(default_factory=list)
    obstacles: List[str] = field(default_factory=list)
    importance: Optional[str] = None


@dataclass
class Contract(BaseObjective):
    """Contract-specific fields"""
    client: Optional[str] = None
    contractor: Optional[str] = None
    terms: Optional[str] = None
    payment: Optional[str] = None
    penalties: Optional[str] = None
    special_conditions: List[str] = field(default_factory=list)
    parties: Optional[str] = None
    outcome: Optional[str] = None
    obligations_accepted: List[str] = field(default_factory=list)
    lasting_effects: List[str] = field(default_factory=list)


@dataclass
class ContractTemplate:
    """Template for creating new contracts."""
    id: str = ""
    name: str = ""
    type: str = ""
    status: str = ""
    priority: str = ""
    quest_giver: str = ""
    location: str = ""
    description: str = ""
    objectives: List[str] = field(default_factory=list)
    rewards: List[str] = field(default_factory=list)
    deadline: str = ""
    notes: str = ""


@dataclass
class ObjectivesAndContracts:
    """All character objectives and contracts."""
    active_contracts: List[Contract] = field(default_factory=list)
    current_objectives: List[Quest] = field(default_factory=list)
    completed_objectives: List[Union[Quest, Contract]] = field(default_factory=list)
    contract_templates: Dict[str, ContractTemplate] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ===== MAIN CHARACTER CLASS =====

@dataclass
class Character:
    """Complete character definition combining all aspects."""
    # Core information (required fields first)
    character_base: CharacterBase
    characteristics: PhysicalCharacteristics
    ability_scores: AbilityScores
    combat_stats: CombatStats
    background_info: BackgroundInfo
    personality: PersonalityTraits
    backstory: Backstory

    # Optional fields
    organizations: List[Organization] = field(default_factory=list)
    allies: List[Ally] = field(default_factory=list)
    enemies: List[Enemy] = field(default_factory=list)
    proficiencies: List[Proficiency] = field(default_factory=list)
    damage_modifiers: List[DamageModifier] = field(default_factory=list)
    passive_scores: Optional[PassiveScores] = None
    senses: Optional[Senses] = None
    action_economy: Optional[ActionEconomy] = None
    features_and_traits: Optional[FeaturesAndTraits] = None
    inventory: Optional[Inventory] = None
    spell_list: Optional[SpellList] = None
    objectives_and_contracts: Optional[ObjectivesAndContracts] = None
    notes: Dict[str, Any] = field(default_factory=dict)
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None


# ===== UTILITY FUNCTIONS =====

def create_empty_character(name: str, race: str, character_class: str) -> Character:
    """Create a minimal character with default empty values."""
    return Character(
        character_base=CharacterBase(
            name=name,
            race=race,
            character_class=character_class,
            total_level=1,
            alignment="Neutral",
            background="Unknown"
        ),
        characteristics=PhysicalCharacteristics(
            alignment="Neutral",
            gender="Unknown",
            eyes="Unknown",
            size="Medium",
            height="5'0\"",
            hair="Unknown",
            skin="Unknown",
            age=18,
            weight="150 lb"
        ),
        ability_scores=AbilityScores(
            strength=10, dexterity=10, constitution=10,
            intelligence=10, wisdom=10, charisma=10
        ),
        combat_stats=CombatStats(
            max_hp=10, armor_class=10, initiative_bonus=0, speed=30
        ),
        background_info=BackgroundInfo(
            name="Unknown",
            feature=BackgroundFeature(name="Unknown", description="")
        ),
        personality=PersonalityTraits(),
        backstory=Backstory(
            title="Unknown",
            family_backstory=FamilyBackstory(parents="Unknown")
        ),
        passive_scores=PassiveScores(perception=10),
        senses=Senses(
            senses={"darkvision": 60}  # Common for many races
        ),
        action_economy=ActionEconomy(),
        features_and_traits=FeaturesAndTraits(),
        inventory=Inventory(total_weight=0.0),
        spell_list=SpellList(),
        objectives_and_contracts=ObjectivesAndContracts()
    )


# ===== TYPE ALIASES =====

CharacterDict = Dict[str, Any]
SpellLevel = Literal["cantrip", "1st_level", "2nd_level", "3rd_level", "4th_level",
                     "5th_level", "6th_level", "7th_level", "8th_level", "9th_level"]
ActionType = Literal["action", "bonus_action", "reaction", "no_action", "feature"]
ProficiencyType = Literal["armor", "weapon", "tool", "language", "skill", "saving_throw"]
DamageModifierType = Literal["resistance", "immunity", "vulnerability"]
ObjectiveStatus = Literal["Active", "In Progress", "Completed", "Failed", "Suspended", "Abandoned"]
ObjectivePriority = Literal["Absolute", "Critical", "High", "Medium", "Low"]
