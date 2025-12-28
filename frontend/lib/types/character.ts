/**
 * Character Types - Frontend TypeScript definitions
 *
 * This file re-exports types from auto-generated files and adds frontend-specific types.
 * The Python backend (src/rag/character/character_types.py) is the source of truth.
 *
 * Generated types are in: ./generated/character.ts and ./generated/schemas_character.ts
 */

// ============================================================================
// Re-export all generated types from Python Pydantic models
// ============================================================================

// Character dataclasses (from src/rag/character/character_types.py)
export * from './generated/character'

// API schemas (from api/schemas/character.py)
export type {
  CharacterResponse,
  CharacterListResponse,
  CharacterCreateRequest,
  CharacterUpdateRequest,
  FetchCharacterRequest,
  FetchCharacterResponse,
  SectionUpdateRequest,
  SectionUpdateResponse,
} from './generated/schemas_character'

// ============================================================================
// Type Aliases for Backward Compatibility
// ============================================================================

// Import Character from generated to create CharacterData alias
import type { Character as GeneratedCharacter } from './generated/character'
import type { CharacterResponse } from './generated/schemas_character'

/**
 * CharacterData - Full character data structure
 * Alias for the generated Character type from Python dataclasses
 */
export type CharacterData = GeneratedCharacter

/**
 * Character - API response format (for backwards compatibility)
 * Use CharacterResponse directly in new code
 * @deprecated Use CharacterResponse instead
 */
export type Character = CharacterResponse

// ============================================================================
// Frontend-Only Types (WebSocket events, UI-specific)
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

// Character section keys for partial updates
export type CharacterSectionKey =
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

/**
 * SectionName - Alias for CharacterSectionKey (backward compatibility)
 */
export type SectionName = CharacterSectionKey
