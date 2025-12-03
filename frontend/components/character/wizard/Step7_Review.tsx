/**
 * Step 7: Review & Save
 *
 * Final character preview and database save.
 * Uses wizard store directly.
 */

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ScrollText, Check, Loader2, AlertTriangle, Swords, Backpack, Sparkles, User } from 'lucide-react'
import { useWizardStore } from '@/lib/stores/wizardStore'

export function Step7_Review() {
  const router = useRouter()
  const {
    characterData,
    characterSummary,
    prevStep,
    setIsSaving,
    setSavedCharacterId,
    setError,
    clearDraft,
    isSaving,
    error,
    savedCharacterId,
  } = useWizardStore()

  const [saveSuccess, setSaveSuccess] = useState(false)

  const handleSave = async () => {
    if (!characterData) {
      setError('No character data to save')
      return
    }

    setIsSaving(true)
    setError(null)

    try {
      const response = await fetch('/api/characters', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(characterData),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `Failed to save character: ${response.status}`)
      }

      const result = await response.json()
      setSavedCharacterId(result.id)
      setSaveSuccess(true)
      clearDraft()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save character'
      setError(errorMessage)
    } finally {
      setIsSaving(false)
    }
  }

  const handleGoToChat = () => {
    // Navigate to chat with the newly created character
    router.push('/')
  }

  const handleCreateAnother = () => {
    // Reset and start over
    router.push('/character/create')
    window.location.reload()
  }

  // Character name helper
  const characterName = characterSummary?.name || characterData?.character_base?.name || 'Unknown Character'

  // Section data helpers
  const abilityScores = characterData?.ability_scores
  const combatStats = characterData?.combat_stats
  const inventory = characterData?.inventory
  const spellList = characterData?.spell_list
  const actionEconomy = characterData?.action_economy
  const features = characterData?.features_and_traits
  const personality = characterData?.personality
  const backstory = characterData?.backstory

  // Calculate modifier
  const formatMod = (score: number | undefined) => {
    if (!score) return '+0'
    const mod = Math.floor((score - 10) / 2)
    return mod >= 0 ? `+${mod}` : `${mod}`
  }

  // Count spells
  const totalSpells = (() => {
    if (!spellList?.spells) return 0
    let count = 0
    Object.values(spellList.spells).forEach((classSpells: any) => {
      if (typeof classSpells === 'object') {
        Object.values(classSpells).forEach((levelSpells: any) => {
          if (Array.isArray(levelSpells)) count += levelSpells.length
        })
      }
    })
    return count
  })()

  // Success state
  if (saveSuccess && savedCharacterId) {
    return (
      <div className="p-8 md:p-12">
        <div className="max-w-xl mx-auto text-center">
          <div className="w-20 h-20 rounded-2xl bg-emerald-500/20 flex items-center justify-center mx-auto mb-6">
            <Check className="w-10 h-10 text-emerald-500" />
          </div>
          <h2 className="text-3xl font-display tracking-wide text-gradient-gold text-shadow-sm mb-4">
            Character Saved!
          </h2>
          <p className="text-muted-foreground mb-8">
            <span className="font-display text-foreground">{characterName}</span> has been saved to your character library.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleGoToChat}
              className="btn-primary px-8 py-3"
            >
              Start Chatting
            </button>
            <button
              onClick={handleCreateAnother}
              className="btn-ghost px-8 py-3"
            >
              Create Another
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 md:p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={prevStep}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
        >
          <span>←</span>
          <span className="text-sm font-display">Back</span>
        </button>
        <span className="text-sm text-muted-foreground font-display">Step 7 of 7</span>
      </div>

      {/* Title */}
      <div className="text-center mb-8">
        <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4 glow-gold-sm">
          <ScrollText className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-2xl md:text-3xl font-display tracking-wide text-gradient-gold text-shadow-sm mb-2">
          Review & Save
        </h2>
        <p className="text-muted-foreground">
          Review your character before saving to the database
        </p>
      </div>

      {/* Character Header Card */}
      <div className="card-arcane p-6 mb-6">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
            <span className="text-3xl">⚔️</span>
          </div>
          <div>
            <h3 className="text-2xl font-display text-gradient-gold">{characterName}</h3>
            <p className="text-muted-foreground">
              {characterSummary?.race || characterData?.character_base?.race || 'Unknown Race'}{' '}
              {characterSummary?.character_class || characterData?.character_base?.character_class || 'Unknown Class'}{' '}
              (Level {characterSummary?.level || characterData?.character_base?.total_level || 1})
            </p>
          </div>
        </div>
      </div>

      {/* Summary Grid */}
      <div className="grid md:grid-cols-2 gap-4 mb-8">
        {/* Stats */}
        <div className="card-elevated p-4">
          <div className="flex items-center gap-2 mb-3">
            <Swords className="w-5 h-5 text-primary" />
            <h4 className="font-display text-foreground">Stats & Combat</h4>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {abilityScores && (
              <>
                <div className="text-center p-2 rounded bg-muted/30">
                  <p className="text-xs text-muted-foreground">STR</p>
                  <p className="font-bold">{abilityScores.strength} ({formatMod(abilityScores.strength)})</p>
                </div>
                <div className="text-center p-2 rounded bg-muted/30">
                  <p className="text-xs text-muted-foreground">DEX</p>
                  <p className="font-bold">{abilityScores.dexterity} ({formatMod(abilityScores.dexterity)})</p>
                </div>
                <div className="text-center p-2 rounded bg-muted/30">
                  <p className="text-xs text-muted-foreground">CON</p>
                  <p className="font-bold">{abilityScores.constitution} ({formatMod(abilityScores.constitution)})</p>
                </div>
                <div className="text-center p-2 rounded bg-muted/30">
                  <p className="text-xs text-muted-foreground">INT</p>
                  <p className="font-bold">{abilityScores.intelligence} ({formatMod(abilityScores.intelligence)})</p>
                </div>
                <div className="text-center p-2 rounded bg-muted/30">
                  <p className="text-xs text-muted-foreground">WIS</p>
                  <p className="font-bold">{abilityScores.wisdom} ({formatMod(abilityScores.wisdom)})</p>
                </div>
                <div className="text-center p-2 rounded bg-muted/30">
                  <p className="text-xs text-muted-foreground">CHA</p>
                  <p className="font-bold">{abilityScores.charisma} ({formatMod(abilityScores.charisma)})</p>
                </div>
              </>
            )}
          </div>
          {combatStats && (
            <div className="grid grid-cols-4 gap-2 mt-3 pt-3 border-t border-border">
              <div className="text-center">
                <p className="text-xs text-muted-foreground">HP</p>
                <p className="font-bold text-red-500">{combatStats.max_hp}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-muted-foreground">AC</p>
                <p className="font-bold text-blue-500">{combatStats.armor_class}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-muted-foreground">Init</p>
                <p className="font-bold text-yellow-500">{formatMod(10 + (combatStats.initiative_bonus || 0))}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-muted-foreground">Speed</p>
                <p className="font-bold text-green-500">{combatStats.speed}ft</p>
              </div>
            </div>
          )}
        </div>

        {/* Equipment */}
        <div className="card-elevated p-4">
          <div className="flex items-center gap-2 mb-3">
            <Backpack className="w-5 h-5 text-primary" />
            <h4 className="font-display text-foreground">Equipment & Spells</h4>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded bg-muted/30">
              <p className="text-xs text-muted-foreground">Equipped Items</p>
              <p className="text-xl font-bold text-foreground">{inventory?.equipped_items?.length || 0}</p>
            </div>
            <div className="p-3 rounded bg-muted/30">
              <p className="text-xs text-muted-foreground">Backpack Items</p>
              <p className="text-xl font-bold text-foreground">{inventory?.backpack?.length || 0}</p>
            </div>
            <div className="p-3 rounded bg-purple-500/10">
              <p className="text-xs text-muted-foreground">Total Spells</p>
              <p className="text-xl font-bold text-purple-500">{totalSpells}</p>
            </div>
            <div className="p-3 rounded bg-muted/30">
              <p className="text-xs text-muted-foreground">Actions</p>
              <p className="text-xl font-bold text-foreground">{actionEconomy?.actions?.length || 0}</p>
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="card-elevated p-4">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-primary" />
            <h4 className="font-display text-foreground">Features & Traits</h4>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded bg-muted/30">
              <p className="text-xs text-muted-foreground">Racial</p>
              <p className="text-xl font-bold text-foreground">{features?.racial_traits?.length || 0}</p>
            </div>
            <div className="p-3 rounded bg-muted/30">
              <p className="text-xs text-muted-foreground">Class</p>
              <p className="text-xl font-bold text-foreground">
                {features?.class_features
                  ? Object.values(features.class_features).reduce((total, levelFeatures) =>
                      total + Object.values(levelFeatures).reduce((sum, f) => sum + f.length, 0), 0
                    )
                  : 0}
              </p>
            </div>
            <div className="p-3 rounded bg-muted/30">
              <p className="text-xs text-muted-foreground">Feats</p>
              <p className="text-xl font-bold text-foreground">{features?.feats?.length || 0}</p>
            </div>
          </div>
        </div>

        {/* Personality */}
        <div className="card-elevated p-4">
          <div className="flex items-center gap-2 mb-3">
            <User className="w-5 h-5 text-primary" />
            <h4 className="font-display text-foreground">Personality & Story</h4>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded bg-pink-500/10">
              <p className="text-xs text-muted-foreground">Personality</p>
              <p className="text-xl font-bold text-pink-500">
                {(personality?.personality_traits?.length || 0) +
                  (personality?.ideals?.length || 0) +
                  (personality?.bonds?.length || 0) +
                  (personality?.flaws?.length || 0)}
              </p>
            </div>
            <div className="p-3 rounded bg-muted/30">
              <p className="text-xs text-muted-foreground">Backstory</p>
              <p className="text-xl font-bold text-foreground">{backstory?.sections?.length || 0} sections</p>
            </div>
          </div>
          {backstory?.title && (
            <p className="mt-3 text-sm text-muted-foreground italic">"{backstory.title}"</p>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-destructive/10 border border-destructive/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-destructive">Save Failed</p>
            <p className="text-sm text-destructive/80">{error}</p>
          </div>
        </div>
      )}

      {/* Save Button */}
      <div className="flex justify-center">
        <button
          onClick={handleSave}
          disabled={isSaving || !characterData}
          className="btn-primary px-10 py-4 text-lg flex items-center gap-3"
        >
          {isSaving ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Saving to Database...</span>
            </>
          ) : (
            <>
              <Check className="w-5 h-5" />
              <span>Save Character</span>
            </>
          )}
        </button>
      </div>
    </div>
  )
}
