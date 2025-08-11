import React, { useState } from 'react';
import { Save, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import { 
  ValidationProvider, 
  ValidationSummary, 
  ValidatedInput, 
  ValidatedSelect,
  ValidatedTextarea,
  UnsavedChangesWarning,
  useValidation
} from './validation';

interface DemoData {
  character_base: {
    name: string;
    race: string;
    class: string;
    total_level: number;
    alignment: string;
    background: string;
  };
  characteristics: {
    age: number;
    height: string;
    weight: string;
  };
  description: string;
}

const initialData: DemoData = {
  character_base: {
    name: '',
    race: '',
    class: '',
    total_level: 1,
    alignment: '',
    background: ''
  },
  characteristics: {
    age: 0,
    height: '',
    weight: ''
  },
  description: ''
};

const DemoForm: React.FC = () => {
  const [data, setData] = useState<DemoData>(initialData);
  const { validationState, validateForm, hasErrors, hasWarnings } = useValidation();

  const updateField = (fieldPath: string, value: any) => {
    const keys = fieldPath.split('.');
    const newData = { ...data };
    let current: any = newData;

    for (let i = 0; i < keys.length - 1; i++) {
      current[keys[i]] = { ...current[keys[i]] };
      current = current[keys[i]];
    }

    current[keys[keys.length - 1]] = value;
    setData(newData);
  };

  const handleSave = async () => {
    try {
      // In a real app, this would save to the backend
      const result = await validateForm('demo_character.json', data);
      if (result.is_valid) {
        alert('Character saved successfully!');
      } else {
        alert('Please fix validation errors before saving.');
      }
    } catch (error) {
      console.error('Save failed:', error);
      alert('Save failed. Please try again.');
    }
  };

  const handleReset = () => {
    setData(initialData);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Validation Demo</h2>
          <p className="text-gray-400 mt-1">
            Demonstrates real-time validation with immediate feedback
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleReset}
            className="flex items-center px-4 py-2 text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-md transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Reset
          </button>
          <button
            onClick={handleSave}
            disabled={hasErrors}
            className={`flex items-center px-4 py-2 rounded-md transition-colors ${
              hasErrors
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            <Save className="w-4 h-4 mr-2" />
            Save Character
          </button>
        </div>
      </div>

      {/* Validation Summary */}
      <ValidationSummary showWhenValid />

      {/* Form Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Basic Information */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <CheckCircle className="w-5 h-5 mr-2 text-green-400" />
            Basic Information
          </h3>
          <div className="space-y-4">
            <ValidatedInput
              fieldPath="character_base.name"
              label="Character Name"
              value={data.character_base.name}
              onChange={(value) => updateField('character_base.name', value)}
              required
              placeholder="Enter character name"
            />
            
            <ValidatedSelect
              fieldPath="character_base.race"
              label="Race"
              value={data.character_base.race}
              onChange={(value) => updateField('character_base.race', value)}
              options={[
                'Human', 'Elf', 'Dwarf', 'Halfling', 'Dragonborn', 
                'Gnome', 'Half-Elf', 'Half-Orc', 'Tiefling'
              ]}
              required
              placeholder="Select race"
            />
            
            <ValidatedSelect
              fieldPath="character_base.class"
              label="Class"
              value={data.character_base.class}
              onChange={(value) => updateField('character_base.class', value)}
              options={[
                'Barbarian', 'Bard', 'Cleric', 'Druid', 'Fighter',
                'Monk', 'Paladin', 'Ranger', 'Rogue', 'Sorcerer',
                'Warlock', 'Wizard'
              ]}
              required
              placeholder="Select class"
            />
            
            <ValidatedInput
              fieldPath="character_base.total_level"
              label="Level"
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
              placeholder="e.g., Acolyte, Criminal, Folk Hero"
            />
          </div>
        </div>

        {/* Physical Characteristics */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <AlertCircle className="w-5 h-5 mr-2 text-blue-400" />
            Physical Characteristics
          </h3>
          <div className="space-y-4">
            <ValidatedInput
              fieldPath="characteristics.age"
              label="Age"
              type="number"
              value={data.characteristics.age}
              onChange={(value) => updateField('characteristics.age', value)}
              min={1}
              max={1000}
              placeholder="Character's age"
            />
            
            <ValidatedInput
              fieldPath="characteristics.height"
              label="Height"
              value={data.characteristics.height}
              onChange={(value) => updateField('characteristics.height', value)}
              placeholder="e.g., 5'10&quot;, 180cm"
            />
            
            <ValidatedInput
              fieldPath="characteristics.weight"
              label="Weight"
              value={data.characteristics.weight}
              onChange={(value) => updateField('characteristics.weight', value)}
              placeholder="e.g., 180 lbs, 80 kg"
            />
            
            <ValidatedTextarea
              fieldPath="description"
              label="Character Description"
              value={data.description}
              onChange={(value) => updateField('description', value)}
              rows={6}
              placeholder="Describe your character's appearance, personality, and background..."
              maxLength={1000}
              showCharCount
            />
          </div>
        </div>
      </div>

      {/* Status Information */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-300 mb-2">Validation Status</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${hasErrors ? 'bg-red-500' : 'bg-green-500'}`} />
            <span className="text-gray-300">
              {hasErrors ? `${validationState.errors.length} Errors` : 'No Errors'}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${hasWarnings ? 'bg-yellow-500' : 'bg-gray-500'}`} />
            <span className="text-gray-300">
              {hasWarnings ? `${validationState.warnings.length} Warnings` : 'No Warnings'}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${validationState.isValidating ? 'bg-blue-500 animate-pulse' : 'bg-gray-500'}`} />
            <span className="text-gray-300">
              {validationState.isValidating ? 'Validating...' : 'Ready'}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${validationState.hasUnsavedChanges ? 'bg-orange-500' : 'bg-gray-500'}`} />
            <span className="text-gray-300">
              {validationState.hasUnsavedChanges ? 'Unsaved Changes' : 'Saved'}
            </span>
          </div>
        </div>
      </div>

      {/* Unsaved Changes Warning */}
      <UnsavedChangesWarning
        onSave={handleSave}
        onDiscard={handleReset}
        position="floating"
      />
    </div>
  );
};

export const ValidationDemo: React.FC = () => {
  // Mock schema for demonstration
  const mockSchema = {
    type: 'object',
    properties: {
      character_base: {
        type: 'object',
        properties: {
          name: { type: 'string', required: true, minLength: 2, maxLength: 50 },
          race: { type: 'string', required: true },
          class: { type: 'string', required: true },
          total_level: { type: 'number', required: true, minimum: 1, maximum: 20 },
          alignment: { type: 'string' },
          background: { type: 'string' }
        }
      },
      characteristics: {
        type: 'object',
        properties: {
          age: { type: 'number', minimum: 1, maximum: 1000 },
          height: { type: 'string' },
          weight: { type: 'string' }
        }
      },
      description: { type: 'string', maxLength: 1000 }
    }
  };

  return (
    <ValidationProvider 
      filename="demo_character.json" 
      schema={mockSchema}
    >
      <div className="min-h-screen bg-gray-900 p-6">
        <div className="max-w-6xl mx-auto">
          <DemoForm />
        </div>
      </div>
    </ValidationProvider>
  );
};