/**
 * Step 4: Equipment
 *
 * Edit inventory (equipped items + backpack) and spell list.
 * Forms include all user-editable fields from Python backend types.
 */

'use client'

import { useState } from 'react'
import { Backpack, Sparkles, ChevronDown, ChevronUp, Plus, Trash2, X } from 'lucide-react'
import { useWizardStore } from '@/lib/stores/wizardStore'
import { StepLayout, EditorCard, DualEditorGrid, SectionDivider } from './StepLayout'
import type { InventoryItem, Spell } from '@/lib/types/character'

const SPELL_LEVELS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

const ITEM_TYPES = [
  'Adventuring Gear',
  'Armor',
  'Weapon',
  'Tool',
  'Potion',
  'Scroll',
  'Wondrous Item',
  'Ring',
  'Wand',
  'Rod',
  'Staff',
  'Ammunition',
  'Container',
  'Other',
]

const ITEM_RARITIES = [
  'Common',
  'Uncommon',
  'Rare',
  'Very Rare',
  'Legendary',
  'Artifact',
]

const SPELL_SCHOOLS = [
  'Abjuration',
  'Conjuration',
  'Divination',
  'Enchantment',
  'Evocation',
  'Illusion',
  'Necromancy',
  'Transmutation',
]

const CASTING_TIMES = [
  '1 action',
  '1 bonus action',
  '1 reaction',
  '1 minute',
  '10 minutes',
  '1 hour',
  '8 hours',
  '24 hours',
  'Special',
]

const DURATIONS = [
  'Instantaneous',
  '1 round',
  '1 minute',
  '10 minutes',
  '1 hour',
  '8 hours',
  '24 hours',
  'Until dispelled',
  'Special',
]

const RANGES = [
  'Self',
  'Touch',
  '5 feet',
  '10 feet',
  '30 feet',
  '60 feet',
  '90 feet',
  '120 feet',
  '150 feet',
  '300 feet',
  '500 feet',
  '1 mile',
  'Sight',
  'Unlimited',
  'Special',
]

export function Step4_Equipment() {
  const { characterData, updateSection, prevStep, nextStep } = useWizardStore()
  const [expandedSpellLevel, setExpandedSpellLevel] = useState<number | null>(null)
  const [showAddItem, setShowAddItem] = useState(false)
  const [showAddSpell, setShowAddSpell] = useState(false)

  // Item form state
  const [newItem, setNewItem] = useState({
    name: '',
    type: 'Adventuring Gear',
    description: '',
    weight: 0,
    quantity: 1,
    rarity: 'Common',
    magic: false,
    canAttune: false,
    attunementDescription: '',
  })

  // Spell form state
  const [newSpell, setNewSpell] = useState({
    name: '',
    level: 0,
    school: 'Evocation',
    casting_time: '1 action',
    range: '60 feet',
    duration: 'Instantaneous',
    description: '',
    concentration: false,
    ritual: false,
    verbal: true,
    somatic: true,
    material: '',
    area: '',
  })

  const inventory = characterData?.inventory || {
    total_weight: 0,
    weight_unit: 'lbs',
    equipped_items: [],
    backpack: [],
    valuables: [],
  }

  const spellList = characterData?.spell_list || {
    spellcasting: {},
    spells: {},
  }

  // Inventory helpers
  const getItemName = (item: InventoryItem) => item.definition?.name || 'Unknown Item'
  const getItemWeight = (item: InventoryItem) => item.definition?.weight || 0

  const resetItemForm = () => {
    setNewItem({
      name: '',
      type: 'Adventuring Gear',
      description: '',
      weight: 0,
      quantity: 1,
      rarity: 'Common',
      magic: false,
      canAttune: false,
      attunementDescription: '',
    })
  }

  const addNewItem = () => {
    if (!newItem.name.trim()) return

    const item: InventoryItem = {
      definition: {
        name: newItem.name.trim(),
        type: newItem.type,
        description: newItem.description.trim() || undefined,
        weight: newItem.weight,
        rarity: newItem.rarity,
        magic: newItem.magic,
        canAttune: newItem.canAttune,
        attunementDescription: newItem.canAttune && newItem.attunementDescription ? newItem.attunementDescription : undefined,
      },
      quantity: newItem.quantity,
      isAttuned: false,
      equipped: false,
    }

    updateSection('inventory', {
      ...inventory,
      backpack: [...(inventory.backpack || []), item],
    })

    resetItemForm()
    setShowAddItem(false)
  }

  const moveToEquipped = (backpackIndex: number) => {
    const item = inventory.backpack[backpackIndex]
    if (!item) return

    const newBackpack = inventory.backpack.filter((_, i) => i !== backpackIndex)
    const newEquipped = [...inventory.equipped_items, { ...item, equipped: true }]

    updateSection('inventory', {
      ...inventory,
      backpack: newBackpack,
      equipped_items: newEquipped,
    })
  }

  const moveToBackpack = (equippedIndex: number) => {
    const item = inventory.equipped_items[equippedIndex]
    if (!item) return

    const newEquipped = inventory.equipped_items.filter((_, i) => i !== equippedIndex)
    const newBackpack = [...inventory.backpack, { ...item, equipped: false }]

    updateSection('inventory', {
      ...inventory,
      equipped_items: newEquipped,
      backpack: newBackpack,
    })
  }

  const updateItemQuantity = (type: 'equipped_items' | 'backpack', index: number, quantity: number) => {
    const items = [...inventory[type]]
    items[index] = { ...items[index], quantity: Math.max(1, quantity) }
    updateSection('inventory', { ...inventory, [type]: items })
  }

  const removeItem = (type: 'equipped_items' | 'backpack', index: number) => {
    const items = inventory[type].filter((_, i) => i !== index)
    updateSection('inventory', { ...inventory, [type]: items })
  }

  const totalWeight = () => {
    let total = 0
    inventory.backpack?.forEach(item => {
      total += getItemWeight(item) * item.quantity
    })
    inventory.equipped_items?.forEach(item => {
      total += getItemWeight(item) * item.quantity
    })
    return total.toFixed(1)
  }

  // Spell helpers
  const getAllSpells = (): Spell[] => {
    if (!spellList.spells) return []

    const allSpells: Spell[] = []
    Object.values(spellList.spells).forEach((classSpells: any) => {
      if (typeof classSpells === 'object') {
        Object.entries(classSpells).forEach(([levelKey, spells]: [string, any]) => {
          if (Array.isArray(spells)) {
            allSpells.push(...spells)
          }
        })
      }
    })
    return allSpells
  }

  const getSpellsByLevel = (level: number): Spell[] => {
    return getAllSpells().filter(s => s.level === level)
  }

  const resetSpellForm = () => {
    setNewSpell({
      name: '',
      level: 0,
      school: 'Evocation',
      casting_time: '1 action',
      range: '60 feet',
      duration: 'Instantaneous',
      description: '',
      concentration: false,
      ritual: false,
      verbal: true,
      somatic: true,
      material: '',
      area: '',
    })
  }

  const addNewSpell = () => {
    if (!newSpell.name.trim()) return

    const spell: Spell = {
      name: newSpell.name.trim(),
      level: newSpell.level,
      school: newSpell.school,
      casting_time: newSpell.casting_time,
      range: newSpell.range,
      components: {
        verbal: newSpell.verbal,
        somatic: newSpell.somatic,
        material: newSpell.material.trim() || false,
      },
      duration: newSpell.duration,
      description: newSpell.description.trim(),
      concentration: newSpell.concentration,
      ritual: newSpell.ritual,
      tags: [],
      area: newSpell.area.trim() || undefined,
    }

    const currentSpells = spellList.spells || {}
    const customSpells = (currentSpells as any)['Custom'] || {}
    const levelKey = newSpell.level.toString()
    const levelSpells = customSpells[levelKey] || []

    updateSection('spell_list', {
      ...spellList,
      spells: {
        ...currentSpells,
        Custom: {
          ...customSpells,
          [levelKey]: [...levelSpells, spell],
        },
      },
    })

    resetSpellForm()
    setShowAddSpell(false)
    setExpandedSpellLevel(newSpell.level)
  }

  const removeSpell = (spellToRemove: Spell) => {
    const currentSpells = { ...(spellList.spells || {}) }

    Object.keys(currentSpells).forEach((className) => {
      const classSpells = { ...(currentSpells as any)[className] }
      Object.keys(classSpells).forEach((levelKey) => {
        if (Array.isArray(classSpells[levelKey])) {
          classSpells[levelKey] = classSpells[levelKey].filter(
            (s: Spell) => !(s.name === spellToRemove.name && s.level === spellToRemove.level)
          )
        }
      })
      ;(currentSpells as any)[className] = classSpells
    })

    updateSection('spell_list', {
      ...spellList,
      spells: currentSpells,
    })
  }

  const getLevelName = (level: number) => {
    if (level === 0) return 'Cantrips'
    if (level === 1) return '1st Level'
    if (level === 2) return '2nd Level'
    if (level === 3) return '3rd Level'
    return `${level}th Level`
  }

  const totalSpells = getAllSpells().length
  const spellcastingInfo = Object.values(spellList.spellcasting || {})[0]

  return (
    <StepLayout
      stepNumber={4}
      title="Equipment & Spells"
      subtitle="Manage your inventory and spellbook"
      icon={Backpack}
      onBack={prevStep}
      onContinue={nextStep}
      continueLabel="Save & Continue"
    >
      <DualEditorGrid>
        {/* Inventory */}
        <EditorCard title="Inventory" icon={Backpack} variant="default">
          <div className="space-y-4">
            {/* Add Item Button */}
            <button
              onClick={() => setShowAddItem(!showAddItem)}
              className="w-full py-3 px-4 rounded-xl border-2 border-dashed border-primary/30 text-primary hover:bg-primary/5 hover:border-primary/50 transition-all flex items-center justify-center gap-2 group"
            >
              <Plus className="w-4 h-4 transition-transform group-hover:scale-110" />
              <span className="font-medium">Add Item</span>
            </button>

            {/* Add Item Form */}
            {showAddItem && (
              <div className="p-4 rounded-xl bg-primary/5 border border-primary/20 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-display text-sm text-primary">New Item</h4>
                  <button onClick={() => { setShowAddItem(false); resetItemForm() }} className="p-1 hover:bg-muted rounded">
                    <X className="w-4 h-4 text-muted-foreground" />
                  </button>
                </div>

                {/* Name */}
                <div>
                  <label className="block text-xs text-muted-foreground mb-1.5">Item Name *</label>
                  <input
                    type="text"
                    value={newItem.name}
                    onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
                    placeholder="e.g., Rope (50 ft), Healing Potion"
                    className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-primary/50"
                  />
                </div>

                {/* Type & Rarity */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1.5">Type</label>
                    <select
                      value={newItem.type}
                      onChange={(e) => setNewItem({ ...newItem, type: e.target.value })}
                      className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-primary/50"
                    >
                      {ITEM_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1.5">Rarity</label>
                    <select
                      value={newItem.rarity}
                      onChange={(e) => setNewItem({ ...newItem, rarity: e.target.value })}
                      className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-primary/50"
                    >
                      {ITEM_RARITIES.map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </div>
                </div>

                {/* Weight & Quantity */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1.5">Weight (lbs)</label>
                    <input
                      type="number"
                      min="0"
                      step="0.1"
                      value={newItem.weight}
                      onChange={(e) => setNewItem({ ...newItem, weight: parseFloat(e.target.value) || 0 })}
                      className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-primary/50"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1.5">Quantity</label>
                    <input
                      type="number"
                      min="1"
                      value={newItem.quantity}
                      onChange={(e) => setNewItem({ ...newItem, quantity: parseInt(e.target.value) || 1 })}
                      className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-primary/50"
                    />
                  </div>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-xs text-muted-foreground mb-1.5">Description</label>
                  <textarea
                    value={newItem.description}
                    onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
                    placeholder="Item description, properties, or notes..."
                    rows={2}
                    className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm resize-none focus:outline-none focus:border-primary/50"
                  />
                </div>

                {/* Magic Item Options */}
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newItem.magic}
                      onChange={(e) => setNewItem({ ...newItem, magic: e.target.checked })}
                      className="w-4 h-4 rounded border-border text-primary focus:ring-primary/50"
                    />
                    <span className="text-sm text-foreground">Magic Item</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newItem.canAttune}
                      onChange={(e) => setNewItem({ ...newItem, canAttune: e.target.checked })}
                      className="w-4 h-4 rounded border-border text-primary focus:ring-primary/50"
                    />
                    <span className="text-sm text-foreground">Requires Attunement</span>
                  </label>
                </div>

                {/* Attunement Description */}
                {newItem.canAttune && (
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1.5">Attunement Requirements</label>
                    <input
                      type="text"
                      value={newItem.attunementDescription}
                      onChange={(e) => setNewItem({ ...newItem, attunementDescription: e.target.value })}
                      placeholder="e.g., by a spellcaster, by a cleric or paladin"
                      className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-primary/50"
                    />
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <button
                    onClick={addNewItem}
                    disabled={!newItem.name.trim()}
                    className="flex-1 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary/90 transition-colors"
                  >
                    Add to Backpack
                  </button>
                  <button
                    onClick={() => { setShowAddItem(false); resetItemForm() }}
                    className="px-4 py-2.5 bg-muted text-foreground rounded-lg text-sm hover:bg-muted/80 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            <SectionDivider label="Equipped" />

            {/* Equipped Items */}
            {!inventory.equipped_items?.length ? (
              <div className="text-center py-6 text-muted-foreground text-sm border border-dashed border-border rounded-xl">
                No equipped items
              </div>
            ) : (
              <div className="space-y-2">
                {inventory.equipped_items.map((item, index) => (
                  <div key={index} className="flex items-center gap-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground truncate">{getItemName(item)}</p>
                      <p className="text-xs text-muted-foreground">
                        {getItemWeight(item)} lbs × {item.quantity}
                        {item.definition?.magic && ' · Magic'}
                      </p>
                    </div>
                    <button
                      onClick={() => moveToBackpack(index)}
                      className="px-2 py-1 text-xs bg-muted hover:bg-muted/80 rounded-lg transition-colors"
                    >
                      Unequip
                    </button>
                    <button
                      onClick={() => removeItem('equipped_items', index)}
                      className="p-1.5 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <SectionDivider label="Backpack" />

            {/* Backpack */}
            {!inventory.backpack?.length ? (
              <div className="text-center py-6 text-muted-foreground text-sm border border-dashed border-border rounded-xl">
                No items in backpack
              </div>
            ) : (
              <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1">
                {inventory.backpack.map((item, index) => (
                  <div key={index} className="flex items-center gap-2 p-3 rounded-xl bg-card/50 border border-border/50">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground truncate">{getItemName(item)}</p>
                      <p className="text-xs text-muted-foreground">
                        {getItemWeight(item)} lbs
                        {item.definition?.rarity && item.definition.rarity !== 'Common' && ` · ${item.definition.rarity}`}
                      </p>
                    </div>
                    <input
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => updateItemQuantity('backpack', index, parseInt(e.target.value) || 1)}
                      className="w-14 px-2 py-1 text-center text-sm bg-muted border border-border rounded-lg"
                    />
                    <button
                      onClick={() => moveToEquipped(index)}
                      className="px-2 py-1 text-xs bg-emerald-500/20 text-emerald-600 hover:bg-emerald-500/30 rounded-lg transition-colors"
                    >
                      Equip
                    </button>
                    <button
                      onClick={() => removeItem('backpack', index)}
                      className="p-1.5 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Weight Summary */}
            <div className="rounded-xl bg-gradient-to-br from-primary/10 to-amber-500/5 border border-primary/20 p-4">
              <div className="flex items-center justify-between">
                <span className="font-display text-sm text-foreground">Total Weight</span>
                <span className="text-2xl font-bold font-display text-primary">{totalWeight()} lbs</span>
              </div>
            </div>
          </div>
        </EditorCard>

        {/* Spells */}
        <EditorCard title="Spellbook" icon={Sparkles} variant="magic">
          <div className="space-y-4">
            {/* Add Spell Button */}
            <button
              onClick={() => setShowAddSpell(!showAddSpell)}
              className="w-full py-3 px-4 rounded-xl border-2 border-dashed border-violet-500/30 text-violet-400 hover:bg-violet-500/5 hover:border-violet-500/50 transition-all flex items-center justify-center gap-2 group"
            >
              <Plus className="w-4 h-4 transition-transform group-hover:scale-110" />
              <span className="font-medium">Add Spell</span>
            </button>

            {/* Add Spell Form */}
            {showAddSpell && (
              <div className="p-4 rounded-xl bg-violet-500/5 border border-violet-500/20 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-display text-sm text-violet-400">New Spell</h4>
                  <button onClick={() => { setShowAddSpell(false); resetSpellForm() }} className="p-1 hover:bg-muted rounded">
                    <X className="w-4 h-4 text-muted-foreground" />
                  </button>
                </div>

                {/* Name */}
                <div>
                  <label className="block text-xs text-muted-foreground mb-1.5">Spell Name *</label>
                  <input
                    type="text"
                    value={newSpell.name}
                    onChange={(e) => setNewSpell({ ...newSpell, name: e.target.value })}
                    placeholder="e.g., Fireball, Mage Hand"
                    className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-violet-500/50"
                  />
                </div>

                {/* Level & School */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1.5">Level</label>
                    <select
                      value={newSpell.level}
                      onChange={(e) => setNewSpell({ ...newSpell, level: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-violet-500/50"
                    >
                      <option value={0}>Cantrip</option>
                      {[1,2,3,4,5,6,7,8,9].map(l => (
                        <option key={l} value={l}>{getLevelName(l)}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1.5">School</label>
                    <select
                      value={newSpell.school}
                      onChange={(e) => setNewSpell({ ...newSpell, school: e.target.value })}
                      className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-violet-500/50"
                    >
                      {SPELL_SCHOOLS.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                </div>

                {/* Casting Time & Range */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1.5">Casting Time</label>
                    <select
                      value={newSpell.casting_time}
                      onChange={(e) => setNewSpell({ ...newSpell, casting_time: e.target.value })}
                      className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-violet-500/50"
                    >
                      {CASTING_TIMES.map(ct => <option key={ct} value={ct}>{ct}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1.5">Range</label>
                    <select
                      value={newSpell.range}
                      onChange={(e) => setNewSpell({ ...newSpell, range: e.target.value })}
                      className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-violet-500/50"
                    >
                      {RANGES.map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </div>
                </div>

                {/* Duration & Area */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1.5">Duration</label>
                    <select
                      value={newSpell.duration}
                      onChange={(e) => setNewSpell({ ...newSpell, duration: e.target.value })}
                      className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-violet-500/50"
                    >
                      {DURATIONS.map(d => <option key={d} value={d}>{d}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1.5">Area of Effect</label>
                    <input
                      type="text"
                      value={newSpell.area}
                      onChange={(e) => setNewSpell({ ...newSpell, area: e.target.value })}
                      placeholder="e.g., 20-foot radius"
                      className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-violet-500/50"
                    />
                  </div>
                </div>

                {/* Components */}
                <div>
                  <label className="block text-xs text-muted-foreground mb-2">Components</label>
                  <div className="flex flex-wrap gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={newSpell.verbal}
                        onChange={(e) => setNewSpell({ ...newSpell, verbal: e.target.checked })}
                        className="w-4 h-4 rounded border-border text-violet-500 focus:ring-violet-500/50"
                      />
                      <span className="text-sm text-foreground">V (Verbal)</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={newSpell.somatic}
                        onChange={(e) => setNewSpell({ ...newSpell, somatic: e.target.checked })}
                        className="w-4 h-4 rounded border-border text-violet-500 focus:ring-violet-500/50"
                      />
                      <span className="text-sm text-foreground">S (Somatic)</span>
                    </label>
                  </div>
                  <div className="mt-2">
                    <input
                      type="text"
                      value={newSpell.material}
                      onChange={(e) => setNewSpell({ ...newSpell, material: e.target.value })}
                      placeholder="Material components (leave empty if none)"
                      className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:border-violet-500/50"
                    />
                  </div>
                </div>

                {/* Properties */}
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newSpell.concentration}
                      onChange={(e) => setNewSpell({ ...newSpell, concentration: e.target.checked })}
                      className="w-4 h-4 rounded border-border text-violet-500 focus:ring-violet-500/50"
                    />
                    <span className="text-sm text-foreground">Concentration</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newSpell.ritual}
                      onChange={(e) => setNewSpell({ ...newSpell, ritual: e.target.checked })}
                      className="w-4 h-4 rounded border-border text-violet-500 focus:ring-violet-500/50"
                    />
                    <span className="text-sm text-foreground">Ritual</span>
                  </label>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-xs text-muted-foreground mb-1.5">Description</label>
                  <textarea
                    value={newSpell.description}
                    onChange={(e) => setNewSpell({ ...newSpell, description: e.target.value })}
                    placeholder="Spell effect and mechanics..."
                    rows={3}
                    className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm resize-none focus:outline-none focus:border-violet-500/50"
                  />
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <button
                    onClick={addNewSpell}
                    disabled={!newSpell.name.trim()}
                    className="flex-1 py-2.5 bg-violet-600 text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-violet-500 transition-colors"
                  >
                    Add Spell
                  </button>
                  <button
                    onClick={() => { setShowAddSpell(false); resetSpellForm() }}
                    className="px-4 py-2.5 bg-muted text-foreground rounded-lg text-sm hover:bg-muted/80 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Spellcasting Stats */}
            {spellcastingInfo && (
              <div className="grid grid-cols-3 gap-3 p-4 rounded-xl bg-violet-500/10 border border-violet-500/20">
                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">Ability</p>
                  <p className="font-bold text-violet-400">{spellcastingInfo.ability?.toUpperCase() || '-'}</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">Save DC</p>
                  <p className="font-bold text-violet-400">{spellcastingInfo.spell_save_dc || '-'}</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">Attack</p>
                  <p className="font-bold text-violet-400">
                    {spellcastingInfo.spell_attack_bonus !== undefined
                      ? (spellcastingInfo.spell_attack_bonus >= 0 ? '+' : '') + spellcastingInfo.spell_attack_bonus
                      : '-'}
                  </p>
                </div>
              </div>
            )}

            <SectionDivider label="Known Spells" />

            {/* Spell Levels */}
            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
              {SPELL_LEVELS.map((level) => {
                const spells = getSpellsByLevel(level)
                if (spells.length === 0) return null

                const isExpanded = expandedSpellLevel === level

                return (
                  <div key={level} className="rounded-xl border border-border/50 overflow-hidden">
                    <button
                      onClick={() => setExpandedSpellLevel(isExpanded ? null : level)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-muted/30 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{level === 0 ? '🔮' : '✨'}</span>
                        <span className="font-medium text-foreground">{getLevelName(level)}</span>
                        <span className="px-2 py-0.5 text-xs font-bold bg-violet-500/20 text-violet-400 rounded-lg">{spells.length}</span>
                      </div>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                      )}
                    </button>

                    {isExpanded && (
                      <div className="px-4 pb-4 pt-2 border-t border-border/30 space-y-2">
                        {spells.map((spell, idx) => (
                          <div key={idx} className="p-3 rounded-lg bg-card/50 border border-border/30">
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-foreground">{spell.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  {spell.school} · {spell.casting_time} · {spell.range}
                                </p>
                              </div>
                              <div className="flex items-center gap-1 flex-shrink-0">
                                {spell.concentration && (
                                  <span className="px-1.5 py-0.5 text-[10px] bg-amber-500/20 text-amber-400 rounded">C</span>
                                )}
                                {spell.ritual && (
                                  <span className="px-1.5 py-0.5 text-[10px] bg-blue-500/20 text-blue-400 rounded">R</span>
                                )}
                                <button
                                  onClick={() => removeSpell(spell)}
                                  className="p-1 text-red-400 hover:bg-red-500/10 rounded transition-colors"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                            {spell.description && (
                              <p className="mt-2 text-xs text-muted-foreground line-clamp-2">
                                {spell.description}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}

              {totalSpells === 0 && (
                <div className="text-center py-10 text-muted-foreground">
                  <Sparkles className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">No spells known</p>
                </div>
              )}
            </div>

            {/* Spell Summary */}
            <div className="rounded-xl bg-gradient-to-br from-violet-500/10 to-purple-500/5 border border-violet-500/20 p-4">
              <div className="flex items-center justify-between">
                <span className="font-display text-sm text-foreground">Total Spells</span>
                <span className="text-2xl font-bold font-display text-violet-400">{totalSpells}</span>
              </div>
            </div>
          </div>
        </EditorCard>
      </DualEditorGrid>
    </StepLayout>
  )
}
