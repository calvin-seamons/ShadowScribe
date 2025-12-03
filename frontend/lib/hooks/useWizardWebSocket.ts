/**
 * useWizardWebSocket - WebSocket hook for character creation wizard
 *
 * Connects WebSocket character creation progress events to the wizard Zustand store.
 * Should be called once at the wizard component level.
 */

'use client'

import { useEffect, useRef, useCallback } from 'react'
import { websocketService } from '@/lib/services/websocket'
import { useWizardStore } from '@/lib/stores/wizardStore'
import type { CharacterCreationEvent } from '@/lib/types/character'

export function useWizardWebSocket() {
  const {
    setParserStatus,
    setCompletedCount,
    setIsCreating,
    setCharacterData,
    setCharacterSummary,
    setError,
    nextStep,
  } = useWizardStore()

  const handlerRegistered = useRef(false)

  // Handle WebSocket progress events
  const handleProgressEvent = useCallback((event: CharacterCreationEvent) => {
    switch (event.type) {
      case 'fetch_started':
        setIsCreating(true)
        break

      case 'fetch_complete':
        // Fetch complete, parsers will start
        break

      case 'parser_started':
        setParserStatus(event.parser, {
          parser: event.parser,
          status: 'started',
        })
        break

      case 'parser_progress':
        setParserStatus(event.parser, {
          parser: event.parser,
          status: 'in_progress',
          message: event.message,
        })
        break

      case 'parser_complete':
        setParserStatus(event.parser, {
          parser: event.parser,
          status: 'complete',
          execution_time_ms: event.execution_time_ms,
        })
        setCompletedCount(event.completed)
        break

      case 'assembly_started':
        // Character assembly started
        break

      case 'creation_complete':
        setCharacterSummary(event.character_summary)
        if (event.character_data) {
          setCharacterData(event.character_data)
        }
        setIsCreating(false)
        // Auto-advance to next step after short delay
        setTimeout(() => {
          nextStep()
        }, 500)
        break

      case 'creation_error':
        setError(event.error)
        if (event.parser) {
          setParserStatus(event.parser, {
            parser: event.parser,
            status: 'error',
            message: event.error,
          })
        }
        setIsCreating(false)
        break
    }
  }, [setParserStatus, setCompletedCount, setIsCreating, setCharacterData, setCharacterSummary, setError, nextStep])

  // Register WebSocket handler on mount
  useEffect(() => {
    if (!handlerRegistered.current) {
      websocketService.onProgress(handleProgressEvent)
      handlerRegistered.current = true
    }
  }, [handleProgressEvent])

  // Create character from URL
  const createCharacter = useCallback(async (url: string): Promise<void> => {
    const { setUrl, resetParsers, setStep } = useWizardStore.getState()

    // Store URL and reset parser state
    setUrl(url)
    resetParsers()
    setIsCreating(true)

    // Move to parsing step
    setStep(2)

    try {
      // This triggers WebSocket connection and character creation
      await websocketService.createCharacter(url)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create character'
      setError(errorMessage)
      setIsCreating(false)
      throw err
    }
  }, [setIsCreating, setError])

  return {
    createCharacter,
  }
}
