/**
 * Inventory Editor
 * 
 * Simple editor for equipped items and backpack inventory
 * Items are either equipped or in backpack - no slot-based system
 */

'use client'

import { useState } from 'react'

interface InventoryItem {
  name: string
  quantity: number
  weight?: number
  description?: string
  definition?: {
    name?: string
    weight?: number
    description?: string
    [key: string]: any
  }
  [key: string]: any
}

interface InventoryData {
  equipped_items?: InventoryItem[]
  backpack?: InventoryItem[]
  currency?: {
    copper?: number
    silver?: number
    electrum?: number
    gold?: number
    platinum?: number
  }
  [key: string]: any
}

interface InventoryEditorProps {
  data: InventoryData | null
  onSave: (data: InventoryData) => void
}

export function InventoryEditor({ data, onSave }: InventoryEditorProps) {
  const [inventory, setInventory] = useState<InventoryData>(() => {
    const initial = data || {
      equipped_items: [],
      backpack: [],
    }
    
    // Ensure equipped_items is an array
    if (!Array.isArray(initial.equipped_items)) {
      initial.equipped_items = []
    }
    
    // Ensure backpack is an array
    if (!Array.isArray(initial.backpack)) {
      initial.backpack = []
    }
    
    return initial
  })
  const [isSaving, setIsSaving] = useState(false)
  
  const updateInventory = (newInventory: InventoryData) => {
    setInventory(newInventory)
  }
  
  const handleSave = async () => {
    setIsSaving(true)
    try {
      await onSave(inventory)
    } finally {
      setIsSaving(false)
    }
  }
  
  // Backpack operations
  const updateBackpackItem = (index: number, field: string, value: any) => {
    const updated = [...(inventory.backpack || [])]
    updated[index] = { ...updated[index], [field]: value }
    updateInventory({ ...inventory, backpack: updated })
  }
  
  // Move item from backpack to equipped
  const moveToEquipped = (backpackIndex: number) => {
    const item = inventory.backpack?.[backpackIndex]
    if (!item) return
    
    const newBackpack = inventory.backpack?.filter((_, i) => i !== backpackIndex) || []
    const newEquipped = [...(inventory.equipped_items || []), item]
    
    updateInventory({
      ...inventory,
      backpack: newBackpack,
      equipped_items: newEquipped
    })
  }
  
  // Move item from equipped to backpack
  const moveToBackpack = (equippedIndex: number) => {
    const item = inventory.equipped_items?.[equippedIndex]
    if (!item) return
    
    const newEquipped = inventory.equipped_items?.filter((_, i) => i !== equippedIndex) || []
    const newBackpack = [...(inventory.backpack || []), item]
    
    updateInventory({
      ...inventory,
      equipped_items: newEquipped,
      backpack: newBackpack
    })
  }
  
  const totalWeight = () => {
    let total = 0
    inventory.backpack?.forEach(item => {
      const weight = item.definition?.weight || item.weight || 0
      total += weight * item.quantity
    })
    inventory.equipped_items?.forEach(item => {
      const weight = item.definition?.weight || item.weight || 0
      total += weight * item.quantity
    })
    return total.toFixed(1)
  }
  
  const getItemName = (item: InventoryItem) => item.definition?.name || item.name || 'Unknown Item'
  const getItemWeight = (item: InventoryItem) => item.definition?.weight || item.weight || 0
  
  return (
    <div className="space-y-6">
      {/* Info Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-sm text-blue-800">
          ℹ️ <strong>Item Management:</strong> Inventory data is imported from D&D Beyond. Move items between equipped and backpack using the buttons.
        </p>
      </div>
      
      {/* Equipped Items */}
      <div>
        <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
          <span>🛡️</span> Equipped Items
          <span className="text-sm font-normal text-gray-500">({inventory.equipped_items?.length || 0})</span>
        </h3>
        
        {!inventory.equipped_items || inventory.equipped_items.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <p className="text-gray-500">No equipped items</p>
            <p className="text-xs text-gray-400 mt-2">Equip items from your backpack below</p>
          </div>
        ) : (
          <div className="space-y-2">
            {inventory.equipped_items.map((item, index) => (
              <div key={index} className="bg-white border border-green-200 rounded-lg p-3">
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{getItemName(item)}</div>
                    <div className="text-xs text-gray-500">
                      {getItemWeight(item)} lbs × {item.quantity}
                    </div>
                  </div>
                  <button
                    onClick={() => moveToBackpack(index)}
                    className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center gap-1"
                    title="Move to backpack"
                  >
                    <span>🎒</span> Unequip
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Backpack */}
      <div>
        <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
          <span>🎒</span> Backpack
          <span className="text-sm font-normal text-gray-500">({inventory.backpack?.length || 0})</span>
        </h3>
        
        {!inventory.backpack || inventory.backpack.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <p className="text-gray-500">No items in backpack</p>
          </div>
        ) : (
          <div className="space-y-2">
            {inventory.backpack.map((item, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-lg p-3">
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{getItemName(item)}</div>
                    <div className="text-xs text-gray-500">
                      {getItemWeight(item)} lbs × {item.quantity}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => updateBackpackItem(index, 'quantity', parseInt(e.target.value) || 1)}
                      className="w-16 px-2 py-1 border border-gray-300 rounded text-center text-sm"
                      title="Quantity"
                    />
                    <button
                      onClick={() => moveToEquipped(index)}
                      className="px-3 py-1.5 text-sm bg-green-500 text-white rounded hover:bg-green-600 flex items-center gap-1"
                      title="Equip item"
                    >
                      <span>🛡️</span> Equip
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Weight Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <span className="font-bold text-blue-800">Total Carried Weight:</span>
          <span className="text-2xl font-bold text-blue-600">{totalWeight()} lbs</span>
        </div>
      </div>
      
      {/* Save Button */}
      <div className="flex justify-end pt-4">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed font-medium transition-all transform hover:scale-105 active:scale-95 disabled:transform-none"
        >
          {isSaving ? 'Saving...' : 'Save Inventory'}
        </button>
      </div>
    </div>
  )
}
