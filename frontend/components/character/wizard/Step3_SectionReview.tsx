/**
 * Step 3: Section Review & Edit
 *
 * Accordion UI for reviewing and editing character sections
 */

'use client'

import { useState } from 'react'
import type { CharacterData } from '@/lib/types/character'
import {
  AbilityScoresEditor,
  BackstoryEditor,
  PersonalityEditor,
  InventoryEditor,
  SpellListEditor,
  ActionsEditor,
  CombatStatsEditor,
  FeaturesAndTraitsEditor,
} from '../editors'
import { ChevronDown, Check, ArrowRight, Swords, Backpack, Sparkles, Target, Award, ScrollText, Heart, FileEdit } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Step3_SectionReviewProps {
  characterData: CharacterData | null
  onSectionSave: (sectionName: string, sectionData: any) => Promise<void>
  onNext: () => void
}

type SectionName = 'ability_scores' | 'combat_stats' | 'inventory' | 'spell_list' | 'action_economy' | 'features_and_traits' | 'backstory' | 'personality'

interface SectionConfig {
  name: SectionName
  label: string
  icon: React.ReactNode
  description: string
  hasEditor: boolean
}

const SECTIONS: SectionConfig[] = [
  {
    name: 'ability_scores',
    label: 'Ability Scores',
    icon: <Swords className="w-5 h-5" />,
    description: 'Strength, Dexterity, Constitution, Intelligence, Wisdom, Charisma',
    hasEditor: true,
  },
  {
    name: 'combat_stats',
    label: 'Combat Stats',
    icon: <Heart className="w-5 h-5" />,
    description: 'Hit Points, Armor Class, Initiative, Speed',
    hasEditor: true,
  },
  {
    name: 'inventory',
    label: 'Inventory & Equipment',
    icon: <Backpack className="w-5 h-5" />,
    description: 'Weapons, armor, items, and currency',
    hasEditor: true,
  },
  {
    name: 'spell_list',
    label: 'Spells',
    icon: <Sparkles className="w-5 h-5" />,
    description: 'Known spells, spell slots, and spellcasting abilities',
    hasEditor: true,
  },
  {
    name: 'action_economy',
    label: 'Actions & Attacks',
    icon: <Target className="w-5 h-5" />,
    description: 'Available actions, attacks, and bonus actions',
    hasEditor: true,
  },
  {
    name: 'features_and_traits',
    label: 'Features & Traits',
    icon: <Award className="w-5 h-5" />,
    description: 'Class features, racial traits, and special abilities',
    hasEditor: true,
  },
  {
    name: 'backstory',
    label: 'Backstory',
    icon: <ScrollText className="w-5 h-5" />,
    description: 'Character history, family, and defining moments',
    hasEditor: true,
  },
  {
    name: 'personality',
    label: 'Personality',
    icon: <Heart className="w-5 h-5" />,
    description: 'Traits, ideals, bonds, and flaws',
    hasEditor: true,
  },
]

export function Step3_SectionReview({
  characterData,
  onSectionSave,
  onNext,
}: Step3_SectionReviewProps) {
  const [expandedSection, setExpandedSection] = useState<SectionName | null>(null)
  const [savingSection, setSavingSection] = useState<SectionName | null>(null)

  const toggleSection = (sectionName: SectionName) => {
    setExpandedSection(expandedSection === sectionName ? null : sectionName)
  }

  const handleSectionSave = async (sectionName: SectionName) => {
    if (!characterData || !characterData[sectionName]) return

    setSavingSection(sectionName)
    try {
      await onSectionSave(sectionName, characterData[sectionName])
    } finally {
      setSavingSection(null)
    }
  }

  if (!characterData) {
    return (
      <div className="p-12 text-center">
        <p className="text-muted-foreground">No character data available</p>
      </div>
    )
  }

  return (
    <div className="p-6 md:p-10">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-5">
            <FileEdit className="w-8 h-8 text-primary" />
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-2">
            Review & Edit Sections
          </h2>
          <p className="text-muted-foreground">
            Review each section and make any necessary changes before saving
          </p>
        </div>

        {/* Section Accordion */}
        <div className="space-y-3 mb-10">
          {SECTIONS.map((section) => {
            const isExpanded = expandedSection === section.name
            const isSaving = savingSection === section.name
            const hasData = !!characterData[section.name]

            return (
              <div
                key={section.name}
                className={cn(
                  'rounded-xl border overflow-hidden transition-all',
                  isExpanded ? 'border-primary/30 bg-card shadow-lg' : 'border-border/50 bg-card/50 hover:bg-card'
                )}
              >
                {/* Section Header */}
                <button
                  onClick={() => toggleSection(section.name)}
                  className="w-full px-5 py-4 flex items-center gap-4 transition-colors"
                >
                  <div className={cn(
                    'w-10 h-10 rounded-xl flex items-center justify-center transition-colors',
                    isExpanded ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'
                  )}>
                    {section.icon}
                  </div>
                  <div className="flex-1 text-left">
                    <h3 className="font-semibold text-foreground">{section.label}</h3>
                    <p className="text-sm text-muted-foreground">{section.description}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    {hasData && (
                      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600 text-xs font-medium">
                        <Check className="w-3 h-3" />
                        Loaded
                      </span>
                    )}
                    <ChevronDown className={cn(
                      'w-5 h-5 text-muted-foreground transition-transform',
                      isExpanded && 'rotate-180'
                    )} />
                  </div>
                </button>

                {/* Section Content (expanded) */}
                {isExpanded && (
                  <div className="px-5 pb-5 border-t border-border/50">
                    <div className="pt-5">
                      {hasData ? (
                        <div>
                          {/* Render appropriate editor based on section */}
                          {section.hasEditor ? (
                            <>
                              {section.name === 'ability_scores' && (
                                <AbilityScoresEditor
                                  data={characterData[section.name]}
                                  onSave={async (data) => handleSectionSave(section.name)}
                                />
                              )}
                              {section.name === 'combat_stats' && (
                                <CombatStatsEditor
                                  data={characterData[section.name]}
                                  onSave={async (data) => handleSectionSave(section.name)}
                                />
                              )}
                              {section.name === 'inventory' && (
                                <InventoryEditor
                                  data={characterData[section.name]}
                                  onSave={async (data) => handleSectionSave(section.name)}
                                />
                              )}
                              {section.name === 'spell_list' && (
                                <SpellListEditor
                                  data={characterData[section.name]}
                                  onSave={async (data) => handleSectionSave(section.name)}
                                />
                              )}
                              {section.name === 'action_economy' && (
                                <ActionsEditor
                                  data={characterData[section.name]}
                                  onSave={async (data) => handleSectionSave(section.name)}
                                />
                              )}
                              {section.name === 'features_and_traits' && (
                                <FeaturesAndTraitsEditor
                                  data={characterData[section.name]}
                                  onSave={async (data) => handleSectionSave(section.name)}
                                />
                              )}
                              {section.name === 'backstory' && (
                                <BackstoryEditor
                                  data={characterData[section.name]}
                                  onSave={async (data) => handleSectionSave(section.name)}
                                />
                              )}
                              {section.name === 'personality' && (
                                <PersonalityEditor
                                  data={characterData[section.name]}
                                  onSave={async (data) => handleSectionSave(section.name)}
                                />
                              )}
                            </>
                          ) : (
                            <>
                              {/* JSON Preview for sections without editors yet */}
                              <div className="rounded-xl bg-muted/30 border border-border/50 p-4 mb-4">
                                <p className="text-xs text-muted-foreground mb-2">Section Data Preview:</p>
                                <pre className="text-xs text-foreground/80 overflow-x-auto max-h-60 overflow-y-auto font-mono">
                                  {JSON.stringify(characterData[section.name], null, 2)}
                                </pre>
                              </div>

                              <div className="flex items-center justify-between">
                                <p className="text-sm text-muted-foreground">
                                  Full editing UI coming soon. Save as-is or edit later.
                                </p>
                                <button
                                  onClick={() => handleSectionSave(section.name)}
                                  disabled={isSaving}
                                  className="btn-secondary text-sm"
                                >
                                  {isSaving ? 'Saving...' : 'Save Section'}
                                </button>
                              </div>
                            </>
                          )}
                        </div>
                      ) : (
                        <div className="text-center py-10 text-muted-foreground">
                          <p>No data available for this section</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Navigation */}
        <button
          onClick={onNext}
          className="btn-primary w-full py-4 text-lg flex items-center justify-center gap-2"
        >
          Continue to Preview & Save
          <ArrowRight className="w-5 h-5" />
        </button>

        {/* Info Box */}
        <div className="mt-6 p-4 rounded-xl bg-muted/30 border border-border/50">
          <p className="text-sm text-muted-foreground">
            <strong className="text-foreground">Tip:</strong> You can save individual sections now or skip to the final step to save everything at once.
          </p>
        </div>
      </div>
    </div>
  )
}
