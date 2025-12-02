/**
 * Backstory Editor
 * 
 * Text area editor for character backstory sections
 */

'use client'

import { useState } from 'react'

interface BackstorySection {
  heading: string
  content: string
}

interface FamilyBackstory {
  parents: string
  sections?: BackstorySection[]
}

interface BackstoryData {
  title?: string
  family_backstory?: FamilyBackstory
  sections?: BackstorySection[]
  organizations?: Array<{
    name: string
    role: string
    description: string
  }>
  [key: string]: any
}

interface BackstoryEditorProps {
  data: BackstoryData | null
  onSave: (data: BackstoryData) => void
}

export function BackstoryEditor({ data, onSave }: BackstoryEditorProps) {
  const [backstory, setBackstory] = useState<BackstoryData>(data || {
    title: '',
    family_backstory: { parents: '' },
    sections: [],
    organizations: [],
  })
  const [isSaving, setIsSaving] = useState(false)
  const [expandedSection, setExpandedSection] = useState<number | null>(null)
  
  const handleSave = async () => {
    setIsSaving(true)
    try {
      await onSave(backstory)
    } finally {
      setIsSaving(false)
    }
  }
  
  const updateBackstory = (newBackstory: BackstoryData) => {
    setBackstory(newBackstory)
  }

  const updateTitle = (value: string) => {
    updateBackstory({ ...backstory, title: value })
  }
  
  const updateFamilyParents = (value: string) => {
    updateBackstory({
      ...backstory,
      family_backstory: {
        ...backstory.family_backstory,
        parents: value
      } as FamilyBackstory
    })
  }
  
  const updateSection = (index: number, field: 'heading' | 'content', value: string) => {
    const sections = [...(backstory.sections || [])]
    sections[index] = { ...sections[index], [field]: value }
    updateBackstory({ ...backstory, sections })
  }
  
  const addSection = () => {
    const sections = [...(backstory.sections || [])]
    sections.push({ heading: 'New Section', content: '' })
    updateBackstory({ ...backstory, sections })
  }
  
  const removeSection = (index: number) => {
    const sections = backstory.sections?.filter((_, i) => i !== index) || []
    updateBackstory({ ...backstory, sections })
  }
  
  return (
    <div className="space-y-6">
      {/* Info Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-sm text-blue-800">
          ℹ️ <strong>Backstory Data:</strong> This backstory was parsed from D&D Beyond notes using AI. Sections are organized for easy reading and editing.
        </p>
      </div>
      
      {/* Title */}
      <div>
        <label className="block text-sm font-bold text-gray-900 mb-2">
          Backstory Title
        </label>
        <input
          type="text"
          value={backstory.title || ''}
          onChange={(e) => updateTitle(e.target.value)}
          placeholder="e.g., 'The Shadow's Apprentice'"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
      </div>
      
      {/* Family Backstory */}
      <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-lg p-4 border-2 border-amber-300">
        <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
          <span>👨‍👩‍👧‍👦</span> Family Background
        </h3>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Parents & Family
          </label>
          <textarea
            value={backstory.family_backstory?.parents || ''}
            onChange={(e) => updateFamilyParents(e.target.value)}
            placeholder="Describe your character's family background, parents, siblings, and upbringing..."
            rows={5}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent resize-none"
          />
        </div>
        
        {/* Family Sections */}
        {backstory.family_backstory?.sections && backstory.family_backstory.sections.length > 0 && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Family Story Sections
            </label>
            <div className="space-y-2">
              {backstory.family_backstory.sections.map((section, idx) => (
                <div key={idx} className="bg-white rounded p-3 border border-amber-200">
                  <div className="font-bold text-sm text-gray-900 mb-1">{section.heading}</div>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{section.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Backstory Sections */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <span>📜</span> Story Sections
          </h3>
          <button
            onClick={addSection}
            className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm font-medium"
          >
            + Add Section
          </button>
        </div>
        
        {!backstory.sections || backstory.sections.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <p className="text-gray-500">No story sections yet. Click "Add Section" to create one.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {backstory.sections.map((section, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <button
                    onClick={() => setExpandedSection(expandedSection === index ? null : index)}
                    className="flex-1 flex items-center gap-3 text-left"
                  >
                    <span className="text-xl">📖</span>
                    <h4 className="font-bold text-gray-900">{section.heading}</h4>
                  </button>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => removeSection(index)}
                      className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-xs"
                    >
                      🗑️ Delete
                    </button>
                    <button
                      onClick={() => setExpandedSection(expandedSection === index ? null : index)}
                      className="text-lg"
                    >
                      <span className={`transition-transform inline-block ${expandedSection === index ? 'rotate-180' : ''}`}>
                        ▼
                      </span>
                    </button>
                  </div>
                </div>
                
                {expandedSection === index && (
                  <div className="px-4 py-4 border-t border-gray-200 bg-gray-50 space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Section Heading
                      </label>
                      <input
                        type="text"
                        value={section.heading}
                        onChange={(e) => updateSection(index, 'heading', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Content
                      </label>
                      <textarea
                        value={section.content}
                        onChange={(e) => updateSection(index, 'content', e.target.value)}
                        rows={8}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 resize-none font-mono text-sm"
                      />
                      <p className="text-xs text-gray-600 mt-1">
                        {section.content.length} characters
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Organizations */}
      {backstory.organizations && backstory.organizations.length > 0 && (
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-4 border-2 border-purple-300">
          <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
            <span>🏛️</span> Organizations
          </h3>
          <div className="space-y-3">
            {backstory.organizations.map((org, idx) => (
              <div key={idx} className="bg-white rounded-lg p-4 border border-purple-200">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-bold text-gray-900">{org.name}</h4>
                  <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-medium">
                    {org.role}
                  </span>
                </div>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{org.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Save Button */}
      <div className="flex justify-end pt-4">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed font-medium transition-all transform hover:scale-105 active:scale-95 disabled:transform-none"
        >
          {isSaving ? 'Saving...' : 'Save Backstory'}
        </button>
      </div>
    </div>
  )
}
