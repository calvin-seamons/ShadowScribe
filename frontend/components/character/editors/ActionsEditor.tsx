/**
 * Actions Editor
 * 
 * Editor for character actions, attacks, and abilities with full CRUD
 */

'use client'

import { useState } from 'react'

interface CharacterAction {
  name: string
  action_type?: 'action' | 'bonus_action' | 'reaction' | 'free_action'
  attack_type?: 'melee' | 'ranged' | 'spell'
  attack_bonus?: number
  damage?: string
  range?: string
  description?: string
  limited_uses?: {
    max_uses: number
    current_uses: number
    recharge: string
  }
  [key: string]: any
}

interface ActionsData {
  actions?: CharacterAction[]
  attacks_per_action?: number
  [key: string]: any
}

interface ActionsEditorProps {
  data: ActionsData | null
  onSave: (data: ActionsData) => void
}

export function ActionsEditor({ data, onSave }: ActionsEditorProps) {
  const [actions, setActions] = useState<ActionsData>(data || {
    actions: [],
    attacks_per_action: 1,
  })
  const [isSaving, setIsSaving] = useState(false)
  const [expandedAction, setExpandedAction] = useState<number | null>(null)
  
  const handleSave = async () => {
    setIsSaving(true)
    try {
      await onSave(actions)
    } finally {
      setIsSaving(false)
    }
  }
  
  const updateActionsData = (newActions: ActionsData) => {
    setActions(newActions)
  }

  const addAction = () => {
    const newAction: CharacterAction = {
      name: 'New Action',
      action_type: 'action',
      attack_type: 'melee',
      attack_bonus: 0,
      damage: '1d8',
      range: '5 feet',
      description: '',
    }
    updateActionsData({
      ...actions,
      actions: [...(actions.actions || []), newAction]
    })
    setExpandedAction((actions.actions?.length || 0))
  }
  
  const removeAction = (index: number) => {
    updateActionsData({
      ...actions,
      actions: actions.actions?.filter((_, i) => i !== index) || []
    })
    if (expandedAction === index) {
      setExpandedAction(null)
    }
  }
  
  const updateAction = (index: number, field: string, value: any) => {
    const updated = [...(actions.actions || [])]
    updated[index] = { ...updated[index], [field]: value }
    updateActionsData({ ...actions, actions: updated })
  }
  
  const updateLimitedUses = (index: number, field: string, value: any) => {
    const updated = [...(actions.actions || [])]
    updated[index] = {
      ...updated[index],
      limited_uses: {
        ...(updated[index].limited_uses || { max_uses: 0, current_uses: 0, recharge: 'short rest' }),
        [field]: value
      }
    }
    updateActionsData({ ...actions, actions: updated })
  }
  
  const getActionTypeIcon = (type?: string) => {
    switch (type) {
      case 'action': return '⚔️'
      case 'bonus_action': return '⚡'
      case 'reaction': return '🛡️'
      case 'free_action': return '💨'
      default: return '⚔️'
    }
  }
  
  return (
    <div className="space-y-6">
      {/* Attacks Per Action */}
      <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-lg p-4 border-2 border-red-300">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-gray-900">Attacks per Action</h3>
            <p className="text-xs text-gray-600">Number of attacks when taking the Attack action</p>
          </div>
          <input
            type="number"
            min="1"
            max="4"
            value={actions.attacks_per_action || 1}
            onChange={(e) => setActions({ ...actions, attacks_per_action: parseInt(e.target.value) || 1 })}
            className="w-20 px-3 py-2 text-center text-2xl font-bold border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
          />
        </div>
      </div>
      
      {/* Actions List */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-bold text-gray-900">Actions & Attacks</h3>
          <button
            onClick={addAction}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
          >
            + Add Action
          </button>
        </div>
        
        {!actions.actions || actions.actions.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <p className="text-gray-500">No actions configured</p>
            <p className="text-xs text-gray-400 mt-2">Add actions like attacks, spells, or special abilities</p>
          </div>
        ) : (
          <div className="space-y-3">
            {actions.actions.map((action, index) => {
              const isExpanded = expandedAction === index
              
              return (
                <div key={index} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  {/* Action Header */}
                  <button
                    onClick={() => setExpandedAction(isExpanded ? null : index)}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{getActionTypeIcon(action.action_type)}</span>
                      <div className="text-left">
                        <h4 className="font-bold text-gray-900">{action.name}</h4>
                        <p className="text-xs text-gray-600 capitalize">
                          {action.action_type?.replace('_', ' ')} • {action.attack_type || 'melee'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {action.attack_bonus !== undefined && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm font-bold">
                          +{action.attack_bonus}
                        </span>
                      )}
                      <span className={`text-xl transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                        ▼
                      </span>
                    </div>
                  </button>
                  
                  {/* Expanded Action Details */}
                  {isExpanded && (
                    <div className="px-4 py-4 border-t border-gray-200 bg-gray-50 space-y-4">
                      {/* Basic Info */}
                      <div className="grid md:grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Action Name
                          </label>
                          <input
                            type="text"
                            value={action.name}
                            onChange={(e) => updateAction(index, 'name', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Action Type
                          </label>
                          <select
                            value={action.action_type || 'action'}
                            onChange={(e) => updateAction(index, 'action_type', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                          >
                            <option value="action">Action</option>
                            <option value="bonus_action">Bonus Action</option>
                            <option value="reaction">Reaction</option>
                            <option value="free_action">Free Action</option>
                          </select>
                        </div>
                      </div>
                      
                      {/* Attack Details */}
                      <div className="grid md:grid-cols-3 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Attack Type
                          </label>
                          <select
                            value={action.attack_type || 'melee'}
                            onChange={(e) => updateAction(index, 'attack_type', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                          >
                            <option value="melee">Melee</option>
                            <option value="ranged">Ranged</option>
                            <option value="spell">Spell</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Attack Bonus
                          </label>
                          <input
                            type="number"
                            value={action.attack_bonus || 0}
                            onChange={(e) => updateAction(index, 'attack_bonus', parseInt(e.target.value) || 0)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Range
                          </label>
                          <input
                            type="text"
                            value={action.range || ''}
                            onChange={(e) => updateAction(index, 'range', e.target.value)}
                            placeholder="5 feet"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                      </div>
                      
                      {/* Damage */}
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Damage (e.g., "1d8+3 slashing")
                        </label>
                        <input
                          type="text"
                          value={action.damage || ''}
                          onChange={(e) => updateAction(index, 'damage', e.target.value)}
                          placeholder="1d8+3 slashing"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                      
                      {/* Description */}
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Description
                        </label>
                        <textarea
                          value={action.description || ''}
                          onChange={(e) => updateAction(index, 'description', e.target.value)}
                          rows={3}
                          placeholder="Describe the action, special effects, or conditions..."
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 resize-none"
                        />
                      </div>
                      
                      {/* Limited Uses */}
                      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                        <label className="block text-sm font-bold text-gray-900 mb-2">
                          Limited Uses (Optional)
                        </label>
                        <div className="grid grid-cols-3 gap-3">
                          <div>
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              Max Uses
                            </label>
                            <input
                              type="number"
                              min="0"
                              value={action.limited_uses?.max_uses || 0}
                              onChange={(e) => updateLimitedUses(index, 'max_uses', parseInt(e.target.value) || 0)}
                              className="w-full px-2 py-1 border border-gray-300 rounded"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              Current Uses
                            </label>
                            <input
                              type="number"
                              min="0"
                              value={action.limited_uses?.current_uses || 0}
                              onChange={(e) => updateLimitedUses(index, 'current_uses', parseInt(e.target.value) || 0)}
                              className="w-full px-2 py-1 border border-gray-300 rounded"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              Recharge
                            </label>
                            <select
                              value={action.limited_uses?.recharge || 'short rest'}
                              onChange={(e) => updateLimitedUses(index, 'recharge', e.target.value)}
                              className="w-full px-2 py-1 border border-gray-300 rounded"
                            >
                              <option value="short rest">Short Rest</option>
                              <option value="long rest">Long Rest</option>
                              <option value="dawn">Dawn</option>
                            </select>
                          </div>
                        </div>
                      </div>
                      
                      {/* Remove Button */}
                      <div className="flex justify-end pt-2">
                        <button
                          onClick={() => removeAction(index)}
                          className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 font-medium"
                        >
                          Remove Action
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
      
      {/* Save Button */}
      <div className="flex justify-end pt-4">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed font-medium transition-all transform hover:scale-105 active:scale-95 disabled:transform-none"
        >
          {isSaving ? 'Saving...' : 'Save Actions'}
        </button>
      </div>
    </div>
  )
}
