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

// Character creation wizard types
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

// Full character data structure (parsed from D&D Beyond)
export interface CharacterData {
  character_base?: any
  ability_scores?: any
  combat_stats?: any
  inventory?: any
  spell_list?: any
  action_economy?: any
  features_and_traits?: any
  backstory?: any
  personality?: any
  background_info?: any
  [key: string]: any
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
