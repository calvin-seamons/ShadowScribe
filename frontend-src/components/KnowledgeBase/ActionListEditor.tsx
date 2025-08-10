import React, { useState, useCallback } from 'react';
import {
    Sword,
    Zap,
    Shield,
    Clock,
    Target,
    Plus,
    Trash2,
    ChevronDown,
    ChevronRight,
    AlertCircle,
    Star,
    Activity,
    Sparkles,
    Eye
} from 'lucide-react';
import { ValidationError } from '../../services/knowledgeBaseApi';
import { ArrayEditor } from './ArrayEditor';

interface WeaponAttack {
    name: string;
    type: 'weapon_attack' | 'melee_attack' | 'ranged_attack';
    properties?: string[];
    range: string;
    reach?: boolean;
    attack_bonus: number;
    damage: string | {
        one_handed?: string;
        two_handed?: string;
    };
    damage_type: string;
    charges?: {
        current: number;
        maximum: number;
    };
    weapon_properties?: string[];
    special_options?: Array<{
        name: string;
        effect: string;
    }>;
}

interface ActionUses {
    current?: number;
    maximum: number;
    reset: 'short_rest' | 'long_rest' | 'dawn' | 'turn';
}

interface ActionPool {
    current: number;
    maximum: number;
    reset: 'short_rest' | 'long_rest' | 'dawn';
}

interface BaseAction {
    name: string;
    type: string;
    description?: string;
    effect?: string;
    range?: string;
    duration?: string;
    trigger?: string;
    uses?: ActionUses;
    pool?: ActionPool;
    save_dc?: number;
    uses_per_turn?: number;
}

interface Action extends BaseAction {
    sub_actions?: WeaponAttack[];
    options?: Array<{
        name: string;
        type: string;
        effect: string;
        trigger?: string;
    }>;
    effects?: Array<{
        name: string;
        cost: string | number;
        effect: string;
    }>;
}

interface SpellAction extends BaseAction {
    spell_level: number;
    class: string;
    legacy?: boolean;
    casting_time?: string;
    components?: {
        verbal?: boolean;
        somatic?: boolean;
        material?: boolean;
        material_component?: string;
    };
    concentration?: boolean;
}

interface SpecialAbility extends BaseAction {
    action_required?: 'action' | 'bonus_action' | 'reaction' | 'none';
    cost?: string;
    damage?: {
        base: string;
        per_spell_level?: string;
        maximum?: string;
        vs_undead_fiend?: string;
    };
    damage_type?: string;
    effects?: string[];
    restrictions?: string;
}

interface ActionEconomy {
    actions: Action[];
    bonus_actions: (Action | SpellAction)[];
    reactions: (Action | SpellAction)[];
    other_actions: (Action | SpellAction)[];
    special_abilities: SpecialAbility[];
}

interface ActionListData {
    character_actions: {
        attacks_per_action?: number;
        action_economy: ActionEconomy;
        combat_actions_reference?: string[];
    };
    metadata: {
        version: string;
        last_updated: string;
        notes: string[];
    };
}

interface ActionListEditorProps {
    data: ActionListData;
    onChange: (data: ActionListData) => void;
    validationErrors?: ValidationError[];
}

export const ActionListEditor: React.FC<ActionListEditorProps> = ({
    data,
    onChange,
    validationErrors = []
}) => {
    const [activeTab, setActiveTab] = useState<'actions' | 'bonus_actions' | 'reactions' | 'other_actions' | 'special_abilities'>('actions');
    const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

    const updateData = useCallback((updates: Partial<ActionListData>) => {
        onChange({ ...data, ...updates });
    }, [data, onChange]);

    const updateActionEconomy = useCallback((actionEconomy: ActionEconomy) => {
        updateData({
            character_actions: {
                ...data.character_actions,
                action_economy: actionEconomy
            }
        });
    }, [data, updateData]);

    const toggleItemExpansion = (itemKey: string) => {
        const newExpanded = new Set(expandedItems);
        if (newExpanded.has(itemKey)) {
            newExpanded.delete(itemKey);
        } else {
            newExpanded.add(itemKey);
        }
        setExpandedItems(newExpanded);
    };

    const addAction = (category: keyof ActionEconomy) => {
        const newAction: Action = {
            name: '',
            type: category === 'actions' ? 'action' :
                category === 'bonus_actions' ? 'bonus_action' :
                    category === 'reactions' ? 'reaction' :
                        category === 'other_actions' ? 'free_action' : 'special',
            description: ''
        };

        const updatedEconomy = {
            ...data.character_actions.action_economy,
            [category]: [...data.character_actions.action_economy[category], newAction]
        };

        updateActionEconomy(updatedEconomy);
    };

    const updateAction = (category: keyof ActionEconomy, index: number, updatedAction: any) => {
        const updatedActions = [...data.character_actions.action_economy[category]];
        updatedActions[index] = updatedAction;

        const updatedEconomy = {
            ...data.character_actions.action_economy,
            [category]: updatedActions
        };

        updateActionEconomy(updatedEconomy);
    };

    const removeAction = (category: keyof ActionEconomy, index: number) => {
        const updatedActions = data.character_actions.action_economy[category].filter((_, i) => i !== index);

        const updatedEconomy = {
            ...data.character_actions.action_economy,
            [category]: updatedActions
        };

        updateActionEconomy(updatedEconomy);
    };

    const renderWeaponAttackEditor = (attack: WeaponAttack, actionIndex: number, attackIndex: number) => {
        const updateAttack = (updatedAttack: WeaponAttack) => {
            const action = data.character_actions.action_economy.actions[actionIndex] as Action;
            const updatedSubActions = [...(action.sub_actions || [])];
            updatedSubActions[attackIndex] = updatedAttack;

            updateAction('actions', actionIndex, {
                ...action,
                sub_actions: updatedSubActions
            });
        };

        return (
            <div className="border border-gray-600 rounded-md p-4 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">
                            Attack Name <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="text"
                            value={attack.name}
                            onChange={(e) => updateAttack({ ...attack, name: e.target.value })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="Enter attack name"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Attack Type</label>
                        <select
                            value={attack.type}
                            onChange={(e) => updateAttack({ ...attack, type: e.target.value as WeaponAttack['type'] })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                            <option value="weapon_attack">Weapon Attack</option>
                            <option value="melee_attack">Melee Attack</option>
                            <option value="ranged_attack">Ranged Attack</option>
                        </select>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Range</label>
                        <input
                            type="text"
                            value={attack.range}
                            onChange={(e) => updateAttack({ ...attack, range: e.target.value })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="e.g., 5 ft, 150/600 ft"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Attack Bonus</label>
                        <input
                            type="number"
                            value={attack.attack_bonus}
                            onChange={(e) => updateAttack({ ...attack, attack_bonus: Number(e.target.value) || 0 })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Damage Type</label>
                        <input
                            type="text"
                            value={attack.damage_type}
                            onChange={(e) => updateAttack({ ...attack, damage_type: e.target.value })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="e.g., slashing, piercing"
                        />
                    </div>
                </div>

                {/* Damage Section */}
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Damage</label>
                    {typeof attack.damage === 'string' ? (
                        <div className="flex items-center space-x-2">
                            <input
                                type="text"
                                value={attack.damage}
                                onChange={(e) => updateAttack({ ...attack, damage: e.target.value })}
                                className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                placeholder="e.g., 1d8+5"
                            />
                            <button
                                type="button"
                                onClick={() => updateAttack({
                                    ...attack,
                                    damage: { one_handed: attack.damage as string, two_handed: '' }
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
                                        value={attack.damage.one_handed || ''}
                                        onChange={(e) => updateAttack({
                                            ...attack,
                                            damage: { ...(attack.damage as any), one_handed: e.target.value }
                                        })}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        placeholder="e.g., 1d8+5"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-400 mb-1">Two-Handed</label>
                                    <input
                                        type="text"
                                        value={attack.damage.two_handed || ''}
                                        onChange={(e) => updateAttack({
                                            ...attack,
                                            damage: { ...(attack.damage as any), two_handed: e.target.value }
                                        })}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        placeholder="e.g., 1d10+5"
                                    />
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={() => updateAttack({
                                    ...attack,
                                    damage: (attack.damage as any).one_handed || ''
                                })}
                                className="text-sm text-purple-400 hover:text-purple-300"
                            >
                                Merge to Single Damage
                            </button>
                        </div>
                    )}
                </div>

                {/* Properties */}
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Properties</label>
                    <ArrayEditor
                        items={attack.properties || []}
                        onChange={(properties) => updateAttack({ ...attack, properties })}
                        label="Properties"
                        itemSchema={{
                            key: 'property',
                            type: 'string',
                            label: 'Property',
                            required: false
                        }}
                    />
                </div>

                {/* Weapon Properties */}
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Weapon Properties</label>
                    <ArrayEditor
                        items={attack.weapon_properties || []}
                        onChange={(weapon_properties) => updateAttack({ ...attack, weapon_properties })}
                        label="Weapon Properties"
                        itemSchema={{
                            key: 'weapon_property',
                            type: 'string',
                            label: 'Weapon Property',
                            required: false
                        }}
                    />
                </div>

                {/* Charges */}
                {attack.charges && (
                    <div className="border border-gray-600 rounded-md p-3">
                        <h4 className="text-sm font-medium text-white mb-3">Charges</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Current</label>
                                <input
                                    type="number"
                                    value={attack.charges.current}
                                    onChange={(e) => updateAttack({
                                        ...attack,
                                        charges: {
                                            ...attack.charges!,
                                            current: Number(e.target.value) || 0
                                        }
                                    })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    min="0"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Maximum</label>
                                <input
                                    type="number"
                                    value={attack.charges.maximum}
                                    onChange={(e) => updateAttack({
                                        ...attack,
                                        charges: {
                                            ...attack.charges!,
                                            maximum: Number(e.target.value) || 0
                                        }
                                    })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    min="0"
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* Add Charges Button */}
                {!attack.charges && (
                    <button
                        type="button"
                        onClick={() => updateAttack({
                            ...attack,
                            charges: { current: 1, maximum: 1 }
                        })}
                        className="flex items-center space-x-2 px-3 py-2 border border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400"
                    >
                        <Plus className="w-4 h-4" />
                        <span>Add Charges</span>
                    </button>
                )}

                {/* Special Options */}
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Special Options</label>
                    <ArrayEditor
                        items={attack.special_options || []}
                        onChange={(special_options) => updateAttack({ ...attack, special_options })}
                        label="Special Options"
                        itemSchema={{
                            key: 'special_option',
                            type: 'object',
                            label: 'Special Option',
                            required: false,
                            children: [
                                {
                                    key: 'name',
                                    type: 'string',
                                    label: 'Name',
                                    required: true
                                },
                                {
                                    key: 'effect',
                                    type: 'string',
                                    label: 'Effect',
                                    required: true
                                }
                            ]
                        }}
                    />
                </div>
            </div>
        );
    };
    const renderUsesEditor = (uses: ActionUses, onUpdate: (uses: ActionUses) => void) => (
        <div className="border border-gray-600 rounded-md p-3">
            <h4 className="text-sm font-medium text-white mb-3">Uses</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Current</label>
                    <input
                        type="number"
                        value={uses.current || ''}
                        onChange={(e) => onUpdate({
                            ...uses,
                            current: e.target.value ? Number(e.target.value) : undefined
                        })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        min="0"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Maximum</label>
                    <input
                        type="number"
                        value={uses.maximum}
                        onChange={(e) => onUpdate({
                            ...uses,
                            maximum: Number(e.target.value) || 0
                        })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        min="0"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Reset</label>
                    <select
                        value={uses.reset}
                        onChange={(e) => onUpdate({
                            ...uses,
                            reset: e.target.value as ActionUses['reset']
                        })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                        <option value="short_rest">Short Rest</option>
                        <option value="long_rest">Long Rest</option>
                        <option value="dawn">Dawn</option>
                        <option value="turn">Turn</option>
                    </select>
                </div>
            </div>
        </div>
    );

    const renderPoolEditor = (pool: ActionPool, onUpdate: (pool: ActionPool) => void) => (
        <div className="border border-gray-600 rounded-md p-3">
            <h4 className="text-sm font-medium text-white mb-3">Resource Pool</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Current</label>
                    <input
                        type="number"
                        value={pool.current}
                        onChange={(e) => onUpdate({
                            ...pool,
                            current: Number(e.target.value) || 0
                        })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        min="0"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Maximum</label>
                    <input
                        type="number"
                        value={pool.maximum}
                        onChange={(e) => onUpdate({
                            ...pool,
                            maximum: Number(e.target.value) || 0
                        })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        min="0"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Reset</label>
                    <select
                        value={pool.reset}
                        onChange={(e) => onUpdate({
                            ...pool,
                            reset: e.target.value as ActionPool['reset']
                        })}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                        <option value="short_rest">Short Rest</option>
                        <option value="long_rest">Long Rest</option>
                        <option value="dawn">Dawn</option>
                    </select>
                </div>
            </div>
        </div>
    );

    const renderSpellComponents = (components: SpellAction['components'], onUpdate: (components: SpellAction['components']) => void) => (
        <div className="border border-gray-600 rounded-md p-3">
            <h4 className="text-sm font-medium text-white mb-3">Spell Components</h4>
            <div className="space-y-3">
                <div className="flex items-center space-x-4">
                    <label className="flex items-center space-x-2">
                        <input
                            type="checkbox"
                            checked={components?.verbal || false}
                            onChange={(e) => onUpdate({ ...components, verbal: e.target.checked })}
                            className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="text-sm text-white">Verbal (V)</span>
                    </label>
                    <label className="flex items-center space-x-2">
                        <input
                            type="checkbox"
                            checked={components?.somatic || false}
                            onChange={(e) => onUpdate({ ...components, somatic: e.target.checked })}
                            className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="text-sm text-white">Somatic (S)</span>
                    </label>
                    <label className="flex items-center space-x-2">
                        <input
                            type="checkbox"
                            checked={components?.material || false}
                            onChange={(e) => onUpdate({ ...components, material: e.target.checked })}
                            className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="text-sm text-white">Material (M)</span>
                    </label>
                </div>
                {components?.material && (
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Material Component</label>
                        <input
                            type="text"
                            value={components.material_component || ''}
                            onChange={(e) => onUpdate({ ...components, material_component: e.target.value })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="Describe the material component"
                        />
                    </div>
                )}
            </div>
        </div>
    );

    const renderActionEditor = (action: Action | SpellAction | SpecialAbility, category: keyof ActionEconomy, index: number) => {
        const itemKey = `${category}-${index}`;
        const isExpanded = expandedItems.has(itemKey);
        const isSpell = 'spell_level' in action;
        const isSpecial = category === 'special_abilities';

        const getActionIcon = () => {
            if (isSpell) return <Sparkles className="w-4 h-4 text-blue-400" />;
            if (isSpecial) return <Star className="w-4 h-4 text-yellow-400" />;
            if (category === 'actions') return <Sword className="w-4 h-4 text-red-400" />;
            if (category === 'bonus_actions') return <Zap className="w-4 h-4 text-orange-400" />;
            if (category === 'reactions') return <Shield className="w-4 h-4 text-green-400" />;
            return <Activity className="w-4 h-4 text-gray-400" />;
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
                            {getActionIcon()}
                            <span className="font-medium text-white">
                                {action.name || `${category.replace('_', ' ')} ${index + 1}`}
                            </span>
                        </button>
                        {isSpell && (action as SpellAction).legacy && (
                            <span className="px-2 py-1 text-xs bg-purple-600 text-white rounded">Legacy</span>
                        )}
                        {isSpell && (
                            <span className="px-2 py-1 text-xs bg-blue-600 text-white rounded">
                                Level {(action as SpellAction).spell_level}
                            </span>
                        )}
                    </div>
                    <button
                        type="button"
                        onClick={() => removeAction(category, index)}
                        className="text-red-400 hover:text-red-300 p-1"
                        title="Remove action"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>

                {isExpanded && (
                    <div className="p-4 space-y-4 border-t border-gray-600">
                        {/* Basic Information */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">
                                    Name <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={action.name}
                                    onChange={(e) => updateAction(category, index, { ...action, name: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="Enter action name"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Type</label>
                                <input
                                    type="text"
                                    value={action.type}
                                    onChange={(e) => updateAction(category, index, { ...action, type: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="e.g., action, bonus_action, reaction"
                                />
                            </div>
                        </div>

                        {/* Spell-specific fields */}
                        {isSpell && (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-white mb-2">Spell Level</label>
                                    <input
                                        type="number"
                                        value={(action as SpellAction).spell_level}
                                        onChange={(e) => updateAction(category, index, {
                                            ...action,
                                            spell_level: Number(e.target.value) || 0
                                        })}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        min="0"
                                        max="9"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-white mb-2">Class</label>
                                    <input
                                        type="text"
                                        value={(action as SpellAction).class || ''}
                                        onChange={(e) => updateAction(category, index, {
                                            ...action,
                                            class: e.target.value
                                        })}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        placeholder="e.g., Wizard, Cleric"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-white mb-2">Casting Time</label>
                                    <input
                                        type="text"
                                        value={(action as SpellAction).casting_time || ''}
                                        onChange={(e) => updateAction(category, index, {
                                            ...action,
                                            casting_time: e.target.value
                                        })}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        placeholder="e.g., 1 action, 1 minute"
                                    />
                                </div>
                            </div>
                        )}

                        {/* Special Ability fields */}
                        {isSpecial && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-white mb-2">Action Required</label>
                                    <select
                                        value={(action as SpecialAbility).action_required || ''}
                                        onChange={(e) => updateAction(category, index, {
                                            ...action,
                                            action_required: e.target.value as SpecialAbility['action_required']
                                        })}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    >
                                        <option value="">Select action type</option>
                                        <option value="action">Action</option>
                                        <option value="bonus_action">Bonus Action</option>
                                        <option value="reaction">Reaction</option>
                                        <option value="none">No Action</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-white mb-2">Cost</label>
                                    <input
                                        type="text"
                                        value={(action as SpecialAbility).cost || ''}
                                        onChange={(e) => updateAction(category, index, {
                                            ...action,
                                            cost: e.target.value
                                        })}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        placeholder="e.g., 1 spell slot, Variable"
                                    />
                                </div>
                            </div>
                        )}

                        {/* Common fields */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Range</label>
                                <input
                                    type="text"
                                    value={action.range || ''}
                                    onChange={(e) => updateAction(category, index, { ...action, range: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="e.g., 30 ft, Touch, Self"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Duration</label>
                                <input
                                    type="text"
                                    value={action.duration || ''}
                                    onChange={(e) => updateAction(category, index, { ...action, duration: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="e.g., 1 minute, Instantaneous"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Save DC</label>
                                <input
                                    type="number"
                                    value={action.save_dc || ''}
                                    onChange={(e) => updateAction(category, index, {
                                        ...action,
                                        save_dc: e.target.value ? Number(e.target.value) : undefined
                                    })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    min="1"
                                />
                            </div>
                        </div>

                        {/* Trigger */}
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">Trigger</label>
                            <input
                                type="text"
                                value={action.trigger || ''}
                                onChange={(e) => updateAction(category, index, { ...action, trigger: e.target.value })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                placeholder="When this action can be used"
                            />
                        </div>

                        {/* Description */}
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">Description</label>
                            <textarea
                                value={action.description || ''}
                                onChange={(e) => updateAction(category, index, { ...action, description: e.target.value })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                rows={3}
                                placeholder="Describe what this action does"
                            />
                        </div>

                        {/* Effect */}
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">Effect</label>
                            <textarea
                                value={action.effect || ''}
                                onChange={(e) => updateAction(category, index, { ...action, effect: e.target.value })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                rows={2}
                                placeholder="Mechanical effect of this action"
                            />
                        </div>

                        {/* Spell Components */}
                        {isSpell && (
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Components</label>
                                {renderSpellComponents(
                                    (action as SpellAction).components,
                                    (components) => updateAction(category, index, { ...action, components })
                                )}
                            </div>
                        )}

                        {/* Concentration for spells */}
                        {isSpell && (
                            <div>
                                <label className="flex items-center space-x-2">
                                    <input
                                        type="checkbox"
                                        checked={(action as SpellAction).concentration || false}
                                        onChange={(e) => updateAction(category, index, {
                                            ...action,
                                            concentration: e.target.checked
                                        })}
                                        className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                                    />
                                    <span className="text-sm text-white">Requires Concentration</span>
                                </label>
                            </div>
                        )}

                        {/* Legacy for spells */}
                        {isSpell && (
                            <div>
                                <label className="flex items-center space-x-2">
                                    <input
                                        type="checkbox"
                                        checked={(action as SpellAction).legacy || false}
                                        onChange={(e) => updateAction(category, index, {
                                            ...action,
                                            legacy: e.target.checked
                                        })}
                                        className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                                    />
                                    <span className="text-sm text-white">Legacy Spell</span>
                                </label>
                            </div>
                        )}

                        {/* Uses */}
                        {action.uses && renderUsesEditor(
                            action.uses,
                            (uses) => updateAction(category, index, { ...action, uses })
                        )}

                        {/* Pool */}
                        {action.pool && renderPoolEditor(
                            action.pool,
                            (pool) => updateAction(category, index, { ...action, pool })
                        )}

                        {/* Add Uses/Pool buttons */}
                        <div className="flex space-x-2">
                            {!action.uses && (
                                <button
                                    type="button"
                                    onClick={() => updateAction(category, index, {
                                        ...action,
                                        uses: { maximum: 1, reset: 'long_rest' }
                                    })}
                                    className="flex items-center space-x-2 px-3 py-2 border border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400"
                                >
                                    <Plus className="w-4 h-4" />
                                    <span>Add Uses</span>
                                </button>
                            )}
                            {!action.pool && (
                                <button
                                    type="button"
                                    onClick={() => updateAction(category, index, {
                                        ...action,
                                        pool: { current: 0, maximum: 1, reset: 'long_rest' }
                                    })}
                                    className="flex items-center space-x-2 px-3 py-2 border border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400"
                                >
                                    <Plus className="w-4 h-4" />
                                    <span>Add Pool</span>
                                </button>
                            )}
                        </div>

                        {/* Sub-actions for regular actions */}
                        {category === 'actions' && 'sub_actions' in action && (
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Sub-Actions (Attacks)</label>
                                <div className="space-y-4">
                                    {(action as Action).sub_actions?.map((subAction, subIndex) => (
                                        <div key={subIndex}>
                                            <div className="flex items-center justify-between mb-2">
                                                <h4 className="text-sm font-medium text-white">Attack {subIndex + 1}</h4>
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        const updatedSubActions = (action as Action).sub_actions?.filter((_, i) => i !== subIndex) || [];
                                                        updateAction(category, index, {
                                                            ...action,
                                                            sub_actions: updatedSubActions
                                                        });
                                                    }}
                                                    className="text-red-400 hover:text-red-300 p-1"
                                                    title="Remove attack"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                            {renderWeaponAttackEditor(subAction, index, subIndex)}
                                        </div>
                                    ))}
                                    <button
                                        type="button"
                                        onClick={() => {
                                            const newAttack: WeaponAttack = {
                                                name: '',
                                                type: 'weapon_attack',
                                                range: '5 ft',
                                                attack_bonus: 0,
                                                damage: '1d6',
                                                damage_type: 'slashing'
                                            };
                                            const updatedSubActions = [...((action as Action).sub_actions || []), newAttack];
                                            updateAction(category, index, {
                                                ...action,
                                                sub_actions: updatedSubActions
                                            });
                                        }}
                                        className="w-full flex items-center justify-center space-x-2 px-4 py-2 border-2 border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400"
                                    >
                                        <Plus className="w-4 h-4" />
                                        <span>Add Attack</span>
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Options for actions */}
                        {category === 'actions' && 'options' in action && (
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Options</label>
                                <ArrayEditor
                                    items={(action as Action).options || []}
                                    onChange={(options) => updateAction(category, index, { ...action, options })}
                                    label="Options"
                                    itemSchema={{
                                        key: 'option',
                                        type: 'object',
                                        label: 'Option',
                                        required: false,
                                        children: [
                                            {
                                                key: 'name',
                                                type: 'string',
                                                label: 'Name',
                                                required: true
                                            },
                                            {
                                                key: 'type',
                                                type: 'string',
                                                label: 'Type',
                                                required: true
                                            },
                                            {
                                                key: 'effect',
                                                type: 'string',
                                                label: 'Effect',
                                                required: true
                                            },
                                            {
                                                key: 'trigger',
                                                type: 'string',
                                                label: 'Trigger',
                                                required: false
                                            }
                                        ]
                                    }}
                                />
                            </div>
                        )}

                        {/* Effects for actions */}
                        {category === 'actions' && 'effects' in action && (
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Effects</label>
                                <ArrayEditor
                                    items={(action as Action).effects || []}
                                    onChange={(effects) => updateAction(category, index, { ...action, effects })}
                                    label="Effects"
                                    itemSchema={{
                                        key: 'effect',
                                        type: 'object',
                                        label: 'Effect',
                                        required: false,
                                        children: [
                                            {
                                                key: 'name',
                                                type: 'string',
                                                label: 'Name',
                                                required: true
                                            },
                                            {
                                                key: 'cost',
                                                type: 'string',
                                                label: 'Cost',
                                                required: true
                                            },
                                            {
                                                key: 'effect',
                                                type: 'string',
                                                label: 'Effect',
                                                required: true
                                            }
                                        ]
                                    }}
                                />
                            </div>
                        )}

                        {/* Effects array for special abilities */}
                        {isSpecial && 'effects' in action && (
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Effects</label>
                                <ArrayEditor
                                    items={(action as SpecialAbility).effects || []}
                                    onChange={(effects) => updateAction(category, index, { ...action, effects })}
                                    label="Effects"
                                    itemSchema={{
                                        key: 'effect',
                                        type: 'string',
                                        label: 'Effect',
                                        required: false
                                    }}
                                />
                            </div>
                        )}

                        {/* Damage for special abilities */}
                        {isSpecial && (action as SpecialAbility).damage && (
                            <div className="border border-gray-600 rounded-md p-3">
                                <h4 className="text-sm font-medium text-white mb-3">Damage</h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-white mb-2">Base Damage</label>
                                        <input
                                            type="text"
                                            value={(action as SpecialAbility).damage?.base || ''}
                                            onChange={(e) => updateAction(category, index, {
                                                ...action,
                                                damage: {
                                                    ...(action as SpecialAbility).damage!,
                                                    base: e.target.value
                                                }
                                            })}
                                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                            placeholder="e.g., 2d8"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-white mb-2">Damage Type</label>
                                        <input
                                            type="text"
                                            value={(action as SpecialAbility).damage_type || ''}
                                            onChange={(e) => updateAction(category, index, {
                                                ...action,
                                                damage_type: e.target.value
                                            })}
                                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                            placeholder="e.g., radiant, fire"
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                                    <div>
                                        <label className="block text-sm font-medium text-white mb-2">Per Spell Level</label>
                                        <input
                                            type="text"
                                            value={(action as SpecialAbility).damage?.per_spell_level || ''}
                                            onChange={(e) => updateAction(category, index, {
                                                ...action,
                                                damage: {
                                                    ...(action as SpecialAbility).damage!,
                                                    per_spell_level: e.target.value
                                                }
                                            })}
                                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                            placeholder="e.g., +1d8"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-white mb-2">Maximum</label>
                                        <input
                                            type="text"
                                            value={(action as SpecialAbility).damage?.maximum || ''}
                                            onChange={(e) => updateAction(category, index, {
                                                ...action,
                                                damage: {
                                                    ...(action as SpecialAbility).damage!,
                                                    maximum: e.target.value
                                                }
                                            })}
                                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                            placeholder="e.g., 5d8"
                                        />
                                    </div>
                                </div>
                                <div className="mt-4">
                                    <label className="block text-sm font-medium text-white mb-2">Bonus vs Undead/Fiend</label>
                                    <input
                                        type="text"
                                        value={(action as SpecialAbility).damage?.vs_undead_fiend || ''}
                                        onChange={(e) => updateAction(category, index, {
                                            ...action,
                                            damage: {
                                                ...(action as SpecialAbility).damage!,
                                                vs_undead_fiend: e.target.value
                                            }
                                        })}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        placeholder="e.g., +1d8"
                                    />
                                </div>
                            </div>
                        )}

                        {/* Restrictions for special abilities */}
                        {isSpecial && (
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Restrictions</label>
                                <textarea
                                    value={(action as SpecialAbility).restrictions || ''}
                                    onChange={(e) => updateAction(category, index, {
                                        ...action,
                                        restrictions: e.target.value
                                    })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    rows={2}
                                    placeholder="Any restrictions on this ability"
                                />
                            </div>
                        )}
                    </div>
                )}
            </div>
        );
    };
    const renderTabContent = () => {
        const actions = data.character_actions.action_economy[activeTab];

        return (
            <div className="space-y-4">
                {actions.length > 0 ? (
                    actions.map((action, index) => renderActionEditor(action, activeTab, index))
                ) : (
                    <div className="text-center py-12 text-gray-400 border-2 border-dashed border-gray-600 rounded-md">
                        <div className="flex flex-col items-center space-y-2">
                            {activeTab === 'actions' && <Sword className="w-8 h-8" />}
                            {activeTab === 'bonus_actions' && <Zap className="w-8 h-8" />}
                            {activeTab === 'reactions' && <Shield className="w-8 h-8" />}
                            {activeTab === 'other_actions' && <Activity className="w-8 h-8" />}
                            {activeTab === 'special_abilities' && <Star className="w-8 h-8" />}
                            <p className="text-lg font-medium">No {activeTab.replace('_', ' ')} defined</p>
                            <p className="text-sm">Click "Add {activeTab.replace('_', ' ').slice(0, -1)}" to get started</p>
                        </div>
                    </div>
                )}

                <button
                    type="button"
                    onClick={() => addAction(activeTab)}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-3 border-2 border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400 transition-colors"
                >
                    <Plus className="w-5 h-5" />
                    <span>Add {activeTab.replace('_', ' ').slice(0, -1)}</span>
                </button>
            </div>
        );
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                    <Target className="w-6 h-6 text-purple-400" />
                    <h2 className="text-xl font-bold text-white">Action List Editor</h2>
                </div>
                <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                        <label className="text-sm text-gray-400">Attacks per Action:</label>
                        <input
                            type="number"
                            value={data.character_actions.attacks_per_action || 1}
                            onChange={(e) => updateData({
                                character_actions: {
                                    ...data.character_actions,
                                    attacks_per_action: Number(e.target.value) || 1
                                }
                            })}
                            className="w-16 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                            min="1"
                            max="4"
                        />
                    </div>
                </div>
            </div>

            {/* Validation Errors */}
            {validationErrors.length > 0 && (
                <div className="bg-red-900/20 border border-red-600 rounded-md p-4">
                    <div className="flex items-center space-x-2 mb-2">
                        <AlertCircle className="w-5 h-5 text-red-400" />
                        <h3 className="text-sm font-medium text-red-400">Validation Errors</h3>
                    </div>
                    <ul className="text-sm text-red-300 space-y-1">
                        {validationErrors.map((error, index) => (
                            <li key={index}>• {error.message}</li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Tab Navigation */}
            <div className="border-b border-gray-600">
                <nav className="flex space-x-8">
                    {[
                        { key: 'actions', label: 'Actions', icon: Sword, color: 'text-red-400' },
                        { key: 'bonus_actions', label: 'Bonus Actions', icon: Zap, color: 'text-orange-400' },
                        { key: 'reactions', label: 'Reactions', icon: Shield, color: 'text-green-400' },
                        { key: 'other_actions', label: 'Other Actions', icon: Activity, color: 'text-gray-400' },
                        { key: 'special_abilities', label: 'Special Abilities', icon: Star, color: 'text-yellow-400' }
                    ].map(({ key, label, icon: Icon, color }) => (
                        <button
                            key={key}
                            onClick={() => setActiveTab(key as typeof activeTab)}
                            className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === key
                                ? `border-purple-500 text-purple-400`
                                : `border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300`
                                }`}
                        >
                            <Icon className={`w-4 h-4 ${activeTab === key ? 'text-purple-400' : color}`} />
                            <span>{label}</span>
                            <span className="bg-gray-700 text-gray-300 px-2 py-1 rounded-full text-xs">
                                {data.character_actions.action_economy[key as keyof ActionEconomy].length}
                            </span>
                        </button>
                    ))}
                </nav>
            </div>

            {/* Tab Content */}
            {renderTabContent()}

            {/* Combat Actions Reference */}
            <div className="border-t border-gray-600 pt-6">
                <div className="flex items-center space-x-2 mb-4">
                    <Eye className="w-5 h-5 text-gray-400" />
                    <h3 className="text-lg font-semibold text-white">Combat Actions Reference</h3>
                </div>
                <div>
                    <label className="block text-sm font-medium text-white mb-2">Available Combat Actions</label>
                    <ArrayEditor
                        items={data.character_actions.combat_actions_reference || []}
                        onChange={(combat_actions_reference) => updateData({
                            character_actions: {
                                ...data.character_actions,
                                combat_actions_reference
                            }
                        })}
                        label="Combat Actions"
                        itemSchema={{
                            key: 'action',
                            type: 'string',
                            label: 'Action',
                            required: false
                        }}
                    />
                </div>
            </div>

            {/* Metadata */}
            <div className="border-t border-gray-600 pt-6">
                <div className="flex items-center space-x-2 mb-4">
                    <Clock className="w-5 h-5 text-gray-400" />
                    <h3 className="text-lg font-semibold text-white">Metadata</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Version</label>
                        <input
                            type="text"
                            value={data.metadata.version}
                            onChange={(e) => updateData({
                                metadata: {
                                    ...data.metadata,
                                    version: e.target.value
                                }
                            })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Last Updated</label>
                        <input
                            type="date"
                            value={data.metadata.last_updated}
                            onChange={(e) => updateData({
                                metadata: {
                                    ...data.metadata,
                                    last_updated: e.target.value
                                }
                            })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                    </div>
                </div>
                <div className="mt-4">
                    <label className="block text-sm font-medium text-white mb-2">Notes</label>
                    <ArrayEditor
                        items={data.metadata.notes}
                        onChange={(notes) => updateData({
                            metadata: {
                                ...data.metadata,
                                notes
                            }
                        })}
                        label="Notes"
                        itemSchema={{
                            key: 'note',
                            type: 'string',
                            label: 'Note',
                            required: false
                        }}
                    />
                </div>
            </div>
        </div>
    );
};