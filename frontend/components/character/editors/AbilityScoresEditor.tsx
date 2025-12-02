/**
 * Ability Scores Editor
 *
 * Editor for the 6 core D&D ability scores with automatic modifier calculation
 */

'use client'

import { useState } from 'react'
import { Save, Loader2, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AbilityScoresData {
  strength?: number
  dexterity?: number
  constitution?: number
  intelligence?: number
  wisdom?: number
  charisma?: number
  [key: string]: any
}

interface AbilityScoresEditorProps {
  data: AbilityScoresData | null
  onSave: (data: AbilityScoresData) => void
}

const ABILITIES = [
  { key: 'strength', label: 'Strength', abbr: 'STR', description: 'Physical power, melee attacks', color: 'from-red-500/20 to-red-600/10' },
  { key: 'dexterity', label: 'Dexterity', abbr: 'DEX', description: 'Agility, AC, ranged attacks', color: 'from-green-500/20 to-green-600/10' },
  { key: 'constitution', label: 'Constitution', abbr: 'CON', description: 'Endurance, hit points', color: 'from-orange-500/20 to-orange-600/10' },
  { key: 'intelligence', label: 'Intelligence', abbr: 'INT', description: 'Reasoning, knowledge', color: 'from-blue-500/20 to-blue-600/10' },
  { key: 'wisdom', label: 'Wisdom', abbr: 'WIS', description: 'Awareness, insight', color: 'from-purple-500/20 to-purple-600/10' },
  { key: 'charisma', label: 'Charisma', abbr: 'CHA', description: 'Force of personality', color: 'from-pink-500/20 to-pink-600/10' },
]

export function AbilityScoresEditor({ data, onSave }: AbilityScoresEditorProps) {
  const [scores, setScores] = useState<AbilityScoresData>(data || {
    strength: 10,
    dexterity: 10,
    constitution: 10,
    intelligence: 10,
    wisdom: 10,
    charisma: 10,
  })
  const [isSaving, setIsSaving] = useState(false)

  const calculateModifier = (score: number): number => {
    return Math.floor((score - 10) / 2)
  }

  const formatModifier = (modifier: number): string => {
    return modifier >= 0 ? `+${modifier}` : `${modifier}`
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await onSave(scores)
    } finally {
      setIsSaving(false)
    }
  }

  const updateScore = (ability: string, value: string) => {
    const numValue = parseInt(value) || 0
    // Clamp between 1 and 30 (D&D 5e typical range)
    const clampedValue = Math.max(1, Math.min(30, numValue))
    setScores({ ...scores, [ability]: clampedValue })
  }

  // Calculate summary stats
  const totalScore = ABILITIES.reduce((sum, a) => sum + (scores[a.key] || 0), 0)
  const avgScore = (totalScore / 6).toFixed(1)
  const totalModifiers = ABILITIES.reduce((sum, a) => sum + calculateModifier(scores[a.key] || 0), 0)

  return (
    <div className="space-y-6">
      {/* Ability Scores Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {ABILITIES.map((ability) => {
          const score = scores[ability.key] || 10
          const modifier = calculateModifier(score)

          return (
            <div
              key={ability.key}
              className={cn(
                'rounded-xl p-4 border border-border/50 bg-gradient-to-br',
                ability.color
              )}
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-foreground">{ability.label}</h3>
                  <p className="text-xs text-muted-foreground">{ability.description}</p>
                </div>
                <span className="text-lg font-bold text-primary">{ability.abbr}</span>
              </div>

              <div className="flex items-center gap-3">
                {/* Score Input */}
                <div className="flex-1">
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Score</label>
                  <input
                    type="number"
                    min="1"
                    max="30"
                    value={score}
                    onChange={(e) => updateScore(ability.key, e.target.value)}
                    className="w-full px-3 py-2 text-center text-xl font-bold bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                  />
                </div>

                {/* Modifier Display */}
                <div className="flex-1">
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Modifier</label>
                  <div className={cn(
                    'px-3 py-2 text-center text-xl font-bold rounded-lg border-2',
                    modifier >= 0
                      ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/30'
                      : 'bg-red-500/10 text-red-600 border-red-500/30'
                  )}>
                    {formatModifier(modifier)}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Stats Summary */}
      <div className="rounded-xl bg-muted/30 border border-border/50 p-4">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-muted-foreground flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-medium text-foreground mb-2">Ability Score Summary</p>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Total:</span>{' '}
                <span className="font-semibold text-foreground">{totalScore}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Average:</span>{' '}
                <span className="font-semibold text-foreground">{avgScore}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Total Mods:</span>{' '}
                <span className={cn(
                  'font-semibold',
                  totalModifiers >= 0 ? 'text-emerald-600' : 'text-red-600'
                )}>
                  {formatModifier(totalModifiers)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Reference Guide */}
      <div className="rounded-xl bg-primary/5 border border-primary/20 p-4">
        <p className="font-medium text-foreground mb-2">D&D 5e Score Guidelines</p>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs">
          <div className="text-muted-foreground">
            <span className="font-semibold text-foreground">10-11:</span> Average
          </div>
          <div className="text-muted-foreground">
            <span className="font-semibold text-foreground">14-15:</span> Gifted
          </div>
          <div className="text-muted-foreground">
            <span className="font-semibold text-foreground">18:</span> Exceptional
          </div>
          <div className="text-muted-foreground">
            <span className="font-semibold text-foreground">20:</span> Legendary
          </div>
          <div className="text-muted-foreground">
            <span className="font-semibold text-foreground">30:</span> Divine
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="btn-primary flex items-center gap-2"
        >
          {isSaving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save Ability Scores
            </>
          )}
        </button>
      </div>
    </div>
  )
}
