import React, { useState, useCallback, useMemo } from 'react';
import {
    Sparkles,
    BookOpen,
    Search,
    Filter,
    Plus,
    Trash2,
    ChevronDown,
    ChevronRight,
    AlertCircle,
    Copy
} from 'lucide-react';
import { ValidationError } from '../../services/knowledgeBaseApi';
import { ArrayEditor } from './ArrayEditor';

interface SpellComponents {
    verbal?: boolean;
    somatic?: boolean;
    material?: boolean | string;
}

interface SpellSave {
    type: 'STR' | 'DEX' | 'CON' | 'INT' | 'WIS' | 'CHA';
}

interface SpellRite {
    name: string;
    effect: string;
}

interface SpellEffect {
    name: string;
    cost: string | number;
    effect: string;
}

interface SpellSteedStats {
    size: string;
    type: string;
    alignment: string;
    ac: string;
    hp: string;
    speed: Record<string, string>;
    abilities: Record<string, number>;
    traits?: Record<string, string>;
    actions?: Record<string, string>;
    bonus_actions?: Record<string, string>;
}

interface Spell {
    name: string;
    level: number;
    school: string;
    casting_time: string;
    range: string;
    area?: string;
    components: SpellComponents;
    duration: string;
    concentration: boolean;
    ritual: boolean;
    description: string;
    higher_levels?: string;
    source: string;
    tags: string[];
    save?: SpellSave;
    legacy?: boolean;
    cantrip_scaling?: string;
    rites?: SpellRite[];
    effects?: SpellEffect[];
    steed_stats?: SpellSteedStats;
}

interface ClassSpells {
    cantrips?: Spell[];
    [key: string]: Spell[] | undefined; // For level-based spells like "1st_level", "2nd_level", etc.
}

interface SpellcastingClass {
    spells: ClassSpells;
}

interface SpellListData {
    spellcasting: Record<string, SpellcastingClass>;
    metadata: {
        version: string;
        last_updated: string;
        notes: string[];
    };
}

interface SpellListEditorProps {
    data: SpellListData;
    onChange: (data: SpellListData) => void;
    validationErrors?: ValidationError[];
}

const SPELL_SCHOOLS = [
    'Abjuration', 'Conjuration', 'Divination', 'Enchantment',
    'Evocation', 'Illusion', 'Necromancy', 'Transmutation'
];

const SPELL_TAGS = [
    'Buff', 'Debuff', 'Damage', 'Healing', 'Control', 'Utility',
    'Detection', 'Social', 'Summoning', 'Warding', 'Negation'
];

const SAVE_TYPES = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'];

export const SpellListEditor: React.FC<SpellListEditorProps> = ({
    data,
    onChange,
    validationErrors = []
}) => {
    const [activeClass, setActiveClass] = useState<string>('');
    const [activeLevel, setActiveLevel] = useState<string>('');
    const [searchTerm, setSearchTerm] = useState('');
    const [filterSchool, setFilterSchool] = useState('');
    const [filterTags, setFilterTags] = useState<string[]>([]);
    const [expandedSpells, setExpandedSpells] = useState<Set<string>>(new Set());
    const [showFilters, setShowFilters] = useState(false);

    // Initialize active class if none selected
    React.useEffect(() => {
        if (!activeClass && Object.keys(data.spellcasting).length > 0) {
            const firstClass = Object.keys(data.spellcasting)[0];
            setActiveClass(firstClass);
            
            const firstClassSpells = data.spellcasting[firstClass].spells;
            const levels = Object.keys(firstClassSpells);
            if (levels.length > 0) {
                setActiveLevel(levels[0]);
            }
        }
    }, [data.spellcasting, activeClass]);

    const updateData = useCallback((updates: Partial<SpellListData>) => {
        onChange({ ...data, ...updates });
    }, [data, onChange]);

    const updateSpellcasting = useCallback((spellcasting: Record<string, SpellcastingClass>) => {
        updateData({ spellcasting });
    }, [updateData]);

    const addClass = () => {
        const className = prompt('Enter class name:');
        if (className && !data.spellcasting[className.toLowerCase()]) {
            const newSpellcasting = {
                ...data.spellcasting,
                [className.toLowerCase()]: {
                    spells: {
                        cantrips: []
                    }
                }
            };
            updateSpellcasting(newSpellcasting);
            setActiveClass(className.toLowerCase());
            setActiveLevel('cantrips');
        }
    };

    const removeClass = (className: string) => {
        if (confirm(`Are you sure you want to remove the ${className} class and all its spells?`)) {
            const newSpellcasting = { ...data.spellcasting };
            delete newSpellcasting[className];
            updateSpellcasting(newSpellcasting);
            
            if (activeClass === className) {
                const remainingClasses = Object.keys(newSpellcasting);
                if (remainingClasses.length > 0) {
                    setActiveClass(remainingClasses[0]);
                    const firstClassSpells = newSpellcasting[remainingClasses[0]].spells;
                    const levels = Object.keys(firstClassSpells);
                    setActiveLevel(levels.length > 0 ? levels[0] : '');
                } else {
                    setActiveClass('');
                    setActiveLevel('');
                }
            }
        }
    };

    const addSpellLevel = (className: string) => {
        const levelName = prompt('Enter spell level (e.g., "1st_level", "2nd_level", etc.):');
        if (levelName && !data.spellcasting[className].spells[levelName]) {
            const newSpellcasting = {
                ...data.spellcasting,
                [className]: {
                    ...data.spellcasting[className],
                    spells: {
                        ...data.spellcasting[className].spells,
                        [levelName]: []
                    }
                }
            };
            updateSpellcasting(newSpellcasting);
            setActiveLevel(levelName);
        }
    };

    const removeSpellLevel = (className: string, levelName: string) => {
        if (confirm(`Are you sure you want to remove ${levelName} and all its spells?`)) {
            const newSpells = { ...data.spellcasting[className].spells };
            delete newSpells[levelName];
            
            const newSpellcasting = {
                ...data.spellcasting,
                [className]: {
                    ...data.spellcasting[className],
                    spells: newSpells
                }
            };
            updateSpellcasting(newSpellcasting);
            
            if (activeLevel === levelName) {
                const remainingLevels = Object.keys(newSpells);
                setActiveLevel(remainingLevels.length > 0 ? remainingLevels[0] : '');
            }
        }
    };

    const addSpell = () => {
        if (!activeClass || !activeLevel) return;

        const newSpell: Spell = {
            name: '',
            level: activeLevel === 'cantrips' ? 0 : parseInt(activeLevel.split('_')[0]) || 1,
            school: 'Evocation',
            casting_time: '1 action',
            range: 'Touch',
            components: {
                verbal: false,
                somatic: false,
                material: false
            },
            duration: 'Instantaneous',
            concentration: false,
            ritual: false,
            description: '',
            source: '',
            tags: []
        };

        const currentSpells = data.spellcasting[activeClass].spells[activeLevel] || [];
        const newSpells = [...currentSpells, newSpell];

        const newSpellcasting = {
            ...data.spellcasting,
            [activeClass]: {
                ...data.spellcasting[activeClass],
                spells: {
                    ...data.spellcasting[activeClass].spells,
                    [activeLevel]: newSpells
                }
            }
        };

        updateSpellcasting(newSpellcasting);
    };

    const updateSpell = (spellIndex: number, updatedSpell: Spell) => {
        if (!activeClass || !activeLevel) return;

        const currentSpells = [...(data.spellcasting[activeClass].spells[activeLevel] || [])];
        currentSpells[spellIndex] = updatedSpell;

        const newSpellcasting = {
            ...data.spellcasting,
            [activeClass]: {
                ...data.spellcasting[activeClass],
                spells: {
                    ...data.spellcasting[activeClass].spells,
                    [activeLevel]: currentSpells
                }
            }
        };

        updateSpellcasting(newSpellcasting);
    };

    const removeSpell = (spellIndex: number) => {
        if (!activeClass || !activeLevel) return;

        const currentSpells = data.spellcasting[activeClass].spells[activeLevel] || [];
        const newSpells = currentSpells.filter((_, index) => index !== spellIndex);

        const newSpellcasting = {
            ...data.spellcasting,
            [activeClass]: {
                ...data.spellcasting[activeClass],
                spells: {
                    ...data.spellcasting[activeClass].spells,
                    [activeLevel]: newSpells
                }
            }
        };

        updateSpellcasting(newSpellcasting);
    };

    const duplicateSpell = (spellIndex: number) => {
        if (!activeClass || !activeLevel) return;

        const currentSpells = data.spellcasting[activeClass].spells[activeLevel] || [];
        const spellToDuplicate = currentSpells[spellIndex];
        const duplicatedSpell = {
            ...spellToDuplicate,
            name: `${spellToDuplicate.name} (Copy)`
        };

        const newSpells = [...currentSpells, duplicatedSpell];

        const newSpellcasting = {
            ...data.spellcasting,
            [activeClass]: {
                ...data.spellcasting[activeClass],
                spells: {
                    ...data.spellcasting[activeClass].spells,
                    [activeLevel]: newSpells
                }
            }
        };

        updateSpellcasting(newSpellcasting);
    };

    const toggleSpellExpansion = (spellKey: string) => {
        const newExpanded = new Set(expandedSpells);
        if (newExpanded.has(spellKey)) {
            newExpanded.delete(spellKey);
        } else {
            newExpanded.add(spellKey);
        }
        setExpandedSpells(newExpanded);
    };

    const toggleFilterTag = (tag: string) => {
        setFilterTags(prev => 
            prev.includes(tag) 
                ? prev.filter(t => t !== tag)
                : [...prev, tag]
        );
    };

    const filteredSpells = useMemo(() => {
        if (!activeClass || !activeLevel) return [];

        const spells = data.spellcasting[activeClass]?.spells[activeLevel] || [];
        
        return spells.filter(spell => {
            const matchesSearch = !searchTerm || 
                spell.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                spell.description.toLowerCase().includes(searchTerm.toLowerCase());
            
            const matchesSchool = !filterSchool || spell.school === filterSchool;
            
            const matchesTags = filterTags.length === 0 || 
                filterTags.some(tag => spell.tags.includes(tag));
            
            return matchesSearch && matchesSchool && matchesTags;
        });
    }, [data.spellcasting, activeClass, activeLevel, searchTerm, filterSchool, filterTags]);

    const renderSpellComponents = (components: SpellComponents, onUpdate: (components: SpellComponents) => void) => (
        <div className="border border-gray-600 rounded-md p-3">
            <h4 className="text-sm font-medium text-white mb-3">Components</h4>
            <div className="space-y-3">
                <div className="flex items-center space-x-4">
                    <label className="flex items-center space-x-2">
                        <input
                            type="checkbox"
                            checked={components.verbal || false}
                            onChange={(e) => onUpdate({ ...components, verbal: e.target.checked })}
                            className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="text-sm text-white">Verbal (V)</span>
                    </label>
                    <label className="flex items-center space-x-2">
                        <input
                            type="checkbox"
                            checked={components.somatic || false}
                            onChange={(e) => onUpdate({ ...components, somatic: e.target.checked })}
                            className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="text-sm text-white">Somatic (S)</span>
                    </label>
                    <label className="flex items-center space-x-2">
                        <input
                            type="checkbox"
                            checked={!!components.material}
                            onChange={(e) => onUpdate({ 
                                ...components, 
                                material: e.target.checked ? true : false 
                            })}
                            className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="text-sm text-white">Material (M)</span>
                    </label>
                </div>
                {components.material && (
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Material Component</label>
                        <input
                            type="text"
                            value={typeof components.material === 'string' ? components.material : ''}
                            onChange={(e) => onUpdate({ 
                                ...components, 
                                material: e.target.value || true 
                            })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="Describe the material component"
                        />
                    </div>
                )}
            </div>
        </div>
    );

    const renderSpellEditor = (spell: Spell, index: number) => {
        const spellKey = `${activeClass}-${activeLevel}-${index}`;
        const isExpanded = expandedSpells.has(spellKey);

        return (
            <div key={index} className="border border-gray-600 rounded-md">
                <div className="flex items-center justify-between p-3 bg-gray-750">
                    <div className="flex items-center space-x-2">
                        <button
                            type="button"
                            onClick={() => toggleSpellExpansion(spellKey)}
                            className="flex items-center space-x-2"
                        >
                            {isExpanded ? (
                                <ChevronDown className="w-4 h-4 text-gray-400" />
                            ) : (
                                <ChevronRight className="w-4 h-4 text-gray-400" />
                            )}
                            <Sparkles className="w-4 h-4 text-blue-400" />
                            <span className="font-medium text-white">
                                {spell.name || `Unnamed Spell ${index + 1}`}
                            </span>
                        </button>
                        {spell.concentration && (
                            <span className="text-xs bg-yellow-600 text-yellow-100 px-2 py-1 rounded">
                                Concentration
                            </span>
                        )}
                        {spell.ritual && (
                            <span className="text-xs bg-blue-600 text-blue-100 px-2 py-1 rounded">
                                Ritual
                            </span>
                        )}
                        {spell.legacy && (
                            <span className="text-xs bg-orange-600 text-orange-100 px-2 py-1 rounded">
                                Legacy
                            </span>
                        )}
                    </div>
                    <div className="flex items-center space-x-2">
                        <button
                            type="button"
                            onClick={() => duplicateSpell(index)}
                            className="text-gray-400 hover:text-white p-1"
                            title="Duplicate spell"
                        >
                            <Copy className="w-4 h-4" />
                        </button>
                        <button
                            type="button"
                            onClick={() => removeSpell(index)}
                            className="text-red-400 hover:text-red-300 p-1"
                            title="Remove spell"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {isExpanded && (
                    <div className="p-4 space-y-4 border-t border-gray-600">
                        {/* Basic Information */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">
                                    Spell Name <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={spell.name}
                                    onChange={(e) => updateSpell(index, { ...spell, name: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="Enter spell name"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">School</label>
                                <select
                                    value={spell.school}
                                    onChange={(e) => updateSpell(index, { ...spell, school: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                >
                                    {SPELL_SCHOOLS.map(school => (
                                        <option key={school} value={school}>{school}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Level</label>
                                <input
                                    type="number"
                                    value={spell.level}
                                    onChange={(e) => updateSpell(index, { ...spell, level: Number(e.target.value) || 0 })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    min="0"
                                    max="9"
                                />
                            </div>
                        </div>

                        {/* Casting Details */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Casting Time</label>
                                <input
                                    type="text"
                                    value={spell.casting_time}
                                    onChange={(e) => updateSpell(index, { ...spell, casting_time: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="e.g., 1 action"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Range</label>
                                <input
                                    type="text"
                                    value={spell.range}
                                    onChange={(e) => updateSpell(index, { ...spell, range: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="e.g., 60 feet"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Duration</label>
                                <input
                                    type="text"
                                    value={spell.duration}
                                    onChange={(e) => updateSpell(index, { ...spell, duration: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="e.g., Instantaneous"
                                />
                            </div>
                        </div>

                        {/* Area of Effect */}
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">Area of Effect</label>
                            <input
                                type="text"
                                value={spell.area || ''}
                                onChange={(e) => updateSpell(index, { ...spell, area: e.target.value || undefined })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                placeholder="e.g., 20-foot radius"
                            />
                        </div>

                        {/* Components */}
                        {renderSpellComponents(spell.components, (components) => 
                            updateSpell(index, { ...spell, components })
                        )}

                        {/* Flags */}
                        <div className="flex items-center space-x-6">
                            <label className="flex items-center space-x-2">
                                <input
                                    type="checkbox"
                                    checked={spell.concentration}
                                    onChange={(e) => updateSpell(index, { ...spell, concentration: e.target.checked })}
                                    className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                                />
                                <span className="text-sm text-white">Concentration</span>
                            </label>
                            <label className="flex items-center space-x-2">
                                <input
                                    type="checkbox"
                                    checked={spell.ritual}
                                    onChange={(e) => updateSpell(index, { ...spell, ritual: e.target.checked })}
                                    className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                                />
                                <span className="text-sm text-white">Ritual</span>
                            </label>
                            <label className="flex items-center space-x-2">
                                <input
                                    type="checkbox"
                                    checked={spell.legacy || false}
                                    onChange={(e) => updateSpell(index, { ...spell, legacy: e.target.checked || undefined })}
                                    className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                                />
                                <span className="text-sm text-white">Legacy</span>
                            </label>
                        </div>

                        {/* Save */}
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">Saving Throw</label>
                            <div className="flex items-center space-x-2">
                                <select
                                    value={spell.save?.type || ''}
                                    onChange={(e) => updateSpell(index, { 
                                        ...spell, 
                                        save: e.target.value ? { type: e.target.value as any } : undefined 
                                    })}
                                    className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                >
                                    <option value="">No Save</option>
                                    {SAVE_TYPES.map(save => (
                                        <option key={save} value={save}>{save}</option>
                                    ))}
                                </select>
                                {spell.save && (
                                    <span className="text-sm text-gray-400">saving throw</span>
                                )}
                            </div>
                        </div>

                        {/* Description */}
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">
                                Description <span className="text-red-400">*</span>
                            </label>
                            <textarea
                                value={spell.description}
                                onChange={(e) => updateSpell(index, { ...spell, description: e.target.value })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                rows={4}
                                placeholder="Enter spell description"
                            />
                        </div>

                        {/* Higher Levels */}
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">At Higher Levels</label>
                            <textarea
                                value={spell.higher_levels || ''}
                                onChange={(e) => updateSpell(index, { ...spell, higher_levels: e.target.value || undefined })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                rows={2}
                                placeholder="Describe effects when cast at higher levels"
                            />
                        </div>

                        {/* Cantrip Scaling */}
                        {spell.level === 0 && (
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Cantrip Scaling</label>
                                <textarea
                                    value={spell.cantrip_scaling || ''}
                                    onChange={(e) => updateSpell(index, { ...spell, cantrip_scaling: e.target.value || undefined })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    rows={2}
                                    placeholder="Describe how the cantrip scales with character level"
                                />
                            </div>
                        )}

                        {/* Source */}
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">Source</label>
                            <input
                                type="text"
                                value={spell.source}
                                onChange={(e) => updateSpell(index, { ...spell, source: e.target.value })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                placeholder="e.g., Player's Handbook, pg. 123"
                            />
                        </div>

                        {/* Tags */}
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">Tags</label>
                            <ArrayEditor
                                items={spell.tags}
                                onChange={(tags) => updateSpell(index, { ...spell, tags })}
                                label="Tags"
                                itemSchema={{
                                    key: 'tag',
                                    type: 'string',
                                    label: 'Tag',
                                    required: false,
                                    enum: SPELL_TAGS
                                }}
                            />
                        </div>

                        {/* Special Sections */}
                        {spell.rites && spell.rites.length > 0 && (
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Rites</label>
                                <ArrayEditor
                                    items={spell.rites}
                                    onChange={(rites) => updateSpell(index, { ...spell, rites })}
                                    label="Rites"
                                    itemSchema={{
                                        key: 'rite',
                                        type: 'object',
                                        label: 'Rite',
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
                        )}

                        {spell.effects && spell.effects.length > 0 && (
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Effects</label>
                                <ArrayEditor
                                    items={spell.effects}
                                    onChange={(effects) => updateSpell(index, { ...spell, effects })}
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

                        {/* Add Special Sections */}
                        <div className="flex items-center space-x-2">
                            {!spell.rites && (
                                <button
                                    type="button"
                                    onClick={() => updateSpell(index, { ...spell, rites: [] })}
                                    className="flex items-center space-x-2 px-3 py-2 border border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400"
                                >
                                    <Plus className="w-4 h-4" />
                                    <span>Add Rites</span>
                                </button>
                            )}
                            {!spell.effects && (
                                <button
                                    type="button"
                                    onClick={() => updateSpell(index, { ...spell, effects: [] })}
                                    className="flex items-center space-x-2 px-3 py-2 border border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400"
                                >
                                    <Plus className="w-4 h-4" />
                                    <span>Add Effects</span>
                                </button>
                            )}
                        </div>
                    </div>
                )}
            </div>
        );
    };

    if (Object.keys(data.spellcasting).length === 0) {
        return (
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                        <Sparkles className="w-5 h-5 text-blue-400" />
                        <span>Spell List Editor</span>
                    </h2>
                </div>

                <div className="text-center py-12 border-2 border-dashed border-gray-600 rounded-lg">
                    <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-white mb-2">No Spellcasting Classes</h3>
                    <p className="text-gray-400 mb-4">Add a spellcasting class to start managing spells</p>
                    <button
                        onClick={addClass}
                        className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 mx-auto"
                    >
                        <Plus className="w-4 h-4" />
                        <span>Add Class</span>
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                    <Sparkles className="w-5 h-5 text-blue-400" />
                    <span>Spell List Editor</span>
                </h2>
                <button
                    onClick={addClass}
                    className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                >
                    <Plus className="w-4 h-4" />
                    <span>Add Class</span>
                </button>
            </div>

            {/* Class Tabs */}
            <div className="border-b border-gray-600">
                <div className="flex space-x-1 overflow-x-auto">
                    {Object.keys(data.spellcasting).map(className => (
                        <div key={className} className="flex items-center">
                            <button
                                onClick={() => {
                                    setActiveClass(className);
                                    const levels = Object.keys(data.spellcasting[className].spells);
                                    setActiveLevel(levels.length > 0 ? levels[0] : '');
                                }}
                                className={`px-4 py-2 text-sm font-medium capitalize whitespace-nowrap ${
                                    activeClass === className
                                        ? 'text-purple-400 border-b-2 border-purple-400'
                                        : 'text-gray-400 hover:text-white'
                                }`}
                            >
                                {className}
                            </button>
                            <button
                                onClick={() => removeClass(className)}
                                className="ml-1 text-red-400 hover:text-red-300 p-1"
                                title={`Remove ${className} class`}
                            >
                                <Trash2 className="w-3 h-3" />
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {activeClass && (
                <>
                    {/* Level Tabs */}
                    <div className="border-b border-gray-600">
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex space-x-1 overflow-x-auto">
                                {Object.keys(data.spellcasting[activeClass].spells).map(levelName => (
                                    <div key={levelName} className="flex items-center">
                                        <button
                                            onClick={() => setActiveLevel(levelName)}
                                            className={`px-3 py-1 text-sm font-medium capitalize whitespace-nowrap ${
                                                activeLevel === levelName
                                                    ? 'text-blue-400 border-b-2 border-blue-400'
                                                    : 'text-gray-400 hover:text-white'
                                            }`}
                                        >
                                            {levelName.replace('_', ' ')}
                                        </button>
                                        <button
                                            onClick={() => removeSpellLevel(activeClass, levelName)}
                                            className="ml-1 text-red-400 hover:text-red-300 p-1"
                                            title={`Remove ${levelName}`}
                                        >
                                            <Trash2 className="w-3 h-3" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                            <button
                                onClick={() => addSpellLevel(activeClass)}
                                className="flex items-center space-x-1 px-2 py-1 text-sm text-gray-400 hover:text-white"
                            >
                                <Plus className="w-3 h-3" />
                                <span>Add Level</span>
                            </button>
                        </div>
                    </div>

                    {activeLevel && (
                        <>
                            {/* Search and Filters */}
                            <div className="space-y-4">
                                <div className="flex items-center space-x-4">
                                    <div className="flex-1 relative">
                                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                                        <input
                                            type="text"
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                            className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                            placeholder="Search spells..."
                                        />
                                    </div>
                                    <button
                                        onClick={() => setShowFilters(!showFilters)}
                                        className={`flex items-center space-x-2 px-3 py-2 rounded-md ${
                                            showFilters || filterSchool || filterTags.length > 0
                                                ? 'bg-purple-600 text-white'
                                                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                        }`}
                                    >
                                        <Filter className="w-4 h-4" />
                                        <span>Filters</span>
                                    </button>
                                    <button
                                        onClick={addSpell}
                                        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                                    >
                                        <Plus className="w-4 h-4" />
                                        <span>Add Spell</span>
                                    </button>
                                </div>

                                {showFilters && (
                                    <div className="bg-gray-750 border border-gray-600 rounded-md p-4 space-y-4">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <label className="block text-sm font-medium text-white mb-2">School</label>
                                                <select
                                                    value={filterSchool}
                                                    onChange={(e) => setFilterSchool(e.target.value)}
                                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                                >
                                                    <option value="">All Schools</option>
                                                    {SPELL_SCHOOLS.map(school => (
                                                        <option key={school} value={school}>{school}</option>
                                                    ))}
                                                </select>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-white mb-2">Tags</label>
                                                <div className="flex flex-wrap gap-2">
                                                    {SPELL_TAGS.map(tag => (
                                                        <button
                                                            key={tag}
                                                            onClick={() => toggleFilterTag(tag)}
                                                            className={`px-2 py-1 text-xs rounded ${
                                                                filterTags.includes(tag)
                                                                    ? 'bg-purple-600 text-white'
                                                                    : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                                                            }`}
                                                        >
                                                            {tag}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <button
                                                onClick={() => {
                                                    setFilterSchool('');
                                                    setFilterTags([]);
                                                }}
                                                className="text-sm text-gray-400 hover:text-white"
                                            >
                                                Clear Filters
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Spell List */}
                            <div className="space-y-4">
                                {filteredSpells.length > 0 ? (
                                    <>
                                        <div className="flex items-center justify-between">
                                            <p className="text-sm text-gray-400">
                                                {filteredSpells.length} spell{filteredSpells.length !== 1 ? 's' : ''} 
                                                {searchTerm || filterSchool || filterTags.length > 0 ? ' (filtered)' : ''}
                                            </p>
                                        </div>
                                        {filteredSpells.map((spell) => {
                                            // Find the actual index in the unfiltered array
                                            const actualIndex = (data.spellcasting[activeClass]?.spells[activeLevel] || [])
                                                .findIndex(s => s === spell);
                                            return renderSpellEditor(spell, actualIndex);
                                        })}
                                    </>
                                ) : (
                                    <div className="text-center py-12 border-2 border-dashed border-gray-600 rounded-lg">
                                        <Sparkles className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                                        <h3 className="text-lg font-medium text-white mb-2">
                                            {searchTerm || filterSchool || filterTags.length > 0 
                                                ? 'No Matching Spells' 
                                                : 'No Spells'
                                            }
                                        </h3>
                                        <p className="text-gray-400 mb-4">
                                            {searchTerm || filterSchool || filterTags.length > 0
                                                ? 'Try adjusting your search or filters'
                                                : `Add spells to ${activeLevel.replace('_', ' ')}`
                                            }
                                        </p>
                                        {!(searchTerm || filterSchool || filterTags.length > 0) && (
                                            <button
                                                onClick={addSpell}
                                                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 mx-auto"
                                            >
                                                <Plus className="w-4 h-4" />
                                                <span>Add Spell</span>
                                            </button>
                                        )}
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </>
            )}

            {/* Validation Errors */}
            {validationErrors.length > 0 && (
                <div className="bg-red-900/20 border border-red-600 rounded-md p-4">
                    <div className="flex items-center space-x-2 mb-2">
                        <AlertCircle className="w-4 h-4 text-red-400" />
                        <h3 className="text-sm font-medium text-red-400">Validation Errors</h3>
                    </div>
                    <ul className="text-sm text-red-300 space-y-1">
                        {validationErrors.map((error, index) => (
                            <li key={index}>• {error.message}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};