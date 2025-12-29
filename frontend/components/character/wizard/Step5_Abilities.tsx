/**
 * Step 5: Abilities
 *
 * Edit actions/attacks and features/traits with full CRUD.
 * Uses wizard store directly with arcane-themed styling.
 */

'use client'

import { useState } from 'react'
import { Sparkles, Swords, ChevronDown, ChevronUp, Plus, Trash2, Zap, Shield, Wind, Edit2, X, Check } from 'lucide-react'
import { useWizardStore } from '@/lib/stores/wizardStore'
import { StepLayout, EditorCard, DualEditorGrid, SectionDivider } from './StepLayout'
import type { CharacterAction } from '@/lib/types/character'

type FeatureSection = 'racial' | 'class' | 'feats' | null

// Types for features
interface RacialTrait {
  name: string
  description?: string
  featureType?: string
}

interface ClassFeature {
  name: string
  description?: string
}

interface Feat {
  name: string
  description?: string
  isRepeatable?: boolean
}

/**
 * Render the "Actions & Features" wizard step UI for reviewing and editing combat actions, racial traits, class features, and feats.
 *
 * The component provides full create, read, update, and delete functionality for the action economy and features/traits and updates the wizard store when changes are made.
 *
 * @returns The JSX element for step 5 of the character wizard containing editors for action economy, racial traits, class features, and feats.
 */
export function Step5_Abilities() {
  const { characterData, updateSection, prevStep, nextStep } = useWizardStore()
  const [expandedAction, setExpandedAction] = useState<number | null>(null)
  const [expandedFeatureSection, setExpandedFeatureSection] = useState<FeatureSection>(null)

  // Feature editing states
  const [editingRacialTrait, setEditingRacialTrait] = useState<number | null>(null)
  const [editingFeat, setEditingFeat] = useState<number | null>(null)
  const [editingClassFeature, setEditingClassFeature] = useState<{ className: string; level: string; index: number } | null>(null)

  // New feature form states
  const [showNewRacialForm, setShowNewRacialForm] = useState(false)
  const [showNewFeatForm, setShowNewFeatForm] = useState(false)
  const [showNewClassFeatureForm, setShowNewClassFeatureForm] = useState(false)

  // Form data
  const [newRacialTrait, setNewRacialTrait] = useState<RacialTrait>({ name: '', description: '', featureType: 'trait' })
  const [newFeat, setNewFeat] = useState<Feat>({ name: '', description: '', isRepeatable: false })
  const [newClassFeature, setNewClassFeature] = useState<{ className: string; level: string; feature: ClassFeature }>({
    className: '',
    level: '1',
    feature: { name: '', description: '' }
  })

  const actionEconomy = characterData?.action_economy || {
    attacks_per_action: 1,
    actions: [],
  }

  const features = characterData?.features_and_traits || {
    racial_traits: [],
    class_features: {},
    feats: [],
    modifiers: {},
  }

  // Action type styling
  const getActionStyle = (type?: string | null) => {
    switch (type) {
      case 'action':
        return { icon: <Swords className="w-4 h-4" />, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' }
      case 'bonus_action':
        return { icon: <Zap className="w-4 h-4" />, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' }
      case 'reaction':
        return { icon: <Shield className="w-4 h-4" />, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' }
      case 'free_action':
        return { icon: <Wind className="w-4 h-4" />, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' }
      default:
        return { icon: <Swords className="w-4 h-4" />, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' }
    }
  }

  const updateAction = (index: number, field: string, value: any) => {
const updated = [...(actionEconomy.actions ?? [])]
    updated[index] = { ...updated[index], [field]: value }
    updateSection('action_economy', { ...actionEconomy, actions: updated })
  }

  const addAction = () => {
    const newAction: CharacterAction = {
      name: 'New Action',
      isWeaponAttack: false,
      requiresAmmo: false,
      actionCategory: 'action',
      attackBonus: 0,
    }
    updateSection('action_economy', {
      ...actionEconomy,
actions: [...(actionEconomy.actions ?? []), newAction],
    })
    setExpandedAction(actionEconomy.actions?.length || 0)
  }

  const removeAction = (index: number) => {
    const updated = (actionEconomy.actions ?? []).filter((_: any, i: number) => i !== index)
    updateSection('action_economy', { ...actionEconomy, actions: updated })
    if (expandedAction === index) setExpandedAction(null)
  }

  const stripHtml = (html: string | undefined) => {
    if (!html) return ''
    return html.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').trim()
  }

  const countClassFeatures = () => {
    if (!features.class_features) return 0
    return Object.values(features.class_features).reduce((total: number, levelFeatures: any) =>
      total + Object.values(levelFeatures).reduce((sum: number, f: any) => sum + (Array.isArray(f) ? f.length : 0), 0), 0
    )
  }

  // ==== RACIAL TRAITS CRUD ====
  const addRacialTrait = () => {
    if (!newRacialTrait.name.trim()) return
    const racialTraits = [...(features.racial_traits || []), { ...newRacialTrait }]
    updateSection('features_and_traits', { ...features, racial_traits: racialTraits })
    setNewRacialTrait({ name: '', description: '', featureType: 'trait' })
    setShowNewRacialForm(false)
  }

  const updateRacialTrait = (index: number, field: keyof RacialTrait, value: any) => {
    const racialTraits = [...(features.racial_traits || [])]
    racialTraits[index] = { ...racialTraits[index], [field]: value }
    updateSection('features_and_traits', { ...features, racial_traits: racialTraits })
  }

  const removeRacialTrait = (index: number) => {
    const racialTraits = features.racial_traits?.filter((_: any, i: number) => i !== index) || []
    updateSection('features_and_traits', { ...features, racial_traits: racialTraits })
    if (editingRacialTrait === index) setEditingRacialTrait(null)
  }

  // ==== FEATS CRUD ====
  const addFeat = () => {
    if (!newFeat.name.trim()) return
    const feats = [...(features.feats || []), { ...newFeat }]
    updateSection('features_and_traits', { ...features, feats })
    setNewFeat({ name: '', description: '', isRepeatable: false })
    setShowNewFeatForm(false)
  }

  const updateFeat = (index: number, field: keyof Feat, value: any) => {
    const feats = [...(features.feats || [])]
    feats[index] = { ...feats[index], [field]: value }
    updateSection('features_and_traits', { ...features, feats })
  }

  const removeFeat = (index: number) => {
    const feats = features.feats?.filter((_: any, i: number) => i !== index) || []
    updateSection('features_and_traits', { ...features, feats })
    if (editingFeat === index) setEditingFeat(null)
  }

  // ==== CLASS FEATURES CRUD ====
  const addClassFeature = () => {
    if (!newClassFeature.className.trim() || !newClassFeature.feature.name.trim()) return

    const classFeatures = { ...(features.class_features || {}) } as Record<string, Record<string, ClassFeature[]>>
    if (!classFeatures[newClassFeature.className]) {
      classFeatures[newClassFeature.className] = {}
    }
    if (!classFeatures[newClassFeature.className][newClassFeature.level]) {
      classFeatures[newClassFeature.className][newClassFeature.level] = []
    }
    classFeatures[newClassFeature.className][newClassFeature.level] = [
      ...classFeatures[newClassFeature.className][newClassFeature.level],
      { ...newClassFeature.feature }
    ]

    updateSection('features_and_traits', { ...features, class_features: classFeatures })
    setNewClassFeature({ className: '', level: '1', feature: { name: '', description: '' } })
    setShowNewClassFeatureForm(false)
  }

  const updateClassFeature = (className: string, level: string, index: number, field: keyof ClassFeature, value: any) => {
    const classFeatures = { ...(features.class_features || {}) } as Record<string, Record<string, ClassFeature[]>>
    if (classFeatures[className]?.[level]?.[index]) {
      classFeatures[className][level][index] = { ...classFeatures[className][level][index], [field]: value }
      updateSection('features_and_traits', { ...features, class_features: classFeatures })
    }
  }

  const removeClassFeature = (className: string, level: string, index: number) => {
    const classFeatures = { ...(features.class_features || {}) } as Record<string, Record<string, ClassFeature[]>>
    if (classFeatures[className]?.[level]) {
      classFeatures[className][level] = classFeatures[className][level].filter((_: any, i: number) => i !== index)
      // Clean up empty levels and classes
      if (classFeatures[className][level].length === 0) {
        delete classFeatures[className][level]
        if (Object.keys(classFeatures[className]).length === 0) {
          delete classFeatures[className]
        }
      }
      updateSection('features_and_traits', { ...features, class_features: classFeatures })
    }
    setEditingClassFeature(null)
  }

  // Get existing class names for dropdown
  const existingClassNames = Object.keys(features.class_features || {})

  return (
    <StepLayout
      stepNumber={5}
      title="Actions & Features"
      subtitle="Review your combat actions and character features"
      icon={Sparkles}
      onBack={prevStep}
      onContinue={nextStep}
      continueLabel="Save & Continue"
    >
      <DualEditorGrid>
        {/* Combat Actions Panel */}
        <EditorCard title="Actions & Attacks" icon={Swords} variant="combat">
          <div className="space-y-4">
            {/* Attacks per Action - Hero stat */}
            <div className="relative p-4 rounded-xl bg-gradient-to-br from-red-500/10 to-orange-500/5 border border-red-500/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-display text-sm tracking-wide text-foreground">Attacks per Action</p>
                  <p className="text-xs text-muted-foreground mt-0.5">When taking the Attack action</p>
                </div>
                <div className="relative">
                  <input
                    type="number"
                    min="1"
                    max="4"
                    value={actionEconomy.attacks_per_action || 1}
                    onChange={(e) => updateSection('action_economy', {
                      ...actionEconomy,
                      attacks_per_action: parseInt(e.target.value) || 1,
                    })}
                    className="w-16 h-12 text-center text-2xl font-bold font-display bg-card/80 border-2 border-red-500/30 rounded-xl text-red-400 focus:outline-none focus:border-red-500/60"
                  />
                </div>
              </div>
            </div>

            {/* Add Action */}
            <button
              onClick={addAction}
              className="w-full py-3 px-4 rounded-xl border-2 border-dashed border-red-500/20 text-red-400 hover:bg-red-500/5 hover:border-red-500/40 transition-all flex items-center justify-center gap-2 group"
            >
              <Plus className="w-4 h-4 transition-transform group-hover:scale-110" />
              <span className="font-medium">Add Action</span>
            </button>

            <SectionDivider label="Your Actions" />

            {/* Actions List */}
            <div className="space-y-2 max-h-[350px] overflow-y-auto pr-1 scrollbar-thin">
              {!actionEconomy.actions?.length ? (
                <div className="text-center py-10 text-muted-foreground">
                  <Swords className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">No actions configured</p>
                </div>
              ) : (
                actionEconomy.actions.map((action: any, index: number) => {
                  const isExpanded = expandedAction === index
                  const style = getActionStyle(action.actionCategory)

                  return (
                    <div
                      key={index}
                      className={`rounded-xl border overflow-hidden transition-all ${style.border} ${isExpanded ? 'bg-card/80' : 'bg-card/40 hover:bg-card/60'}`}
                    >
                      <button
                        onClick={() => setExpandedAction(isExpanded ? null : index)}
                        className="w-full px-4 py-3 flex items-center gap-3"
                      >
                        <div className={`w-8 h-8 rounded-lg ${style.bg} flex items-center justify-center ${style.color}`}>
                          {style.icon}
                        </div>
                        <div className="flex-1 text-left min-w-0">
                          <p className="font-medium text-foreground truncate">{action.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {action.actionCategory?.replace('_', ' ') || 'action'}
                            {action.damage?.diceNotation && ` · ${action.damage.diceNotation}`}
                          </p>
                        </div>
                        {action.attackBonus !== undefined && action.attackBonus !== 0 && (
                          <span className={`px-2 py-1 text-xs font-bold ${style.bg} ${style.color} rounded-lg`}>
                            +{action.attackBonus}
                          </span>
                        )}
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-muted-foreground" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-muted-foreground" />
                        )}
                      </button>

                      {isExpanded && (
                        <div className="px-4 pb-4 pt-2 border-t border-border/30 space-y-3">
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="block text-xs text-muted-foreground mb-1.5">Name</label>
                              <input
                                type="text"
                                value={action.name}
                                onChange={(e) => updateAction(index, 'name', e.target.value)}
                                className="w-full px-3 py-2 bg-muted/50 border border-border/50 rounded-lg text-sm focus:outline-none focus:border-primary/50"
                              />
                            </div>
                            <div>
                              <label className="block text-xs text-muted-foreground mb-1.5">Attack Bonus</label>
                              <input
                                type="number"
                                value={action.attackBonus || 0}
                                onChange={(e) => updateAction(index, 'attackBonus', parseInt(e.target.value) || 0)}
                                className="w-full px-3 py-2 bg-muted/50 border border-border/50 rounded-lg text-sm focus:outline-none focus:border-primary/50"
                              />
                            </div>
                          </div>

                          {action.description && (
                            <div>
                              <label className="block text-xs text-muted-foreground mb-1.5">Description</label>
                              <p className="text-sm text-foreground/80 bg-muted/30 p-3 rounded-lg border border-border/30">
                                {action.shortDescription || action.description}
                              </p>
                            </div>
                          )}

                          <button
                            onClick={() => removeAction(index)}
                            className="flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                            Remove Action
                          </button>
                        </div>
                      )}
                    </div>
                  )
                })
              )}
            </div>

            {/* Summary */}
            <div className="grid grid-cols-4 gap-2 pt-2">
              {['action', 'bonus_action', 'reaction', 'free_action'].map((type) => {
                const count = actionEconomy.actions?.filter((a: any) => a.actionCategory === type).length || 0
                const style = getActionStyle(type)
                return (
                  <div key={type} className={`p-2 rounded-lg ${style.bg} border ${style.border} text-center`}>
                    <p className={`text-lg font-bold font-display ${style.color}`}>{count}</p>
                    <p className="text-[10px] text-muted-foreground capitalize">{type.replace('_', ' ').replace('action', '')}</p>
                  </div>
                )
              })}
            </div>
          </div>
        </EditorCard>

        {/* Features & Traits Panel */}
        <EditorCard title="Features & Traits" icon={Sparkles} variant="magic">
          <div className="space-y-3">
            {/* RACIAL TRAITS */}
            <div
              className={`rounded-xl border overflow-hidden transition-all ${
                expandedFeatureSection === 'racial'
                  ? 'border-emerald-500/30 bg-emerald-500/5'
                  : 'border-border/50 bg-card/40 hover:bg-card/60 hover:border-emerald-500/20'
              }`}
            >
              <button
                onClick={() => setExpandedFeatureSection(expandedFeatureSection === 'racial' ? null : 'racial')}
                className="w-full px-4 py-3 flex items-center gap-3"
              >
                <span className="text-xl">🧬</span>
                <span className="flex-1 text-left font-medium text-foreground">Racial Traits</span>
                <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-emerald-500/20 text-emerald-400">
                  {features.racial_traits?.length || 0}
                </span>
                {expandedFeatureSection === 'racial' ? (
                  <ChevronUp className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                )}
              </button>

              {expandedFeatureSection === 'racial' && (
                <div className="px-4 pb-4 pt-2 border-t border-border/30 max-h-[300px] overflow-y-auto">
                  {/* Add New Racial Trait */}
                  {showNewRacialForm ? (
                    <div className="p-3 mb-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 space-y-3">
                      <div>
                        <label className="block text-xs text-muted-foreground mb-1">Name *</label>
                        <input
                          type="text"
                          value={newRacialTrait.name}
                          onChange={(e) => setNewRacialTrait({ ...newRacialTrait, name: e.target.value })}
                          placeholder="Trait name"
                          className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-muted-foreground mb-1">Description</label>
                        <textarea
                          value={newRacialTrait.description || ''}
                          onChange={(e) => setNewRacialTrait({ ...newRacialTrait, description: e.target.value })}
                          placeholder="Describe this trait..."
                          rows={3}
                          className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm resize-none"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={addRacialTrait}
                          disabled={!newRacialTrait.name.trim()}
                          className="flex-1 py-2 rounded-lg bg-emerald-500 text-white text-sm font-medium hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                          <Check className="w-4 h-4" /> Add
                        </button>
                        <button
                          onClick={() => { setShowNewRacialForm(false); setNewRacialTrait({ name: '', description: '', featureType: 'trait' }) }}
                          className="px-4 py-2 rounded-lg border border-border text-sm hover:bg-muted/50"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setShowNewRacialForm(true)}
                      className="w-full mb-3 py-2 rounded-lg border border-dashed border-emerald-500/30 text-emerald-400 text-sm hover:bg-emerald-500/5 flex items-center justify-center gap-2"
                    >
                      <Plus className="w-4 h-4" /> Add Racial Trait
                    </button>
                  )}

                  {/* Existing Racial Traits */}
                  {!features.racial_traits?.length ? (
                    <p className="text-sm text-muted-foreground text-center py-4">No racial traits</p>
                  ) : (
                    <div className="space-y-2">
                      {features.racial_traits.map((trait, idx) => (
                        <div key={idx} className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                          {editingRacialTrait === idx ? (
                            <div className="space-y-2">
                              <input
                                type="text"
                                value={trait.name}
                                onChange={(e) => updateRacialTrait(idx, 'name', e.target.value)}
                                className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm"
                              />
                              <textarea
                                value={trait.description || ''}
                                onChange={(e) => updateRacialTrait(idx, 'description', e.target.value)}
                                rows={3}
                                className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm resize-none"
                              />
                              <button
                                onClick={() => setEditingRacialTrait(null)}
                                className="text-xs text-emerald-400 hover:underline"
                              >
                                Done editing
                              </button>
                            </div>
                          ) : (
                            <>
                              <div className="flex items-start justify-between gap-2">
                                <p className="font-medium text-foreground text-sm">{trait.name}</p>
                                <div className="flex items-center gap-1">
                                  <button
                                    onClick={() => setEditingRacialTrait(idx)}
                                    className="p-1 text-muted-foreground hover:text-emerald-400 transition-colors"
                                  >
                                    <Edit2 className="w-3 h-3" />
                                  </button>
                                  <button
                                    onClick={() => removeRacialTrait(idx)}
                                    className="p-1 text-muted-foreground hover:text-red-400 transition-colors"
                                  >
                                    <Trash2 className="w-3 h-3" />
                                  </button>
                                </div>
                              </div>
                              {trait.description && (
                                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                  {stripHtml(trait.description)}
                                </p>
                              )}
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* CLASS FEATURES */}
            <div
              className={`rounded-xl border overflow-hidden transition-all ${
                expandedFeatureSection === 'class'
                  ? 'border-violet-500/30 bg-violet-500/5'
                  : 'border-border/50 bg-card/40 hover:bg-card/60 hover:border-violet-500/20'
              }`}
            >
              <button
                onClick={() => setExpandedFeatureSection(expandedFeatureSection === 'class' ? null : 'class')}
                className="w-full px-4 py-3 flex items-center gap-3"
              >
                <span className="text-xl">⚔️</span>
                <span className="flex-1 text-left font-medium text-foreground">Class Features</span>
                <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-violet-500/20 text-violet-400">
                  {countClassFeatures()}
                </span>
                {expandedFeatureSection === 'class' ? (
                  <ChevronUp className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                )}
              </button>

              {expandedFeatureSection === 'class' && (
                <div className="px-4 pb-4 pt-2 border-t border-border/30 max-h-[300px] overflow-y-auto">
                  {/* Add New Class Feature */}
                  {showNewClassFeatureForm ? (
                    <div className="p-3 mb-3 rounded-lg bg-violet-500/10 border border-violet-500/30 space-y-3">
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-xs text-muted-foreground mb-1">Class *</label>
                          <input
                            type="text"
                            list="class-names"
                            value={newClassFeature.className}
                            onChange={(e) => setNewClassFeature({ ...newClassFeature, className: e.target.value })}
                            placeholder="e.g., Fighter"
                            className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm"
                          />
                          <datalist id="class-names">
                            {existingClassNames.map(name => (
                              <option key={name} value={name} />
                            ))}
                          </datalist>
                        </div>
                        <div>
                          <label className="block text-xs text-muted-foreground mb-1">Level</label>
                          <select
                            value={newClassFeature.level}
                            onChange={(e) => setNewClassFeature({ ...newClassFeature, level: e.target.value })}
                            className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm"
                          >
                            {[...Array(20)].map((_, i) => (
                              <option key={i + 1} value={String(i + 1)}>{i + 1}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                      <div>
                        <label className="block text-xs text-muted-foreground mb-1">Feature Name *</label>
                        <input
                          type="text"
                          value={newClassFeature.feature.name}
                          onChange={(e) => setNewClassFeature({ ...newClassFeature, feature: { ...newClassFeature.feature, name: e.target.value } })}
                          placeholder="Feature name"
                          className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-muted-foreground mb-1">Description</label>
                        <textarea
                          value={newClassFeature.feature.description || ''}
                          onChange={(e) => setNewClassFeature({ ...newClassFeature, feature: { ...newClassFeature.feature, description: e.target.value } })}
                          placeholder="Describe this feature..."
                          rows={3}
                          className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm resize-none"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={addClassFeature}
                          disabled={!newClassFeature.className.trim() || !newClassFeature.feature.name.trim()}
                          className="flex-1 py-2 rounded-lg bg-violet-500 text-white text-sm font-medium hover:bg-violet-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                          <Check className="w-4 h-4" /> Add
                        </button>
                        <button
                          onClick={() => { setShowNewClassFeatureForm(false); setNewClassFeature({ className: '', level: '1', feature: { name: '', description: '' } }) }}
                          className="px-4 py-2 rounded-lg border border-border text-sm hover:bg-muted/50"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setShowNewClassFeatureForm(true)}
                      className="w-full mb-3 py-2 rounded-lg border border-dashed border-violet-500/30 text-violet-400 text-sm hover:bg-violet-500/5 flex items-center justify-center gap-2"
                    >
                      <Plus className="w-4 h-4" /> Add Class Feature
                    </button>
                  )}

                  {/* Existing Class Features */}
                  {!features.class_features || Object.keys(features.class_features).length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-4">No class features</p>
                  ) : (
                    <div className="space-y-3">
                      {Object.entries(features.class_features).map(([className, levelFeatures]: [string, any]) => (
                        <div key={className}>
                          <p className="font-display text-sm text-violet-400 mb-2">{className}</p>
                          <div className="space-y-1 pl-3 border-l-2 border-violet-500/30">
                            {Object.entries(levelFeatures).map(([level, featuresList]: [string, any]) => (
                              <div key={level}>
                                <p className="text-xs text-violet-400/70 font-medium mb-1">Level {level}</p>
                                {Array.isArray(featuresList) && featuresList.map((feature: ClassFeature, idx: number) => {
                                  const isEditing = editingClassFeature?.className === className &&
                                    editingClassFeature?.level === level &&
                                    editingClassFeature?.index === idx

                                  return (
                                    <div key={idx} className="flex items-start justify-between pl-2 py-1 group">
                                      {isEditing ? (
                                        <div className="flex-1 space-y-2">
                                          <input
                                            type="text"
                                            value={feature.name}
                                            onChange={(e) => updateClassFeature(className, level, idx, 'name', e.target.value)}
                                            className="w-full px-2 py-1 bg-card border border-border rounded text-sm"
                                          />
                                          <textarea
                                            value={feature.description || ''}
                                            onChange={(e) => updateClassFeature(className, level, idx, 'description', e.target.value)}
                                            rows={2}
                                            className="w-full px-2 py-1 bg-card border border-border rounded text-sm resize-none"
                                          />
                                          <button
                                            onClick={() => setEditingClassFeature(null)}
                                            className="text-xs text-violet-400 hover:underline"
                                          >
                                            Done
                                          </button>
                                        </div>
                                      ) : (
                                        <>
                                          <p className="text-sm text-foreground/80">{feature.name}</p>
                                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                              onClick={() => setEditingClassFeature({ className, level, index: idx })}
                                              className="p-1 text-muted-foreground hover:text-violet-400 transition-colors"
                                            >
                                              <Edit2 className="w-3 h-3" />
                                            </button>
                                            <button
                                              onClick={() => removeClassFeature(className, level, idx)}
                                              className="p-1 text-muted-foreground hover:text-red-400 transition-colors"
                                            >
                                              <Trash2 className="w-3 h-3" />
                                            </button>
                                          </div>
                                        </>
                                      )}
                                    </div>
                                  )
                                })}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* FEATS */}
            <div
              className={`rounded-xl border overflow-hidden transition-all ${
                expandedFeatureSection === 'feats'
                  ? 'border-amber-500/30 bg-amber-500/5'
                  : 'border-border/50 bg-card/40 hover:bg-card/60 hover:border-amber-500/20'
              }`}
            >
              <button
                onClick={() => setExpandedFeatureSection(expandedFeatureSection === 'feats' ? null : 'feats')}
                className="w-full px-4 py-3 flex items-center gap-3"
              >
                <span className="text-xl">⭐</span>
                <span className="flex-1 text-left font-medium text-foreground">Feats</span>
                <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-amber-500/20 text-amber-400">
                  {features.feats?.length || 0}
                </span>
                {expandedFeatureSection === 'feats' ? (
                  <ChevronUp className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                )}
              </button>

              {expandedFeatureSection === 'feats' && (
                <div className="px-4 pb-4 pt-2 border-t border-border/30 max-h-[300px] overflow-y-auto">
                  {/* Add New Feat */}
                  {showNewFeatForm ? (
                    <div className="p-3 mb-3 rounded-lg bg-amber-500/10 border border-amber-500/30 space-y-3">
                      <div>
                        <label className="block text-xs text-muted-foreground mb-1">Name *</label>
                        <input
                          type="text"
                          value={newFeat.name}
                          onChange={(e) => setNewFeat({ ...newFeat, name: e.target.value })}
                          placeholder="Feat name"
                          className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-muted-foreground mb-1">Description</label>
                        <textarea
                          value={newFeat.description || ''}
                          onChange={(e) => setNewFeat({ ...newFeat, description: e.target.value })}
                          placeholder="Describe this feat..."
                          rows={3}
                          className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm resize-none"
                        />
                      </div>
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={newFeat.isRepeatable || false}
                          onChange={(e) => setNewFeat({ ...newFeat, isRepeatable: e.target.checked })}
                          className="rounded border-border"
                        />
                        <span className="text-muted-foreground">Repeatable</span>
                      </label>
                      <div className="flex gap-2">
                        <button
                          onClick={addFeat}
                          disabled={!newFeat.name.trim()}
                          className="flex-1 py-2 rounded-lg bg-amber-500 text-white text-sm font-medium hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                          <Check className="w-4 h-4" /> Add
                        </button>
                        <button
                          onClick={() => { setShowNewFeatForm(false); setNewFeat({ name: '', description: '', isRepeatable: false }) }}
                          className="px-4 py-2 rounded-lg border border-border text-sm hover:bg-muted/50"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setShowNewFeatForm(true)}
                      className="w-full mb-3 py-2 rounded-lg border border-dashed border-amber-500/30 text-amber-400 text-sm hover:bg-amber-500/5 flex items-center justify-center gap-2"
                    >
                      <Plus className="w-4 h-4" /> Add Feat
                    </button>
                  )}

                  {/* Existing Feats */}
                  {!features.feats?.length ? (
                    <p className="text-sm text-muted-foreground text-center py-4">No feats</p>
                  ) : (
                    <div className="space-y-2">
                      {features.feats.map((feat, idx) => (
                        <div key={idx} className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
                          {editingFeat === idx ? (
                            <div className="space-y-2">
                              <input
                                type="text"
                                value={feat.name}
                                onChange={(e) => updateFeat(idx, 'name', e.target.value)}
                                className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm"
                              />
                              <textarea
                                value={feat.description || ''}
                                onChange={(e) => updateFeat(idx, 'description', e.target.value)}
                                rows={3}
                                className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm resize-none"
                              />
                              <label className="flex items-center gap-2 text-sm">
                                <input
                                  type="checkbox"
                                  checked={feat.isRepeatable || false}
                                  onChange={(e) => updateFeat(idx, 'isRepeatable', e.target.checked)}
                                  className="rounded border-border"
                                />
                                <span className="text-muted-foreground">Repeatable</span>
                              </label>
                              <button
                                onClick={() => setEditingFeat(null)}
                                className="text-xs text-amber-400 hover:underline"
                              >
                                Done editing
                              </button>
                            </div>
                          ) : (
                            <>
                              <div className="flex items-start justify-between gap-2">
                                <p className="font-medium text-foreground text-sm">{feat.name}</p>
                                <div className="flex items-center gap-1">
                                  {feat.isRepeatable && (
                                    <span className="px-1.5 py-0.5 text-[10px] bg-amber-500/20 text-amber-400 rounded">
                                      Repeatable
                                    </span>
                                  )}
                                  <button
                                    onClick={() => setEditingFeat(idx)}
                                    className="p-1 text-muted-foreground hover:text-amber-400 transition-colors"
                                  >
                                    <Edit2 className="w-3 h-3" />
                                  </button>
                                  <button
                                    onClick={() => removeFeat(idx)}
                                    className="p-1 text-muted-foreground hover:text-red-400 transition-colors"
                                  >
                                    <Trash2 className="w-3 h-3" />
                                  </button>
                                </div>
                              </div>
                              {feat.description && (
                                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                  {stripHtml(feat.description)}
                                </p>
                              )}
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            <SectionDivider />

            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20 text-center">
                <p className="text-2xl font-bold font-display text-emerald-400">{features.racial_traits?.length || 0}</p>
                <p className="text-xs text-muted-foreground">Traits</p>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-violet-500/10 to-violet-500/5 border border-violet-500/20 text-center">
                <p className="text-2xl font-bold font-display text-violet-400">{countClassFeatures()}</p>
                <p className="text-xs text-muted-foreground">Features</p>
              </div>
              <div className="p-3 rounded-xl bg-gradient-to-br from-amber-500/10 to-amber-500/5 border border-amber-500/20 text-center">
                <p className="text-2xl font-bold font-display text-amber-400">{features.feats?.length || 0}</p>
                <p className="text-xs text-muted-foreground">Feats</p>
              </div>
            </div>
          </div>
        </EditorCard>
      </DualEditorGrid>
    </StepLayout>
  )
}