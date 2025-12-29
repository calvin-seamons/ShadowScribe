/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

/**
 * Represents the six core ability scores.
 *
 * EXTRACTION PATHS:
 * - stats[0].value (id=1 = strength)
 * - stats[1].value (id=2 = dexterity)
 * - stats[2].value (id=3 = constitution)
 * - stats[3].value (id=4 = intelligence)
 * - stats[4].value (id=5 = wisdom)
 * - stats[5].value (id=6 = charisma)
 * - overrideStats can override base values if not null
 */
export interface AbilityScores {
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
}
/**
 * How an action is activated.
 *
 * EXTRACTION PATHS:
 * - activationType: Map from actions[].actionType using ACTION_TYPE_MAP
 * - activationTime: actions[].activation.activationTime
 * - activationCondition: Parse from action description or activation data
 */
export interface ActionActivation {
  activationType?: string | null;
  activationTime?: number | null;
  activationCondition?: string | null;
}
/**
 * Damage information for an action.
 *
 * EXTRACTION PATHS:
 * - diceNotation: actions[].dice.diceString or inventory[].definition.damage.diceString
 * - damageType: Map from actions[].damageTypeId or inventory[].definition.damageType
 * - fixedDamage: actions[].value (if no dice)
 * - bonusDamage: Additional damage from modifiers
 * - criticalHitDice: Special crit dice if applicable
 */
export interface ActionDamage {
  diceNotation?: string | null;
  damageType?: string | null;
  fixedDamage?: number | null;
  bonusDamage?: string | null;
  criticalHitDice?: string | null;
}
/**
 * Character's action economy information.
 *
 * EXTRACTION PATHS:
 * - attacks_per_action: NOT DIRECTLY AVAILABLE - Must be calculated from class features
 *   * Look for "Extra Attack" features in classes[].classFeatures[]
 *   * Default is 1, increases based on fighter/ranger/paladin levels
 *   * Some subclasses grant additional attacks
 * - actions: Aggregate from multiple sources:
 *   * actions.class[] (class features that are actions)
 *   * actions.race[] (racial abilities)
 *   * actions.feat[] (feat-granted actions)
 *   * actions.item[] (item-granted actions)
 *   * inventory[] (weapon attacks)
 *   * Convert each to CharacterAction objects
 *
 * MISSING INFORMATION:
 * - No explicit "attacks per action" field in JSON
 * - Must derive from class features and levels
 *
 * LLM ASSISTANCE NEEDED:
 * - Parse class features to identify "Extra Attack" or similar abilities
 * - Calculate attacks per action based on class levels and features
 * - Convert various action sources into unified CharacterAction format
 * - Identify passive vs active abilities
 */
export interface ActionEconomy {
  attacks_per_action?: number;
  actions?: CharacterAction[];
}
/**
 * A complete character action with all relevant information.
 *
 * This unified model represents all types of actions: attacks, features, spells, etc.
 *
 * EXTRACTION PATHS:
 * - name: actions[category][].name or inventory[].definition.name (for weapons)
 * - description: Clean HTML from actions[].description or inventory[].definition.description
 * - shortDescription: actions[].snippet or generated summary
 * - activation: Parse using ActionActivation from actions[].activation and actionType
 * - usage: Parse using ActionUsage from actions[].limitedUse
 * - actionRange: Parse using ActionRange from actions[].range
 * - damage: Parse using ActionDamage from actions[].dice or inventory damage
 * - save: Parse using ActionSave from actions[] save data
 * - actionCategory: "attack", "feature", "spell", "unequipped_weapon", "item"
 * - source: "class", "race", "feat", "item", "background"
 * - sourceFeature: Name of feature/item granting this action
 * - attackBonus: actions[].fixedToHit
 * - isWeaponAttack: True if actions[].attackType in [1, 2] (melee/ranged)
 * - requiresAmmo: True if weapon has "ammunition" or "thrown" property
 * - duration: Parse from spell/ability duration data
 * - materials: Parse from spell components or item requirements
 *
 * ACTION TYPE MAPPINGS:
 * - actionType: 1="action", 2="no_action", 3="bonus_action", 4="reaction", etc.
 * - resetType: 1="short_rest", 2="long_rest", 3="dawn", 4="dusk", etc.
 * - damageTypeId: 1="bludgeoning", 2="piercing", 3="slashing", 4="necrotic", etc.
 * - saveStatId: 1="Strength", 2="Dexterity", 3="Constitution", 4="Intelligence", 5="Wisdom", 6="Charisma"
 */
export interface CharacterAction {
  name: string;
  description?: string | null;
  shortDescription?: string | null;
  activation?: ActionActivation | null;
  usage?: ActionUsage | null;
  actionRange?: ActionRange | null;
  damage?: ActionDamage | null;
  save?: ActionSave | null;
  actionCategory?: string | null;
  source?: string | null;
  sourceFeature?: string | null;
  attackBonus?: number | null;
  isWeaponAttack?: boolean;
  requiresAmmo?: boolean;
  duration?: string | null;
  materials?: string | null;
}
/**
 * Usage limitations for an action.
 *
 * EXTRACTION PATHS:
 * - maxUses: actions[].limitedUse.maxUses
 * - resetType: Map from actions[].limitedUse.resetType using RESET_TYPE_MAP
 * - usesPerActivation: actions[].limitedUse.minNumberConsumed (default 1)
 */
export interface ActionUsage {
  maxUses?: number | null;
  resetType?: string | null;
  usesPerActivation?: number | null;
}
/**
 * Range information for an action.
 *
 * EXTRACTION PATHS:
 * - range: actions[].range.range or inventory[].definition.range
 * - longRange: actions[].range.longRange or inventory[].definition.longRange
 * - aoeType: Map from actions[].range.aoeType (1=sphere, 2=cube, 3=cone, 4=line)
 * - aoeSize: actions[].range.aoeSize
 * - rangeDescription: Generated from range/longRange/aoe data
 */
export interface ActionRange {
  range?: number | null;
  longRange?: number | null;
  aoeType?: string | null;
  aoeSize?: number | null;
  rangeDescription?: string | null;
}
/**
 * Saving throw information.
 *
 * EXTRACTION PATHS:
 * - saveDC: actions[].fixedSaveDc
 * - saveAbility: Map from actions[].saveStatId using ABILITY_MAP
 * - onSuccess: actions[].saveSuccessDescription (clean HTML)
 * - onFailure: actions[].saveFailDescription (clean HTML)
 */
export interface ActionSave {
  saveDC?: number | null;
  saveAbility?: string | null;
  onSuccess?: string | null;
  onFailure?: string | null;
}
/**
 * An ally or contact.
 *
 * EXTRACTION PATHS:
 * - Parse from data.notes.allies (numbered list with markdown formatting)
 *
 * Example structure:
 * "1. **High Acolyte Aldric**: His mentor and leader of the Holy Knights of Kluntul..."
 *
 * NOTE: Requires LLM parsing of markdown-formatted text to extract:
 * - name: Extract from markdown bold text (e.g., "High Acolyte Aldric")
 * - description: Extract descriptive text after the colon
 * - title: May be part of the name or description (e.g., "High Acolyte")
 *
 * The JSON stores allies as a formatted string with numbered entries,
 * not as an array of structured objects.
 */
export interface Ally {
  name: string;
  description: string;
  title?: string | null;
}
/**
 * A background feature with name and description.
 *
 * EXTRACTION PATHS:
 * - name: data.background.definition.featureName
 * - description: data.background.definition.featureDescription (HTML content, may need cleaning)
 *
 * Example from Acolyte background:
 * - name: "Shelter of the Faithful"
 * - description: HTML description of the feature's mechanics and benefits
 */
export interface BackgroundFeature {
  name: string;
  description: string;
}
/**
 * Character background information.
 *
 * EXTRACTION PATHS:
 * - name: data.background.definition.name
 * - feature: Create BackgroundFeature from data.background.definition.featureName and featureDescription
 * - skill_proficiencies: Parse from data.background.definition.skillProficienciesDescription (comma-separated list)
 * - tool_proficiencies: Parse from data.background.definition.toolProficienciesDescription (comma-separated list, may be empty)
 * - language_proficiencies: Parse from data.background.definition.languagesDescription (descriptive text, may need interpretation)
 * - equipment: Parse from data.background.definition.equipmentDescription (descriptive text listing items)
 * - feature_description: Same as data.background.definition.featureDescription (duplicate of feature.description)
 *
 * NOTE: Proficiency descriptions are text that need parsing, not structured arrays.
 * Language descriptions may be vague (e.g., "Two of your choice").
 */
export interface BackgroundInfo {
  name: string;
  feature: BackgroundFeature;
  skill_proficiencies?: string[];
  tool_proficiencies?: string[];
  language_proficiencies?: string[];
  equipment?: string[];
  feature_description?: string | null;
}
/**
 * Complete character backstory.
 *
 *     EXTRACTION PATHS:
 *     - title: Extract first markdown header from data.notes.backstory
 *     - family_backstory: Must be parsed from data.notes.backstory using LLM
 *     - sections: Parse all markdown sections from data.notes.backstory
 *
 *     Example structure in JSON:
 *     data.notes.backstory: "**The Battle of Shadow's Edge**
 *
 * Under the tutelage..."
 *
 *     NOTE: Requires LLM parsing of markdown-formatted free text to extract:
 *     - Section headers (** Header **)
 *     - Section content (text between headers)
 *     - Family information (parents, relationships)
 *     - Story structure and organization
 *
 */
export interface Backstory {
  title: string;
  family_backstory: FamilyBackstory;
  sections?: BackstorySection[];
}
/**
 * Family background information.
 *
 * EXTRACTION PATHS:
 * WARNING: D&D Beyond does NOT store family backstory as a separate structured field.
 *
 * - parents: Must be extracted from the main backstory text (data.notes.backstory)
 * - sections: Must parse markdown sections from data.notes.backstory
 *
 * NOTE: This entire dataclass represents data that must be extracted using an LLM
 * to parse unstructured backstory text and identify family-related information.
 * The backstory is stored as free-form markdown text, not structured data.
 */
export interface FamilyBackstory {
  parents: string;
  sections?: BackstorySection[];
}
/**
 * A section of the character's backstory.
 *
 *     EXTRACTION PATHS:
 *     WARNING: D&D Beyond does NOT store backstory as structured sections.
 *
 *     - Backstory is stored as single markdown text: data.notes.backstory
 *     - Contains markdown formatting (**,
 *
 *  for sections)
 *     - Must parse markdown headers (** text **) to extract section headings
 *     - Must split content between headers to create sections
 *
 *     ALTERNATIVE EXTRACTION:
 *     - heading: Extract from markdown headers in data.notes.backstory
 *     - content: Extract content between headers
 *
 *     NOTE: This requires custom parsing of markdown-formatted text.
 *     Example structure in JSON: "**Header**
 *
 * Content text
 *
 * **Next Header**
 *
 * More content"
 *     Might need to ask LLM to parse into structured sections.
 *
 */
export interface BackstorySection {
  heading: string;
  content: string;
}
/**
 * Base for all objectives
 */
export interface BaseObjective {
  id: string;
  name: string;
  type: string;
  status: "Active" | "In Progress" | "Completed" | "Failed" | "Suspended" | "Abandoned";
  description: string;
  priority?: ("Absolute" | "Critical" | "High" | "Medium" | "Low") | null;
  objectives?: string[];
  rewards?: string[];
  deadline?: string | null;
  notes?: string | null;
  completion_date?: string | null;
  parties?: string | null;
  outcome?: string | null;
  obligations_accepted?: string[];
  lasting_effects?: string[];
}
/**
 * Complete character definition combining all aspects.
 */
export interface Character {
  character_base: CharacterBase;
  characteristics: PhysicalCharacteristics;
  ability_scores: AbilityScores;
  combat_stats: CombatStats;
  background_info: BackgroundInfo;
  personality: PersonalityTraits;
  backstory: Backstory;
  organizations?: Organization[];
  allies?: Ally[];
  enemies?: Enemy[];
  proficiencies?: Proficiency[];
  damage_modifiers?: DamageModifier[];
  passive_scores?: PassiveScores | null;
  senses?: Senses | null;
  action_economy?: ActionEconomy | null;
  features_and_traits?: FeaturesAndTraits | null;
  inventory?: Inventory | null;
  spell_list?: SpellList | null;
  objectives_and_contracts?: ObjectivesAndContracts | null;
  notes?: {
    [k: string]: unknown;
  };
  created_date?: string | null;
  last_updated?: string | null;
}
/**
 * Basic character information.
 *
 * EXTRACTION PATHS:
 * - name: data.name
 * - race: race.fullName (e.g., "Hill Dwarf") or race.baseName for base race
 * - character_class: classes[0].definition.name (primary/starting class)
 * - total_level: sum of all classes[].level
 * - alignment: lookup alignmentId in alignment reference table
 * - background: background.definition.name
 * - subrace: race.subRaceShortName (if race.isSubRace is true)
 * - multiclass_levels: {classes[].definition.name: classes[].level} for each class
 * - lifestyle: lookup lifestyleId in lifestyle reference table
 */
export interface CharacterBase {
  name: string;
  race: string;
  character_class: string;
  total_level: number;
  alignment: string;
  background: string;
  subrace?: string | null;
  multiclass_levels?: {
    [k: string]: number;
  } | null;
  lifestyle?: string | null;
}
/**
 * Physical appearance and traits.
 *
 * EXTRACTION PATHS:
 * - alignment: lookup data.alignmentId in alignment reference table
 * - gender: data.gender
 * - eyes: data.eyes
 * - size: lookup data.race.sizeId in size reference table (4 = Medium)
 * - height: data.height
 * - hair: data.hair
 * - skin: data.skin
 * - age: data.age
 * - weight: data.weight (may need to add unit like "lb")
 * - faith: data.faith
 */
export interface PhysicalCharacteristics {
  alignment: string;
  gender: string;
  eyes: string;
  size: string;
  height: string;
  hair: string;
  skin: string;
  age: number;
  weight: string;
  faith?: string | null;
}
/**
 * Core combat statistics.
 *
 * EXTRACTION PATHS:
 * - max_hp: overrideHitPoints (if not null) or baseHitPoints + bonusHitPoints
 * - armor_class: calculated from equipped armor items in inventory[].definition.armorClass
 * - initiative_bonus: calculated from dex modifier + modifiers
 * - speed: race.weightSpeeds.normal.walk (base walking speed)
 * - hit_dice: classes[].definition.hitDice (per class level)
 */
export interface CombatStats {
  max_hp: number;
  armor_class: number;
  initiative_bonus: number;
  speed: number;
  hit_dice?: {
    [k: string]: string;
  } | null;
}
/**
 * Personality traits, ideals, bonds, and flaws.
 *
 *     EXTRACTION PATHS:
 *     - personality_traits: Split data.traits.personalityTraits on newlines (
 * )
 *     - ideals: Split data.traits.ideals on newlines (
 * )
 *     - bonds: Split data.traits.bonds on newlines (
 * )
 *     - flaws: Split data.traits.flaws on newlines (
 * )
 *
 *     NOTE: These are stored as single strings with newline separators, not arrays.
 *     May contain multiple entries per field separated by
 *  characters.
 *     Probably will need to ask LLM to parse into lists.
 *
 */
export interface PersonalityTraits {
  personality_traits?: string[];
  ideals?: string[];
  bonds?: string[];
  flaws?: string[];
}
/**
 * An organization the character belongs to.
 *
 * EXTRACTION PATHS:
 * - Parse from data.notes.organizations (free text with organization descriptions)
 *
 * Example structure:
 * "The Holy Knights of Kluntul: As a high-ranking officer, Duskryn plays a significant role..."
 *
 * NOTE: Requires LLM parsing of free text to extract:
 * - name: Organization name (e.g., "The Holy Knights of Kluntul")
 * - role: Character's role/position in the organization
 * - description: Organization's purpose and character's involvement
 *
 * The JSON stores this as unstructured descriptive text, not separate fields.
 */
export interface Organization {
  name: string;
  role: string;
  description: string;
}
/**
 * An enemy or rival.
 *
 *     EXTRACTION PATHS:
 *     - Parse from data.notes.enemies (simple text list)
 *
 *     Example structure:
 *     "Xurmurrin, The Voiceless One
 * Anyone who is an enemy of Etherena"
 *
 *     NOTE: Requires LLM parsing of free text to extract:
 *     - name: Extract enemy names from newline-separated text
 *     - description: May need to infer from context or backstory
 *
 *     The JSON stores enemies as simple newline-separated text,
 *     not structured data with separate name/description fields.
 *     Enemy descriptions may need to be extracted from the backstory text.
 *
 */
export interface Enemy {
  name: string;
  description: string;
}
/**
 * Represents a skill, tool, language, or armor proficiency.
 *
 * EXTRACTION PATHS:
 * - Extract from data.modifiers[category] where category in ["race", "class", "background", "item", "feat"]
 * - Filter modifiers where modifier.type == "proficiency"
 * - type: map modifier.subType to appropriate category:
 *   * weapon subtypes (e.g., "warhammer", "battleaxe") -> "weapon"
 *   * tool subtypes (e.g., "smiths-tools", "poisoners-kit") -> "tool"
 *   * skill subtypes (e.g., "insight", "religion") -> "skill"
 *   * armor subtypes -> "armor"
 *   * language subtypes -> "language"
 *   * saving throw subtypes -> "saving_throw"
 * - name: modifier.friendlySubtypeName (e.g., "Smith's Tools", "Warhammer")
 */
export interface Proficiency {
  type: "armor" | "weapon" | "tool" | "language" | "skill" | "saving_throw";
  name: string;
}
/**
 * Damage resistance, immunity, or vulnerability.
 *
 * EXTRACTION PATHS:
 * - Extract from data.modifiers[category] where category in ["race", "class", "background", "item", "feat"]
 * - Filter modifiers where modifier.type in ["resistance", "immunity", "vulnerability"]
 * - damage_type: modifier.subType (e.g., "poison", "acid", "fire")
 * - modifier_type: modifier.type ("resistance", "immunity", or "vulnerability")
 */
export interface DamageModifier {
  damage_type: string;
  modifier_type: "resistance" | "immunity" | "vulnerability";
}
/**
 * Passive perception and other passive abilities.
 *
 * EXTRACTION PATHS:
 * NOTE: D&D Beyond does not store pre-calculated passive scores in the JSON.
 * These must be calculated from ability scores and proficiencies:
 * - perception: 10 + WIS modifier + proficiency bonus (if proficient in Perception)
 * - investigation: 10 + INT modifier + proficiency bonus (if proficient in Investigation)
 * - insight: 10 + WIS modifier + proficiency bonus (if proficient in Insight)
 * - stealth: 10 + DEX modifier + proficiency bonus (if proficient in Stealth)
 *
 * Base ability scores from data.stats[] and overrideStats[]
 * Proficiencies from data.modifiers[category] where type="proficiency" and subType matches skill name
 */
export interface PassiveScores {
  perception: number;
  investigation?: number | null;
  insight?: number | null;
  stealth?: number | null;
}
/**
 * Special senses in D&D 5e.
 *
 * EXTRACTION PATHS:
 * - Extract from data.modifiers[category] where category in ["race", "class", "background", "item", "feat"]
 * - Filter modifiers where modifier.type == "set-base" and modifier.subType contains sense names:
 *   * "darkvision": modifier.value (range in feet, e.g., 60)
 *   * "blindsight": modifier.value (range in feet)
 *   * "tremorsense": modifier.value (range in feet)
 *   * "truesight": modifier.value (range in feet)
 *   * Other special senses as they appear
 * - Some senses may also be found in class features or spell descriptions
 *
 * NOTE: Not all characters will have special senses beyond normal vision.
 *
 * A flexible dictionary to store any type of sense with its range or description.
 * Common examples:
 * - "darkvision": 60 (feet)
 * - "blindsight": 30
 * - "tremorsense": 20
 * - "truesight": 120
 * - "devils_sight": 120
 * - "ethereal_sight": 60
 * - "see_invisibility": 10
 *
 * - "superior_darkvision": 120
 *
 * Values can be integers (ranges in feet) or strings (descriptive values).
 */
export interface Senses {
  senses?: {
    [k: string]: number | string;
  };
}
/**
 * Container for all character features and traits.
 *
 * EXTRACTION PATHS:
 * - racial_traits: Parse from race.racialTraits[] as RacialTrait objects
 * - class_features: Parse from classes[].classFeatures[] organized by class name and level
 *   * Key format: class name (e.g., "Warlock", "Cleric")
 *   * Value format: Dict[int, List[ClassFeature]] - features grouped by required level
 * - feats: Parse from feats[] as Feat objects
 * - modifiers: Parse from modifiers[category][] organized by category
 *   * Categories: "race", "class", "background", "item", "feat", "condition"
 *   * Each category contains List[FeatureModifier]
 *
 * ORGANIZATION:
 * - racial_traits: Flat list of all racial traits (base race + subrace)
 * - class_features: Nested dict by class name, then by level
 * - feats: Flat list of all feats
 * - modifiers: Dict by source category
 *
 * NOTE: Character actions are parsed separately by parse_actions.py into CharacterAction objects.
 *       See ActionEconomy dataclass for the complete action system.
 */
export interface FeaturesAndTraits {
  racial_traits?: RacialTrait[];
  class_features?: {
    [k: string]: {
      [k: string]: ClassFeature[];
    };
  };
  feats?: Feat[];
  modifiers?: {
    [k: string]: FeatureModifier[];
  };
}
/**
 * A racial trait from race or subrace.
 *
 * EXTRACTION PATHS:
 * - name: race.racialTraits[].definition.name
 * - description: race.racialTraits[].definition.description (HTML, needs cleaning)
 * - creatureRules: race.racialTraits[].definition.creatureRules
 * - featureType: Map from race.racialTraits[].definition.featureType
 *   * 1="trait", 2="action", 3="bonus_action", 4="reaction", etc.
 */
export interface RacialTrait {
  name: string;
  description?: string | null;
  creatureRules?:
    | {
        [k: string]: unknown;
      }[]
    | null;
  featureType?: string | null;
}
/**
 * A class or subclass feature.
 *
 * EXTRACTION PATHS:
 * - name: classes[].classFeatures[].definition.name or
 *         classes[].subclassDefinition.classFeatures[].definition.name
 * - description: Corresponding .definition.description (HTML, needs cleaning)
 */
export interface ClassFeature {
  name: string;
  description?: string | null;
}
/**
 * A character feat.
 *
 * EXTRACTION PATHS:
 * - name: feats[].definition.name
 * - description: feats[].definition.description (HTML, needs cleaning)
 * - activation: Parse from feats[].definition.activation
 * - creatureRules: feats[].definition.creatureRules
 * - isRepeatable: feats[].definition.isRepeatable
 */
export interface Feat {
  name: string;
  description?: string | null;
  activation?: FeatureActivation | null;
  creatureRules?:
    | {
        [k: string]: unknown;
      }[]
    | null;
  isRepeatable?: boolean | null;
}
/**
 * Activation information for features and actions.
 *
 * EXTRACTION PATHS:
 * - activationTime: actions[].activation.activationTime or feature activation time
 * - activationType: Map from actions[].actionType using ACTION_TYPE_MAP
 *   * 1="action", 2="no_action", 3="bonus_action", 4="reaction", etc.
 */
export interface FeatureActivation {
  activationTime?: number | null;
  activationType?: string | null;
}
/**
 * A modifier granted by a feature.
 *
 * EXTRACTION PATHS:
 * - type: modifiers[category][].type
 * - subType: modifiers[category][].subType
 * - dice: modifiers[category][].dice
 * - restriction: modifiers[category][].restriction
 * - statId: modifiers[category][].statId
 * - requiresAttunement: modifiers[category][].requiresAttunement
 * - duration: modifiers[category][].duration
 * - friendlyTypeName: modifiers[category][].friendlyTypeName
 * - friendlySubtypeName: modifiers[category][].friendlySubtypeName
 * - bonusTypes: modifiers[category][].bonusTypes
 * - value: modifiers[category][].value
 */
export interface FeatureModifier {
  type?: string | null;
  subType?: string | null;
  dice?: {
    [k: string]: unknown;
  } | null;
  restriction?: string | null;
  statId?: number | null;
  requiresAttunement?: boolean | null;
  duration?: {
    [k: string]: unknown;
  } | null;
  friendlyTypeName?: string | null;
  friendlySubtypeName?: string | null;
  bonusTypes?: string[] | null;
  value?: number | null;
}
/**
 * Character's complete inventory.
 *
 * EXTRACTION PATHS:
 * - total_weight: CALCULATED - sum all inventory[].definition.weight * inventory[].quantity
 *   * Consider inventory[].definition.weightMultiplier (usually 1 or 0)
 *   * Some items like Bag of Holding have weightMultiplier = 0
 * - weight_unit: NOT EXPLICIT - assume "lb" (pounds) as D&D standard
 * - equipped_items: All inventory[] items where inventory[].equipped == true
 * - backpack: All inventory[] items where inventory[].equipped == false
 * - valuables: NOT AVAILABLE - no separate valuables tracking in D&D Beyond
 *
 * INVENTORY ORGANIZATION:
 * - Simple equipped/backpack split based on equipped status
 * - No slot-based categorization
 *
 * CURRENCY TRACKING:
 * - Separate currencies object: {"cp": int, "sp": int, "gp": int, "ep": int, "pp": int}
 * - Not included in regular inventory weight calculations
 */
export interface Inventory {
  total_weight: number;
  weight_unit?: string;
  equipped_items?: InventoryItem[];
  backpack?: InventoryItem[];
  valuables?: {
    [k: string]: unknown;
  }[];
}
/**
 * An inventory item with quantity and equipped status.
 *
 * EXTRACTION PATHS:
 * - definition: Parse inventory[].definition as InventoryItemDefinition
 * - quantity: inventory[].quantity
 * - isAttuned: inventory[].isAttuned
 * - equipped: inventory[].equipped
 * - limitedUse: Parse inventory[].limitedUse as LimitedUse (if present)
 */
export interface InventoryItem {
  definition: InventoryItemDefinition;
  quantity: number;
  isAttuned: boolean;
  equipped: boolean;
  limitedUse?: LimitedUse | null;
}
/**
 * Definition of an inventory item with all properties.
 *
 * EXTRACTION PATHS:
 * - name: inventory[].definition.name
 * - type: inventory[].definition.type
 * - description: inventory[].definition.description (HTML, needs cleaning)
 * - canAttune: inventory[].definition.canAttune
 * - attunementDescription: inventory[].definition.attunementDescription
 * - rarity: inventory[].definition.rarity
 * - weight: inventory[].definition.weight
 * - capacity: inventory[].definition.capacity
 * - capacityWeight: inventory[].definition.capacityWeight
 * - canEquip: inventory[].definition.canEquip
 * - magic: inventory[].definition.magic
 * - tags: inventory[].definition.tags
 * - grantedModifiers: Parse inventory[].definition.grantedModifiers[] as ItemModifier objects
 * - damage: inventory[].definition.damage
 * - damageType: inventory[].definition.damageType
 * - attackType: inventory[].definition.attackType
 * - range: inventory[].definition.range
 * - longRange: inventory[].definition.longRange
 * - isContainer: inventory[].definition.isContainer
 * - isCustomItem: inventory[].definition.isCustomItem
 */
export interface InventoryItemDefinition {
  name?: string | null;
  type?: string | null;
  description?: string | null;
  canAttune?: boolean | null;
  attunementDescription?: string | null;
  rarity?: string | null;
  weight?: number | null;
  capacity?: string | null;
  capacityWeight?: number | null;
  canEquip?: boolean | null;
  magic?: boolean | null;
  tags?: string[] | null;
  grantedModifiers?: ItemModifier[] | null;
  damage?: {
    [k: string]: unknown;
  } | null;
  damageType?: string | null;
  attackType?: number | null;
  range?: number | null;
  longRange?: number | null;
  isContainer?: boolean | null;
  isCustomItem?: boolean | null;
}
/**
 * A modifier granted by an inventory item.
 *
 * EXTRACTION PATHS:
 * - type: inventory[].definition.grantedModifiers[].type
 * - subType: inventory[].definition.grantedModifiers[].subType
 * - restriction: inventory[].definition.grantedModifiers[].restriction
 * - friendlyTypeName: inventory[].definition.grantedModifiers[].friendlyTypeName
 * - friendlySubtypeName: inventory[].definition.grantedModifiers[].friendlySubtypeName
 * - duration: inventory[].definition.grantedModifiers[].duration
 * - fixedValue: inventory[].definition.grantedModifiers[].fixedValue
 * - diceString: inventory[].definition.grantedModifiers[].dice.diceString
 */
export interface ItemModifier {
  type?: string | null;
  subType?: string | null;
  restriction?: string | null;
  friendlyTypeName?: string | null;
  friendlySubtypeName?: string | null;
  duration?: {
    [k: string]: unknown;
  } | null;
  fixedValue?: number | null;
  diceString?: string | null;
}
/**
 * Limited use information for items and features.
 *
 * EXTRACTION PATHS:
 * - maxUses: inventory[].limitedUse.maxUses or actions[].limitedUse.maxUses
 * - numberUsed: inventory[].limitedUse.numberUsed (for items)
 * - resetType: inventory[].limitedUse.resetType or actions[].limitedUse.resetType
 *   * Map: 1="short_rest", 2="long_rest", 3="dawn", 4="dusk", 5="recharge", 6="turn"
 * - resetTypeDescription: inventory[].limitedUse.resetTypeDescription
 */
export interface LimitedUse {
  maxUses?: number | null;
  numberUsed?: number | null;
  resetType?: string | null;
  resetTypeDescription?: string | null;
}
/**
 * Complete spell list organized by class.
 *
 * EXTRACTION PATHS:
 * - spellcasting: Create SpellcastingInfo for each spellcasting class
 *   * Key: class name from classes[].definition.name
 *   * Value: SpellcastingInfo with that class's spellcasting data
 * - spells: Organize all character spells by class and level
 *   * Outer key: class name
 *   * Inner key: spell level ("cantrip", "1st_level", etc.)
 *   * Value: List of Spell objects
 *
 * SPELLCASTING CLASSES:
 * - Only classes with canCastSpells == true have spellcasting
 * - Each class has spellCastingAbilityId for their casting ability
 * - Spell preparation varies by class (spellPrepareType)
 *
 * SPELL ORGANIZATION IN JSON:
 * - spells object contains arrays by source:
 *   * spells.class[] - spells from class features
 *   * spells.race[] - racial spells
 *   * spells.item[] - item-granted spells
 *   * spells.feat[] - feat-granted spells
 *   * spells.background[] - background spells
 *
 * MULTICLASS SPELLCASTING:
 * - Each class tracked separately in classSpells[]
 * - Different classes may have different spell lists
 * - Some classes share spell slots, others don't
 *
 * MISSING INFORMATION:
 * - No pre-organized structure by class and level
 * - Must manually group spells by source class
 * - Spell level organization needs custom logic
 *
 * LLM ASSISTANCE NEEDED:
 * - Identify which classes are spellcasting classes
 * - Group spells by their source class
 * - Organize spells by level within each class
 * - Handle multiclass spellcasting rules
 * - Convert spell level numbers to string format
 * - Create SpellcastingInfo for each casting class
 * - Handle different spell preparation types
 */
export interface SpellList {
  spellcasting?: {
    [k: string]: SpellcastingInfo;
  };
  spells?: {
    [k: string]: {
      [k: string]: Spell[];
    };
  };
}
/**
 * Spellcasting ability information.
 *
 * EXTRACTION PATHS:
 * - ability: classes[].definition.spellCastingAbilityId (requires lookup to ability name)
 * - spell_save_dc: CALCULATED - 8 + proficiency bonus + ability modifier
 * - spell_attack_bonus: CALCULATED - proficiency bonus + ability modifier
 * - cantrips_known: Filter spells where level == 0
 * - spells_known: Filter spells where level > 0
 * - spell_slots: spellSlots[] array with level/available/used
 *
 * SPELLCASTING ABILITY MAPPING:
 * - spellCastingAbilityId to ability name:
 *   * 1 = "strength", 2 = "dexterity", 3 = "constitution"
 *   * 4 = "intelligence", 5 = "wisdom", 6 = "charisma"
 *
 * SPELL SLOT STRUCTURE:
 * - spellSlots[] array with objects: {level, used, available}
 * - Separate pactMagic[] array for warlock slots
 *
 * SPELL ORGANIZATION:
 * - Spells organized by source: spells.class[], spells.race[], etc.
 * - Each source contains spells for that category
 * - prepared/known status tracked per spell
 *
 * MISSING INFORMATION:
 * - Save DC and attack bonus not pre-calculated
 * - Must derive ability name from ID
 * - Need to filter and organize spells by level
 *
 * LLM ASSISTANCE NEEDED:
 * - Map spellCastingAbilityId to ability names
 * - Calculate save DC and attack bonus from ability scores
 * - Filter and organize spells by level (cantrips vs leveled)
 * - Handle multiclass spellcasting scenarios
 * - Convert spell slot structure to level:count format
 */
export interface SpellcastingInfo {
  ability: string;
  spell_save_dc: number;
  spell_attack_bonus: number;
  cantrips_known?: string[];
  spells_known?: string[];
  spell_slots?: {
    [k: string]: number;
  };
}
/**
 * A spell definition.
 *
 * EXTRACTION PATHS:
 * - name: spells.*.*.definition.name (from character's known spells)
 * - level: spells.*.*.definition.level
 * - school: spells.*.*.definition.school (may need lookup)
 * - casting_time: spells.*.*.activation.activationTime + activationType
 * - range: spells.*.*.range.range
 * - components: Create SpellComponents from spell definition (limited data)
 * - duration: spells.*.*.duration (may need parsing)
 * - description: spells.*.*.definition.description (HTML, needs cleaning)
 * - concentration: spells.*.*.concentration
 * - ritual: spells.*.*.castOnlyAsRitual or ritualCastingType
 * - tags: spells.*.*.definition.tags (if available)
 * - area: spells.*.*.range.aoeType + aoeSize
 * - rites: NOT AVAILABLE - see SpellRite comments
 * - charges: spells.*.*.charges (for item spells)
 *
 * SPELL SOURCES IN JSON:
 * - spells.race[] - racial spells
 * - spells.class[] - class spells
 * - spells.background[] - background spells (rare)
 * - spells.item[] - item-granted spells
 * - spells.feat[] - feat-granted spells
 *
 * SPELL STRUCTURE:
 * - Each spell has definition object with basic info
 * - Range object with range/aoe data
 * - Activation object with casting time info
 * - Limited use tracking for charged spells
 *
 * MISSING INFORMATION:
 * - Spell components not fully detailed in character JSON
 * - School might be ID that needs lookup
 * - Duration often needs parsing from description
 * - Tags may not be present for all spells
 *
 * LLM ASSISTANCE NEEDED:
 * - Parse HTML descriptions to clean text
 * - Extract spell components from description text
 * - Convert activation data to readable casting time
 * - Parse duration information from various formats
 * - Map school IDs to school names if needed
 * - Extract area information from range data
 */
export interface Spell {
  name: string;
  level: number;
  school: string;
  casting_time: string;
  range: string;
  components: SpellComponents;
  duration: string;
  description: string;
  concentration?: boolean;
  ritual?: boolean;
  tags?: string[];
  area?: string | null;
  rites?: SpellRite[] | null;
  charges?: number | null;
}
/**
 * Components required for spellcasting.
 *
 * EXTRACTION PATHS:
 * - verbal: NOT DIRECTLY AVAILABLE - must parse from spell definitions
 * - somatic: NOT DIRECTLY AVAILABLE - must parse from spell definitions
 * - material: NOT DIRECTLY AVAILABLE - must parse from spell definitions
 *
 * SPELL COMPONENT SOURCES:
 * - D&D Beyond doesn't store spell components in character JSON
 * - Spell definitions would need to be fetched from separate API/database
 * - Character JSON only contains spell references, not full spell data
 *
 * MISSING INFORMATION:
 * - No spell component data in character JSON
 * - Would need external spell database lookup
 * - Components typically stored as text strings in spell descriptions
 *
 * LLM ASSISTANCE NEEDED:
 * - Parse spell descriptions to identify V/S/M components
 * - Extract material component details from spell text
 * - Convert component text to boolean/string format
 */
export interface SpellComponents {
  verbal?: boolean;
  somatic?: boolean;
  material?: boolean | string;
}
/**
 * A rite option for certain spells.
 *
 * EXTRACTION PATHS:
 * - name: NOT AVAILABLE - D&D Beyond doesn't use rite system
 * - effect: NOT AVAILABLE - D&D Beyond doesn't use rite system
 *
 * RITE SYSTEM:
 * - This appears to be a custom system not used by D&D Beyond
 * - D&D Beyond doesn't have spell "rites" as separate options
 * - May be specific to your campaign/system
 *
 * MISSING INFORMATION:
 * - No rite data in D&D Beyond JSON
 * - Would need custom implementation or campaign-specific data
 *
 * LLM ASSISTANCE NEEDED:
 * - Identify if any spells have variant options that could be considered "rites"
 * - Extract spell options from descriptions if present
 * - Create rite structures from spell variant text
 */
export interface SpellRite {
  name: string;
  effect: string;
}
/**
 * All character objectives and contracts.
 */
export interface ObjectivesAndContracts {
  active_contracts?: Contract[];
  current_objectives?: Quest[];
  completed_objectives?: (Quest | Contract)[];
  contract_templates?: {
    [k: string]: ContractTemplate;
  };
  metadata?: {
    [k: string]: unknown;
  };
}
/**
 * Contract-specific fields
 */
export interface Contract {
  id: string;
  name: string;
  type: string;
  status: "Active" | "In Progress" | "Completed" | "Failed" | "Suspended" | "Abandoned";
  description: string;
  priority?: ("Absolute" | "Critical" | "High" | "Medium" | "Low") | null;
  objectives?: string[];
  rewards?: string[];
  deadline?: string | null;
  notes?: string | null;
  completion_date?: string | null;
  parties?: string | null;
  outcome?: string | null;
  obligations_accepted?: string[];
  lasting_effects?: string[];
  client?: string | null;
  contractor?: string | null;
  terms?: string | null;
  payment?: string | null;
  penalties?: string | null;
  special_conditions?: string[];
}
/**
 * Quest-specific fields
 */
export interface Quest {
  id: string;
  name: string;
  type: string;
  status: "Active" | "In Progress" | "Completed" | "Failed" | "Suspended" | "Abandoned";
  description: string;
  priority?: ("Absolute" | "Critical" | "High" | "Medium" | "Low") | null;
  objectives?: string[];
  rewards?: string[];
  deadline?: string | null;
  notes?: string | null;
  completion_date?: string | null;
  parties?: string | null;
  outcome?: string | null;
  obligations_accepted?: string[];
  lasting_effects?: string[];
  quest_giver?: string | null;
  location?: string | null;
  deity?: string | null;
  purpose?: string | null;
  signs_received?: string[];
  divine_favor?: string | null;
  consequences_of_failure?: string[];
  motivation?: string | null;
  steps?: string[];
  obstacles?: string[];
  importance?: string | null;
}
/**
 * Template for creating new contracts.
 */
export interface ContractTemplate {
  id?: string;
  name?: string;
  type?: string;
  status?: string;
  priority?: string;
  quest_giver?: string;
  location?: string;
  description?: string;
  objectives?: string[];
  rewards?: string[];
  deadline?: string;
  notes?: string;
}
/**
 * An action granted by a feature (from actions data).
 *
 * EXTRACTION PATHS:
 * - limitedUse: Parse from actions[category][].limitedUse
 * - name: actions[category][].name
 * - description: actions[category][].description (HTML, needs cleaning)
 * - abilityModifierStatName: Map from actions[category][].abilityModifierStatId
 *   * 1="Strength", 2="Dexterity", 3="Constitution", 4="Intelligence", 5="Wisdom", 6="Charisma"
 * - onMissDescription: actions[category][].onMissDescription
 * - saveFailDescription: actions[category][].saveFailDescription
 * - saveSuccessDescription: actions[category][].saveSuccessDescription
 * - saveStatId: actions[category][].saveStatId
 * - fixedSaveDc: actions[category][].fixedSaveDc
 * - attackTypeRange: actions[category][].attackTypeRange
 * - actionType: Map from actions[category][].actionType
 * - attackSubtype: actions[category][].attackSubtype
 * - dice: actions[category][].dice
 * - value: actions[category][].value
 * - damageTypeId: actions[category][].damageTypeId
 * - isMartialArts: actions[category][].isMartialArts
 * - isProficient: actions[category][].isProficient
 * - spellRangeType: actions[category][].spellRangeType
 * - range: Parse from actions[category][].range as FeatureRange
 * - activation: Parse from actions[category][].activation as FeatureActivation
 */
export interface FeatureAction {
  limitedUse?: LimitedUse | null;
  name?: string | null;
  description?: string | null;
  abilityModifierStatName?: string | null;
  onMissDescription?: string | null;
  saveFailDescription?: string | null;
  saveSuccessDescription?: string | null;
  saveStatId?: number | null;
  fixedSaveDc?: number | null;
  attackTypeRange?: number | null;
  actionType?: string | null;
  attackSubtype?: number | null;
  dice?: {
    [k: string]: unknown;
  } | null;
  value?: number | null;
  damageTypeId?: number | null;
  isMartialArts?: boolean | null;
  isProficient?: boolean | null;
  spellRangeType?: number | null;
  range?: FeatureRange | null;
  activation?: FeatureActivation | null;
}
/**
 * Range information for feature actions.
 *
 * EXTRACTION PATHS:
 * - range: actions[].range.range
 * - longRange: actions[].range.longRange
 * - aoeType: actions[].range.aoeType (1=sphere, 2=cube, 3=cone, 4=line)
 * - aoeSize: actions[].range.aoeSize
 * - hasAoeSpecialDescription: actions[].range.hasAoeSpecialDescription
 * - minimumRange: actions[].range.minimumRange
 */
export interface FeatureRange {
  range?: number | null;
  longRange?: number | null;
  aoeType?: number | null;
  aoeSize?: number | null;
  hasAoeSpecialDescription?: boolean | null;
  minimumRange?: number | null;
}
