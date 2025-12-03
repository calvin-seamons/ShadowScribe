/**
 * Wizard Store - Centralized state management for character creation wizard
 *
 * This Zustand store serves as the single source of truth for all wizard state:
 * - 7-step navigation (URL → Parse → Stats → Equipment → Abilities → Character → Review)
 * - Character data from parsing
 * - Parser progress tracking
 * - LocalStorage persistence for draft resume
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import type {
  CharacterData,
  CharacterSummary,
  ParserName,
  SectionName
} from '@/lib/types/character'
import {
  saveDraft,
  loadDraft,
  clearDraft,
  hasDraft,
  type WizardDraft
} from '@/lib/services/wizardPersistence'

// ============================================================================
// Types
// ============================================================================

export type WizardStep = 1 | 2 | 3 | 4 | 5 | 6 | 7

export type ParserStatus = 'idle' | 'started' | 'in_progress' | 'complete' | 'error'

export interface ParserProgress {
  parser: ParserName
  status: ParserStatus
  progress?: number
  execution_time_ms?: number
  message?: string
}

export const STEP_CONFIG = {
  1: { name: 'URL', label: 'Enter URL', icon: 'Link' },
  2: { name: 'Parse', label: 'Parsing', icon: 'Loader2' },
  3: { name: 'Stats', label: 'Stats', icon: 'Swords' },
  4: { name: 'Equipment', label: 'Equipment', icon: 'Backpack' },
  5: { name: 'Abilities', label: 'Abilities', icon: 'Sparkles' },
  6: { name: 'Character', label: 'Character', icon: 'User' },
  7: { name: 'Review', label: 'Review & Save', icon: 'Check' },
} as const

export const TOTAL_STEPS = 7

// ============================================================================
// Store Interface
// ============================================================================

interface WizardState {
  // Navigation
  currentStep: WizardStep
  completedSteps: Set<WizardStep>

  // Source data
  dndbeyondUrl: string
  rawJsonData: any | null

  // Parsed character (single source of truth)
  characterData: CharacterData | null
  characterSummary: CharacterSummary | null

  // Parser progress (WebSocket)
  parsers: Record<ParserName, ParserProgress>
  isCreating: boolean
  completedCount: number

  // Post-save
  savedCharacterId: number | null
  isSaving: boolean

  // Errors
  error: string | null

  // Draft status
  hasDraft: boolean

  // Actions - Navigation
  setStep: (step: WizardStep) => void
  nextStep: () => void
  prevStep: () => void
  markStepComplete: (step: WizardStep) => void
  goToStep: (step: WizardStep) => void

  // Actions - Data
  setUrl: (url: string) => void
  setRawJson: (json: any) => void
  setCharacterData: (data: CharacterData) => void
  setCharacterSummary: (summary: CharacterSummary) => void
  updateSection: <T extends SectionName>(section: T, data: CharacterData[T]) => void

  // Actions - Parser progress
  setParserStatus: (parser: ParserName, progress: ParserProgress) => void
  setIsCreating: (isCreating: boolean) => void
  setCompletedCount: (count: number) => void
  resetParsers: () => void

  // Actions - Save
  setSavedCharacterId: (id: number) => void
  setIsSaving: (isSaving: boolean) => void
  setError: (error: string | null) => void

  // Actions - Persistence
  saveToDraft: () => void
  loadFromDraft: () => boolean
  clearDraft: () => void
  checkForDraft: () => boolean

  // Actions - Reset
  reset: () => void
}

// ============================================================================
// Initial State
// ============================================================================

const INITIAL_PARSERS: Record<ParserName, ParserProgress> = {
  core: { parser: 'core', status: 'idle' },
  inventory: { parser: 'inventory', status: 'idle' },
  spells: { parser: 'spells', status: 'idle' },
  features: { parser: 'features', status: 'idle' },
  background: { parser: 'background', status: 'idle' },
  actions: { parser: 'actions', status: 'idle' },
}

const getInitialState = () => ({
  // Navigation
  currentStep: 1 as WizardStep,
  completedSteps: new Set<WizardStep>(),

  // Source data
  dndbeyondUrl: '',
  rawJsonData: null,

  // Parsed character
  characterData: null,
  characterSummary: null,

  // Parser progress
  parsers: { ...INITIAL_PARSERS },
  isCreating: false,
  completedCount: 0,

  // Post-save
  savedCharacterId: null,
  isSaving: false,

  // Errors
  error: null,

  // Draft status
  hasDraft: false,
})

// ============================================================================
// Store
// ============================================================================

export const useWizardStore = create<WizardState>()(
  subscribeWithSelector((set, get) => ({
    ...getInitialState(),

    // ========================================================================
    // Navigation Actions
    // ========================================================================

    setStep: (step) => set({ currentStep: step }),

    nextStep: () => {
      const { currentStep, completedSteps } = get()
      if (currentStep < TOTAL_STEPS) {
        // Mark current step as complete
        const newCompleted = new Set(completedSteps)
        newCompleted.add(currentStep)

        set({
          currentStep: (currentStep + 1) as WizardStep,
          completedSteps: newCompleted,
        })

        // Auto-save draft on step completion
        get().saveToDraft()
      }
    },

    prevStep: () => {
      const { currentStep } = get()
      if (currentStep > 1) {
        set({ currentStep: (currentStep - 1) as WizardStep })
      }
    },

    markStepComplete: (step) => {
      const { completedSteps } = get()
      const newCompleted = new Set(completedSteps)
      newCompleted.add(step)
      set({ completedSteps: newCompleted })
    },

    goToStep: (step) => {
      const { completedSteps, currentStep } = get()
      // Can only go to completed steps or current step + 1
      if (completedSteps.has(step) || step === currentStep || step === currentStep + 1) {
        set({ currentStep: step })
      }
    },

    // ========================================================================
    // Data Actions
    // ========================================================================

    setUrl: (url) => set({ dndbeyondUrl: url }),

    setRawJson: (json) => set({ rawJsonData: json }),

    setCharacterData: (data) => set({ characterData: data }),

    setCharacterSummary: (summary) => set({ characterSummary: summary }),

    updateSection: (section, data) => {
      const { characterData } = get()
      if (!characterData) return

      set({
        characterData: {
          ...characterData,
          [section]: data,
        },
      })

      // Auto-save draft on section update (debounced via persistence service)
      get().saveToDraft()
    },

    // ========================================================================
    // Parser Progress Actions
    // ========================================================================

    setParserStatus: (parser, progress) => {
      const { parsers } = get()
      set({
        parsers: {
          ...parsers,
          [parser]: progress,
        },
      })
    },

    setIsCreating: (isCreating) => set({ isCreating }),

    setCompletedCount: (count) => set({ completedCount: count }),

    resetParsers: () => set({
      parsers: { ...INITIAL_PARSERS },
      completedCount: 0,
      isCreating: false,
    }),

    // ========================================================================
    // Save Actions
    // ========================================================================

    setSavedCharacterId: (id) => set({ savedCharacterId: id }),

    setIsSaving: (isSaving) => set({ isSaving }),

    setError: (error) => set({ error }),

    // ========================================================================
    // Persistence Actions
    // ========================================================================

    saveToDraft: () => {
      const state = get()
      // Only save if we have meaningful progress
      if (state.currentStep > 1 || state.dndbeyondUrl) {
        saveDraft({
          currentStep: state.currentStep,
          completedSteps: Array.from(state.completedSteps),
          dndbeyondUrl: state.dndbeyondUrl,
          characterData: state.characterData,
          characterSummary: state.characterSummary,
          timestamp: Date.now(),
        })
        set({ hasDraft: true })
      }
    },

    loadFromDraft: () => {
      const draft = loadDraft()
      if (!draft) return false

      set({
        currentStep: draft.currentStep as WizardStep,
        completedSteps: new Set(draft.completedSteps as WizardStep[]),
        dndbeyondUrl: draft.dndbeyondUrl,
        characterData: draft.characterData,
        characterSummary: draft.characterSummary,
        hasDraft: true,
      })

      return true
    },

    clearDraft: () => {
      clearDraft()
      set({ hasDraft: false })
    },

    checkForDraft: () => {
      const exists = hasDraft()
      set({ hasDraft: exists })
      return exists
    },

    // ========================================================================
    // Reset
    // ========================================================================

    reset: () => {
      get().clearDraft()
      set(getInitialState())
    },
  }))
)

// ============================================================================
// Selectors
// ============================================================================

export const selectCurrentStepConfig = (state: WizardState) =>
  STEP_CONFIG[state.currentStep]

export const selectIsStepComplete = (step: WizardStep) => (state: WizardState) =>
  state.completedSteps.has(step)

export const selectCanNavigateToStep = (step: WizardStep) => (state: WizardState) =>
  state.completedSteps.has(step) || step === state.currentStep || step === state.currentStep + 1

export const selectParsingProgress = (state: WizardState) => ({
  parsers: state.parsers,
  isCreating: state.isCreating,
  completedCount: state.completedCount,
  totalCount: 6,
})

export const selectCharacterName = (state: WizardState) =>
  state.characterSummary?.name || state.characterData?.character_base?.name || 'Unknown Character'
