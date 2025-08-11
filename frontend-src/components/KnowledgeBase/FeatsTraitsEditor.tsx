import React, { useState, useCallback } from 'react';
import {
    Zap,
    Star,
    Award,
    Calculator,
    Plus,
    Trash2,
    ChevronDown,
    ChevronRight,
    AlertCircle,
    Sword,
    Shield,
    Users
} from 'lucide-react';
import { ValidationError } from '../../services/knowledgeBaseApi';
import { ArrayEditor } from './ArrayEditor';

interface ClassFeature {
    name: string;
    source: string;
    description?: string;
    action_type?: 'action' | 'bonus_action' | 'reaction' | 'no_action';
    uses?: {
        current?: number;
        maximum: number;
        reset: 'short_rest' | 'long_rest' | 'dawn' | 'turn';
    };
    pool?: {
        current: number;
        maximum: number;
        reset: 'short_rest' | 'long_rest' | 'dawn';
    };
    range?: string;
    duration?: string;
    effect?: string;
    effects?: string[];
    passive?: boolean;
    level_gained?: number;
    trigger?: string;
    cost?: string;
    damage?: {
        base: string;
        scaling?: string;
        maximum?: string;
        bonus_vs?: string[];
    };
    save?: {
        type: string;
        dc: number;
    };
    ability?: string;
    spell_save_dc?: number;
    spell_attack_bonus?: number;
    focus?: string;
    preparation?: string;
    spell_slots?: {
        level: number;
        quantity: number;
    };
    spells_known?: number;
    proficiencies?: string[];
    special?: string;
    subclass?: boolean;
    channel_divinity?: {
        uses: {
            maximum: number;
            reset: 'short_rest' | 'long_rest';
        };
        save_dc: number;
    };
    options?: string[];
    timing?: string;
}

interface ClassFeatures {
    level: number;
    patron?: string;
    features: ClassFeature[];
}

interface SpeciesTrait {
    name: string;
    source: string;
    effects?: string[];
    effect?: string;
    range?: string;
    proficiencies?: string[];
}

interface SpeciesTraits {
    species: string;
    subrace?: string;
    traits: SpeciesTrait[];
}

interface Feat {
    name: string;
    source: string;
    from_class?: string;
    ability_increase?: {
        ability: string;
        amount: number;
        maximum: number;
    };
    spells?: Array<{
        name: string;
        level: number;
        legacy?: boolean;
        school?: string;
        uses?: {
            maximum: number;
            reset: 'short_rest' | 'long_rest';
        };
    }>;
    spellcasting_ability?: string;
    special?: string;
    action_type?: 'action' | 'bonus_action' | 'reaction' | 'no_action';
    uses?: {
        maximum: number;
        reset: 'short_rest' | 'long_rest';
    };
    trigger?: string;
    effect?: string;
    timing?: string;
}

interface CalculatedFeatures {
    total_level: number;
    proficiency_bonus: number;
    aura_ranges?: Record<string, string>;
    save_bonuses?: Record<string, number>;
    hp_bonus_per_level?: number;
}

interface FeatsAndTraitsData {
    features_and_traits: {
        class_features: Record<string, ClassFeatures>;
        species_traits: SpeciesTraits;
        feats: Feat[];
        calculated_features: CalculatedFeatures;
    };
    metadata: {
        version: string;
        last_updated: string;
        notes: string[];
    };
}

interface FeatsTraitsEditorProps {
    data: FeatsAndTraitsData;
    onChange: (data: FeatsAndTraitsData) => void;
    validationErrors?: ValidationError[];
}

export const FeatsTraitsEditor: React.FC<FeatsTraitsEditorProps> = ({
    data,
    onChange,
    validationErrors = []
}) => {
    const [activeTab, setActiveTab] = useState<'class_features' | 'species_traits' | 'feats' | 'calculated'>('class_features');
    const [expandedClasses, setExpandedClasses] = useState<Set<string>>(new Set());
    const [expandedFeatures, setExpandedFeatures] = useState<Set<string>>(new Set());



    const updateData = useCallback((updates: Partial<FeatsAndTraitsData>) => {
        onChange({ ...data, ...updates });
    }, [data, onChange]);

    const updateClassFeatures = useCallback((classFeatures: Record<string, ClassFeatures>) => {
        updateData({
            features_and_traits: {
                ...data.features_and_traits,
                class_features: classFeatures
            }
        });
    }, [data, updateData]);

    const updateSpeciesTraits = useCallback((speciesTraits: SpeciesTraits) => {
        updateData({
            features_and_traits: {
                ...data.features_and_traits,
                species_traits: speciesTraits
            }
        });
    }, [data, updateData]);

    const updateFeats = useCallback((feats: Feat[]) => {
        updateData({
            features_and_traits: {
                ...data.features_and_traits,
                feats: feats
            }
        });
    }, [data, updateData]);

    const updateCalculatedFeatures = useCallback((calculatedFeatures: CalculatedFeatures) => {
        updateData({
            features_and_traits: {
                ...data.features_and_traits,
                calculated_features: calculatedFeatures
            }
        });
    }, [data, updateData]);

    const toggleClassExpansion = (className: string) => {
        const newExpanded = new Set(expandedClasses);
        if (newExpanded.has(className)) {
            newExpanded.delete(className);
        } else {
            newExpanded.add(className);
        }
        setExpandedClasses(newExpanded);
    };

    const toggleFeatureExpansion = (featureKey: string) => {
        const newExpanded = new Set(expandedFeatures);
        if (newExpanded.has(featureKey)) {
            newExpanded.delete(featureKey);
        } else {
            newExpanded.add(featureKey);
        }
        setExpandedFeatures(newExpanded);
    };

    const addNewClass = () => {
        const className = prompt('Enter class name:');
        if (className && !data.features_and_traits.class_features[className.toLowerCase()]) {
            const newClassFeatures = {
                ...data.features_and_traits.class_features,
                [className.toLowerCase()]: {
                    level: 1,
                    features: []
                }
            };
            updateClassFeatures(newClassFeatures);
        }
    };

    const removeClass = (className: string) => {
        if (confirm(`Are you sure you want to remove the ${className} class?`)) {
            const newClassFeatures = { ...data.features_and_traits.class_features };
            delete newClassFeatures[className];
            updateClassFeatures(newClassFeatures);
        }
    };

    const addFeatureToClass = (className: string) => {
        const newFeature: ClassFeature = {
            name: '',
            source: '',
            description: ''
        };

        const updatedClass = {
            ...data.features_and_traits.class_features[className],
            features: [...data.features_and_traits.class_features[className].features, newFeature]
        };

        updateClassFeatures({
            ...data.features_and_traits.class_features,
            [className]: updatedClass
        });
    };

    const updateClassFeature = (className: string, featureIndex: number, updatedFeature: ClassFeature) => {
        const updatedFeatures = [...data.features_and_traits.class_features[className].features];
        updatedFeatures[featureIndex] = updatedFeature;

        const updatedClass = {
            ...data.features_and_traits.class_features[className],
            features: updatedFeatures
        };

        updateClassFeatures({
            ...data.features_and_traits.class_features,
            [className]: updatedClass
        });
    };

    const removeFeatureFromClass = (className: string, featureIndex: number) => {
        const updatedFeatures = data.features_and_traits.class_features[className].features.filter((_, i) => i !== featureIndex);

        const updatedClass = {
            ...data.features_and_traits.class_features[className],
            features: updatedFeatures
        };

        updateClassFeatures({
            ...data.features_and_traits.class_features,
            [className]: updatedClass
        });
    };

    const renderClassFeatureEditor = (feature: ClassFeature, className: string, featureIndex: number) => {
        const featureKey = `${className}-${featureIndex}`;
        const isExpanded = expandedFeatures.has(featureKey);

        return (
            <div key={featureIndex} className="border border-gray-600 rounded-md">
                <div className="flex items-center justify-between p-3 bg-gray-750">
                    <div className="flex items-center space-x-2">
                        <button
                            type="button"
                            onClick={() => toggleFeatureExpansion(featureKey)}
                            className="flex items-center space-x-2"
                        >
                            {isExpanded ? (
                                <ChevronDown className="w-4 h-4 text-gray-400" />
                            ) : (
                                <ChevronRight className="w-4 h-4 text-gray-400" />
                            )}
                            <Zap className="w-4 h-4 text-blue-400" />
                            <span className="font-medium text-white">
                                {feature.name || `Feature ${featureIndex + 1}`}
                            </span>
                        </button>
                    </div>
                    <button
                        type="button"
                        onClick={() => removeFeatureFromClass(className, featureIndex)}
                        className="text-red-400 hover:text-red-300 p-1"
                        title="Remove feature"
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
                                    Feature Name <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={feature.name}
                                    onChange={(e) => updateClassFeature(className, featureIndex, { ...feature, name: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="Enter feature name"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">
                                    Source <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={feature.source}
                                    onChange={(e) => updateClassFeature(className, featureIndex, { ...feature, source: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="e.g., PHB, pg. 84"
                                />
                            </div>
                        </div>

                        {/* Description */}
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">Description</label>
                            <textarea
                                value={feature.description || ''}
                                onChange={(e) => updateClassFeature(className, featureIndex, { ...feature, description: e.target.value })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                rows={3}
                                placeholder="Describe the feature"
                            />
                        </div>

                        {/* Action Type and Level */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Action Type</label>
                                <select
                                    value={feature.action_type || ''}
                                    onChange={(e) => updateClassFeature(className, featureIndex, {
                                        ...feature,
                                        action_type: e.target.value as ClassFeature['action_type']
                                    })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                >
                                    <option value="">Select action type</option>
                                    <option value="action">Action</option>
                                    <option value="bonus_action">Bonus Action</option>
                                    <option value="reaction">Reaction</option>
                                    <option value="no_action">No Action</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Level Gained</label>
                                <input
                                    type="number"
                                    value={feature.level_gained || ''}
                                    onChange={(e) => updateClassFeature(className, featureIndex, {
                                        ...feature,
                                        level_gained: e.target.value ? Number(e.target.value) : undefined
                                    })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    min="1"
                                    max="20"
                                />
                            </div>
                            <div>
                                <label className="flex items-center space-x-2 mt-6">
                                    <input
                                        type="checkbox"
                                        checked={feature.passive || false}
                                        onChange={(e) => updateClassFeature(className, featureIndex, { ...feature, passive: e.target.checked })}
                                        className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
                                    />
                                    <span className="text-sm text-white">Passive Feature</span>
                                </label>
                            </div>
                        </div>

                        {/* Range, Duration, Effect */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Range</label>
                                <input
                                    type="text"
                                    value={feature.range || ''}
                                    onChange={(e) => updateClassFeature(className, featureIndex, { ...feature, range: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="e.g., 30 ft, Touch, Self"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Duration</label>
                                <input
                                    type="text"
                                    value={feature.duration || ''}
                                    onChange={(e) => updateClassFeature(className, featureIndex, { ...feature, duration: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="e.g., 1 minute, Instantaneous"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">Trigger</label>
                                <input
                                    type="text"
                                    value={feature.trigger || ''}
                                    onChange={(e) => updateClassFeature(className, featureIndex, { ...feature, trigger: e.target.value })}
                                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="When this feature activates"
                                />
                            </div>
                        </div>

                        {/* Effect */}
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">Effect</label>
                            <textarea
                                value={feature.effect || ''}
                                onChange={(e) => updateClassFeature(className, featureIndex, { ...feature, effect: e.target.value })}
                                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                rows={2}
                                placeholder="What this feature does"
                            />
                        </div>

                        {/* Effects Array */}
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">Multiple Effects</label>
                            <ArrayEditor
                                items={feature.effects || []}
                                onChange={(effects) => updateClassFeature(className, featureIndex, { ...feature, effects })}
                                label="Effects"
                                itemSchema={{
                                    key: 'effect',
                                    type: 'string',
                                    label: 'Effect',
                                    required: false
                                }}
                            />
                        </div>

                        {/* Uses */}
                        {feature.uses && (
                            <div className="border border-gray-600 rounded-md p-3">
                                <h4 className="text-sm font-medium text-white mb-3">Uses</h4>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-white mb-2">Current</label>
                                        <input
                                            type="number"
                                            value={feature.uses.current || ''}
                                            onChange={(e) => updateClassFeature(className, featureIndex, {
                                                ...feature,
                                                uses: {
                                                    ...feature.uses!,
                                                    current: e.target.value ? Number(e.target.value) : undefined
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
                                            value={feature.uses.maximum}
                                            onChange={(e) => updateClassFeature(className, featureIndex, {
                                                ...feature,
                                                uses: {
                                                    ...feature.uses!,
                                                    maximum: Number(e.target.value) || 0
                                                }
                                            })}
                                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                            min="0"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-white mb-2">Reset</label>
                                        <select
                                            value={feature.uses.reset}
                                            onChange={(e) => updateClassFeature(className, featureIndex, {
                                                ...feature,
                                                uses: {
                                                    ...feature.uses!,
                                                    reset: e.target.value as 'short_rest' | 'long_rest' | 'dawn' | 'turn'
                                                }
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
                        )}

                        {/* Add Uses Button */}
                        {!feature.uses && (
                            <button
                                type="button"
                                onClick={() => updateClassFeature(className, featureIndex, {
                                    ...feature,
                                    uses: { maximum: 1, reset: 'long_rest' }
                                })}
                                className="flex items-center space-x-2 px-3 py-2 border border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400"
                            >
                                <Plus className="w-4 h-4" />
                                <span>Add Uses</span>
                            </button>
                        )}

                        {/* Remove Uses Button */}
                        {feature.uses && (
                            <button
                                type="button"
                                onClick={() => updateClassFeature(className, featureIndex, {
                                    ...feature,
                                    uses: undefined
                                })}
                                className="flex items-center space-x-2 px-3 py-2 text-red-400 hover:text-red-300"
                            >
                                <Trash2 className="w-4 h-4" />
                                <span>Remove Uses</span>
                            </button>
                        )}
                    </div>
                )}
            </div>
        );
    };

    const renderClassFeaturesTab = () => {
        const classFeatures = data?.features_and_traits?.class_features || {};
        
        return (
            <div className="space-y-6">
                {Object.entries(classFeatures).map(([className, classData]) => {
                    const isExpanded = expandedClasses.has(className);

                    return (
                    <div key={className} className="border border-gray-600 rounded-lg">
                        <div className="flex items-center justify-between p-4 bg-gray-750">
                            <div className="flex items-center space-x-3">
                                <button
                                    type="button"
                                    onClick={() => toggleClassExpansion(className)}
                                    className="flex items-center space-x-2"
                                >
                                    {isExpanded ? (
                                        <ChevronDown className="w-5 h-5 text-gray-400" />
                                    ) : (
                                        <ChevronRight className="w-5 h-5 text-gray-400" />
                                    )}
                                    <Sword className="w-5 h-5 text-green-400" />
                                    <span className="text-lg font-semibold text-white capitalize">
                                        {className}
                                    </span>
                                </button>
                                <span className="text-sm text-gray-400">
                                    Level {classData.level} • {classData.features.length} features
                                </span>
                            </div>
                            <div className="flex items-center space-x-2">
                                <input
                                    type="number"
                                    value={classData.level}
                                    onChange={(e) => {
                                        const updatedClass = {
                                            ...classData,
                                            level: Number(e.target.value) || 1
                                        };
                                        updateClassFeatures({
                                            ...data.features_and_traits.class_features,
                                            [className]: updatedClass
                                        });
                                    }}
                                    className="w-16 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    min="1"
                                    max="20"
                                />
                                <button
                                    type="button"
                                    onClick={() => removeClass(className)}
                                    className="text-red-400 hover:text-red-300 p-1"
                                    title="Remove class"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>

                        {isExpanded && (
                            <div className="p-4 space-y-4 border-t border-gray-600">
                                {/* Patron field for Warlock */}
                                {className.toLowerCase() === 'warlock' && (
                                    <div>
                                        <label className="block text-sm font-medium text-white mb-2">Patron</label>
                                        <input
                                            type="text"
                                            value={classData.patron || ''}
                                            onChange={(e) => {
                                                const updatedClass = {
                                                    ...classData,
                                                    patron: e.target.value
                                                };
                                                updateClassFeatures({
                                                    ...data.features_and_traits.class_features,
                                                    [className]: updatedClass
                                                });
                                            }}
                                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                            placeholder="e.g., The Hexblade"
                                        />
                                    </div>
                                )}

                                {/* Features */}
                                <div className="space-y-3">
                                    {classData.features.map((feature, index) =>
                                        renderClassFeatureEditor(feature, className, index)
                                    )}
                                </div>

                                {/* Add Feature Button */}
                                <button
                                    type="button"
                                    onClick={() => addFeatureToClass(className)}
                                    className="w-full flex items-center justify-center space-x-2 px-4 py-2 border-2 border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400 transition-colors"
                                >
                                    <Plus className="w-4 h-4" />
                                    <span>Add Feature</span>
                                </button>
                            </div>
                        )}
                    </div>
                );
            })}

            {/* Add Class Button */}
            <button
                type="button"
                onClick={addNewClass}
                className="w-full flex items-center justify-center space-x-2 px-4 py-3 border-2 border-dashed border-gray-600 rounded-lg text-gray-400 hover:border-green-500 hover:text-green-400 transition-colors"
            >
                <Plus className="w-5 h-5" />
                <span>Add Class</span>
            </button>
        </div>
    );
}

    const renderSpeciesTraitsTab = () => (
        <div className="space-y-6">
            {/* Species Information */}
            <div className="border border-gray-600 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-4">
                    <Users className="w-5 h-5 text-orange-400" />
                    <h3 className="text-lg font-semibold text-white">Species Information</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">
                            Species <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="text"
                            value={data?.features_and_traits?.species_traits?.species || ''}
                            onChange={(e) => updateSpeciesTraits({
                                ...data.features_and_traits.species_traits,
                                species: e.target.value
                            })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="e.g., Dwarf, Elf, Human"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Subrace</label>
                        <input
                            type="text"
                            value={data?.features_and_traits?.species_traits?.subrace || ''}
                            onChange={(e) => updateSpeciesTraits({
                                ...data.features_and_traits.species_traits,
                                subrace: e.target.value
                            })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="e.g., Mountain Dwarf, High Elf"
                        />
                    </div>
                </div>
            </div>

            {/* Species Traits */}
            <div className="border border-gray-600 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                        <Shield className="w-5 h-5 text-orange-400" />
                        <h3 className="text-lg font-semibold text-white">Species Traits</h3>
                    </div>
                    <button
                        type="button"
                        onClick={() => {
                            const newTrait: SpeciesTrait = {
                                name: '',
                                source: '',
                                effect: ''
                            };
                            updateSpeciesTraits({
                                ...data.features_and_traits.species_traits,
                                traits: [...data.features_and_traits.species_traits.traits, newTrait]
                            });
                        }}
                        className="flex items-center space-x-2 px-3 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-md transition-colors"
                    >
                        <Plus className="w-4 h-4" />
                        <span>Add Trait</span>
                    </button>
                </div>

                <div className="space-y-4">
                    {data.features_and_traits.species_traits.traits.map((trait, index) => (
                        <div key={index} className="border border-gray-600 rounded-md p-4">
                            <div className="flex items-center justify-between mb-3">
                                <h4 className="font-medium text-white">
                                    {trait.name || `Trait ${index + 1}`}
                                </h4>
                                <button
                                    type="button"
                                    onClick={() => {
                                        const updatedTraits = data.features_and_traits.species_traits.traits.filter((_, i) => i !== index);
                                        updateSpeciesTraits({
                                            ...data.features_and_traits.species_traits,
                                            traits: updatedTraits
                                        });
                                    }}
                                    className="text-red-400 hover:text-red-300 p-1"
                                    title="Remove trait"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label className="block text-sm font-medium text-white mb-2">
                                        Trait Name <span className="text-red-400">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        value={trait.name}
                                        onChange={(e) => {
                                            const updatedTraits = [...data.features_and_traits.species_traits.traits];
                                            updatedTraits[index] = { ...trait, name: e.target.value };
                                            updateSpeciesTraits({
                                                ...data.features_and_traits.species_traits,
                                                traits: updatedTraits
                                            });
                                        }}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        placeholder="e.g., Darkvision"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-white mb-2">
                                        Source <span className="text-red-400">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        value={trait.source}
                                        onChange={(e) => {
                                            const updatedTraits = [...data.features_and_traits.species_traits.traits];
                                            updatedTraits[index] = { ...trait, source: e.target.value };
                                            updateSpeciesTraits({
                                                ...data.features_and_traits.species_traits,
                                                traits: updatedTraits
                                            });
                                        }}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        placeholder="e.g., BR, pg. 20"
                                    />
                                </div>
                            </div>

                            {trait.range && (
                                <div className="mb-4">
                                    <label className="block text-sm font-medium text-white mb-2">Range</label>
                                    <input
                                        type="text"
                                        value={trait.range}
                                        onChange={(e) => {
                                            const updatedTraits = [...data.features_and_traits.species_traits.traits];
                                            updatedTraits[index] = { ...trait, range: e.target.value };
                                            updateSpeciesTraits({
                                                ...data.features_and_traits.species_traits,
                                                traits: updatedTraits
                                            });
                                        }}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        placeholder="e.g., 60 ft"
                                    />
                                </div>
                            )}

                            {trait.effect && (
                                <div className="mb-4">
                                    <label className="block text-sm font-medium text-white mb-2">Effect</label>
                                    <textarea
                                        value={trait.effect}
                                        onChange={(e) => {
                                            const updatedTraits = [...data.features_and_traits.species_traits.traits];
                                            updatedTraits[index] = { ...trait, effect: e.target.value };
                                            updateSpeciesTraits({
                                                ...data.features_and_traits.species_traits,
                                                traits: updatedTraits
                                            });
                                        }}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        rows={2}
                                        placeholder="Describe what this trait does"
                                    />
                                </div>
                            )}

                            {trait.effects && (
                                <div className="mb-4">
                                    <label className="block text-sm font-medium text-white mb-2">Multiple Effects</label>
                                    <ArrayEditor
                                        items={trait.effects}
                                        onChange={(effects) => {
                                            const updatedTraits = [...data.features_and_traits.species_traits.traits];
                                            updatedTraits[index] = { ...trait, effects };
                                            updateSpeciesTraits({
                                                ...data.features_and_traits.species_traits,
                                                traits: updatedTraits
                                            });
                                        }}
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

                            {trait.proficiencies && (
                                <div>
                                    <label className="block text-sm font-medium text-white mb-2">Proficiencies</label>
                                    <ArrayEditor
                                        items={trait.proficiencies}
                                        onChange={(proficiencies) => {
                                            const updatedTraits = [...data.features_and_traits.species_traits.traits];
                                            updatedTraits[index] = { ...trait, proficiencies };
                                            updateSpeciesTraits({
                                                ...data.features_and_traits.species_traits,
                                                traits: updatedTraits
                                            });
                                        }}
                                        label="Proficiencies"
                                        itemSchema={{
                                            key: 'proficiency',
                                            type: 'string',
                                            label: 'Proficiency',
                                            required: false
                                        }}
                                    />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );

    const renderFeatsTab = () => (
        <div className="space-y-6">
            <div className="border border-gray-600 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                        <Award className="w-5 h-5 text-yellow-400" />
                        <h3 className="text-lg font-semibold text-white">Feats</h3>
                    </div>
                    <button
                        type="button"
                        onClick={() => {
                            const newFeat: Feat = {
                                name: '',
                                source: ''
                            };
                            updateFeats([...data.features_and_traits.feats, newFeat]);
                        }}
                        className="flex items-center space-x-2 px-3 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-md transition-colors"
                    >
                        <Plus className="w-4 h-4" />
                        <span>Add Feat</span>
                    </button>
                </div>

                <div className="space-y-4">
                    {data.features_and_traits.feats.map((feat, index) => (
                        <div key={index} className="border border-gray-600 rounded-md p-4">
                            <div className="flex items-center justify-between mb-3">
                                <h4 className="font-medium text-white">
                                    {feat.name || `Feat ${index + 1}`}
                                </h4>
                                <button
                                    type="button"
                                    onClick={() => {
                                        const updatedFeats = data.features_and_traits.feats.filter((_, i) => i !== index);
                                        updateFeats(updatedFeats);
                                    }}
                                    className="text-red-400 hover:text-red-300 p-1"
                                    title="Remove feat"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label className="block text-sm font-medium text-white mb-2">
                                        Feat Name <span className="text-red-400">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        value={feat.name}
                                        onChange={(e) => {
                                            const updatedFeats = [...data.features_and_traits.feats];
                                            updatedFeats[index] = { ...feat, name: e.target.value };
                                            updateFeats(updatedFeats);
                                        }}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        placeholder="e.g., Lucky, Fey Touched"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-white mb-2">
                                        Source <span className="text-red-400">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        value={feat.source}
                                        onChange={(e) => {
                                            const updatedFeats = [...data.features_and_traits.feats];
                                            updatedFeats[index] = { ...feat, source: e.target.value };
                                            updateFeats(updatedFeats);
                                        }}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        placeholder="e.g., PHB, pg. 167"
                                    />
                                </div>
                            </div>

                            {/* Additional feat fields can be added here similar to the pattern above */}
                            {feat.effect && (
                                <div className="mb-4">
                                    <label className="block text-sm font-medium text-white mb-2">Effect</label>
                                    <textarea
                                        value={feat.effect}
                                        onChange={(e) => {
                                            const updatedFeats = [...data.features_and_traits.feats];
                                            updatedFeats[index] = { ...feat, effect: e.target.value };
                                            updateFeats(updatedFeats);
                                        }}
                                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        rows={3}
                                        placeholder="Describe what this feat does"
                                    />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );

    const renderCalculatedFeaturesTab = () => (
        <div className="space-y-6">
            <div className="border border-gray-600 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-4">
                    <Calculator className="w-5 h-5 text-purple-400" />
                    <h3 className="text-lg font-semibold text-white">Calculated Features</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Total Level</label>
                        <input
                            type="number"
                            value={data.features_and_traits.calculated_features.total_level}
                            onChange={(e) => updateCalculatedFeatures({
                                ...data.features_and_traits.calculated_features,
                                total_level: Number(e.target.value) || 0
                            })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                            min="1"
                            max="20"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Proficiency Bonus</label>
                        <input
                            type="number"
                            value={data.features_and_traits.calculated_features.proficiency_bonus}
                            onChange={(e) => updateCalculatedFeatures({
                                ...data.features_and_traits.calculated_features,
                                proficiency_bonus: Number(e.target.value) || 0
                            })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                            min="2"
                            max="6"
                        />
                    </div>
                </div>

                {data.features_and_traits.calculated_features.hp_bonus_per_level !== undefined && (
                    <div className="mt-4">
                        <label className="block text-sm font-medium text-white mb-2">HP Bonus Per Level</label>
                        <input
                            type="number"
                            value={data.features_and_traits.calculated_features.hp_bonus_per_level}
                            onChange={(e) => updateCalculatedFeatures({
                                ...data.features_and_traits.calculated_features,
                                hp_bonus_per_level: Number(e.target.value) || 0
                            })}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                            min="0"
                        />
                    </div>
                )}
            </div>
        </div>
    )

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                    <Star className="w-6 h-6 text-purple-400" />
                    <h2 className="text-xl font-bold text-white">Feats & Traits Editor</h2>
                </div>
                {validationErrors.length > 0 && (
                    <div className="flex items-center space-x-2 text-red-400">
                        <AlertCircle className="w-5 h-5" />
                        <span className="text-sm">{validationErrors.length} validation error{validationErrors.length !== 1 ? 's' : ''}</span>
                    </div>
                )}
            </div>

            {/* Tab Navigation */}
            <div className="border-b border-gray-600">
                <nav className="flex space-x-8">
                    {[
                        { key: 'class_features', label: 'Class Features', icon: Sword },
                        { key: 'species_traits', label: 'Species Traits', icon: Users },
                        { key: 'feats', label: 'Feats', icon: Award },
                        { key: 'calculated', label: 'Calculated', icon: Calculator }
                    ].map(({ key, label, icon: Icon }) => (
                        <button
                            key={key}
                            onClick={() => setActiveTab(key as typeof activeTab)}
                            className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === key
                                ? 'border-purple-500 text-purple-400'
                                : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                                }`}
                        >
                            <Icon className="w-4 h-4" />
                            <span>{label}</span>
                        </button>
                    ))}
                </nav>
            </div>

            {/* Tab Content */}
            <div className="min-h-[400px]">
                {activeTab === 'class_features' && renderClassFeaturesTab()}
                {activeTab === 'species_traits' && renderSpeciesTraitsTab()}
                {activeTab === 'feats' && renderFeatsTab()}
                {activeTab === 'calculated' && renderCalculatedFeaturesTab()}
            </div>

            {/* Validation Errors */}
            {validationErrors.length > 0 && (
                <div className="border border-red-600 rounded-md p-4 bg-red-900/20">
                    <div className="flex items-center space-x-2 mb-3">
                        <AlertCircle className="w-5 h-5 text-red-400" />
                        <h3 className="font-medium text-red-400">Validation Errors</h3>
                    </div>
                    <ul className="space-y-1">
                        {validationErrors.map((error, index) => (
                            <li key={index} className="text-sm text-red-300">
                                <span className="font-medium">{error.field_path}:</span> {error.message}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};