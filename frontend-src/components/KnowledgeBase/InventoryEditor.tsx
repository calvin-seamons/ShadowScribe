import React, { useState, useCallback, useMemo } from 'react';
import {
    Package,
    Sword,
    Shield,
    Sparkles,
    Circle,
    Shirt,
    Weight,
    Plus,
    Trash2,
    ChevronDown,
    ChevronRight,
    AlertCircle,
    Star,
    Calculator,
    Eye,
    Zap
} from 'lucide-react';
import { ValidationError } from '../../services/knowledgeBaseApi';
import { ArrayEditor } from './ArrayEditor';



interface ItemSpell {
    name: string;
    level: number;
    legacy?: boolean;
    charges?: number;
    uses?: string;
    save_dc?: number;
}

interface BaseItem {
    name: string;
    type: string;
    rarity: 'Common' | 'Uncommon' | 'Rare' | 'Very Rare' | 'Legendary' | 'Artifact';
    weight?: number;
    cost?: string | null;
    quantity?: number;
    equipped?: boolean;
    requires_attunement?: boolean | string;
    attunement_process?: string;
    description?: string;
    source?: string;
    tags?: string[];
    legacy?: boolean;
}

interface WeaponItem extends BaseItem {
    proficient?: boolean;
    attack_type?: 'Melee' | 'Ranged';
    reach?: string;
    damage?: {
        one_handed?: string;
        two_handed?: string;
    } | string;
    damage_type?: string;
    properties?: string[];
    version?: number;
    magical_bonus?: string;
    special_features?: {
        critical_range?: string;
        extra_damage?: string;
        curse?: {
            trigger: string;
            save: string;
            success_effect: string;
            failure_effect: string;
        };
        random_properties?: string[];
        [key: string]: any;
    };
    spell_charges?: {
        save_dc: number;
        recharge: string;
        spells: ItemSpell[];
    };
    lore?: string;
}

interface ArmorItem extends BaseItem {
    armor_class?: number;
    armor_class_bonus?: string;
    magical_bonus?: string;
    special?: string;
}

interface WondrousItem extends BaseItem {
    effect?: string;
    features?: Record<string, any>;
    spells?: ItemSpell[];
    special?: string;
}

interface ConsumableItem extends BaseItem {
    contents?: string;
    weight_formula?: string;
    effects?: {
        dump_all?: string;
        plant_bean?: string;
        [key: string]: any;
    } | string[];
    effect?: string;
    special?: string;
}

interface UtilityItem extends BaseItem {
    effect?: string;
    command_word?: string;
}

interface ClothingItem extends BaseItem {
    armor_class?: number;
}

type InventoryItem = WeaponItem | ArmorItem | WondrousItem | ConsumableItem | UtilityItem | ClothingItem;

interface EquippedItems {
    weapons: WeaponItem[];
    armor: ArmorItem[];
    wondrous_items: WondrousItem[];
    rods?: WondrousItem[];
}

interface InventoryData {
    inventory: {
        total_weight: number;
        weight_unit: string;
        equipped_items: EquippedItems;
        consumables: ConsumableItem[];
        utility_items: UtilityItem[];
        clothing: ClothingItem[];
    };
    metadata: {
        version: string;
        last_updated: string;
        notes: string[];
    };
}

interface InventoryEditorProps {
    data: InventoryData;
    onChange: (data: InventoryData) => void;
    validationErrors?: ValidationError[];
}

export const InventoryEditor: React.FC<InventoryEditorProps> = ({
    data,
    onChange,
    validationErrors = []
}) => {
    const [activeTab, setActiveTab] = useState<'equipped' | 'consumables' | 'utility' | 'clothing' | 'weight'>('equipped');
    const [activeEquippedTab, setActiveEquippedTab] = useState<'weapons' | 'armor' | 'wondrous_items' | 'rods'>('weapons');
    const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

    const updateData = useCallback((updates: Partial<InventoryData>) => {
        onChange({ ...data, ...updates });
    }, [data, onChange]);

    const updateInventory = useCallback((inventory: InventoryData['inventory']) => {
        updateData({ inventory });
    }, [updateData]);

    // Calculate total weight
    const calculatedWeight = useMemo(() => {
        let totalWeight = 0;
        
        // Equipped items
        const equipped = data.inventory.equipped_items;
        [...equipped.weapons, ...equipped.armor, ...equipped.wondrous_items, ...(equipped.rods || [])].forEach(item => {
            if (item.weight) {
                totalWeight += item.weight * (item.quantity || 1);
            }
        });

        // Other items
        [...data.inventory.consumables, ...data.inventory.utility_items, ...data.inventory.clothing].forEach(item => {
            if (item.weight) {
                totalWeight += item.weight * (item.quantity || 1);
            }
        });

        return Math.round(totalWeight * 10) / 10; // Round to 1 decimal place
    }, [data.inventory]);

    const toggleItemExpansion = (itemKey: string) => {
        const newExpanded = new Set(expandedItems);
        if (newExpanded.has(itemKey)) {
            newExpanded.delete(itemKey);
        } else {
            newExpanded.add(itemKey);
        }
        setExpandedItems(newExpanded);
    };

    const addItem = (category: keyof InventoryData['inventory'], subcategory?: string) => {
        const newItem: BaseItem = {
            name: '',
            type: subcategory === 'weapons' ? 'Weapon' : 
                  subcategory === 'armor' ? 'Armor' :
                  subcategory === 'wondrous_items' || subcategory === 'rods' ? 'Wondrous Item' :
                  category === 'consumables' ? 'Potion' :
                  category === 'utility_items' ? 'Adventuring Gear' :
                  'Clothing',
            rarity: 'Common',
            weight: 0,
            cost: null,
            quantity: 1,
            equipped: false
        };

        if (category === 'equipped_items' && subcategory) {
            const updatedEquipped = {
                ...data.inventory.equipped_items,
                [subcategory]: [...(data.inventory.equipped_items[subcategory as keyof EquippedItems] || []), newItem]
            };
            updateInventory({
                ...data.inventory,
                equipped_items: updatedEquipped
            });
        } else {
            const updatedItems = [...(data.inventory[category] as any[]), newItem];
            updateInventory({
                ...data.inventory,
                [category]: updatedItems
            });
        }
    };

    const updateItem = (category: keyof InventoryData['inventory'], index: number, updatedItem: InventoryItem, subcategory?: string) => {
        if (category === 'equipped_items' && subcategory) {
            const updatedItems = [...(data.inventory.equipped_items[subcategory as keyof EquippedItems] || [])];
            updatedItems[index] = updatedItem;
            const updatedEquipped = {
                ...data.inventory.equipped_items,
                [subcategory]: updatedItems
            };
            updateInventory({
                ...data.inventory,
                equipped_items: updatedEquipped
            });
        } else {
            const updatedItems = [...(data.inventory[category] as any[])];
            updatedItems[index] = updatedItem;
            updateInventory({
                ...data.inventory,
                [category]: updatedItems
            });
        }
    };

    const removeItem = (category: keyof InventoryData['inventory'], index: number, subcategory?: string) => {
        if (category === 'equipped_items' && subcategory) {
            const updatedItems = (data.inventory.equipped_items[subcategory as keyof EquippedItems] || []).filter((_, i) => i !== index);
            const updatedEquipped = {
                ...data.inventory.equipped_items,
                [subcategory]: updatedItems
            };
            updateInventory({
                ...data.inventory,
                equipped_items: updatedEquipped
            });
        } else {
            const updatedItems = (data.inventory[category] as any[]).filter((_, i) => i !== index);
            updateInventory({
                ...data.inventory,
                [category]: updatedItems
            });
        }
    };

    const renderBasicItemFields = (item: BaseItem, onUpdate: (item: BaseItem) => void) => (
        <div className="space-y-4">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">
                        Item Name <span className="text-red-400">*</span>
                    </label>
                    <input
                        type="text"
                        value={item.name}
                        onChange={(e) => onUpdate({ ...item, name: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Enter item name"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Type</label>
                    <input
                        type="text"
                        value={item.type}
                        onChange={(e) => onUpdate({ ...item, type: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="e.g., Weapon, Armor, Wondrous Item"
                    />
                </div>
            </div>

            {/* Rarity and Basic Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Rarity</label>
                    <select
                        value={item.rarity}
                        onChange={(e) => onUpdate({ ...item, rarity: e.target.value as BaseItem['rarity'] })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                        <option value="Common">Common</option>
                        <option value="Uncommon">Uncommon</option>
                        <option value="Rare">Rare</option>
                        <option value="Very Rare">Very Rare</option>
                        <option value="Legendary">Legendary</option>
                        <option value="Artifact">Artifact</option>
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Weight (lb)</label>
                    <input
                        type="number"
                        value={item.weight || ''}
                        onChange={(e) => onUpdate({ ...item, weight: e.target.value ? Number(e.target.value) : undefined })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        min="0"
                        step="0.1"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Cost</label>
                    <input
                        type="text"
                        value={item.cost || ''}
                        onChange={(e) => onUpdate({ ...item, cost: e.target.value || null })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="e.g., 50 gp"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Quantity</label>
                    <input
                        type="number"
                        value={item.quantity || 1}
                        onChange={(e) => onUpdate({ ...item, quantity: Number(e.target.value) || 1 })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        min="1"
                    />
                </div>
            </div>

            {/* Status Checkboxes */}
            <div className="flex flex-wrap items-center space-x-6">
                <label className="flex items-center space-x-2">
                    <input
                        type="checkbox"
                        checked={item.equipped || false}
                        onChange={(e) => onUpdate({ ...item, equipped: e.target.checked })}
                        className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="text-sm text-white">Equipped</span>
                </label>
                <label className="flex items-center space-x-2">
                    <input
                        type="checkbox"
                        checked={!!item.requires_attunement}
                        onChange={(e) => onUpdate({ 
                            ...item, 
                            requires_attunement: e.target.checked ? true : undefined 
                        })}
                        className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="text-sm text-white">Requires Attunement</span>
                </label>
                <label className="flex items-center space-x-2">
                    <input
                        type="checkbox"
                        checked={item.legacy || false}
                        onChange={(e) => onUpdate({ ...item, legacy: e.target.checked })}
                        className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="text-sm text-white">Legacy Item</span>
                </label>
            </div>

            {/* Attunement Process */}
            {item.requires_attunement && (
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Attunement Process</label>
                    <textarea
                        value={item.attunement_process || ''}
                        onChange={(e) => onUpdate({ ...item, attunement_process: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        rows={3}
                        placeholder="Describe the attunement process"
                    />
                </div>
            )}

            {/* Description */}
            <div>
                <label className="block text-sm font-medium text-white mb-2">Description</label>
                <textarea
                    value={item.description || ''}
                    onChange={(e) => onUpdate({ ...item, description: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    rows={3}
                    placeholder="Describe the item"
                />
            </div>

            {/* Source and Tags */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Source</label>
                    <input
                        type="text"
                        value={item.source || ''}
                        onChange={(e) => onUpdate({ ...item, source: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="e.g., DMG, pg. 150"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Tags</label>
                    <ArrayEditor
                        items={item.tags || []}
                        onChange={(tags) => onUpdate({ ...item, tags })}
                        label="Tags"
                        itemSchema={{
                            key: 'tag',
                            type: 'string',
                            label: 'Tag',
                            required: false
                        }}
                    />
                </div>
            </div>
        </div>
    );

    const renderWeaponFields = (weapon: WeaponItem, onUpdate: (weapon: WeaponItem) => void) => (
        <div className="space-y-4">
            {/* Weapon-specific fields */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Attack Type</label>
                    <select
                        value={weapon.attack_type || ''}
                        onChange={(e) => onUpdate({ ...weapon, attack_type: e.target.value as 'Melee' | 'Ranged' })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                        <option value="">Select type</option>
                        <option value="Melee">Melee</option>
                        <option value="Ranged">Ranged</option>
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Reach</label>
                    <input
                        type="text"
                        value={weapon.reach || ''}
                        onChange={(e) => onUpdate({ ...weapon, reach: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="e.g., 5 ft"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Damage Type</label>
                    <input
                        type="text"
                        value={weapon.damage_type || ''}
                        onChange={(e) => onUpdate({ ...weapon, damage_type: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="e.g., slashing, piercing"
                    />
                </div>
            </div>

            {/* Damage */}
            <div>
                <label className="block text-sm font-medium text-white mb-2">Damage</label>
                {typeof weapon.damage === 'string' ? (
                    <div className="flex items-center space-x-2">
                        <input
                            type="text"
                            value={weapon.damage}
                            onChange={(e) => onUpdate({ ...weapon, damage: e.target.value })}
                            className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="e.g., 1d8+5"
                        />
                        <button
                            type="button"
                            onClick={() => onUpdate({
                                ...weapon,
                                damage: { one_handed: weapon.damage as string, two_handed: '' }
                            })}
                            className="px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                        >
                            Split Damage
                        </button>
                    </div>
                ) : (
                    <div className="space-y-2">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs text-gray-400 mb-1">One-Handed</label>
                                <input
                                    type="text"
                                    value={weapon.damage?.one_handed || ''}
                                    onChange={(e) => onUpdate({
                                        ...weapon,
                                        damage: { ...(weapon.damage as any), one_handed: e.target.value }
                                    })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="e.g., 1d8+5"
                                />
                            </div>
                            <div>
                                <label className="block text-xs text-gray-400 mb-1">Two-Handed</label>
                                <input
                                    type="text"
                                    value={weapon.damage?.two_handed || ''}
                                    onChange={(e) => onUpdate({
                                        ...weapon,
                                        damage: { ...(weapon.damage as any), two_handed: e.target.value }
                                    })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="e.g., 1d10+5"
                                />
                            </div>
                        </div>
                        <button
                            type="button"
                            onClick={() => onUpdate({
                                ...weapon,
                                damage: (weapon.damage as any)?.one_handed || ''
                            })}
                            className="text-sm text-purple-400 hover:text-purple-300"
                        >
                            Merge to Single Damage
                        </button>
                    </div>
                )}
            </div>

            {/* Properties and Magical Bonus */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Properties</label>
                    <ArrayEditor
                        items={weapon.properties || []}
                        onChange={(properties) => onUpdate({ ...weapon, properties })}
                        label="Properties"
                        itemSchema={{
                            key: 'property',
                            type: 'string',
                            label: 'Property',
                            required: false
                        }}
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Magical Bonus</label>
                    <input
                        type="text"
                        value={weapon.magical_bonus || ''}
                        onChange={(e) => onUpdate({ ...weapon, magical_bonus: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="e.g., +3"
                    />
                </div>
            </div>

            {/* Proficiency */}
            <div>
                <label className="flex items-center space-x-2">
                    <input
                        type="checkbox"
                        checked={weapon.proficient || false}
                        onChange={(e) => onUpdate({ ...weapon, proficient: e.target.checked })}
                        className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="text-sm text-white">Proficient with this weapon</span>
                </label>
            </div>
        </div>
    );

    const renderArmorFields = (armor: ArmorItem, onUpdate: (armor: ArmorItem) => void) => (
        <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Armor Class</label>
                    <input
                        type="number"
                        value={armor.armor_class || ''}
                        onChange={(e) => onUpdate({ ...armor, armor_class: e.target.value ? Number(e.target.value) : undefined })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        min="10"
                        max="25"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">AC Bonus</label>
                    <input
                        type="text"
                        value={armor.armor_class_bonus || ''}
                        onChange={(e) => onUpdate({ ...armor, armor_class_bonus: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="e.g., +2"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Magical Bonus</label>
                    <input
                        type="text"
                        value={armor.magical_bonus || ''}
                        onChange={(e) => onUpdate({ ...armor, magical_bonus: e.target.value })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="e.g., +1 to AC"
                    />
                </div>
            </div>

            {/* Special Properties */}
            <div>
                <label className="block text-sm font-medium text-white mb-2">Special Properties</label>
                <textarea
                    value={armor.special || ''}
                    onChange={(e) => onUpdate({ ...armor, special: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    rows={2}
                    placeholder="Special armor properties"
                />
            </div>
        </div>
    );

    const renderMagicalItemFields = (item: WondrousItem, onUpdate: (item: WondrousItem) => void) => (
        <div className="space-y-4">
            {/* Effect */}
            <div>
                <label className="block text-sm font-medium text-white mb-2">Effect</label>
                <textarea
                    value={item.effect || ''}
                    onChange={(e) => onUpdate({ ...item, effect: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    rows={3}
                    placeholder="What this item does"
                />
            </div>

            {/* Spells */}
            {item.spells && item.spells.length > 0 && (
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Spells</label>
                    <ArrayEditor
                        items={item.spells}
                        onChange={(spells) => onUpdate({ ...item, spells })}
                        label="Spells"
                        itemSchema={{
                            key: 'spell',
                            type: 'object',
                            label: 'Spell',
                            required: false,
                            children: [
                                {
                                    key: 'name',
                                    type: 'string',
                                    label: 'Spell Name',
                                    required: true
                                },
                                {
                                    key: 'level',
                                    type: 'number',
                                    label: 'Spell Level',
                                    required: true,
                                    minimum: 0,
                                    maximum: 9
                                },
                                {
                                    key: 'uses',
                                    type: 'string',
                                    label: 'Uses',
                                    required: false
                                },
                                {
                                    key: 'save_dc',
                                    type: 'number',
                                    label: 'Save DC',
                                    required: false,
                                    minimum: 8,
                                    maximum: 30
                                }
                            ]
                        }}
                    />
                </div>
            )}

            {/* Add Spells Button */}
            {(!item.spells || item.spells.length === 0) && (
                <button
                    type="button"
                    onClick={() => onUpdate({
                        ...item,
                        spells: [{ name: '', level: 1 }]
                    })}
                    className="flex items-center space-x-2 px-3 py-2 border border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400"
                >
                    <Sparkles className="w-4 h-4" />
                    <span>Add Spells</span>
                </button>
            )}

            {/* Special Properties */}
            <div>
                <label className="block text-sm font-medium text-white mb-2">Special Properties</label>
                <textarea
                    value={item.special || ''}
                    onChange={(e) => onUpdate({ ...item, special: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    rows={2}
                    placeholder="Special item properties"
                />
            </div>
        </div>
    );

    const renderItemEditor = (item: InventoryItem, category: keyof InventoryData['inventory'], index: number, subcategory?: string) => {
        const itemKey = `${category}-${subcategory || ''}-${index}`;
        const isExpanded = expandedItems.has(itemKey);
        
        const getItemIcon = () => {
            if (subcategory === 'weapons' || item.type.toLowerCase().includes('weapon')) {
                return <Sword className="w-4 h-4 text-red-400" />;
            }
            if (subcategory === 'armor' || item.type.toLowerCase().includes('armor')) {
                return <Shield className="w-4 h-4 text-blue-400" />;
            }
            if (category === 'consumables' || item.type.toLowerCase().includes('potion')) {
                return <Circle className="w-4 h-4 text-green-400" />;
            }
            if (category === 'clothing') {
                return <Shirt className="w-4 h-4 text-purple-400" />;
            }
            if (item.rarity !== 'Common') {
                return <Sparkles className="w-4 h-4 text-yellow-400" />;
            }
            return <Package className="w-4 h-4 text-gray-400" />;
        };

        const getRarityColor = (rarity: string) => {
            switch (rarity) {
                case 'Uncommon': return 'text-green-400';
                case 'Rare': return 'text-blue-400';
                case 'Very Rare': return 'text-purple-400';
                case 'Legendary': return 'text-orange-400';
                case 'Artifact': return 'text-red-400';
                default: return 'text-gray-400';
            }
        };

        return (
            <div key={index} className="border border-gray-600 rounded-md">
                <div className="flex items-center justify-between p-3 bg-gray-750">
                    <div className="flex items-center space-x-2">
                        <button
                            type="button"
                            onClick={() => toggleItemExpansion(itemKey)}
                            className="flex items-center space-x-2"
                        >
                            {isExpanded ? (
                                <ChevronDown className="w-4 h-4 text-gray-400" />
                            ) : (
                                <ChevronRight className="w-4 h-4 text-gray-400" />
                            )}
                            {getItemIcon()}
                            <span className="font-medium text-white">
                                {item.name || `Item ${index + 1}`}
                            </span>
                        </button>
                        <div className="flex items-center space-x-2">
                            <span className={`text-xs px-2 py-1 rounded ${getRarityColor(item.rarity)} bg-gray-800`}>
                                {item.rarity}
                            </span>
                            {item.equipped && (
                                <Eye className="w-4 h-4 text-green-400" />
                            )}
                            {item.requires_attunement && (
                                <Star className="w-4 h-4 text-yellow-400" />
                            )}
                            {item.weight && (
                                <span className="text-xs text-gray-400 flex items-center space-x-1">
                                    <Weight className="w-3 h-3" />
                                    <span>{item.weight * (item.quantity || 1)} lb</span>
                                </span>
                            )}
                        </div>
                    </div>
                    <button
                        type="button"
                        onClick={() => removeItem(category, index, subcategory)}
                        className="text-red-400 hover:text-red-300 p-1"
                        title="Remove item"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>

                {isExpanded && (
                    <div className="p-4 space-y-6 border-t border-gray-600">
                        {/* Basic Fields */}
                        {renderBasicItemFields(item, (updatedItem) => 
                            updateItem(category, index, updatedItem, subcategory)
                        )}

                        {/* Type-specific Fields */}
                        {(subcategory === 'weapons' || item.type.toLowerCase().includes('weapon')) && 
                            renderWeaponFields(item as WeaponItem, (updatedItem) => 
                                updateItem(category, index, updatedItem, subcategory)
                            )
                        }

                        {(subcategory === 'armor' || item.type.toLowerCase().includes('armor')) && 
                            renderArmorFields(item as ArmorItem, (updatedItem) => 
                                updateItem(category, index, updatedItem, subcategory)
                            )
                        }

                        {(subcategory === 'wondrous_items' || subcategory === 'rods' || 
                          (item.type.toLowerCase().includes('wondrous') || item.rarity !== 'Common')) && 
                            renderMagicalItemFields(item as WondrousItem, (updatedItem) => 
                                updateItem(category, index, updatedItem, subcategory)
                            )
                        }
                    </div>
                )}
            </div>
        );
    };

    const renderEquippedTab = () => (
        <div className="space-y-6">
            {/* Equipped Items Sub-tabs */}
            <div className="flex space-x-1 bg-gray-800 p-1 rounded-lg">
                {[
                    { key: 'weapons', label: 'Weapons', icon: Sword },
                    { key: 'armor', label: 'Armor', icon: Shield },
                    { key: 'wondrous_items', label: 'Wondrous Items', icon: Sparkles },
                    { key: 'rods', label: 'Rods', icon: Zap }
                ].map(({ key, label, icon: Icon }) => (
                    <button
                        key={key}
                        onClick={() => setActiveEquippedTab(key as any)}
                        className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                            activeEquippedTab === key
                                ? 'bg-purple-600 text-white'
                                : 'text-gray-400 hover:text-white hover:bg-gray-700'
                        }`}
                    >
                        <Icon className="w-4 h-4" />
                        <span>{label}</span>
                        <span className="text-xs bg-gray-600 px-2 py-1 rounded">
                            {(data.inventory.equipped_items[key as keyof EquippedItems] || []).length}
                        </span>
                    </button>
                ))}
            </div>

            {/* Items List */}
            <div className="space-y-4">
                {(data.inventory.equipped_items[activeEquippedTab] || []).map((item, index) =>
                    renderItemEditor(item, 'equipped_items', index, activeEquippedTab)
                )}

                {/* Add Item Button */}
                <button
                    type="button"
                    onClick={() => addItem('equipped_items', activeEquippedTab)}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-3 border-2 border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400 transition-colors"
                >
                    <Plus className="w-5 h-5" />
                    <span>Add {activeEquippedTab.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                </button>
            </div>
        </div>
    );

    const renderWeightTab = () => (
        <div className="space-y-6">
            {/* Weight Summary */}
            <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
                        <Calculator className="w-5 h-5" />
                        <span>Weight Management</span>
                    </h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                        <div className="text-2xl font-bold text-purple-400">
                            {calculatedWeight}
                        </div>
                        <div className="text-sm text-gray-400">Calculated Weight</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-white">
                            {data.inventory.total_weight}
                        </div>
                        <div className="text-sm text-gray-400">Recorded Weight</div>
                    </div>
                    <div className="text-center">
                        <div className={`text-2xl font-bold ${
                            Math.abs(calculatedWeight - data.inventory.total_weight) > 0.1 
                                ? 'text-red-400' 
                                : 'text-green-400'
                        }`}>
                            {Math.abs(calculatedWeight - data.inventory.total_weight).toFixed(1)}
                        </div>
                        <div className="text-sm text-gray-400">Difference</div>
                    </div>
                </div>

                {/* Update Weight Button */}
                {Math.abs(calculatedWeight - data.inventory.total_weight) > 0.1 && (
                    <div className="mt-4 text-center">
                        <button
                            type="button"
                            onClick={() => updateInventory({
                                ...data.inventory,
                                total_weight: calculatedWeight
                            })}
                            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                        >
                            Update to Calculated Weight
                        </button>
                    </div>
                )}
            </div>

            {/* Manual Weight Override */}
            <div className="bg-gray-800 rounded-lg p-6">
                <h4 className="text-md font-semibold text-white mb-4">Manual Weight Override</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Total Weight</label>
                        <input
                            type="number"
                            value={data.inventory.total_weight}
                            onChange={(e) => updateInventory({
                                ...data.inventory,
                                total_weight: Number(e.target.value) || 0
                            })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                            step="0.1"
                            min="0"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Weight Unit</label>
                        <select
                            value={data.inventory.weight_unit}
                            onChange={(e) => updateInventory({
                                ...data.inventory,
                                weight_unit: e.target.value
                            })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                            <option value="lb">Pounds (lb)</option>
                            <option value="kg">Kilograms (kg)</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderCategoryTab = (category: 'consumables' | 'utility_items' | 'clothing') => {
        const items = data.inventory[category];
        const categoryLabels = {
            consumables: 'Consumables',
            utility_items: 'Utility Items',
            clothing: 'Clothing'
        };

        return (
            <div className="space-y-4">
                {items.map((item, index) =>
                    renderItemEditor(item, category, index)
                )}

                {/* Add Item Button */}
                <button
                    type="button"
                    onClick={() => addItem(category)}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-3 border-2 border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400 transition-colors"
                >
                    <Plus className="w-5 h-5" />
                    <span>Add {categoryLabels[category].slice(0, -1)}</span>
                </button>
            </div>
        );
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
                    <Package className="w-6 h-6" />
                    <span>Inventory Editor</span>
                </h2>
                <div className="flex items-center space-x-4 text-sm text-gray-400">
                    <div className="flex items-center space-x-1">
                        <Weight className="w-4 h-4" />
                        <span>{data.inventory.total_weight} {data.inventory.weight_unit}</span>
                    </div>
                </div>
            </div>

            {/* Validation Errors */}
            {validationErrors.length > 0 && (
                <div className="bg-red-900/20 border border-red-500 rounded-md p-4">
                    <div className="flex items-center space-x-2 mb-2">
                        <AlertCircle className="w-5 h-5 text-red-400" />
                        <span className="font-medium text-red-400">Validation Errors</span>
                    </div>
                    <ul className="list-disc list-inside space-y-1 text-red-300">
                        {validationErrors.map((error, index) => (
                            <li key={index}>{error.message}</li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Tabs */}
            <div className="flex space-x-1 bg-gray-800 p-1 rounded-lg">
                {[
                    { key: 'equipped', label: 'Equipped Items', icon: Eye },
                    { key: 'consumables', label: 'Consumables', icon: Circle },
                    { key: 'utility', label: 'Utility Items', icon: Package },
                    { key: 'clothing', label: 'Clothing', icon: Shirt },
                    { key: 'weight', label: 'Weight Management', icon: Calculator }
                ].map(({ key, label, icon: Icon }) => (
                    <button
                        key={key}
                        onClick={() => setActiveTab(key as any)}
                        className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                            activeTab === key
                                ? 'bg-purple-600 text-white'
                                : 'text-gray-400 hover:text-white hover:bg-gray-700'
                        }`}
                    >
                        <Icon className="w-4 h-4" />
                        <span>{label}</span>
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="min-h-[400px]">
                {activeTab === 'equipped' && renderEquippedTab()}
                {activeTab === 'consumables' && renderCategoryTab('consumables')}
                {activeTab === 'utility' && renderCategoryTab('utility_items')}
                {activeTab === 'clothing' && renderCategoryTab('clothing')}
                {activeTab === 'weight' && renderWeightTab()}
            </div>
        </div>
    );
};