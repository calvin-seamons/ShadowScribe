/**
 * Wizard Progress Indicator
 *
 * Shows current step in the wizard with visual progress bar
 */

'use client'

import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface WizardProgressProps {
  currentStep: number
  totalSteps: number
}

const STEP_LABELS = [
  { title: 'Import', subtitle: 'D&D Beyond URL' },
  { title: 'Parse', subtitle: 'Processing data' },
  { title: 'Review', subtitle: 'Edit sections' },
  { title: 'Save', subtitle: 'Finalize character' }
]

export function WizardProgress({ currentStep, totalSteps }: WizardProgressProps) {
  return (
    <div className="mb-10">
      {/* Steps container */}
      <div className="relative flex justify-between">
        {/* Progress line background */}
        <div className="absolute top-5 left-0 right-0 h-0.5 bg-border/50" />

        {/* Progress line active */}
        <div
          className="absolute top-5 left-0 h-0.5 bg-gradient-to-r from-primary to-primary/80 transition-all duration-500"
          style={{ width: `${((currentStep - 1) / (totalSteps - 1)) * 100}%` }}
        />

        {/* Step indicators */}
        {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => {
          const isCompleted = step < currentStep
          const isCurrent = step === currentStep
          const isPending = step > currentStep

          return (
            <div
              key={step}
              className="relative flex flex-col items-center z-10"
            >
              {/* Step circle */}
              <div
                className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300',
                  isCompleted && 'bg-primary text-primary-foreground shadow-lg shadow-primary/30',
                  isCurrent && 'bg-primary text-primary-foreground ring-4 ring-primary/20 shadow-lg shadow-primary/30 scale-110',
                  isPending && 'bg-card border-2 border-border text-muted-foreground'
                )}
              >
                {isCompleted ? (
                  <Check className="w-5 h-5" />
                ) : (
                  step
                )}
              </div>

              {/* Step labels */}
              <div className="mt-3 text-center">
                <p
                  className={cn(
                    'text-sm font-medium transition-colors',
                    isCurrent && 'text-primary',
                    isCompleted && 'text-foreground',
                    isPending && 'text-muted-foreground'
                  )}
                >
                  {STEP_LABELS[step - 1]?.title}
                </p>
                <p className="text-xs text-muted-foreground/60 mt-0.5 hidden sm:block">
                  {STEP_LABELS[step - 1]?.subtitle}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
