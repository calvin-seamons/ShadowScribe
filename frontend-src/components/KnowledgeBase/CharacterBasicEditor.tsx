import React, { useState, useEffect, useCallback } from 'react';
import {
  User,
  Shield,
  Zap,
  Eye,
  Calculator,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import {
  ValidationProvider,
  ValidationSummary,
  ValidatedInput,
  ValidatedSelect,
  UnsavedChangesWarning
} from './validation';

interface CharacterData {
  character_base: {
    name: string;
    race: string;
    subrace?: string;
    class: string;
    warlock_level?: number;
    paladin_level?: number;
    total_level: number;
    alignment: string;
    background: string;
    lifestyle: string;
    hit_dice: Record<string, string>;
  };
  characteristics: {
    alignment: string;
    gender: string;
    eyes: string;
    size: string;
    height: string;
    hair: string;
    skin: string;
    age: number;
    weight: string;
  };
  ability_scores: {
    strength: number;
    dexterity: number;
    constitution: number;
    intelligence: number;
    wisdom: number;
    charisma: number;
  };
  combat_stats: {
    max_hp: number;
    armor_class: number;
    initiative_bonus: number;
    speed: number;
  };
  proficiencies: Array<{
    type: 'armor' | 'weapon' | 'tool' | 'language';
    name: string;
  }>;
  damage_modifiers?: Array<{
    damage_type: string;
    modifier_type: 'resistance' | 'immunity' | 'vulnerability';
  }>;
  passive_scores: {
    perception: number;
    investigation: number;
    insight: number;
  };
  senses?: {
    darkvision?: number;
    blindsight?: number;
    tremorsense?: number;
    truesight?: number;
  };
}

interface CharacterBasicEditorProps {
  data: CharacterData;
  onChange: (data: CharacterData) => void;
  filename?: string;
  onSave?: () => void;
}

export const CharacterBasicEditor: React.FC<CharacterBasicEditorProps> = ({
  data,
  onChange,
  filename,
  onSave
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['character_base', 'ability_scores', 'combat_stats'])
  );

  // Calculate proficiency bonus based on total level
  const calculateProficiencyBonus = useCallback((level: number): number => {
    return Math.ceil(level / 4) + 1;
  }, []);

  // Calculate ability modifier
  const calculateModifier = useCallback((score: number): number => {
    return Math.floor((score - 10) / 2);
  }, []);

  // Update calculated fields when relevant data changes
  useEffect(() => {
    const updatedData = { ...data };
    let hasChanges = false;

    // Update proficiency bonus in passive scores if needed
    const proficiencyBonus = calculateProficiencyBonus(data.character_base.total_level);
    const wisdomMod = calculateModifier(data.ability_scores.wisdom);
    const intelligenceMod = calculateModifier(data.ability_scores.intelligence);

    // Calculate passive perception (10 + Wisdom modifier + proficiency bonus if proficient)
    const expectedPerception = 10 + wisdomMod + proficiencyBonus;
    if (data.passive_scores.perception !== expectedPerception) {
      updatedData.passive_scores.perception = expectedPerception;
      hasChanges = true;
    }

    // Calculate passive investigation (10 + Intelligence modifier)
    const expectedInvestigation = 10 + intelligenceMod;
    if (data.passive_scores.investigation !== expectedInvestigation) {
      updatedData.passive_scores.investigation = expectedInvestigation;
      hasChanges = true;
    }

    // Calculate passive insight (10 + Wisdom modifier)
    const expectedInsight = 10 + wisdomMod;
    if (data.passive_scores.insight !== expectedInsight) {
      updatedData.passive_scores.insight = expectedInsight;
      hasChanges = true;
    }

    // Update initiative bonus (Dexterity modifier)
    const dexterityMod = calculateModifier(data.ability_scores.dexterity);
    if (data.combat_stats.initiative_bonus !== dexterityMod) {
      updatedData.combat_stats.initiative_bonus = dexterityMod;
      hasChanges = true;
    }

    if (hasChanges) {
      onChange(updatedData);
    }
  }, [data, onChange, calculateProficiencyBonus, calculateModifier]);

  const toggleSection = (sectionKey: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionKey)) {
      newExpanded.delete(sectionKey);
    } else {
      newExpanded.add(sectionKey);
    }
    setExpandedSections(newExpanded);
  };

  const updateField = (path: string, value: any) => {
    const keys = path.split('.');
    const updatedData = { ...data };
    let current: any = updatedData;

    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) {
        current[keys[i]] = {};
      } else {
        current[keys[i]] = { ...current[keys[i]] };
      }
      current = current[keys[i]];
    }

    current[keys[keys.length - 1]] = value;
    onChange(updatedData);
  };

  const renderSection = (
    sectionKey: string,
    title: string,
    icon: React.ReactNode,
    children: React.ReactNode
  ) => {
    const isExpanded = expandedSections.has(sectionKey);

    return (
      <div className="border border-gray-600 rounded-lg overflow-hidden">
        <button
          type="button"
          onClick={() => toggleSection(sectionKey)}
          className="w-full flex items-center justify-between p-4 bg-gray-750 hover:bg-gray-700 transition-colors"
        >
          <div className="flex items-center space-x-3">
            {icon}
            <h3 className="text-lg font-medium text-white">{title}</h3>
          </div>
          {isExpanded ? (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronRight className="w-5 h-5 text-gray-400" />
          )}
        </button>

        {isExpanded && (
          <div className="p-4 bg-gray-800 border-t border-gray-600">
            {children}
          </div>
        )}
      </div>
    );
  };

  // const renderCheckbox = (
  //   fieldPath: string,
  //   label: string,
  //   description?: string
  // ) => {
  //   const value = fieldPath.split('.').reduce((obj: any, key) => obj?.[key], data);

  //   return (
  //     <div className="space-y-2">
  //       <label className="flex items-center space-x-3">
  //         <input
  //           type="checkbox"
  //           checked={Boolean(value)}
  //           onChange={(e) => updateField(fieldPath, e.target.checked)}
  //           className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
  //         />
  //         <span className="text-sm font-medium text-white">{label}</span>
  //       </label>
  //       {description && (
  //         <div className="flex items-start space-x-2 text-sm text-gray-400 ml-6">
  //           <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
  //           <p>{description}</p>
  //         </div>
  //       )}
  //     </div>
  //   );
  // };

  return (
    <ValidationProvider filename={filename}>
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">Character Basic Information</h2>
          <p className="text-sm text-gray-400 mt-1">
            Edit your character's core stats and information
          </p>
        </div>

        {/* Validation Summary */}
        <div className="p-4 border-b border-gray-700">
          <ValidationSummary showWhenValid />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-6 max-w-4xl">

            {/* Character Base */}
            {renderSection(
              'character_base',
              'Basic Information',
              <User className="w-5 h-5 text-purple-400" />,
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ValidatedInput
                  fieldPath="character_base.name"
                  label="Character Name"
                  value={data.character_base.name}
                  onChange={(value) => updateField('character_base.name', value)}
                  required
                  placeholder="Enter character name"
                />
                <ValidatedInput
                  fieldPath="character_base.race"
                  label="Race"
                  value={data.character_base.race}
                  onChange={(value) => updateField('character_base.race', value)}
                  required
                  placeholder="e.g., Human, Elf, Dwarf"
                />
                <ValidatedInput
                  fieldPath="character_base.subrace"
                  label="Subrace"
                  value={data.character_base.subrace || ''}
                  onChange={(value) => updateField('character_base.subrace', value)}
                  placeholder="e.g., Hill Dwarf, High Elf"
                />
                <ValidatedInput
                  fieldPath="character_base.class"
                  label="Class"
                  value={data.character_base.class}
                  onChange={(value) => updateField('character_base.class', value)}
                  required
                  placeholder="e.g., Fighter, Wizard"
                />
                <ValidatedInput
                  fieldPath="character_base.total_level"
                  label="Total Level"
                  type="number"
                  value={data.character_base.total_level}
                  onChange={(value) => updateField('character_base.total_level', value)}
                  required
                  min={1}
                  max={20}
                />
                <ValidatedSelect
                  fieldPath="character_base.alignment"
                  label="Alignment"
                  value={data.character_base.alignment}
                  onChange={(value) => updateField('character_base.alignment', value)}
                  options={[
                    'Lawful Good', 'Neutral Good', 'Chaotic Good',
                    'Lawful Neutral', 'True Neutral', 'Chaotic Neutral',
                    'Lawful Evil', 'Neutral Evil', 'Chaotic Evil'
                  ]}
                  placeholder="Select alignment"
                />
                <ValidatedInput
                  fieldPath="character_base.background"
                  label="Background"
                  value={data.character_base.background}
                  onChange={(value) => updateField('character_base.background', value)}
                  placeholder="e.g., Acolyte, Criminal"
                />
                <ValidatedSelect
                  fieldPath="character_base.lifestyle"
                  label="Lifestyle"
                  value={data.character_base.lifestyle}
                  onChange={(value) => updateField('character_base.lifestyle', value)}
                  options={[
                    'Wretched', 'Squalid', 'Poor', 'Modest', 'Comfortable', 'Wealthy', 'Aristocrat'
                  ]}
                  placeholder="Select lifestyle"
                />
              </div>
            )}

            {/* Characteristics */}
            {renderSection(
              'characteristics',
              'Physical Characteristics',
              <Eye className="w-5 h-5 text-blue-400" />,
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ValidatedSelect
                  fieldPath="characteristics.gender"
                  label="Gender"
                  value={data.characteristics.gender}
                  onChange={(value) => updateField('characteristics.gender', value)}
                  options={['Male', 'Female', 'Non-binary', 'Other']}
                  placeholder="Select gender"
                />
                <ValidatedInput
                  fieldPath="characteristics.age"
                  label="Age"
                  type="number"
                  value={data.characteristics.age}
                  onChange={(value) => updateField('characteristics.age', value)}
                  min={0}
                  max={1000}
                />
                <ValidatedInput
                  fieldPath="characteristics.height"
                  label="Height"
                  value={data.characteristics.height}
                  onChange={(value) => updateField('characteristics.height', value)}
                  placeholder="e.g., 5'10&quot;"
                />
                <ValidatedInput
                  fieldPath="characteristics.weight"
                  label="Weight"
                  value={data.characteristics.weight}
                  onChange={(value) => updateField('characteristics.weight', value)}
                  placeholder="e.g., 180 lb"
                />
                <ValidatedInput
                  fieldPath="characteristics.eyes"
                  label="Eye Color"
                  value={data.characteristics.eyes}
                  onChange={(value) => updateField('characteristics.eyes', value)}
                  placeholder="e.g., Brown, Blue"
                />
                <ValidatedInput
                  fieldPath="characteristics.hair"
                  label="Hair"
                  value={data.characteristics.hair}
                  onChange={(value) => updateField('characteristics.hair', value)}
                  placeholder="e.g., Long black hair"
                />
                <ValidatedInput
                  fieldPath="characteristics.skin"
                  label="Skin"
                  value={data.characteristics.skin}
                  onChange={(value) => updateField('characteristics.skin', value)}
                  placeholder="e.g., Pale, Tanned"
                />
                <ValidatedSelect
                  fieldPath="characteristics.size"
                  label="Size"
                  value={data.characteristics.size}
                  onChange={(value) => updateField('characteristics.size', value)}
                  options={['Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Gargantuan']}
                  placeholder="Select size"
                />
              </div>
            )}

            {/* Ability Scores */}
            {renderSection(
              'ability_scores',
              'Ability Scores',
              <Zap className="w-5 h-5 text-yellow-400" />,
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(data.ability_scores).map(([ability, score]) => (
                  <div key={ability} className="space-y-2">
                    <div className="text-center">
                      <div className="text-sm font-medium text-white capitalize mb-1">
                        {ability}
                      </div>
                      <input
                        type="number"
                        value={score}
                        onChange={(e) => updateField(`ability_scores.${ability}`, Number(e.target.value) || 0)}
                        min={1}
                        max={30}
                        className="w-16 h-16 text-center text-lg font-bold bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                      <div className="text-xs text-gray-400 mt-1">
                        Modifier: {calculateModifier(score) >= 0 ? '+' : ''}{calculateModifier(score)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Combat Stats */}
            {renderSection(
              'combat_stats',
              'Combat Statistics',
              <Shield className="w-5 h-5 text-red-400" />,
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ValidatedInput
                  fieldPath="combat_stats.max_hp"
                  label="Maximum HP"
                  type="number"
                  value={data.combat_stats.max_hp}
                  onChange={(value) => updateField('combat_stats.max_hp', value)}
                  required
                  min={1}
                />
                <ValidatedInput
                  fieldPath="combat_stats.armor_class"
                  label="Armor Class"
                  type="number"
                  value={data.combat_stats.armor_class}
                  onChange={(value) => updateField('combat_stats.armor_class', value)}
                  required
                  min={1}
                />
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-white">
                    Initiative Bonus
                    <span className="text-xs text-gray-400 ml-2">(Auto-calculated from Dexterity)</span>
                  </label>
                  <input
                    type="number"
                    value={data.combat_stats.initiative_bonus}
                    readOnly
                    className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-md text-gray-300 cursor-not-allowed"
                  />
                </div>
                <ValidatedInput
                  fieldPath="combat_stats.speed"
                  label="Speed (feet)"
                  type="number"
                  value={data.combat_stats.speed}
                  onChange={(value) => updateField('combat_stats.speed', value)}
                  min={0}
                />
              </div>
            )}

            {/* Passive Scores */}
            {renderSection(
              'passive_scores',
              'Passive Scores',
              <Calculator className="w-5 h-5 text-green-400" />,
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-white">
                    Passive Perception
                    <span className="text-xs text-gray-400 ml-2">(Auto-calculated)</span>
                  </label>
                  <input
                    type="number"
                    value={data.passive_scores.perception}
                    readOnly
                    className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-md text-gray-300 cursor-not-allowed"
                  />
                </div>
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-white">
                    Passive Investigation
                    <span className="text-xs text-gray-400 ml-2">(Auto-calculated)</span>
                  </label>
                  <input
                    type="number"
                    value={data.passive_scores.investigation}
                    readOnly
                    className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-md text-gray-300 cursor-not-allowed"
                  />
                </div>
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-white">
                    Passive Insight
                    <span className="text-xs text-gray-400 ml-2">(Auto-calculated)</span>
                  </label>
                  <input
                    type="number"
                    value={data.passive_scores.insight}
                    readOnly
                    className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-md text-gray-300 cursor-not-allowed"
                  />
                </div>
              </div>
            )}

            {/* Senses */}
            {renderSection(
              'senses',
              'Special Senses',
              <Eye className="w-5 h-5 text-indigo-400" />,
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ValidatedInput
                  fieldPath="senses.darkvision"
                  label="Darkvision (feet)"
                  type="number"
                  value={data.senses?.darkvision || 0}
                  onChange={(value) => updateField('senses.darkvision', value)}
                  min={0}
                />
                <ValidatedInput
                  fieldPath="senses.blindsight"
                  label="Blindsight (feet)"
                  type="number"
                  value={data.senses?.blindsight || 0}
                  onChange={(value) => updateField('senses.blindsight', value)}
                  min={0}
                />
                <ValidatedInput
                  fieldPath="senses.tremorsense"
                  label="Tremorsense (feet)"
                  type="number"
                  value={data.senses?.tremorsense || 0}
                  onChange={(value) => updateField('senses.tremorsense', value)}
                  min={0}
                />
                <ValidatedInput
                  fieldPath="senses.truesight"
                  label="Truesight (feet)"
                  type="number"
                  value={data.senses?.truesight || 0}
                  onChange={(value) => updateField('senses.truesight', value)}
                  min={0}
                />
              </div>
            )}

          </div>
        </div>

        {/* Unsaved Changes Warning */}
        <UnsavedChangesWarning
          onSave={onSave}
          position="bottom"
        />
      </div>
    </ValidationProvider>
  );
};