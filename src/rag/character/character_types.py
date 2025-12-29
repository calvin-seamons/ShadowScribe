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

NOTE: These are Pydantic models (BaseModel) that serve as the single source of truth.
TypeScript types are auto-generated from these models using pydantic-to-typescript.
"""

from typing import Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


# ===== CORE CHARACTER TYPES =====

class AbilityScores(BaseModel):
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


class CombatStats(BaseModel):
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
    hit_dice: dict[str, str] | None = None


class CharacterBase(BaseModel):
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
    subrace: str | None = None
    multiclass_levels: dict[str, int] | None = None
    lifestyle: str | None = None


class PhysicalCharacteristics(BaseModel):
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
    faith: str | None = None


class Proficiency(BaseModel):
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


class DamageModifier(BaseModel):
    """Damage resistance, immunity, or vulnerability.

    EXTRACTION PATHS:
    - Extract from data.modifiers[category] where category in ["race", "class", "background", "item", "feat"]
    - Filter modifiers where modifier.type in ["resistance", "immunity", "vulnerability"]
    - damage_type: modifier.subType (e.g., "poison", "acid", "fire")
    - modifier_type: modifier.type ("resistance", "immunity", or "vulnerability")
    """
    damage_type: str
    modifier_type: Literal["resistance", "immunity", "vulnerability"]


class PassiveScores(BaseModel):
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
    investigation: int | None = None
    insight: int | None = None
    stealth: int | None = None


class Senses(BaseModel):
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
    senses: dict[str, int | str] = Field(default_factory=dict)


# ===== BACKGROUND AND PERSONALITY TYPES =====

class BackgroundFeature(BaseModel):
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


class BackgroundInfo(BaseModel):
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
    skill_proficiencies: list[str] = Field(default_factory=list)
    tool_proficiencies: list[str] = Field(default_factory=list)
    language_proficiencies: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    feature_description: str | None = None


class PersonalityTraits(BaseModel):
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
    personality_traits: list[str] = Field(default_factory=list)
    ideals: list[str] = Field(default_factory=list)
    bonds: list[str] = Field(default_factory=list)
    flaws: list[str] = Field(default_factory=list)


class BackstorySection(BaseModel):
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


class FamilyBackstory(BaseModel):
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
    sections: list[BackstorySection] = Field(default_factory=list)


class Backstory(BaseModel):
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
    sections: list[BackstorySection] = Field(default_factory=list)


class Organization(BaseModel):
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


class Ally(BaseModel):
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
    title: str | None = None


class Enemy(BaseModel):
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

class ActionActivation(BaseModel):
    """How an action is activated.

    EXTRACTION PATHS:
    - activationType: Map from actions[].actionType using ACTION_TYPE_MAP
    - activationTime: actions[].activation.activationTime
    - activationCondition: Parse from action description or activation data
    """
    activationType: str | None = None  # "action", "bonus_action", "reaction", etc.
    activationTime: int | None = None  # Number of time units
    activationCondition: str | None = None  # Special conditions for activation


class ActionUsage(BaseModel):
    """Usage limitations for an action.

    EXTRACTION PATHS:
    - maxUses: actions[].limitedUse.maxUses
    - resetType: Map from actions[].limitedUse.resetType using RESET_TYPE_MAP
    - usesPerActivation: actions[].limitedUse.minNumberConsumed (default 1)
    """
    maxUses: int | None = None
    resetType: str | None = None  # "short_rest", "long_rest", "dawn", etc.
    usesPerActivation: int | None = None


class ActionRange(BaseModel):
    """Range information for an action.

    EXTRACTION PATHS:
    - range: actions[].range.range or inventory[].definition.range
    - longRange: actions[].range.longRange or inventory[].definition.longRange
    - aoeType: Map from actions[].range.aoeType (1=sphere, 2=cube, 3=cone, 4=line)
    - aoeSize: actions[].range.aoeSize
    - rangeDescription: Generated from range/longRange/aoe data
    """
    range: int | None = None  # Range in feet
    longRange: int | None = None  # Long range in feet
    aoeType: str | None = None  # Area of effect type
    aoeSize: int | None = None  # AOE size in feet
    rangeDescription: str | None = None  # Human-readable range


class ActionDamage(BaseModel):
    """Damage information for an action.

    EXTRACTION PATHS:
    - diceNotation: actions[].dice.diceString or inventory[].definition.damage.diceString
    - damageType: Map from actions[].damageTypeId or inventory[].definition.damageType
    - fixedDamage: actions[].value (if no dice)
    - bonusDamage: Additional damage from modifiers
    - criticalHitDice: Special crit dice if applicable
    """
    diceNotation: str | None = None  # e.g., "1d8+3"
    damageType: str | None = None  # "slashing", "fire", etc.
    fixedDamage: int | None = None
    bonusDamage: str | None = None
    criticalHitDice: str | None = None


class ActionSave(BaseModel):
    """Saving throw information.

    EXTRACTION PATHS:
    - saveDC: actions[].fixedSaveDc
    - saveAbility: Map from actions[].saveStatId using ABILITY_MAP
    - onSuccess: actions[].saveSuccessDescription (clean HTML)
    - onFailure: actions[].saveFailDescription (clean HTML)
    """
    saveDC: int | None = None
    saveAbility: str | None = None  # "Dexterity", "Wisdom", etc.
    onSuccess: str | None = None
    onFailure: str | None = None


class CharacterAction(BaseModel):
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
    description: str | None = None
    shortDescription: str | None = None  # Snippet or summary

    # Action mechanics
    activation: ActionActivation | None = None
    usage: ActionUsage | None = None
    actionRange: ActionRange | None = None
    damage: ActionDamage | None = None
    save: ActionSave | None = None

    # Classification
    actionCategory: str | None = None  # "attack", "feature", "item", "spell"
    source: str | None = None  # "class", "race", "feat", "item", "background"
    sourceFeature: str | None = None  # Name of the feature/item granting this action

    # Combat details
    attackBonus: int | None = None
    isWeaponAttack: bool = False
    requiresAmmo: bool = False

    # Special properties
    duration: str | None = None
    materials: str | None = None  # Required items or materials


class ActionEconomy(BaseModel):
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
    actions: list[CharacterAction] = Field(default_factory=list)


# ===== FEATURES AND TRAITS TYPES =====

class FeatureActivation(BaseModel):
    """Activation information for features and actions.

    EXTRACTION PATHS:
    - activationTime: actions[].activation.activationTime or feature activation time
    - activationType: Map from actions[].actionType using ACTION_TYPE_MAP
      * 1="action", 2="no_action", 3="bonus_action", 4="reaction", etc.
    """
    activationTime: int | None = None
    activationType: str | None = None  # Converted to human-readable string


class FeatureRange(BaseModel):
    """Range information for feature actions.

    EXTRACTION PATHS:
    - range: actions[].range.range
    - longRange: actions[].range.longRange
    - aoeType: actions[].range.aoeType (1=sphere, 2=cube, 3=cone, 4=line)
    - aoeSize: actions[].range.aoeSize
    - hasAoeSpecialDescription: actions[].range.hasAoeSpecialDescription
    - minimumRange: actions[].range.minimumRange
    """
    range: int | None = None
    longRange: int | None = None
    aoeType: int | None = None
    aoeSize: int | None = None
    hasAoeSpecialDescription: bool | None = None
    minimumRange: int | None = None


class RacialTrait(BaseModel):
    """A racial trait from race or subrace.

    EXTRACTION PATHS:
    - name: race.racialTraits[].definition.name
    - description: race.racialTraits[].definition.description (HTML, needs cleaning)
    - creatureRules: race.racialTraits[].definition.creatureRules
    - featureType: Map from race.racialTraits[].definition.featureType
      * 1="trait", 2="action", 3="bonus_action", 4="reaction", etc.
    """
    name: str
    description: str | None = None
    creatureRules: list[dict[str, Any]] | None = None
    featureType: str | None = None  # Converted to human-readable string


class ClassFeature(BaseModel):
    """A class or subclass feature.

    EXTRACTION PATHS:
    - name: classes[].classFeatures[].definition.name or
            classes[].subclassDefinition.classFeatures[].definition.name
    - description: Corresponding .definition.description (HTML, needs cleaning)
    """
    name: str
    description: str | None = None


class LimitedUse(BaseModel):
    """Limited use information for items and features.

    EXTRACTION PATHS:
    - maxUses: inventory[].limitedUse.maxUses or actions[].limitedUse.maxUses
    - numberUsed: inventory[].limitedUse.numberUsed (for items)
    - resetType: inventory[].limitedUse.resetType or actions[].limitedUse.resetType
      * Map: 1="short_rest", 2="long_rest", 3="dawn", 4="dusk", 5="recharge", 6="turn"
    - resetTypeDescription: inventory[].limitedUse.resetTypeDescription
    """
    maxUses: int | None = None
    numberUsed: int | None = None
    resetType: str | None = None  # Human-readable string
    resetTypeDescription: str | None = None


class Feat(BaseModel):
    """A character feat.

    EXTRACTION PATHS:
    - name: feats[].definition.name
    - description: feats[].definition.description (HTML, needs cleaning)
    - activation: Parse from feats[].definition.activation
    - creatureRules: feats[].definition.creatureRules
    - isRepeatable: feats[].definition.isRepeatable
    """
    name: str
    description: str | None = None
    activation: FeatureActivation | None = None
    creatureRules: list[dict[str, Any]] | None = None
    isRepeatable: bool | None = None


class FeatureAction(BaseModel):
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
    limitedUse: LimitedUse | None = None
    name: str | None = None
    description: str | None = None
    abilityModifierStatName: str | None = None  # Human readable name
    onMissDescription: str | None = None
    saveFailDescription: str | None = None
    saveSuccessDescription: str | None = None
    saveStatId: int | None = None
    fixedSaveDc: int | None = None
    attackTypeRange: int | None = None
    actionType: str | None = None  # Converted to human-readable string
    attackSubtype: int | None = None
    dice: dict[str, Any] | None = None
    value: int | None = None
    damageTypeId: int | None = None
    isMartialArts: bool | None = None
    isProficient: bool | None = None
    spellRangeType: int | None = None
    range: FeatureRange | None = None
    activation: FeatureActivation | None = None


class FeatureModifier(BaseModel):
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
    type: str | None = None
    subType: str | None = None
    dice: dict[str, Any] | None = None
    restriction: str | None = None
    statId: int | None = None
    requiresAttunement: bool | None = None
    duration: dict[str, Any] | None = None
    friendlyTypeName: str | None = None
    friendlySubtypeName: str | None = None
    bonusTypes: list[str] | None = None
    value: int | None = None


class FeaturesAndTraits(BaseModel):
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
    racial_traits: list[RacialTrait] = Field(default_factory=list)
    class_features: dict[str, dict[int, list[ClassFeature]]] = Field(default_factory=dict)
    feats: list[Feat] = Field(default_factory=list)
    modifiers: dict[str, list[FeatureModifier]] = Field(default_factory=dict)


# ===== INVENTORY TYPES =====

class ItemModifier(BaseModel):
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
    type: str | None = None
    subType: str | None = None
    restriction: str | None = None
    friendlyTypeName: str | None = None
    friendlySubtypeName: str | None = None
    duration: dict[str, Any] | None = None
    fixedValue: int | None = None
    diceString: str | None = None


class InventoryItemDefinition(BaseModel):
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
    name: str | None = None
    type: str | None = None
    description: str | None = None
    canAttune: bool | None = None
    attunementDescription: str | None = None
    rarity: str | None = None
    weight: int | float | None = None
    capacity: str | None = None
    capacityWeight: int | None = None
    canEquip: bool | None = None
    magic: bool | None = None
    tags: list[str] | None = None
    grantedModifiers: list[ItemModifier] | None = None
    damage: dict[str, Any] | None = None
    damageType: str | None = None
    attackType: int | None = None
    range: int | None = None
    longRange: int | None = None
    isContainer: bool | None = None
    isCustomItem: bool | None = None


class InventoryItem(BaseModel):
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
    limitedUse: LimitedUse | None = None


class Inventory(BaseModel):
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
    equipped_items: list[InventoryItem] = Field(default_factory=list)
    backpack: list[InventoryItem] = Field(default_factory=list)
    valuables: list[dict[str, Any]] = Field(default_factory=list)


# ===== SPELL TYPES =====

class SpellComponents(BaseModel):
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
    material: bool | str = False


class SpellRite(BaseModel):
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


class Spell(BaseModel):
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
    tags: list[str] = Field(default_factory=list)
    area: str | None = None
    rites: list[SpellRite] | None = None
    charges: int | None = None


class SpellcastingInfo(BaseModel):
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
    cantrips_known: list[str] = Field(default_factory=list)
    spells_known: list[str] = Field(default_factory=list)
    spell_slots: dict[int, int] = Field(default_factory=dict)


class SpellList(BaseModel):
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
    spellcasting: dict[str, SpellcastingInfo] = Field(default_factory=dict)
    spells: dict[str, dict[str, list[Spell]]] = Field(default_factory=dict)


# ===== OBJECTIVES AND CONTRACTS TYPES =====

class BaseObjective(BaseModel):
    """Base for all objectives"""
    id: str
    name: str
    type: str
    status: Literal["Active", "In Progress", "Completed", "Failed", "Suspended", "Abandoned"]
    description: str
    priority: Literal["Absolute", "Critical", "High", "Medium", "Low"] | None = None
    objectives: list[str] = Field(default_factory=list)
    rewards: list[str] = Field(default_factory=list)
    deadline: str | None = None
    notes: str | None = None
    completion_date: str | None = None
    parties: str | None = None
    outcome: str | None = None
    obligations_accepted: list[str] = Field(default_factory=list)
    lasting_effects: list[str] = Field(default_factory=list)


class Quest(BaseObjective):
    """Quest-specific fields"""
    quest_giver: str | None = None
    location: str | None = None
    deity: str | None = None
    purpose: str | None = None
    signs_received: list[str] = Field(default_factory=list)
    divine_favor: str | None = None
    consequences_of_failure: list[str] = Field(default_factory=list)
    motivation: str | None = None
    steps: list[str] = Field(default_factory=list)
    obstacles: list[str] = Field(default_factory=list)
    importance: str | None = None


class Contract(BaseObjective):
    """Contract-specific fields"""
    client: str | None = None
    contractor: str | None = None
    terms: str | None = None
    payment: str | None = None
    penalties: str | None = None
    special_conditions: list[str] = Field(default_factory=list)
    parties: str | None = None
    outcome: str | None = None
    obligations_accepted: list[str] = Field(default_factory=list)
    lasting_effects: list[str] = Field(default_factory=list)


class ContractTemplate(BaseModel):
    """Template for creating new contracts."""
    id: str = ""
    name: str = ""
    type: str = ""
    status: str = ""
    priority: str = ""
    quest_giver: str = ""
    location: str = ""
    description: str = ""
    objectives: list[str] = Field(default_factory=list)
    rewards: list[str] = Field(default_factory=list)
    deadline: str = ""
    notes: str = ""


class ObjectivesAndContracts(BaseModel):
    """All character objectives and contracts."""
    active_contracts: list[Contract] = Field(default_factory=list)
    current_objectives: list[Quest] = Field(default_factory=list)
    completed_objectives: list[Quest | Contract] = Field(default_factory=list)
    contract_templates: dict[str, ContractTemplate] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ===== MAIN CHARACTER CLASS =====

class Character(BaseModel):
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
    organizations: list[Organization] = Field(default_factory=list)
    allies: list[Ally] = Field(default_factory=list)
    enemies: list[Enemy] = Field(default_factory=list)
    proficiencies: list[Proficiency] = Field(default_factory=list)
    damage_modifiers: list[DamageModifier] = Field(default_factory=list)
    passive_scores: PassiveScores | None = None
    senses: Senses | None = None
    action_economy: ActionEconomy | None = None
    features_and_traits: FeaturesAndTraits | None = None
    inventory: Inventory | None = None
    spell_list: SpellList | None = None
    objectives_and_contracts: ObjectivesAndContracts | None = None
    notes: dict[str, Any] = Field(default_factory=dict)
    created_date: datetime | None = None
    last_updated: datetime | None = None


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

CharacterDict = dict[str, Any]
SpellLevel = Literal["cantrip", "1st_level", "2nd_level", "3rd_level", "4th_level",
                     "5th_level", "6th_level", "7th_level", "8th_level", "9th_level"]
ActionType = Literal["action", "bonus_action", "reaction", "no_action", "feature"]
ProficiencyType = Literal["armor", "weapon", "tool", "language", "skill", "saving_throw"]
DamageModifierType = Literal["resistance", "immunity", "vulnerability"]
ObjectiveStatus = Literal["Active", "In Progress", "Completed", "Failed", "Suspended", "Abandoned"]
ObjectivePriority = Literal["Absolute", "Critical", "High", "Medium", "Low"]
