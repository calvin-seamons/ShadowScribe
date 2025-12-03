/**
 * Step 5: Abilities
 *
 * Edit actions/attacks and view features/traits.
 * Uses wizard store directly with arcane-themed styling.
 */

'use client'

import { useState } from 'react'
import { Sparkles, Swords, ChevronDown, ChevronUp, Plus, Trash2, Zap, Shield, Wind } from 'lucide-react'
import { useWizardStore } from '@/lib/stores/wizardStore'
import { StepLayout, EditorCard, DualEditorGrid, SectionDivider } from './StepLayout'
import type { CharacterAction } from '@/lib/types/character'

type FeatureSection = 'racial' | 'class' | 'feats' | null

export function Step5_Abilities() {
  const { characterData, updateSection, prevStep, nextStep } = useWizardStore()
  const [expandedAction, setExpandedAction] = useState<number | null>(null)
  const [expandedFeatureSection, setExpandedFeatureSection] = useState<FeatureSection>(null)

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
    const updated = [...(actionEconomy.actions || [])]
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
      actions: [...(actionEconomy.actions || []), newAction],
    })
    setExpandedAction(actionEconomy.actions?.length || 0)
  }

  const removeAction = (index: number) => {
    const updated = actionEconomy.actions.filter((_, i) => i !== index)
    updateSection('action_economy', { ...actionEconomy, actions: updated })
    if (expandedAction === index) setExpandedAction(null)
  }

  const stripHtml = (html: string | undefined) => {
    if (!html) return ''
    return html.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').trim()
  }

  const countClassFeatures = () => {
    if (!features.class_features) return 0
    return Object.values(features.class_features).reduce((total, levelFeatures) =>
      total + Object.values(levelFeatures).reduce((sum, f) => sum + f.length, 0), 0
    )
  }

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
                actionEconomy.actions.map((action, index) => {
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
                const count = actionEconomy.actions?.filter(a => a.actionCategory === type).length || 0
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
            {/* Feature Categories */}
            {[
              { key: 'racial', label: 'Racial Traits', icon: '🧬', count: features.racial_traits?.length || 0, color: 'emerald' },
              { key: 'class', label: 'Class Features', icon: '⚔️', count: countClassFeatures(), color: 'violet' },
              { key: 'feats', label: 'Feats', icon: '⭐', count: features.feats?.length || 0, color: 'amber' },
            ].map(({ key, label, icon, count, color }) => (
              <div
                key={key}
                className={`rounded-xl border overflow-hidden transition-all ${
                  expandedFeatureSection === key
                    ? `border-${color}-500/30 bg-${color}-500/5`
                    : 'border-border/50 bg-card/40 hover:bg-card/60 hover:border-violet-500/20'
                }`}
              >
                <button
                  onClick={() => setExpandedFeatureSection(expandedFeatureSection === key ? null : key as FeatureSection)}
                  className="w-full px-4 py-3 flex items-center gap-3"
                >
                  <span className="text-xl">{icon}</span>
                  <span className="flex-1 text-left font-medium text-foreground">{label}</span>
                  <span className={`px-2.5 py-1 text-xs font-bold rounded-lg bg-violet-500/20 text-violet-400`}>
                    {count}
                  </span>
                  {expandedFeatureSection === key ? (
                    <ChevronUp className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  )}
                </button>

                {/* Expanded Content */}
                {expandedFeatureSection === key && (
                  <div className="px-4 pb-4 pt-2 border-t border-border/30 max-h-[300px] overflow-y-auto">
                    {key === 'racial' && (
                      !features.racial_traits?.length ? (
                        <p className="text-sm text-muted-foreground text-center py-6">No racial traits</p>
                      ) : (
                        <div className="space-y-2">
                          {features.racial_traits.map((trait, idx) => (
                            <div key={idx} className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                              <p className="font-medium text-foreground text-sm">{trait.name}</p>
                              {trait.description && (
                                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                  {stripHtml(trait.description)}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      )
                    )}

                    {key === 'class' && (
                      !features.class_features || Object.keys(features.class_features).length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-6">No class features</p>
                      ) : (
                        <div className="space-y-3">
                          {Object.entries(features.class_features).map(([className, levelFeatures]) => (
                            <div key={className}>
                              <p className="font-display text-sm text-violet-400 mb-2">{className}</p>
                              <div className="space-y-1 pl-3 border-l-2 border-violet-500/30">
                                {Object.entries(levelFeatures).map(([level, featuresList]) => (
                                  <div key={level}>
                                    <p className="text-xs text-violet-400/70 font-medium">Level {level}</p>
                                    {featuresList.map((feature, idx) => (
                                      <p key={idx} className="text-sm text-foreground/80 pl-2">{feature.name}</p>
                                    ))}
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      )
                    )}

                    {key === 'feats' && (
                      !features.feats?.length ? (
                        <p className="text-sm text-muted-foreground text-center py-6">No feats</p>
                      ) : (
                        <div className="space-y-2">
                          {features.feats.map((feat, idx) => (
                            <div key={idx} className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
                              <div className="flex items-start justify-between gap-2">
                                <p className="font-medium text-foreground text-sm">{feat.name}</p>
                                {feat.isRepeatable && (
                                  <span className="px-1.5 py-0.5 text-[10px] bg-amber-500/20 text-amber-400 rounded">
                                    Repeatable
                                  </span>
                                )}
                              </div>
                              {feat.description && (
                                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                  {stripHtml(feat.description)}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      )
                    )}
                  </div>
                )}
              </div>
            ))}

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
