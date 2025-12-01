/**
 * React hook for character creation with WebSocket progress tracking
 * 
 * This hook manages the state for character creation including:
 * - Parser progress tracking (6 parsers: core, inventory, spells, features, background, actions)
 * - Loading state
 * - Error handling
 * - Character ID upon completion
 * 
 * Usage:
 * ```tsx
 * const { createCharacter, parsers, isCreating, error, characterId } = useCharacterCreation()
 * 
 * const handleCreate = async () => {
 *   try {
 *     const id = await createCharacter(jsonData)
 *     console.log('Character created:', id)
 *   } catch (err) {
 *     console.error('Creation failed:', err)
 *   }
 * }
 * ```
 */

import { useState, useCallback, useRef } from 'react'
import { websocketService } from '@/lib/services/websocket'
import type { 
  CharacterCreationEvent, 
  CharacterSummary,
  CharacterData,
  ParserName 
} from '@/lib/types/character'

export type ParserStatus = 'idle' | 'started' | 'in_progress' | 'complete' | 'error'

export interface ParserProgress {
  parser: ParserName
  status: ParserStatus
  progress?: number
  execution_time_ms?: number
  message?: string
}

export interface UseCharacterCreationResult {
  /**
   * Create a character from URL or JSON data
   * @param urlOrJsonData - D&D Beyond URL string or complete JSON data object
   * @returns Promise resolving to character ID (generated from name)
   */
  createCharacter: (urlOrJsonData: string | any) => Promise<string>
  
  /**
   * Current state of all 6 parsers
   */
  parsers: Record<ParserName, ParserProgress>
  
  /**
   * Whether character creation is in progress
   */
  isCreating: boolean
  
  /**
   * Error message if creation failed
   */
  error: string | null
  
  /**
   * Character ID after successful creation (null before completion)
   */
  characterId: string | null
  
  /**
   * Character summary after successful creation
   */
  characterSummary: CharacterSummary | null
  
  /**
   * Full parsed character data after successful creation
   */
  characterData: CharacterData | null
  
  /**
   * All progress events received during creation
   */
  progressEvents: CharacterCreationEvent[]
  
  /**
   * Reset all state back to initial values
   */
  resetProgress: () => void
  
  /**
   * Number of completed parsers
   */
  completedCount: number
  
  /**
   * Total number of parsers (always 6)
   */
  totalCount: number
}

const INITIAL_PARSERS: Record<ParserName, ParserProgress> = {
  core: { parser: 'core', status: 'idle' },
  inventory: { parser: 'inventory', status: 'idle' },
  spells: { parser: 'spells', status: 'idle' },
  features: { parser: 'features', status: 'idle' },
  background: { parser: 'background', status: 'idle' },
  actions: { parser: 'actions', status: 'idle' },
}

/**
 * Custom hook for managing character creation with real-time progress
 */
export function useCharacterCreation(): UseCharacterCreationResult {
  const [parsers, setParsers] = useState<Record<ParserName, ParserProgress>>(INITIAL_PARSERS)
  const [isCreating, setIsCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [characterId, setCharacterId] = useState<string | null>(null)
  const [characterSummary, setCharacterSummary] = useState<CharacterSummary | null>(null)
  const [characterData, setCharacterData] = useState<CharacterData | null>(null)
  const [progressEvents, setProgressEvents] = useState<CharacterCreationEvent[]>([])
  const [completedCount, setCompletedCount] = useState(0)
  
  // Use ref to track if progress handler is registered
  const progressHandlerRegistered = useRef(false)
  
  const createCharacter = useCallback(async (urlOrJsonData: string | any): Promise<string> => {
    // Reset state
    setParsers(INITIAL_PARSERS)
    setIsCreating(true)
    setError(null)
    setCharacterId(null)
    setCharacterSummary(null)
    setCharacterData(null)
    setProgressEvents([])
    setCompletedCount(0)
    
    // Register progress handler (only once)
    if (!progressHandlerRegistered.current) {
      websocketService.onProgress((event: CharacterCreationEvent) => {
        // Store all events for debugging/display
        setProgressEvents(prev => [...prev, event])
        
        // Handle different event types
        switch (event.type) {
          case 'fetch_started':
            // Fetching from D&D Beyond started
            break
          
          case 'fetch_complete':
            // Fetching complete
            break
          
          case 'parser_started':
            setParsers(prev => ({
              ...prev,
              [event.parser as string]: {
                parser: event.parser,
                status: 'started',
              }
            }))
            break
          
          case 'parser_progress':
            setParsers(prev => ({
              ...prev,
              [event.parser]: {
                parser: event.parser,
                status: 'in_progress',
                message: event.message,
              }
            }))
            break
          
          case 'parser_complete':
            setParsers(prev => ({
              ...prev,
              [event.parser as string]: {
                parser: event.parser,
                status: 'complete',
                execution_time_ms: event.execution_time_ms,
              }
            }))
            setCompletedCount(event.completed)
            break
          
          case 'assembly_started':
            // Character assembly started
            break
          
          case 'creation_complete':
            // Set character summary and full parsed data
            setCharacterSummary(event.character_summary)
            if (event.character_data) {
              setCharacterData(event.character_data)
            }
            // Generate ID from name (kebab-case)
            const id = event.character_summary.name
              .toLowerCase()
              .replace(/[^a-z0-9]+/g, '-')
              .replace(/^-+|-+$/g, '')
            setCharacterId(id)
            break
          
          case 'creation_error':
            if (event.parser) {
              setParsers(prev => ({
                ...prev,
                [event.parser as string]: {
                  parser: event.parser,
                  status: 'error',
                  message: event.error,
                }
              }))
            }
            break
        }
      })
      progressHandlerRegistered.current = true
    }
    
    try {
      // Call WebSocket service to create character
      const summary = await websocketService.createCharacter(urlOrJsonData)
      
      // Generate character ID from name
      const id = summary.name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '')
      
      setCharacterId(id)
      setCharacterSummary(summary)
      setIsCreating(false)
      
      return id
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(errorMessage)
      setIsCreating(false)
      throw err
    }
  }, [])
  
  const resetProgress = useCallback(() => {
    setParsers(INITIAL_PARSERS)
    setIsCreating(false)
    setError(null)
    setCharacterId(null)
    setCharacterSummary(null)
    setCharacterData(null)
    setProgressEvents([])
    setCompletedCount(0)
  }, [])
  
  return {
    createCharacter,
    parsers,
    isCreating,
    error,
    characterId,
    characterSummary,
    characterData,
    progressEvents,
    resetProgress,
    completedCount,
    totalCount: 6,
  }
}
