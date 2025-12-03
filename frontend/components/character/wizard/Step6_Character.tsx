/**
 * Step 6: Character
 *
 * Edit personality traits and backstory.
 * Uses wizard store directly.
 */

'use client'

import { useState } from 'react'
import { User, ChevronDown, ChevronUp, Plus, Trash2 } from 'lucide-react'
import { useWizardStore } from '@/lib/stores/wizardStore'
import { StepLayout, EditorCard, DualEditorGrid } from './StepLayout'
import type { PersonalityTraits, Backstory, BackstorySection } from '@/lib/types/character'

export function Step6_Character() {
  const { characterData, updateSection, prevStep, nextStep } = useWizardStore()
  const [expandedBackstorySection, setExpandedBackstorySection] = useState<number | null>(null)

  // Normalize personality data - backend may send arrays or strings
  const normalizeField = (field: string[] | string | undefined): string => {
    if (!field) return ''
    if (Array.isArray(field)) return field.join('\n')
    return field
  }

  const personality = characterData?.personality || {
    personality_traits: [],
    ideals: [],
    bonds: [],
    flaws: [],
  }

  const backstory = characterData?.backstory || {
    title: '',
    family_backstory: { parents: '', sections: [] },
    sections: [],
  }

  // Personality helpers
  const updatePersonalityField = (field: keyof PersonalityTraits, value: string) => {
    // Store as array (split by newlines)
    const arrayValue = value.split('\n').filter(line => line.trim())
    updateSection('personality', { ...personality, [field]: arrayValue })
  }

  const getFieldCount = (field: string[] | string | undefined): number => {
    if (!field) return 0
    if (Array.isArray(field)) return field.filter(t => t.trim()).length
    return field.split('\n').filter(t => t.trim()).length
  }

  // Backstory helpers
  const updateBackstoryTitle = (value: string) => {
    updateSection('backstory', { ...backstory, title: value })
  }

  const updateFamilyParents = (value: string) => {
    updateSection('backstory', {
      ...backstory,
      family_backstory: {
        ...backstory.family_backstory,
        parents: value,
      },
    })
  }

  const updateBackstorySection = (index: number, field: 'heading' | 'content', value: string) => {
    const sections = [...(backstory.sections || [])]
    sections[index] = { ...sections[index], [field]: value }
    updateSection('backstory', { ...backstory, sections })
  }

  const addBackstorySection = () => {
    const sections = [...(backstory.sections || [])]
    sections.push({ heading: 'New Section', content: '' })
    updateSection('backstory', { ...backstory, sections })
    setExpandedBackstorySection(sections.length - 1)
  }

  const removeBackstorySection = (index: number) => {
    const sections = backstory.sections?.filter((_, i) => i !== index) || []
    updateSection('backstory', { ...backstory, sections })
    if (expandedBackstorySection === index) setExpandedBackstorySection(null)
  }

  return (
    <StepLayout
      stepNumber={6}
      title="Personality & Story"
      subtitle="Define your character's personality and backstory"
      icon={User}
      onBack={prevStep}
      onContinue={nextStep}
      continueLabel="Save & Continue"
    >
      <DualEditorGrid>
        {/* Personality */}
        <EditorCard title="Personality" icon={User}>
          <div className="space-y-4">
            {/* Personality Traits */}
            <div>
              <label className="block text-sm font-display text-foreground mb-2">
                Personality Traits
                <span className="text-xs text-muted-foreground ml-2">
                  ({getFieldCount(personality.personality_traits)} traits)
                </span>
              </label>
              <textarea
                value={normalizeField(personality.personality_traits)}
                onChange={(e) => updatePersonalityField('personality_traits', e.target.value)}
                placeholder="What defines your character's personality?&#10;One trait per line..."
                rows={3}
                className="w-full px-4 py-2 bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50 resize-none text-sm"
              />
            </div>

            {/* Ideals */}
            <div>
              <label className="block text-sm font-display text-foreground mb-2">
                Ideals
                <span className="text-xs text-muted-foreground ml-2">
                  ({getFieldCount(personality.ideals)} ideals)
                </span>
              </label>
              <textarea
                value={normalizeField(personality.ideals)}
                onChange={(e) => updatePersonalityField('ideals', e.target.value)}
                placeholder="What principles drive your character?&#10;One ideal per line..."
                rows={3}
                className="w-full px-4 py-2 bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50 resize-none text-sm"
              />
            </div>

            {/* Bonds */}
            <div>
              <label className="block text-sm font-display text-foreground mb-2">
                Bonds
                <span className="text-xs text-muted-foreground ml-2">
                  ({getFieldCount(personality.bonds)} bonds)
                </span>
              </label>
              <textarea
                value={normalizeField(personality.bonds)}
                onChange={(e) => updatePersonalityField('bonds', e.target.value)}
                placeholder="What connections anchor your character?&#10;One bond per line..."
                rows={3}
                className="w-full px-4 py-2 bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50 resize-none text-sm"
              />
            </div>

            {/* Flaws */}
            <div>
              <label className="block text-sm font-display text-foreground mb-2">
                Flaws
                <span className="text-xs text-muted-foreground ml-2">
                  ({getFieldCount(personality.flaws)} flaws)
                </span>
              </label>
              <textarea
                value={normalizeField(personality.flaws)}
                onChange={(e) => updatePersonalityField('flaws', e.target.value)}
                placeholder="What weaknesses does your character have?&#10;One flaw per line..."
                rows={3}
                className="w-full px-4 py-2 bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50 resize-none text-sm"
              />
            </div>

            {/* Personality Summary */}
            <div className="rounded-lg bg-pink-500/10 border border-pink-500/20 p-4">
              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <p className="text-lg font-bold text-pink-600">{getFieldCount(personality.personality_traits)}</p>
                  <p className="text-xs text-muted-foreground">Traits</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-pink-600">{getFieldCount(personality.ideals)}</p>
                  <p className="text-xs text-muted-foreground">Ideals</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-pink-600">{getFieldCount(personality.bonds)}</p>
                  <p className="text-xs text-muted-foreground">Bonds</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-pink-600">{getFieldCount(personality.flaws)}</p>
                  <p className="text-xs text-muted-foreground">Flaws</p>
                </div>
              </div>
            </div>
          </div>
        </EditorCard>

        {/* Backstory */}
        <EditorCard title="Backstory" icon={User}>
          <div className="space-y-4">
            {/* Title */}
            <div>
              <label className="block text-sm font-display text-foreground mb-2">
                Backstory Title
              </label>
              <input
                type="text"
                value={backstory.title || ''}
                onChange={(e) => updateBackstoryTitle(e.target.value)}
                placeholder="e.g., 'The Shadow's Apprentice'"
                className="w-full px-4 py-2 bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50"
              />
            </div>

            {/* Family Background */}
            <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-4">
              <h4 className="font-display text-foreground mb-2 flex items-center gap-2">
                <span>👨‍👩‍👧‍👦</span>
                Family Background
              </h4>
              <textarea
                value={backstory.family_backstory?.parents || ''}
                onChange={(e) => updateFamilyParents(e.target.value)}
                placeholder="Describe your character's family and upbringing..."
                rows={4}
                className="w-full px-4 py-2 bg-card border border-border rounded-lg focus:ring-2 focus:ring-primary/50 resize-none text-sm"
              />
            </div>

            {/* Story Sections */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-display text-foreground flex items-center gap-2">
                  <span>📜</span>
                  Story Sections
                </h4>
                <button
                  onClick={addBackstorySection}
                  className="px-3 py-1 text-xs rounded-lg border border-dashed border-primary/30 text-primary hover:bg-primary/5 transition-colors flex items-center gap-1"
                >
                  <Plus className="w-3 h-3" />
                  Add
                </button>
              </div>

              <div className="space-y-2 max-h-[250px] overflow-y-auto">
                {!backstory.sections?.length ? (
                  <div className="text-center py-6 text-muted-foreground text-sm border border-dashed border-border rounded-lg">
                    No story sections yet
                  </div>
                ) : (
                  backstory.sections.map((section, index) => {
                    const isExpanded = expandedBackstorySection === index

                    return (
                      <div key={index} className="rounded-lg border border-border overflow-hidden">
                        <button
                          onClick={() => setExpandedBackstorySection(isExpanded ? null : index)}
                          className="w-full px-4 py-3 flex items-center justify-between hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <span>📖</span>
                            <span className="font-medium text-foreground">{section.heading}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                removeBackstorySection(index)
                              }}
                              className="p-1 text-destructive hover:bg-destructive/10 rounded transition-colors"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                            {isExpanded ? (
                              <ChevronUp className="w-4 h-4 text-muted-foreground" />
                            ) : (
                              <ChevronDown className="w-4 h-4 text-muted-foreground" />
                            )}
                          </div>
                        </button>

                        {isExpanded && (
                          <div className="px-4 py-3 border-t border-border bg-muted/30 space-y-3">
                            <div>
                              <label className="block text-xs text-muted-foreground mb-1">Heading</label>
                              <input
                                type="text"
                                value={section.heading}
                                onChange={(e) => updateBackstorySection(index, 'heading', e.target.value)}
                                className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm"
                              />
                            </div>
                            <div>
                              <label className="block text-xs text-muted-foreground mb-1">Content</label>
                              <textarea
                                value={section.content}
                                onChange={(e) => updateBackstorySection(index, 'content', e.target.value)}
                                rows={5}
                                className="w-full px-3 py-2 bg-card border border-border rounded-lg resize-none text-sm"
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })
                )}
              </div>
            </div>

            {/* Backstory Summary */}
            <div className="rounded-lg bg-primary/5 border border-primary/20 p-4">
              <div className="flex items-center justify-between">
                <span className="font-display text-foreground">Story Sections</span>
                <span className="text-xl font-bold text-primary">{backstory.sections?.length || 0}</span>
              </div>
            </div>
          </div>
        </EditorCard>
      </DualEditorGrid>
    </StepLayout>
  )
}
