/**
 * Step 3: Stats
 *
 * Edit ability scores and combat stats.
 * Uses wizard store directly - parent step handles save.
 */

'use client'

import { Swords, Info } from 'lucide-react'
import { useWizardStore } from '@/lib/stores/wizardStore'
import { StepLayout, EditorCard, DualEditorGrid } from './StepLayout'
import { cn } from '@/lib/utils'
import type { AbilityScores, CombatStats } from '@/lib/types/character'

const ABILITIES = [
  { key: 'strength' as const, label: 'Strength', abbr: 'STR', description: 'Physical power, melee attacks', color: 'from-red-500/20 to-red-600/10' },
  { key: 'dexterity' as const, label: 'Dexterity', abbr: 'DEX', description: 'Agility, AC, ranged attacks', color: 'from-green-500/20 to-green-600/10' },
  { key: 'constitution' as const, label: 'Constitution', abbr: 'CON', description: 'Endurance, hit points', color: 'from-orange-500/20 to-orange-600/10' },
  { key: 'intelligence' as const, label: 'Intelligence', abbr: 'INT', description: 'Reasoning, knowledge', color: 'from-blue-500/20 to-blue-600/10' },
  { key: 'wisdom' as const, label: 'Wisdom', abbr: 'WIS', description: 'Awareness, insight', color: 'from-purple-500/20 to-purple-600/10' },
  { key: 'charisma' as const, label: 'Charisma', abbr: 'CHA', description: 'Force of personality', color: 'from-pink-500/20 to-pink-600/10' },
]

export function Step3_Stats() {
  const { characterData, updateSection, prevStep, nextStep } = useWizardStore()

  const abilityScores = characterData?.ability_scores || {
    strength: 10,
    dexterity: 10,
    constitution: 10,
    intelligence: 10,
    wisdom: 10,
    charisma: 10,
  }

  const combatStats = characterData?.combat_stats || {
    max_hp: 0,
    armor_class: 10,
    initiative_bonus: 0,
    speed: 30,
  }

  const calculateModifier = (score: number): number => Math.floor((score - 10) / 2)
  const formatModifier = (mod: number): string => mod >= 0 ? `+${mod}` : `${mod}`

  const updateAbilityScore = (key: keyof AbilityScores, value: number) => {
    const clamped = Math.max(1, Math.min(30, value))
    updateSection('ability_scores', { ...abilityScores, [key]: clamped })
  }

  const updateCombatStat = (key: keyof CombatStats, value: number | Record<string, string>) => {
    updateSection('combat_stats', { ...combatStats, [key]: value })
  }

  // Summary calculations
  const totalScore = ABILITIES.reduce((sum, a) => sum + (abilityScores[a.key] || 0), 0)
  const avgScore = (totalScore / 6).toFixed(1)
  const totalModifiers = ABILITIES.reduce((sum, a) => sum + calculateModifier(abilityScores[a.key] || 0), 0)

  return (
    <StepLayout
      stepNumber={3}
      title="Ability Scores & Combat"
      subtitle="Review and adjust your character's core statistics"
      icon={Swords}
      onBack={prevStep}
      onContinue={nextStep}
      continueLabel="Save & Continue"
    >
      <DualEditorGrid>
        {/* Ability Scores */}
        <EditorCard title="Ability Scores" icon={Swords}>
          <div className="space-y-4">
            {ABILITIES.map((ability) => {
              const score = abilityScores[ability.key] || 10
              const modifier = calculateModifier(score)

              return (
                <div
                  key={ability.key}
                  className={cn(
                    'rounded-xl p-4 border border-border/50 bg-gradient-to-br',
                    ability.color
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <span className="font-display text-foreground">{ability.label}</span>
                      <p className="text-xs text-muted-foreground">{ability.description}</p>
                    </div>
                    <span className="text-sm font-bold text-primary">{ability.abbr}</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="flex-1">
                      <input
                        type="number"
                        min="1"
                        max="30"
                        value={score}
                        onChange={(e) => updateAbilityScore(ability.key, parseInt(e.target.value) || 10)}
                        className="w-full px-3 py-2 text-center text-xl font-bold bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                      />
                    </div>
                    <div className="flex-1">
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

            {/* Summary */}
            <div className="rounded-xl bg-muted/30 border border-border/50 p-4">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-foreground mb-2">Summary</p>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Total:</span>{' '}
                      <span className="font-semibold text-foreground">{totalScore}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Avg:</span>{' '}
                      <span className="font-semibold text-foreground">{avgScore}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Mods:</span>{' '}
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
          </div>
        </EditorCard>

        {/* Combat Stats */}
        <EditorCard title="Combat Statistics" icon={Swords}>
          <div className="space-y-4">
            {/* HP and AC */}
            <div className="grid grid-cols-2 gap-4">
              {/* Hit Points */}
              <div className="card-elevated p-4 bg-gradient-to-br from-red-500/10 to-red-600/5">
                <label className="block text-sm font-display text-muted-foreground mb-2 flex items-center gap-2">
                  <span className="text-xl">❤️</span>
                  <span>Max HP</span>
                </label>
                <input
                  type="number"
                  min="1"
                  value={combatStats.max_hp || 0}
                  onChange={(e) => updateCombatStat('max_hp', parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-2 text-2xl font-bold text-center bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50"
                />
              </div>

              {/* Armor Class */}
              <div className="card-elevated p-4 bg-gradient-to-br from-blue-500/10 to-blue-600/5">
                <label className="block text-sm font-display text-muted-foreground mb-2 flex items-center gap-2">
                  <span className="text-xl">🛡️</span>
                  <span>Armor Class</span>
                </label>
                <input
                  type="number"
                  min="1"
                  value={combatStats.armor_class || 10}
                  onChange={(e) => updateCombatStat('armor_class', parseInt(e.target.value) || 10)}
                  className="w-full px-3 py-2 text-2xl font-bold text-center bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50"
                />
              </div>
            </div>

            {/* Initiative and Speed */}
            <div className="grid grid-cols-2 gap-4">
              {/* Initiative */}
              <div className="card-elevated p-4 bg-gradient-to-br from-yellow-500/10 to-yellow-600/5">
                <label className="block text-sm font-display text-muted-foreground mb-2 flex items-center gap-2">
                  <span className="text-xl">⚡</span>
                  <span>Initiative</span>
                </label>
                <input
                  type="number"
                  value={combatStats.initiative_bonus || 0}
                  onChange={(e) => updateCombatStat('initiative_bonus', parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-2 text-2xl font-bold text-center bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50"
                />
                <p className="text-xs text-muted-foreground mt-1 text-center">
                  d20 {formatModifier(combatStats.initiative_bonus || 0)}
                </p>
              </div>

              {/* Speed */}
              <div className="card-elevated p-4 bg-gradient-to-br from-green-500/10 to-green-600/5">
                <label className="block text-sm font-display text-muted-foreground mb-2 flex items-center gap-2">
                  <span className="text-xl">👟</span>
                  <span>Speed</span>
                </label>
                <div className="relative">
                  <input
                    type="number"
                    min="0"
                    step="5"
                    value={combatStats.speed || 30}
                    onChange={(e) => updateCombatStat('speed', parseInt(e.target.value) || 30)}
                    className="w-full px-3 py-2 pr-10 text-2xl font-bold text-center bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm font-bold text-muted-foreground">ft</span>
                </div>
              </div>
            </div>

            {/* Hit Dice */}
            {combatStats.hit_dice && Object.keys(combatStats.hit_dice).length > 0 && (
              <div className="card-elevated p-4">
                <h4 className="text-sm font-display text-muted-foreground mb-3 flex items-center gap-2">
                  <span className="text-xl">🎲</span>
                  <span>Hit Dice</span>
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(combatStats.hit_dice).map(([className, dice]) => (
                    <div key={className} className="bg-muted/30 rounded-lg p-3 text-center">
                      <div className="text-xs font-medium text-muted-foreground mb-1">{className}</div>
                      <div className="text-lg font-bold text-foreground">{dice}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Reference */}
            <div className="rounded-xl bg-primary/5 border border-primary/20 p-4">
              <p className="font-display text-sm text-foreground mb-2">Quick Reference</p>
              <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                <div><span className="text-foreground">AC 10:</span> Unarmored</div>
                <div><span className="text-foreground">AC 15:</span> Chain shirt</div>
                <div><span className="text-foreground">AC 18:</span> Plate armor</div>
                <div><span className="text-foreground">30 ft:</span> Standard speed</div>
              </div>
            </div>
          </div>
        </EditorCard>
      </DualEditorGrid>
    </StepLayout>
  )
}
