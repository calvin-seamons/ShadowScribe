/**
 * Wizard Persistence Service
 *
 * Handles localStorage persistence for character creation wizard drafts.
 * Allows users to resume character creation after browser refresh.
 */

import type { CharacterData, CharacterSummary } from '@/lib/types/character'
import type { WizardStep } from '@/lib/stores/wizardStore'

// ============================================================================
// Constants
// ============================================================================

const STORAGE_KEY = 'shadowscribe-wizard-draft'
const EXPIRATION_HOURS = 24

// ============================================================================
// Types
// ============================================================================

export interface WizardDraft {
  currentStep: number
  completedSteps: number[]
  dndbeyondUrl: string
  characterData: CharacterData | null
  characterSummary: CharacterSummary | null
  timestamp: number
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Check if a draft has expired
 */
function isDraftExpired(timestamp: number): boolean {
  const now = Date.now()
  const expirationMs = EXPIRATION_HOURS * 60 * 60 * 1000
  return now - timestamp > expirationMs
}

/**
 * Check if localStorage is available
 */
function isStorageAvailable(): boolean {
  try {
    const test = '__storage_test__'
    localStorage.setItem(test, test)
    localStorage.removeItem(test)
    return true
  } catch {
    return false
  }
}

// ============================================================================
// Debounced Save
// ============================================================================

let saveTimeout: ReturnType<typeof setTimeout> | null = null
const DEBOUNCE_MS = 500

/**
 * Debounced save to prevent excessive writes
 */
function debouncedSave(draft: WizardDraft): void {
  if (saveTimeout) {
    clearTimeout(saveTimeout)
  }

  saveTimeout = setTimeout(() => {
    performSave(draft)
    saveTimeout = null
  }, DEBOUNCE_MS)
}

/**
 * Perform the actual save to localStorage
 */
function performSave(draft: WizardDraft): void {
  if (!isStorageAvailable()) {
    console.warn('localStorage not available, draft not saved')
    return
  }

  try {
    const serialized = JSON.stringify(draft)
    localStorage.setItem(STORAGE_KEY, serialized)
  } catch (err) {
    console.error('Failed to save wizard draft:', err)
  }
}

// ============================================================================
// Public API
// ============================================================================

/**
 * Save wizard state to localStorage (debounced)
 */
export function saveDraft(draft: WizardDraft): void {
  debouncedSave(draft)
}

/**
 * Save wizard state immediately (bypass debounce)
 */
export function saveDraftImmediately(draft: WizardDraft): void {
  if (saveTimeout) {
    clearTimeout(saveTimeout)
    saveTimeout = null
  }
  performSave(draft)
}

/**
 * Load wizard draft from localStorage
 * Returns null if no draft exists or if it has expired
 */
export function loadDraft(): WizardDraft | null {
  if (!isStorageAvailable()) {
    return null
  }

  try {
    const serialized = localStorage.getItem(STORAGE_KEY)
    if (!serialized) {
      return null
    }

    const draft = JSON.parse(serialized) as WizardDraft

    // Check if draft has expired
    if (isDraftExpired(draft.timestamp)) {
      clearDraft()
      return null
    }

    return draft
  } catch (err) {
    console.error('Failed to load wizard draft:', err)
    return null
  }
}

/**
 * Clear wizard draft from localStorage
 */
export function clearDraft(): void {
  if (saveTimeout) {
    clearTimeout(saveTimeout)
    saveTimeout = null
  }

  if (!isStorageAvailable()) {
    return
  }

  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (err) {
    console.error('Failed to clear wizard draft:', err)
  }
}

/**
 * Check if a valid draft exists in localStorage
 */
export function hasDraft(): boolean {
  if (!isStorageAvailable()) {
    return false
  }

  try {
    const serialized = localStorage.getItem(STORAGE_KEY)
    if (!serialized) {
      return false
    }

    const draft = JSON.parse(serialized) as WizardDraft

    // Check if draft has expired
    if (isDraftExpired(draft.timestamp)) {
      clearDraft()
      return false
    }

    // Check if draft has meaningful progress (beyond step 1 with no URL)
    return draft.currentStep > 1 || Boolean(draft.dndbeyondUrl && draft.dndbeyondUrl.length > 0)
  } catch {
    return false
  }
}

/**
 * Get draft age in human-readable format
 */
export function getDraftAge(): string | null {
  const draft = loadDraft()
  if (!draft) {
    return null
  }

  const ageMs = Date.now() - draft.timestamp
  const ageMinutes = Math.floor(ageMs / (60 * 1000))
  const ageHours = Math.floor(ageMs / (60 * 60 * 1000))

  if (ageMinutes < 1) {
    return 'just now'
  } else if (ageMinutes < 60) {
    return `${ageMinutes} minute${ageMinutes === 1 ? '' : 's'} ago`
  } else {
    return `${ageHours} hour${ageHours === 1 ? '' : 's'} ago`
  }
}

/**
 * Get the character name from the draft (if available)
 */
export function getDraftCharacterName(): string | null {
  const draft = loadDraft()
  if (!draft) {
    return null
  }

  return (
    draft.characterSummary?.name ||
    draft.characterData?.character_base?.name ||
    null
  )
}
