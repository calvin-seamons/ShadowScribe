/**
 * Character Types - Frontend TypeScript definitions
 *
 * IMPORTANT: These types mirror the Python dataclasses in:
 * src/rag/character/character_types.py
 *
 * The Python backend is the source of truth. When updating types,
 * always check the backend definitions first.
 */

// ============================================================================
// Database Character (from API responses)
// ============================================================================

export interface Character {
  id: string
  name: string
  race: string | null
  character_class: string | null
  level: number | null
  data: any
  created_at: string | null
  updated_at: string | null
}

export interface CharacterListResponse {
  characters: Character[]
}

// ============================================================================
// Character Creation Progress Types
// ============================================================================

export type ParserName = 'core' | 'inventory' | 'spells' | 'features' | 'background' | 'actions'

export type ProgressEventType = 'parser_started' | 'parser_complete' | 'parser_progress'

export interface CharacterCreationProgress {
  type: ProgressEventType
  parser: ParserName
  completed: number
  total: number
  execution_time_ms?: number
  message?: string
}

export interface CharacterSummary {
  name: string
  race: string
  character_class: string
  level: number
  hp: number
  ac: number
}

// ============================================================================
// Core Character Types (mirrors Python dataclasses)
// ============================================================================

/**
 * AbilityScores - The six core ability scores
 * Python: AbilityScores dataclass
 */
export interface AbilityScores {
  strength: number
  dexterity: number
  constitution: number
  intelligence: number
  wisdom: number
  charisma: number
}

/**
 * CombatStats - Core combat statistics
 * Python: CombatStats dataclass
 */
export interface CombatStats {
  max_hp: number
  armor_class: number
  initiative_bonus: number
  speed: number
  hit_dice?: Record<string, string> | null
}

/**
 * CharacterBase - Basic character information
 * Python: CharacterBase dataclass
 */
export interface CharacterBase {
  name: string
  race: string
  character_class: string
  total_level: number
  alignment: string
  background: string
  subrace?: string | null
  multiclass_levels?: Record<string, number> | null
  lifestyle?: string | null
}

/**
 * PhysicalCharacteristics - Physical appearance and traits
 * Python: PhysicalCharacteristics dataclass
 */
export interface PhysicalCharacteristics {
  alignment: string
  gender: string
  eyes: string
  size: string
  height: string
  hair: string
  skin: string
  age: number
  weight: string
  faith?: string | null
}

// ============================================================================
// Proficiencies and Modifiers
// ============================================================================

export type ProficiencyType = 'armor' | 'weapon' | 'tool' | 'language' | 'skill' | 'saving_throw'

export interface Proficiency {
  type: ProficiencyType
  name: string
}

export type DamageModifierType = 'resistance' | 'immunity' | 'vulnerability'

export interface DamageModifier {
  damage_type: string
  modifier_type: DamageModifierType
}

export interface PassiveScores {
  perception: number
  investigation?: number | null
  insight?: number | null
  stealth?: number | null
}

export interface Senses {
  senses: Record<string, number | string>
}

// ============================================================================
// Background and Personality Types
// ============================================================================

export interface BackgroundFeature {
  name: string
  description: string
}

export interface BackgroundInfo {
  name: string
  feature: BackgroundFeature
  skill_proficiencies: string[]
  tool_proficiencies: string[]
  language_proficiencies: string[]
  equipment: string[]
  feature_description?: string | null
}

export interface PersonalityTraits {
  personality_traits: string[]
  ideals: string[]
  bonds: string[]
  flaws: string[]
}

export interface BackstorySection {
  heading: string
  content: string
}

export interface FamilyBackstory {
  parents: string
  sections: BackstorySection[]
}

export interface Backstory {
  title: string
  family_backstory: FamilyBackstory
  sections: BackstorySection[]
}

export interface Organization {
  name: string
  role: string
  description: string
}

export interface Ally {
  name: string
  description: string
  title?: string | null
}

export interface Enemy {
  name: string
  description: string
}

// ============================================================================
// Combat and Action Types
// ============================================================================

export interface ActionActivation {
  activationType?: string | null
  activationTime?: number | null
  activationCondition?: string | null
}

export interface ActionUsage {
  maxUses?: number | null
  resetType?: string | null
  usesPerActivation?: number | null
}

export interface ActionRange {
  range?: number | null
  longRange?: number | null
  aoeType?: string | null
  aoeSize?: number | null
  rangeDescription?: string | null
}

export interface ActionDamage {
  diceNotation?: string | null
  damageType?: string | null
  fixedDamage?: number | null
  bonusDamage?: string | null
  criticalHitDice?: string | null
}

export interface ActionSave {
  saveDC?: number | null
  saveAbility?: string | null
  onSuccess?: string | null
  onFailure?: string | null
}

export interface CharacterAction {
  name: string
  description?: string | null
  shortDescription?: string | null
  activation?: ActionActivation | null
  usage?: ActionUsage | null
  actionRange?: ActionRange | null
  damage?: ActionDamage | null
  save?: ActionSave | null
  actionCategory?: string | null
  source?: string | null
  sourceFeature?: string | null
  attackBonus?: number | null
  isWeaponAttack: boolean
  requiresAmmo: boolean
  duration?: string | null
  materials?: string | null
}

export interface ActionEconomy {
  attacks_per_action: number
  actions: CharacterAction[]
}

// ============================================================================
// Features and Traits Types
// ============================================================================

export interface FeatureActivation {
  activationTime?: number | null
  activationType?: string | null
}

export interface FeatureRange {
  range?: number | null
  longRange?: number | null
  aoeType?: number | null
  aoeSize?: number | null
  hasAoeSpecialDescription?: boolean | null
  minimumRange?: number | null
}

export interface RacialTrait {
  name: string
  description?: string | null
  creatureRules?: Record<string, any>[] | null
  featureType?: string | null
}

export interface ClassFeature {
  name: string
  description?: string | null
}

export interface Feat {
  name: string
  description?: string | null
  activation?: FeatureActivation | null
  creatureRules?: Record<string, any>[] | null
  isRepeatable?: boolean | null
}

export interface LimitedUse {
  maxUses?: number | null
  numberUsed?: number | null
  resetType?: string | null
  resetTypeDescription?: string | null
}

export interface FeatureAction {
  limitedUse?: LimitedUse | null
  name?: string | null
  description?: string | null
  abilityModifierStatName?: string | null
  onMissDescription?: string | null
  saveFailDescription?: string | null
  saveSuccessDescription?: string | null
  saveStatId?: number | null
  fixedSaveDc?: number | null
  attackTypeRange?: number | null
  actionType?: string | null
  attackSubtype?: number | null
  dice?: Record<string, any> | null
  value?: number | null
  damageTypeId?: number | null
  isMartialArts?: boolean | null
  isProficient?: boolean | null
  spellRangeType?: number | null
  range?: FeatureRange | null
  activation?: FeatureActivation | null
}

export interface FeatureModifier {
  type?: string | null
  subType?: string | null
  dice?: Record<string, any> | null
  restriction?: string | null
  statId?: number | null
  requiresAttunement?: boolean | null
  duration?: Record<string, any> | null
  friendlyTypeName?: string | null
  friendlySubtypeName?: string | null
  bonusTypes?: string[] | null
  value?: number | null
}

export interface FeaturesAndTraits {
  racial_traits: RacialTrait[]
  class_features: Record<string, Record<number, ClassFeature[]>>
  feats: Feat[]
  modifiers: Record<string, FeatureModifier[]>
}

// ============================================================================
// Inventory Types
// ============================================================================

export interface ItemModifier {
  type?: string | null
  subType?: string | null
  restriction?: string | null
  friendlyTypeName?: string | null
  friendlySubtypeName?: string | null
  duration?: Record<string, any> | null
  fixedValue?: number | null
  diceString?: string | null
}

export interface InventoryItemDefinition {
  name?: string | null
  type?: string | null
  description?: string | null
  canAttune?: boolean | null
  attunementDescription?: string | null
  rarity?: string | null
  weight?: number | null
  capacity?: string | null
  capacityWeight?: number | null
  canEquip?: boolean | null
  magic?: boolean | null
  tags?: string[] | null
  grantedModifiers?: ItemModifier[] | null
  damage?: Record<string, any> | null
  damageType?: string | null
  attackType?: number | null
  range?: number | null
  longRange?: number | null
  isContainer?: boolean | null
  isCustomItem?: boolean | null
}

export interface InventoryItem {
  definition: InventoryItemDefinition
  quantity: number
  isAttuned: boolean
  equipped: boolean
  limitedUse?: LimitedUse | null
}

export interface Inventory {
  total_weight: number
  weight_unit: string
  equipped_items: InventoryItem[]
  backpack: InventoryItem[]
  valuables: Record<string, any>[]
}

// ============================================================================
// Spell Types
// ============================================================================

export interface SpellComponents {
  verbal: boolean
  somatic: boolean
  material: boolean | string
}

export interface SpellRite {
  name: string
  effect: string
}

export interface Spell {
  name: string
  level: number
  school: string
  casting_time: string
  range: string
  components: SpellComponents
  duration: string
  description: string
  concentration: boolean
  ritual: boolean
  tags: string[]
  area?: string | null
  rites?: SpellRite[] | null
  charges?: number | null
}

export interface SpellcastingInfo {
  ability: string
  spell_save_dc: number
  spell_attack_bonus: number
  cantrips_known: string[]
  spells_known: string[]
  spell_slots: Record<number, number>
}

export interface SpellList {
  spellcasting: Record<string, SpellcastingInfo>
  spells: Record<string, Record<string, Spell[]>>
}

// ============================================================================
// Objectives and Contracts Types
// ============================================================================

export type ObjectiveStatus = 'Active' | 'In Progress' | 'Completed' | 'Failed' | 'Suspended' | 'Abandoned'
export type ObjectivePriority = 'Absolute' | 'Critical' | 'High' | 'Medium' | 'Low'

export interface BaseObjective {
  id: string
  name: string
  type: string
  status: ObjectiveStatus
  description: string
  priority?: ObjectivePriority | null
  objectives: string[]
  rewards: string[]
  deadline?: string | null
  notes?: string | null
  completion_date?: string | null
  parties?: string | null
  outcome?: string | null
  obligations_accepted: string[]
  lasting_effects: string[]
}

export interface Quest extends BaseObjective {
  quest_giver?: string | null
  location?: string | null
  deity?: string | null
  purpose?: string | null
  signs_received: string[]
  divine_favor?: string | null
  consequences_of_failure: string[]
  motivation?: string | null
  steps: string[]
  obstacles: string[]
  importance?: string | null
}

export interface Contract extends BaseObjective {
  client?: string | null
  contractor?: string | null
  terms?: string | null
  payment?: string | null
  penalties?: string | null
  special_conditions: string[]
}

export interface ContractTemplate {
  id: string
  name: string
  type: string
  status: string
  priority: string
  quest_giver: string
  location: string
  description: string
  objectives: string[]
  rewards: string[]
  deadline: string
  notes: string
}

export interface ObjectivesAndContracts {
  active_contracts: Contract[]
  current_objectives: Quest[]
  completed_objectives: (Quest | Contract)[]
  contract_templates: Record<string, ContractTemplate>
  metadata: Record<string, any>
}

// ============================================================================
// Main Character Data Structure
// ============================================================================

/**
 * CharacterData - Complete character definition
 *
 * This mirrors the Python Character dataclass in character_types.py
 * The backend is the source of truth for this structure.
 */
export interface CharacterData {
  // Core information (required in Python)
  character_base?: CharacterBase
  characteristics?: PhysicalCharacteristics
  ability_scores?: AbilityScores
  combat_stats?: CombatStats
  background_info?: BackgroundInfo
  personality?: PersonalityTraits
  backstory?: Backstory

  // Optional fields
  organizations?: Organization[]
  allies?: Ally[]
  enemies?: Enemy[]
  proficiencies?: Proficiency[]
  damage_modifiers?: DamageModifier[]
  passive_scores?: PassiveScores | null
  senses?: Senses | null
  action_economy?: ActionEconomy | null
  features_and_traits?: FeaturesAndTraits | null
  inventory?: Inventory | null
  spell_list?: SpellList | null
  objectives_and_contracts?: ObjectivesAndContracts | null
  notes?: Record<string, any>
  created_date?: string | null
  last_updated?: string | null

  // Allow additional fields from backend
  [key: string]: any
}

// ============================================================================
// Section Name Type (for wizard store)
// ============================================================================

export type SectionName =
  | 'character_base'
  | 'characteristics'
  | 'ability_scores'
  | 'combat_stats'
  | 'background_info'
  | 'personality'
  | 'backstory'
  | 'organizations'
  | 'allies'
  | 'enemies'
  | 'proficiencies'
  | 'damage_modifiers'
  | 'passive_scores'
  | 'senses'
  | 'action_economy'
  | 'features_and_traits'
  | 'inventory'
  | 'spell_list'
  | 'objectives_and_contracts'

// Wizard step type
export type WizardStep = 1 | 2 | 3 | 4 | 5 | 6 | 7

// ============================================================================
// WebSocket Event Types
// ============================================================================

export interface CharacterCreationComplete {
  type: 'creation_complete'
  character_summary: CharacterSummary
  character_data?: CharacterData
  character_id?: string
  character_name?: string
}

export interface CharacterCreationError {
  type: 'creation_error'
  error: string
  parser?: ParserName
}

export interface FetchStarted {
  type: 'fetch_started'
  url: string
}

export interface FetchComplete {
  type: 'fetch_complete'
  character_name: string
}

export interface AssemblyStarted {
  type: 'assembly_started'
}

export type CharacterCreationEvent =
  | FetchStarted
  | FetchComplete
  | CharacterCreationProgress
  | AssemblyStarted
  | CharacterCreationComplete
  | CharacterCreationError
