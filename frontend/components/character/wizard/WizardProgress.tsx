/**
 * WizardProgress - Elegant progress header for character creation wizard
 *
 * Clean, properly aligned progress indicator with step nodes.
 */

'use client'

import { Check, Link2, Loader2, Swords, Backpack, Sparkles, User, ScrollText } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWizardStore, type WizardStep } from '@/lib/stores/wizardStore'

interface WizardProgressProps {
  currentStep: number
  totalSteps: number
}

const STEP_ICONS = {
  1: Link2,
  2: Loader2,
  3: Swords,
  4: Backpack,
  5: Sparkles,
  6: User,
  7: ScrollText,
} as const

const STEP_LABELS = {
  1: 'Import',
  2: 'Parse',
  3: 'Stats',
  4: 'Gear',
  5: 'Abilities',
  6: 'Story',
  7: 'Review',
} as const

export function WizardProgress({ currentStep, totalSteps }: WizardProgressProps) {
  const { completedSteps, goToStep } = useWizardStore()

  const handleStepClick = (step: number) => {
    if (completedSteps.has(step as WizardStep) || step === currentStep) {
      goToStep(step as WizardStep)
    }
  }

  const currentLabel = STEP_LABELS[currentStep as keyof typeof STEP_LABELS]
  const progressPercent = ((currentStep - 1) / (totalSteps - 1)) * 100

  return (
    <div className="mb-8">
      {/* Current step badge */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-3 px-5 py-2.5 rounded-full bg-card border border-primary/20 shadow-lg shadow-primary/5">
          <span className="text-xs uppercase tracking-[0.15em] text-muted-foreground font-medium">
            Step {currentStep} of {totalSteps}
          </span>
          <span className="w-px h-4 bg-border" />
          <span className="font-display text-sm tracking-wide text-primary">
            {currentLabel}
          </span>
        </div>
      </div>

      {/* Progress track with nodes */}
      <div className="relative max-w-2xl mx-auto px-6">
        {/* Track container - positions the line between first and last node centers */}
        <div className="absolute top-5 left-6 right-6 h-0.5">
          {/* Background track */}
          <div
            className="absolute inset-0 bg-border/40 rounded-full"
            style={{ left: '20px', right: '20px' }}
          />
          {/* Progress fill */}
          <div
            className="absolute top-0 bottom-0 bg-gradient-to-r from-primary to-primary/80 rounded-full transition-all duration-500 ease-out"
            style={{
              left: '20px',
              width: `calc(${progressPercent}% - 40px * ${progressPercent / 100})`,
            }}
          />
        </div>

        {/* Step nodes */}
        <div className="relative flex justify-between">
          {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => {
            const isCompleted = completedSteps.has(step as WizardStep)
            const isCurrent = step === currentStep
            const isPending = step > currentStep && !isCompleted
            const canNavigate = isCompleted || isCurrent
            const Icon = STEP_ICONS[step as keyof typeof STEP_ICONS]
            const label = STEP_LABELS[step as keyof typeof STEP_LABELS]

            return (
              <button
                key={step}
                onClick={() => handleStepClick(step)}
                disabled={!canNavigate}
                className={cn(
                  'group flex flex-col items-center',
                  canNavigate ? 'cursor-pointer' : 'cursor-default'
                )}
              >
                {/* Node */}
                <div
                  className={cn(
                    'relative w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 bg-background',
                    isCompleted && 'bg-primary/15 border-2 border-primary text-primary',
                    isCurrent && 'bg-primary text-primary-foreground border-2 border-primary',
                    isPending && 'bg-card border-2 border-border text-muted-foreground/40',
                    canNavigate && !isCurrent && 'hover:border-primary/60 hover:text-primary'
                  )}
                  style={isCurrent ? {
                    boxShadow: '0 0 0 4px hsl(var(--primary) / 0.15), 0 0 20px hsl(var(--primary) / 0.3)'
                  } : undefined}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5" strokeWidth={2.5} />
                  ) : (
                    <Icon className={cn(
                      'w-5 h-5',
                      step === 2 && isCurrent && 'animate-spin'
                    )} />
                  )}
                </div>

                {/* Label */}
                <span
                  className={cn(
                    'mt-2 text-[11px] uppercase tracking-wide font-medium transition-colors',
                    isCurrent && 'text-primary',
                    isCompleted && 'text-foreground/70',
                    isPending && 'text-muted-foreground/30',
                    canNavigate && !isCurrent && 'group-hover:text-primary'
                  )}
                >
                  {label}
                </span>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
