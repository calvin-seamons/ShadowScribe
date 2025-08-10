import React, { useState, useEffect, useCallback } from 'react';
import { 
  User, 
  Shield, 
  Zap, 
  Eye,
  Calculator,
  AlertCircle,
  Info,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { ValidationError } from '../../services/knowledgeBaseApi';

interface CharacterData {
  character_base: {
    name: string;
    race: string;
    subrace?: string;
    class: string;
    warlock_level?: number;
    paladin_level?: number;
    total_level: number;
    experience_points: number;
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
    current_hp: number;
    temp_hp: number;
    armor_class: number;
    initiative_bonus: number;
    speed: number;
    inspiration: boolean;
  };
  proficiencies: Array<{
    type: 'armor' | 'weapon' | 'tool' | 'language';
    name: string;
  }>;
  damage_modifiers?: Array<{
    damage_type: string;
    modifier_type: 'resistance' | 'immunity' | 'vulnerability';
    source: string;
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
  onValidationErrors: (errors: ValidationError[]) => void;
}

export const CharacterBasicEditor: React.FC<CharacterBasicEditorProps> = ({
  data,
  onChange,
  onValidationErrors
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['character_base', 'ability_scores', 'combat_stats'])
  );
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);

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

  // Validation
  const validateData = useCallback((): ValidationError[] => {
    const errors: ValidationError[] = [];

    // Required fields validation
    if (!data.character_base.name?.trim()) {
      errors.push({
        field_path: 'character_base.name',
        message: 'Character name is required',
        error_type: 'required'
      });
    }

    if (!data.character_base.race?.trim()) {
      errors.push({
        field_path: 'character_base.race',
        message: 'Race is required',
        error_type: 'required'
      });
    }

    if (!data.character_base.class?.trim()) {
      errors.push({
        field_path: 'character_base.class',
        message: 'Class is required',
        error_type: 'required'
      });
    }

    if (data.character_base.total_level < 1 || data.character_base.total_level > 20) {
      errors.push({
        field_path: 'character_base.total_level',
        message: 'Total level must be between 1 and 20',
        error_type: 'custom'
      });
    }

    // Ability scores validation (typically 1-30 range)
    Object.entries(data.ability_scores).forEach(([ability, score]) => {
      if (score < 1 || score > 30) {
        errors.push({
          field_path: `ability_scores.${ability}`,
          message: `${ability.charAt(0).toUpperCase() + ability.slice(1)} must be between 1 and 30`,
          error_type: 'custom'
        });
      }
    });

    // Combat stats validation
    if (data.combat_stats.max_hp < 1) {
      errors.push({
        field_path: 'combat_stats.max_hp',
        message: 'Maximum HP must be at least 1',
        error_type: 'custom'
      });
    }

    if (data.combat_stats.current_hp < 0) {
      errors.push({
        field_path: 'combat_stats.current_hp',
        message: 'Current HP cannot be negative',
        error_type: 'custom'
      });
    }

    if (data.combat_stats.armor_class < 1) {
      errors.push({
        field_path: 'combat_stats.armor_class',
        message: 'Armor Class must be at least 1',
        error_type: 'custom'
      });
    }

    return errors;
  }, [data]);

  useEffect(() => {
    const errors = validateData();
    setValidationErrors(errors);
    onValidationErrors(errors);
  }, [validateData, onValidationErrors]);

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
      current[keys[i]] = { ...current[keys[i]] };
      current = current[keys[i]];
    }

    current[keys[keys.length - 1]] = value;
    onChange(updatedData);
  };

  const getFieldError = (fieldPath: string): ValidationError | undefined => {
    return validationErrors.find(error => error.field_path === fieldPath);
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

  const renderInput = (
    fieldPath: string,
    label: string,
    type: 'text' | 'number' = 'text',
    required: boolean = false,
    min?: number,
    max?: number,
    placeholder?: string
  ) => {
    const value = fieldPath.split('.').reduce((obj: any, key) => obj?.[key], data);
    const error = getFieldError(fieldPath);
    const hasError = !!error;

    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-white">
          {label}
          {required && <span className="text-red-400 ml-1">*</span>}
        </label>
        <input
          type={type}
          value={String(value || '')}
          onChange={(e) => {
            const newValue = type === 'number' 
              ? (e.target.value ? Number(e.target.value) : 0)
              : e.target.value;
            updateField(fieldPath, newValue);
          }}
          min={min}
          max={max}
          placeholder={placeholder}
          className={`w-full px-3 py-2 bg-gray-700 border rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 ${
            hasError ? 'border-red-500' : 'border-gray-600'
          }`}
        />
        {error && (
          <div className="flex items-center space-x-2 text-sm text-red-400">
            <AlertCircle className="w-4 h-4" />
            <span>{error.message}</span>
          </div>
        )}
      </div>
    );
  };

  const renderSelect = (
    fieldPath: string,
    label: string,
    options: string[],
    required: boolean = false,
    placeholder: string = 'Select...'
  ) => {
    const value = fieldPath.split('.').reduce((obj: any, key) => obj?.[key], data);
    const error = getFieldError(fieldPath);
    const hasError = !!error;

    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-white">
          {label}
          {required && <span className="text-red-400 ml-1">*</span>}
        </label>
        <select
          value={String(value || '')}
          onChange={(e) => updateField(fieldPath, e.target.value)}
          className={`w-full px-3 py-2 bg-gray-700 border rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500 ${
            hasError ? 'border-red-500' : 'border-gray-600'
          }`}
        >
          <option value="">{placeholder}</option>
          {options.map(option => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
        {error && (
          <div className="flex items-center space-x-2 text-sm text-red-400">
            <AlertCircle className="w-4 h-4" />
            <span>{error.message}</span>
          </div>
        )}
      </div>
    );
  };

  const renderCheckbox = (
    fieldPath: string,
    label: string,
    description?: string
  ) => {
    const value = fieldPath.split('.').reduce((obj: any, key) => obj?.[key], data);

    return (
      <div className="space-y-2">
        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={Boolean(value)}
            onChange={(e) => updateField(fieldPath, e.target.checked)}
            className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
          />
          <span className="text-sm font-medium text-white">{label}</span>
        </label>
        {description && (
          <div className="flex items-start space-x-2 text-sm text-gray-400 ml-6">
            <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <p>{description}</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-xl font-bold text-white">Character Basic Information</h2>
        <p className="text-sm text-gray-400 mt-1">
          Edit your character's core stats and information
        </p>
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
              {renderInput('character_base.name', 'Character Name', 'text', true, undefined, undefined, 'Enter character name')}
              {renderInput('character_base.race', 'Race', 'text', true, undefined, undefined, 'e.g., Human, Elf, Dwarf')}
              {renderInput('character_base.subrace', 'Subrace', 'text', false, undefined, undefined, 'e.g., Hill Dwarf, High Elf')}
              {renderInput('character_base.class', 'Class', 'text', true, undefined, undefined, 'e.g., Fighter, Wizard')}
              {renderInput('character_base.total_level', 'Total Level', 'number', true, 1, 20)}
              {renderInput('character_base.experience_points', 'Experience Points', 'number', false, 0)}
              {renderSelect('character_base.alignment', 'Alignment', [
                'Lawful Good', 'Neutral Good', 'Chaotic Good',
                'Lawful Neutral', 'True Neutral', 'Chaotic Neutral',
                'Lawful Evil', 'Neutral Evil', 'Chaotic Evil'
              ], false, 'Select alignment')}
              {renderInput('character_base.background', 'Background', 'text', false, undefined, undefined, 'e.g., Acolyte, Criminal')}
              {renderSelect('character_base.lifestyle', 'Lifestyle', [
                'Wretched', 'Squalid', 'Poor', 'Modest', 'Comfortable', 'Wealthy', 'Aristocrat'
              ], false, 'Select lifestyle')}
            </div>
          )}

          {/* Characteristics */}
          {renderSection(
            'characteristics',
            'Physical Characteristics',
            <Eye className="w-5 h-5 text-blue-400" />,
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {renderSelect('characteristics.gender', 'Gender', [
                'Male', 'Female', 'Non-binary', 'Other'
              ], false, 'Select gender')}
              {renderInput('characteristics.age', 'Age', 'number', false, 0, 1000)}
              {renderInput('characteristics.height', 'Height', 'text', false, undefined, undefined, 'e.g., 5\'10"')}
              {renderInput('characteristics.weight', 'Weight', 'text', false, undefined, undefined, 'e.g., 180 lb')}
              {renderInput('characteristics.eyes', 'Eye Color', 'text', false, undefined, undefined, 'e.g., Brown, Blue')}
              {renderInput('characteristics.hair', 'Hair', 'text', false, undefined, undefined, 'e.g., Long black hair')}
              {renderInput('characteristics.skin', 'Skin', 'text', false, undefined, undefined, 'e.g., Pale, Tanned')}
              {renderSelect('characteristics.size', 'Size', [
                'Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Gargantuan'
              ], false, 'Select size')}
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
              {renderInput('combat_stats.max_hp', 'Maximum HP', 'number', true, 1)}
              {renderInput('combat_stats.current_hp', 'Current HP', 'number', true, 0)}
              {renderInput('combat_stats.temp_hp', 'Temporary HP', 'number', false, 0)}
              {renderInput('combat_stats.armor_class', 'Armor Class', 'number', true, 1)}
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
              {renderInput('combat_stats.speed', 'Speed (feet)', 'number', false, 0)}
              {renderCheckbox('combat_stats.inspiration', 'Has Inspiration', 'Whether the character currently has inspiration')}
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
              {renderInput('senses.darkvision', 'Darkvision (feet)', 'number', false, 0)}
              {renderInput('senses.blindsight', 'Blindsight (feet)', 'number', false, 0)}
              {renderInput('senses.tremorsense', 'Tremorsense (feet)', 'number', false, 0)}
              {renderInput('senses.truesight', 'Truesight (feet)', 'number', false, 0)}
            </div>
          )}

        </div>
      </div>
    </div>
  );
};