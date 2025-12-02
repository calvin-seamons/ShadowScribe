/**
 * Multi-Step Character Creation Wizard
 *
 * A comprehensive 4-step wizard for importing and creating D&D characters:
 * 1. URL Input - Fetch character from D&D Beyond
 * 2. Parsing Progress - Real-time parser status with progress bars
 * 3. Section Review - Edit character sections (ability scores, inventory, etc.)
 * 4. Preview & Save - Final character preview and database save
 */

'use client'

import { useState, useEffect } from 'react'
import { useCharacterCreation } from '@/lib/hooks/useCharacterCreation'
import { LogoText } from '@/components/Logo'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import type { CharacterSummary } from '@/lib/types/character'

// Step components
import {
  Step1_UrlInput,
  Step2_ParsingProgress,
  Step3_SectionReview,
  Step4_PreviewAndSave,
  WizardProgress
} from './wizard'

const TOTAL_STEPS = 4

export function CharacterCreationWizard() {
  const [currentStep, setCurrentStep] = useState(1)
  const [dndbeyondUrl, setDndbeyondUrl] = useState('')
  const [characterJsonData, setCharacterJsonData] = useState<any>(null) // Raw D&D Beyond JSON
  const [savedCharacterId, setSavedCharacterId] = useState<string | null>(null)

  const {
    createCharacter,
    parsers,
    isCreating,
    error,
    characterId,
    characterSummary,
    characterData, // Parsed character with all sections
    progressEvents,
    resetProgress,
    completedCount,
    totalCount,
  } = useCharacterCreation()

  // Auto-advance to step 3 when parsing completes
  useEffect(() => {
    if (currentStep === 2 && completedCount === totalCount && !isCreating && characterSummary) {
      // Small delay to show completion state
      setTimeout(() => {
        setCurrentStep(3)
      }, 1000)
    }
  }, [currentStep, completedCount, totalCount, isCreating, characterSummary])

  const handleNextStep = () => {
    if (currentStep < TOTAL_STEPS) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleFetchCharacter = async (url: string) => {
    setDndbeyondUrl(url)

    try {
      // Fetch from D&D Beyond API
      const response = await fetch('/api/characters/fetch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || errorData.detail || 'Failed to fetch character')
      }

      const data = await response.json()
      setCharacterJsonData(data.json_data)

      // Move to step 2 (parsing)
      setCurrentStep(2)

      // Start character creation via WebSocket
      await createCharacter(data.json_data)

    } catch (err) {
      console.error('Error fetching character:', err)
      // Error will be displayed by Step1 component
    }
  }

  const handleSectionSave = async (section: string, data: any) => {
    if (!savedCharacterId) {
      console.error('No character ID available for section update')
      return
    }

    try {
      const response = await fetch(`/api/characters/${savedCharacterId}/${section}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data })
      })

      if (!response.ok) {
        throw new Error('Failed to save section')
      }

      console.log(`Section ${section} saved successfully`)
    } catch (err) {
      console.error(`Error saving section ${section}:`, err)
      throw err
    }
  }

  const handleFinalSave = async () => {
    if (!characterData) {
      console.error('No character data available to save')
      return
    }

    try {
      // Save complete character to database using parsed data
      const response = await fetch('/api/characters', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ character: characterData })
      })

      if (!response.ok) {
        throw new Error('Failed to save character')
      }

      const data = await response.json()
      setSavedCharacterId(data.id)

      console.log('Character saved successfully:', data.id)
      return data.id
    } catch (err) {
      console.error('Error saving character:', err)
      throw err
    }
  }

  const handleReset = () => {
    setCurrentStep(1)
    setDndbeyondUrl('')
    setCharacterJsonData(null)
    setSavedCharacterId(null)
    resetProgress()
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Ambient background effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 right-1/4 w-[600px] h-[600px] bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-1/4 w-[500px] h-[500px] bg-accent/5 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-border/50 bg-card/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back to Chat</span>
          </Link>
          <LogoText size="sm" />
        </div>
      </header>

      {/* Main content */}
      <main className="relative z-0 py-8 px-4">
        <div className="max-w-5xl mx-auto">
          {/* Page header */}
          <div className="text-center mb-10">
            <h1 className="text-4xl md:text-5xl font-bold mb-3 text-gradient-gold text-shadow-sm">
              Character Creation
            </h1>
            <p className="text-lg text-muted-foreground max-w-xl mx-auto">
              Import your D&D Beyond character and bring them into ShadowScribe
            </p>
          </div>

          {/* Progress Indicator */}
          <WizardProgress currentStep={currentStep} totalSteps={TOTAL_STEPS} />

          {/* Main Content Card */}
          <div className="card-elevated overflow-hidden">
            {currentStep === 1 && (
              <Step1_UrlInput
                onFetch={handleFetchCharacter}
                onNext={handleNextStep}
              />
            )}

            {currentStep === 2 && (
              <Step2_ParsingProgress
                parsers={parsers}
                isCreating={isCreating}
                error={error}
                completedCount={completedCount}
                totalCount={totalCount}
                characterSummary={characterSummary}
                onNext={handleNextStep}
              />
            )}

            {currentStep === 3 && (
              <Step3_SectionReview
                characterData={characterData || {}}
                onSectionSave={handleSectionSave}
                onNext={handleNextStep}
              />
            )}

            {currentStep === 4 && (
              <Step4_PreviewAndSave
                characterData={characterData || {}}
                savedCharacterId={savedCharacterId ? Number(savedCharacterId) : null}
                onSave={handleFinalSave}
                onReset={handleReset}
              />
            )}
          </div>

          {/* Debug Info (development only) */}
          {process.env.NODE_ENV === 'development' && (
            <details className="mt-6 rounded-xl bg-card/50 border border-border/50 p-4">
              <summary className="cursor-pointer font-medium text-sm text-muted-foreground">
                Debug Info
              </summary>
              <div className="mt-3 space-y-1 text-xs font-mono text-muted-foreground/60">
                <div>Current Step: {currentStep}</div>
                <div>Character ID: {characterId || 'N/A'}</div>
                <div>Saved ID: {savedCharacterId || 'N/A'}</div>
                <div>Is Creating: {isCreating.toString()}</div>
                <div>Completed: {completedCount}/{totalCount}</div>
                <div>Has Character Data: {!!characterData ? 'Yes' : 'No'}</div>
                <div>Has Raw JSON: {!!characterJsonData ? 'Yes' : 'No'}</div>
                <div>Has Summary: {!!characterSummary ? 'Yes' : 'No'}</div>
                <div>Progress Events: {progressEvents.length}</div>
              </div>
            </details>
          )}
        </div>
      </main>
    </div>
  )
}
