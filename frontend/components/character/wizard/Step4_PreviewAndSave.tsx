/**
 * Step 4: Preview & Save
 *
 * Final preview of character with save to database
 */

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import type { CharacterData } from '@/lib/types/character'
import { Save, Loader2, AlertTriangle, PartyPopper, MessageSquare, User, RefreshCw, Backpack, Sparkles, ScrollText, Heart, Shield, Zap, Eye } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Step4_PreviewAndSaveProps {
  characterData: CharacterData | null
  savedCharacterId: number | null
  onSave: () => Promise<void>
  onReset: () => void
}

export function Step4_PreviewAndSave({
  characterData,
  savedCharacterId,
  onSave,
  onReset,
}: Step4_PreviewAndSaveProps) {
  const router = useRouter()
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const handleSave = async () => {
    setIsSaving(true)
    setSaveError(null)
    try {
      await onSave()
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save character')
    } finally {
      setIsSaving(false)
    }
  }

  if (!characterData) {
    return (
      <div className="p-12 text-center">
        <p className="text-muted-foreground">No character data available</p>
      </div>
    )
  }

  // If character is already saved, show success state
  if (savedCharacterId) {
    return (
      <div className="p-8 md:p-12">
        <div className="max-w-2xl mx-auto text-center">
          <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-6">
            <PartyPopper className="w-10 h-10 text-emerald-500" />
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-emerald-500 mb-3">
            Character Saved!
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            {characterData.character_base?.name || 'Your character'} is now ready for adventure
          </p>

          <div className="rounded-xl bg-emerald-500/5 border border-emerald-500/20 p-6 mb-8">
            <p className="text-sm text-muted-foreground mb-1">Character ID</p>
            <p className="text-2xl font-bold text-foreground font-mono">{savedCharacterId}</p>
          </div>

          <div className="space-y-3">
            <button
              onClick={() => {
                const characterName = characterData.character_base?.name
                if (characterName) {
                  const encodedName = encodeURIComponent(characterName)
                  router.push(`/?character=${encodedName}`)
                }
              }}
              className="btn-primary w-full py-4 text-lg flex items-center justify-center gap-3"
            >
              <MessageSquare className="w-5 h-5" />
              Start Chatting with {characterData.character_base?.name || 'Character'}
            </button>
            <a
              href={`/characters/${savedCharacterId}`}
              className="btn-secondary w-full py-3 flex items-center justify-center gap-2"
            >
              <User className="w-4 h-4" />
              View Character Details
            </a>
            <button
              onClick={onReset}
              className="btn-ghost w-full py-3 flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Import Another Character
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Otherwise show preview and save UI
  const charBase = characterData.character_base
  const abilityScores = characterData.ability_scores
  const combatStats = characterData.combat_stats
  const inventory = characterData.inventory
  const spellList = characterData.spell_list
  const backstory = characterData.backstory
  const personality = characterData.personality

  return (
    <div className="p-6 md:p-10">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-5">
            <Eye className="w-8 h-8 text-primary" />
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-2">
            Character Preview
          </h2>
          <p className="text-muted-foreground">
            Review your character before saving to the database
          </p>
        </div>

        {/* Error Display */}
        {saveError && (
          <div className="flex items-start gap-3 p-4 rounded-xl bg-destructive/10 border border-destructive/20 mb-8">
            <AlertTriangle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-destructive">Save Failed</p>
              <p className="text-sm text-destructive/80 mt-1">{saveError}</p>
            </div>
          </div>
        )}

        {/* Character Summary Card */}
        <div className="rounded-2xl bg-gradient-to-br from-primary/5 via-card to-accent/5 border border-border/50 p-6 md:p-8 mb-8">
          {/* Character header */}
          <div className="text-center mb-8">
            <h3 className="text-3xl md:text-4xl font-bold text-gradient-gold mb-2">
              {charBase?.name || 'Unknown Character'}
            </h3>
            <p className="text-lg text-muted-foreground">
              {charBase?.race && charBase?.character_class
                ? `${charBase.race} ${charBase.character_class}`
                : 'Unknown Race/Class'}
            </p>
          </div>

          {/* Core Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard label="Level" value={charBase?.total_level || '?'} color="primary" />
            <StatCard
              label="Hit Points"
              value={`${combatStats?.current_hp || '?'}/${combatStats?.max_hp || '?'}`}
              color="destructive"
            />
            <StatCard
              label="Armor Class"
              value={combatStats?.armor_class || '?'}
              color="secondary"
            />
            <StatCard
              label="Initiative"
              value={
                combatStats?.initiative_bonus !== undefined
                  ? combatStats.initiative_bonus >= 0
                    ? `+${combatStats.initiative_bonus}`
                    : combatStats.initiative_bonus
                  : '?'
              }
              color="accent"
            />
          </div>

          {/* Ability Scores */}
          {abilityScores && (
            <div className="rounded-xl bg-card/50 border border-border/50 p-4">
              <h4 className="font-semibold text-foreground mb-4 text-center">Ability Scores</h4>
              <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                {[
                  { label: 'STR', value: abilityScores.strength },
                  { label: 'DEX', value: abilityScores.dexterity },
                  { label: 'CON', value: abilityScores.constitution },
                  { label: 'INT', value: abilityScores.intelligence },
                  { label: 'WIS', value: abilityScores.wisdom },
                  { label: 'CHA', value: abilityScores.charisma },
                ].map(({ label, value }) => (
                  <div key={label} className="text-center p-3 rounded-lg bg-muted/30">
                    <span className="text-xs text-muted-foreground block mb-1">{label}</span>
                    <span className="text-xl font-bold text-foreground">{value || '?'}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Section Summary */}
        <div className="grid md:grid-cols-2 gap-4 mb-10">
          {inventory && (
            <SummaryCard
              icon={<Backpack className="w-5 h-5" />}
              title="Inventory"
              content={`${Object.keys(inventory.equipped_items || {}).length} equipped, ${inventory.backpack?.length || 0} items`}
            />
          )}
          {spellList && (
            <SummaryCard
              icon={<Sparkles className="w-5 h-5" />}
              title="Spells"
              content={`${spellList.spells?.length || 0} spells known`}
            />
          )}
          {backstory && (
            <SummaryCard
              icon={<ScrollText className="w-5 h-5" />}
              title="Backstory"
              content={backstory.early_life?.substring(0, 60) + '...' || 'No backstory'}
            />
          )}
          {personality && (
            <SummaryCard
              icon={<Heart className="w-5 h-5" />}
              title="Personality"
              content={personality.traits?.substring(0, 60) + '...' || 'No traits'}
            />
          )}
        </div>

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="btn-primary w-full py-4 text-lg flex items-center justify-center gap-3"
        >
          {isSaving ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Saving Character...
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              Save Character to Database
            </>
          )}
        </button>

        {/* Info Box */}
        <div className="mt-6 p-5 rounded-xl bg-muted/30 border border-border/50">
          <h4 className="font-medium text-foreground mb-2">What happens when you save?</h4>
          <ul className="space-y-1.5 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-primary" />
              Character data is stored in the database
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-primary" />
              You can view and edit the character anytime
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-primary" />
              Character becomes available for AI assistant queries
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-primary" />
              Original D&D Beyond data is preserved
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}

interface StatCardProps {
  label: string
  value: string | number
  color?: 'primary' | 'secondary' | 'accent' | 'destructive'
}

function StatCard({ label, value, color = 'primary' }: StatCardProps) {
  const colorClasses = {
    primary: 'text-primary',
    secondary: 'text-secondary-foreground',
    accent: 'text-accent',
    destructive: 'text-destructive',
  }

  return (
    <div className="rounded-xl bg-card/50 border border-border/50 p-4 text-center">
      <span className="text-xs text-muted-foreground block mb-1">{label}</span>
      <span className={cn('text-2xl md:text-3xl font-bold', colorClasses[color])}>
        {value}
      </span>
    </div>
  )
}

interface SummaryCardProps {
  icon: React.ReactNode
  title: string
  content: string
}

function SummaryCard({ icon, title, content }: SummaryCardProps) {
  return (
    <div className="rounded-xl bg-card/50 border border-border/50 p-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center text-muted-foreground">
          {icon}
        </div>
        <h4 className="font-medium text-foreground">{title}</h4>
      </div>
      <p className="text-sm text-muted-foreground line-clamp-2">{content}</p>
    </div>
  )
}
