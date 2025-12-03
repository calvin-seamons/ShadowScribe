/**
 * StepLayout - Arcane-themed layout for wizard editor steps
 *
 * Features illuminated manuscript styling with:
 * - Ornate section dividers and corner flourishes
 * - Asymmetric panel layouts with visual depth
 * - Custom decorative borders and backgrounds
 */

'use client'

import { ReactNode } from 'react'
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface StepLayoutProps {
  stepNumber: number
  totalSteps?: number
  title: string
  subtitle?: string
  icon?: LucideIcon
  children: ReactNode
  onBack?: () => void
  onContinue: () => void
  continueLabel?: string
  isSaving?: boolean
  canContinue?: boolean
  showBack?: boolean
}

export function StepLayout({
  stepNumber,
  totalSteps = 7,
  title,
  subtitle,
  icon: Icon,
  children,
  onBack,
  onContinue,
  continueLabel = 'Save & Continue',
  isSaving = false,
  canContinue = true,
  showBack = true,
}: StepLayoutProps) {
  return (
    <div className="animate-fade-in-up p-6 md:p-8">
      {/* Title Section with ornate styling */}
      <div className="relative text-center mb-10">
        {/* Decorative line flourishes */}
        <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 flex items-center justify-center pointer-events-none">
          <div className="flex-1 h-px bg-gradient-to-r from-transparent via-transparent to-primary/30" />
          <div className="w-32 md:w-48" />
          <div className="flex-1 h-px bg-gradient-to-l from-transparent via-transparent to-primary/30" />
        </div>

        <div className="relative inline-block">
          {Icon && (
            <div className="relative inline-flex items-center justify-center w-14 h-14 mb-4">
              {/* Rotating outer ring */}
              <div
                className="absolute inset-0 rounded-full border border-primary/30"
                style={{
                  background: 'conic-gradient(from 0deg, transparent, hsl(var(--primary) / 0.1), transparent, hsl(var(--primary) / 0.2), transparent)'
                }}
              />
              {/* Inner glow circle */}
              <div className="absolute inset-1 rounded-full bg-gradient-to-br from-primary/20 to-transparent" />
              {/* Icon */}
              <Icon className="relative w-7 h-7 text-primary" />
            </div>
          )}
          <h2 className="text-2xl md:text-3xl font-display tracking-wider text-gradient-gold mb-2">
            {title}
          </h2>
          {subtitle && (
            <p className="text-sm text-muted-foreground max-w-md mx-auto tracking-wide">
              {subtitle}
            </p>
          )}
        </div>
      </div>

      {/* Content Area */}
      <div className="mb-10">
        {children}
      </div>

      {/* Navigation Footer with decorative elements */}
      <div className="relative">
        {/* Top border decoration */}
        <div className="absolute -top-4 left-1/2 -translate-x-1/2 flex items-center gap-2">
          <div className="w-8 h-px bg-gradient-to-r from-transparent to-border" />
          <div className="w-1.5 h-1.5 rotate-45 bg-primary/40" />
          <div className="w-8 h-px bg-gradient-to-l from-transparent to-border" />
        </div>

        <div className="flex justify-center gap-4 pt-2">
          {showBack && onBack && (
            <button
              onClick={onBack}
              className="group relative px-6 py-3 font-display text-sm tracking-wide text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
              <span>Back</span>
            </button>
          )}
          <button
            onClick={onContinue}
            disabled={!canContinue || isSaving}
            className="btn-primary px-8 py-3 text-base flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <span>{continueLabel}</span>
                <ChevronRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * EditorCard - Ornate panel wrapper for editors
 * Features decorative corners and themed backgrounds
 */
interface EditorCardProps {
  title: string
  icon?: LucideIcon
  children: ReactNode
  className?: string
  variant?: 'combat' | 'magic' | 'default'
}

export function EditorCard({
  title,
  icon: Icon,
  children,
  className = '',
  variant = 'default',
}: EditorCardProps) {
  // Theme colors based on variant
  const themes = {
    combat: {
      accent: 'from-red-500/20 to-orange-500/10',
      border: 'border-red-500/20',
      iconBg: 'bg-gradient-to-br from-red-500/20 to-orange-500/10',
      iconColor: 'text-red-400',
      glow: 'shadow-red-500/5',
    },
    magic: {
      accent: 'from-violet-500/20 to-purple-500/10',
      border: 'border-violet-500/20',
      iconBg: 'bg-gradient-to-br from-violet-500/20 to-purple-500/10',
      iconColor: 'text-violet-400',
      glow: 'shadow-violet-500/5',
    },
    default: {
      accent: 'from-primary/15 to-amber-500/5',
      border: 'border-primary/20',
      iconBg: 'bg-gradient-to-br from-primary/20 to-amber-500/10',
      iconColor: 'text-primary',
      glow: 'shadow-primary/5',
    },
  }

  const theme = themes[variant]

  return (
    <div className={`relative group ${className}`}>
      {/* Main card container */}
      <div className={`
        relative overflow-hidden rounded-2xl
        bg-gradient-to-br from-card via-card to-card/80
        border ${theme.border}
        shadow-xl ${theme.glow}
        transition-all duration-300
        hover:shadow-2xl hover:border-opacity-40
      `}>
        {/* Decorative corner accents */}
        <div className="absolute top-0 left-0 w-16 h-16 pointer-events-none">
          <div className={`absolute top-0 left-0 w-full h-px bg-gradient-to-r ${theme.accent}`} />
          <div className={`absolute top-0 left-0 h-full w-px bg-gradient-to-b ${theme.accent}`} />
          <div className={`absolute top-2 left-2 w-2 h-2 border-t border-l ${theme.border} opacity-60`} />
        </div>
        <div className="absolute top-0 right-0 w-16 h-16 pointer-events-none">
          <div className={`absolute top-0 right-0 w-full h-px bg-gradient-to-l ${theme.accent}`} />
          <div className={`absolute top-0 right-0 h-full w-px bg-gradient-to-b ${theme.accent}`} />
          <div className={`absolute top-2 right-2 w-2 h-2 border-t border-r ${theme.border} opacity-60`} />
        </div>
        <div className="absolute bottom-0 left-0 w-16 h-16 pointer-events-none">
          <div className={`absolute bottom-0 left-0 w-full h-px bg-gradient-to-r ${theme.accent}`} />
          <div className={`absolute bottom-0 left-0 h-full w-px bg-gradient-to-t ${theme.accent}`} />
          <div className={`absolute bottom-2 left-2 w-2 h-2 border-b border-l ${theme.border} opacity-60`} />
        </div>
        <div className="absolute bottom-0 right-0 w-16 h-16 pointer-events-none">
          <div className={`absolute bottom-0 right-0 w-full h-px bg-gradient-to-l ${theme.accent}`} />
          <div className={`absolute bottom-0 right-0 h-full w-px bg-gradient-to-t ${theme.accent}`} />
          <div className={`absolute bottom-2 right-2 w-2 h-2 border-b border-r ${theme.border} opacity-60`} />
        </div>

        {/* Background gradient overlay */}
        <div className={`absolute inset-0 bg-gradient-to-br ${theme.accent} opacity-30 pointer-events-none`} />

        {/* Content */}
        <div className="relative p-5 md:p-6">
          {/* Header */}
          <div className="flex items-center gap-3 mb-5 pb-4 border-b border-border/50">
            {Icon && (
              <div className={`
                relative w-10 h-10 rounded-xl ${theme.iconBg}
                flex items-center justify-center
                ring-1 ring-inset ring-white/10
              `}>
                <Icon className={`w-5 h-5 ${theme.iconColor}`} />
              </div>
            )}
            <div className="flex-1">
              <h3 className="font-display text-base tracking-wide text-foreground">{title}</h3>
            </div>
          </div>

          {/* Body */}
          {children}
        </div>
      </div>
    </div>
  )
}

/**
 * DualEditorGrid - Asymmetric grid with visual connection
 */
export function DualEditorGrid({ children }: { children: ReactNode }) {
  return (
    <div className="relative">
      {/* Connection line between panels (desktop only) */}
      <div className="hidden lg:block absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 z-10">
        <div className="flex flex-col items-center gap-1">
          <div className="w-px h-8 bg-gradient-to-b from-transparent to-border/50" />
          <div className="w-2 h-2 rotate-45 border border-primary/30 bg-card" />
          <div className="w-px h-8 bg-gradient-to-t from-transparent to-border/50" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10">
        {children}
      </div>
    </div>
  )
}

/**
 * StatBlock - Compact stat display with D&D styling
 */
interface StatBlockProps {
  label: string
  value: string | number
  subtext?: string
  variant?: 'gold' | 'red' | 'blue' | 'purple'
}

export function StatBlock({ label, value, subtext, variant = 'gold' }: StatBlockProps) {
  const colors = {
    gold: 'from-amber-500/20 to-yellow-500/10 border-amber-500/30 text-amber-400',
    red: 'from-red-500/20 to-orange-500/10 border-red-500/30 text-red-400',
    blue: 'from-blue-500/20 to-cyan-500/10 border-blue-500/30 text-blue-400',
    purple: 'from-violet-500/20 to-purple-500/10 border-violet-500/30 text-violet-400',
  }

  return (
    <div className={`
      relative p-3 rounded-xl
      bg-gradient-to-br ${colors[variant].split(' ').slice(0, 2).join(' ')}
      border ${colors[variant].split(' ')[2]}
    `}>
      <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">{label}</p>
      <p className={`text-2xl font-bold font-display ${colors[variant].split(' ')[3]}`}>{value}</p>
      {subtext && <p className="text-xs text-muted-foreground mt-0.5">{subtext}</p>}
    </div>
  )
}

/**
 * ActionItem - Styled list item for actions/abilities
 */
interface ActionItemProps {
  icon: string
  name: string
  detail?: string
  badge?: string | number
  onClick?: () => void
  isExpanded?: boolean
  children?: ReactNode
}

export function ActionItem({ icon, name, detail, badge, onClick, isExpanded, children }: ActionItemProps) {
  return (
    <div className="group rounded-xl border border-border/50 bg-card/50 overflow-hidden transition-all hover:border-primary/30 hover:bg-card/80">
      <button
        onClick={onClick}
        className="w-full px-4 py-3 flex items-center gap-3 text-left"
      >
        <span className="text-lg flex-shrink-0">{icon}</span>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-foreground truncate">{name}</p>
          {detail && (
            <p className="text-xs text-muted-foreground truncate">{detail}</p>
          )}
        </div>
        {badge !== undefined && (
          <span className="px-2.5 py-1 text-xs font-bold bg-primary/20 text-primary rounded-lg">
            {typeof badge === 'number' ? `+${badge}` : badge}
          </span>
        )}
        {onClick && (
          <ChevronRight className={`w-4 h-4 text-muted-foreground transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
        )}
      </button>
      {isExpanded && children && (
        <div className="px-4 pb-4 pt-2 border-t border-border/50 bg-muted/20">
          {children}
        </div>
      )}
    </div>
  )
}

/**
 * SectionDivider - Ornate divider between sections
 */
export function SectionDivider({ label }: { label?: string }) {
  return (
    <div className="relative flex items-center gap-4 my-6">
      <div className="flex-1 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
      {label && (
        <span className="text-xs uppercase tracking-widest text-muted-foreground/60 font-medium">
          {label}
        </span>
      )}
      <div className="flex-1 h-px bg-gradient-to-l from-transparent via-border to-transparent" />
    </div>
  )
}
