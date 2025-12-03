/**
 * Character Creation Wizard
 *
 * 7-step wizard for importing and creating D&D characters:
 * 1. URL Input - Fetch character from D&D Beyond
 * 2. Parsing Progress - Real-time parser status
 * 3. Stats - Edit ability scores and combat stats
 * 4. Equipment - Edit inventory and spells
 * 5. Abilities - Edit actions and features
 * 6. Character - Edit personality and backstory
 * 7. Review & Save - Final preview and database save
 *
 * Uses Zustand store as single source of truth.
 */

'use client'

import { useEffect } from 'react'
import { useWizardStore, TOTAL_STEPS } from '@/lib/stores/wizardStore'
import { useWizardWebSocket } from '@/lib/hooks/useWizardWebSocket'

// Step components
import { WizardProgress } from './wizard/WizardProgress'
import { Step1_UrlInput } from './wizard/Step1_UrlInput'
import { Step2_ParsingProgress } from './wizard/Step2_ParsingProgress'
import { Step3_Stats } from './wizard/Step3_Stats'
import { Step4_Equipment } from './wizard/Step4_Equipment'
import { Step5_Abilities } from './wizard/Step5_Abilities'
import { Step6_Character } from './wizard/Step6_Character'
import { Step7_Review } from './wizard/Step7_Review'

export function CharacterCreationWizard() {
  const {
    currentStep,
    hasDraft,
    checkForDraft,
    loadFromDraft,
    reset,
  } = useWizardStore()

  // Initialize WebSocket connection for parsing
  useWizardWebSocket()

  // Check for existing draft on mount
  useEffect(() => {
    checkForDraft()
  }, [checkForDraft])

  // Warn about unsaved changes before leaving
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (currentStep > 1) {
        e.preventDefault()
        e.returnValue = ''
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [currentStep])

  const handleResumeDraft = () => {
    loadFromDraft()
  }

  const handleStartFresh = () => {
    reset()
  }

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <Step1_UrlInput />
      case 2:
        return <Step2_ParsingProgress />
      case 3:
        return <Step3_Stats />
      case 4:
        return <Step4_Equipment />
      case 5:
        return <Step5_Abilities />
      case 6:
        return <Step6_Character />
      case 7:
        return <Step7_Review />
      default:
        return <Step1_UrlInput />
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Ambient background effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 right-1/4 w-[600px] h-[600px] bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-1/4 w-[500px] h-[500px] bg-accent/5 rounded-full blur-3xl" />
      </div>

      {/* Main content */}
      <main className="relative z-0 py-6 px-4">
        <div className="max-w-5xl mx-auto">
          {/* Progress Header */}
          <WizardProgress currentStep={currentStep} totalSteps={TOTAL_STEPS} />

          {/* Resume Draft Modal */}
          {hasDraft && currentStep === 1 && (
            <div className="mb-8 p-6 rounded-xl bg-card border border-primary/30 shadow-lg">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-2xl">📜</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-display text-lg mb-1">Resume Previous Session?</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    You have an unfinished character creation in progress.
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={handleResumeDraft}
                      className="btn-primary px-4 py-2"
                    >
                      Resume
                    </button>
                    <button
                      onClick={handleStartFresh}
                      className="btn-ghost px-4 py-2"
                    >
                      Start Fresh
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Main Content Card */}
          <div className="card-elevated overflow-hidden">
            {renderStep()}
          </div>
        </div>
      </main>
    </div>
  )
}
