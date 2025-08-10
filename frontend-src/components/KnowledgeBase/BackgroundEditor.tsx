import React, { useState, useEffect, useCallback } from 'react';
import { 
  BookOpen, 
  Users, 
  Heart, 
  Shield, 
  Sword,
  Plus,
  Trash2,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  Info,
  Edit3
} from 'lucide-react';
import { ValidationError } from '../../services/knowledgeBaseApi';
import { ArrayEditor } from './ArrayEditor';

interface BackgroundData {
  character_id: number;
  background: {
    name: string;
    feature: {
      name: string;
      description: string;
    };
  };
  characteristics: {
    alignment: string;
    gender: string;
    eyes: string;
    size: string;
    height: string;
    faith?: string;
    hair: string;
    skin: string;
    age: number;
    weight: string;
    personality_traits: string[];
    ideals: string[];
    bonds: string[];
    flaws: string[];
  };
  backstory: {
    title: string;
    family_backstory?: {
      parents: string;
      sections: Array<{
        heading: string;
        content: string;
      }>;
    };
    sections: Array<{
      heading: string;
      content: string;
    }>;
  };
  organizations: Array<{
    name: string;
    role: string;
    description: string;
  }>;
  allies: Array<{
    name: string;
    title?: string;
    description: string;
  }>;
  enemies: Array<{
    name: string;
    description: string;
  }>;
  notes: Record<string, string>;
}

interface BackgroundEditorProps {
  data: BackgroundData;
  onChange: (data: BackgroundData) => void;
  onValidationErrors: (errors: ValidationError[]) => void;
}

export const BackgroundEditor: React.FC<BackgroundEditorProps> = ({
  data,
  onChange,
  onValidationErrors
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['background', 'characteristics', 'backstory'])
  );
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);

  // Validation
  const validateData = useCallback((): ValidationError[] => {
    const errors: ValidationError[] = [];

    // Required fields validation
    if (!data.background.name?.trim()) {
      errors.push({
        field_path: 'background.name',
        message: 'Background name is required',
        error_type: 'required'
      });
    }

    if (!data.background.feature.name?.trim()) {
      errors.push({
        field_path: 'background.feature.name',
        message: 'Background feature name is required',
        error_type: 'required'
      });
    }

    if (!data.backstory.title?.trim()) {
      errors.push({
        field_path: 'backstory.title',
        message: 'Backstory title is required',
        error_type: 'required'
      });
    }

    // Validate that arrays have at least one item for personality traits
    if (!data.characteristics.personality_traits || data.characteristics.personality_traits.length === 0) {
      errors.push({
        field_path: 'characteristics.personality_traits',
        message: 'At least one personality trait is required',
        error_type: 'required'
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

  const renderTextarea = (
    fieldPath: string,
    label: string,
    required: boolean = false,
    placeholder?: string,
    rows: number = 4
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
        <textarea
          value={String(value || '')}
          onChange={(e) => updateField(fieldPath, e.target.value)}
          placeholder={placeholder}
          rows={rows}
          className={`w-full px-3 py-2 bg-gray-700 border rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-vertical ${
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

  const renderStringArray = (
    fieldPath: string,
    label: string,
    _placeholder: string = 'Add new item'
  ) => {
    const value = fieldPath.split('.').reduce((obj: any, key) => obj?.[key], data) || [];
    const error = getFieldError(fieldPath);

    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-white">
          {label}
        </label>
        <ArrayEditor
          items={Array.isArray(value) ? value : []}
          onChange={(newItems) => updateField(fieldPath, newItems)}
          itemSchema={{
            key: 'item',
            type: 'string',
            label: 'Item',
            required: false
          }}
          label={label}
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

  const renderBackstorySections = () => {
    const sections = data.backstory.sections || [];
    
    const addSection = () => {
      const newSections = [...sections, { heading: '', content: '' }];
      updateField('backstory.sections', newSections);
    };

    const removeSection = (index: number) => {
      const newSections = sections.filter((_, i) => i !== index);
      updateField('backstory.sections', newSections);
    };

    const updateSection = (index: number, field: 'heading' | 'content', value: string) => {
      const newSections = [...sections];
      newSections[index] = { ...newSections[index], [field]: value };
      updateField('backstory.sections', newSections);
    };

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="block text-sm font-medium text-white">
            Backstory Sections
          </label>
          <button
            type="button"
            onClick={addSection}
            className="flex items-center space-x-2 px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-md text-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Add Section</span>
          </button>
        </div>

        {sections.length === 0 ? (
          <div className="text-center py-8 text-gray-400 border-2 border-dashed border-gray-600 rounded-md">
            <BookOpen className="w-8 h-8 mx-auto mb-2" />
            <p className="text-sm">No backstory sections yet</p>
            <p className="text-xs mt-1">Click "Add Section" to get started</p>
          </div>
        ) : (
          <div className="space-y-4">
            {sections.map((section, index) => (
              <div key={index} className="border border-gray-600 rounded-md p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-300">Section {index + 1}</span>
                  <button
                    type="button"
                    onClick={() => removeSection(index)}
                    className="text-red-400 hover:text-red-300 p-1"
                    title="Remove section"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                
                <div className="space-y-3">
                  <input
                    type="text"
                    value={section.heading}
                    onChange={(e) => updateSection(index, 'heading', e.target.value)}
                    placeholder="Section heading"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <textarea
                    value={section.content}
                    onChange={(e) => updateSection(index, 'content', e.target.value)}
                    placeholder="Section content"
                    rows={4}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-vertical"
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderFamilyBackstory = () => {
    const familyBackstory = data.backstory.family_backstory;
    const sections = familyBackstory?.sections || [];
    
    const addFamilySection = () => {
      const newSections = [...sections, { heading: '', content: '' }];
      updateField('backstory.family_backstory.sections', newSections);
    };

    const removeFamilySection = (index: number) => {
      const newSections = sections.filter((_, i) => i !== index);
      updateField('backstory.family_backstory.sections', newSections);
    };

    const updateFamilySection = (index: number, field: 'heading' | 'content', value: string) => {
      const newSections = [...sections];
      newSections[index] = { ...newSections[index], [field]: value };
      updateField('backstory.family_backstory.sections', newSections);
    };

    return (
      <div className="space-y-4">
        <div className="space-y-3">
          {renderInput('backstory.family_backstory.parents', 'Parents/Guardians', 'text', false, 'Names of parents or guardians')}
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-white">
              Family History Sections
            </label>
            <button
              type="button"
              onClick={addFamilySection}
              className="flex items-center space-x-2 px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-md text-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Add Section</span>
            </button>
          </div>

          {sections.length === 0 ? (
            <div className="text-center py-6 text-gray-400 border-2 border-dashed border-gray-600 rounded-md">
              <p className="text-sm">No family history sections yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {sections.map((section, index) => (
                <div key={index} className="border border-gray-600 rounded-md p-3 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-300">Family Section {index + 1}</span>
                    <button
                      type="button"
                      onClick={() => removeFamilySection(index)}
                      className="text-red-400 hover:text-red-300 p-1"
                      title="Remove section"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={section.heading}
                      onChange={(e) => updateFamilySection(index, 'heading', e.target.value)}
                      placeholder="Section heading"
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                    <textarea
                      value={section.content}
                      onChange={(e) => updateFamilySection(index, 'content', e.target.value)}
                      placeholder="Section content"
                      rows={3}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-vertical"
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-xl font-bold text-white">Character Background</h2>
        <p className="text-sm text-gray-400 mt-1">
          Edit your character's background, personality, and story
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-6 max-w-4xl">
          
          {/* Background Information */}
          {renderSection(
            'background',
            'Background Information',
            <BookOpen className="w-5 h-5 text-blue-400" />,
            <div className="space-y-4">
              {renderInput('background.name', 'Background Name', 'text', true, 'e.g., Acolyte, Criminal, Folk Hero')}
              {renderInput('background.feature.name', 'Background Feature Name', 'text', true, 'Name of your background feature')}
              {renderTextarea('background.feature.description', 'Background Feature Description', false, 'Describe what your background feature does', 6)}
            </div>
          )}

          {/* Personality & Traits */}
          {renderSection(
            'characteristics',
            'Personality & Traits',
            <Heart className="w-5 h-5 text-pink-400" />,
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {renderInput('characteristics.faith', 'Faith/Religion', 'text', false, 'Deity or religious belief')}
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  {renderStringArray('characteristics.personality_traits', 'Personality Traits')}
                  {renderStringArray('characteristics.ideals', 'Ideals')}
                </div>
                <div className="space-y-4">
                  {renderStringArray('characteristics.bonds', 'Bonds')}
                  {renderStringArray('characteristics.flaws', 'Flaws')}
                </div>
              </div>
            </div>
          )}

          {/* Backstory */}
          {renderSection(
            'backstory',
            'Character Backstory',
            <Edit3 className="w-5 h-5 text-green-400" />,
            <div className="space-y-6">
              {renderInput('backstory.title', 'Backstory Title', 'text', true, 'Title for your character\'s story')}
              
              <div className="space-y-4">
                <h4 className="text-md font-medium text-white border-b border-gray-600 pb-2">Family Background</h4>
                {renderFamilyBackstory()}
              </div>
              
              <div className="space-y-4">
                <h4 className="text-md font-medium text-white border-b border-gray-600 pb-2">Main Story</h4>
                {renderBackstorySections()}
              </div>
            </div>
          )}

          {/* Organizations */}
          {renderSection(
            'organizations',
            'Organizations',
            <Shield className="w-5 h-5 text-yellow-400" />,
            <ArrayEditor
              items={data.organizations || []}
              onChange={(newItems) => updateField('organizations', newItems)}
              itemSchema={{
                key: 'organization',
                type: 'object',
                label: 'Organization',
                required: false,
                children: [
                  { key: 'name', type: 'string', label: 'Organization Name', required: true },
                  { key: 'role', type: 'string', label: 'Your Role', required: true },
                  { key: 'description', type: 'string', label: 'Description', required: false }
                ]
              }}
              label="Organizations"
            />
          )}

          {/* Allies */}
          {renderSection(
            'allies',
            'Allies & Contacts',
            <Users className="w-5 h-5 text-green-400" />,
            <ArrayEditor
              items={data.allies || []}
              onChange={(newItems) => updateField('allies', newItems)}
              itemSchema={{
                key: 'ally',
                type: 'object',
                label: 'Ally',
                required: false,
                children: [
                  { key: 'name', type: 'string', label: 'Name', required: true },
                  { key: 'title', type: 'string', label: 'Title/Position', required: false },
                  { key: 'description', type: 'string', label: 'Description', required: true }
                ]
              }}
              label="Allies"
            />
          )}

          {/* Enemies */}
          {renderSection(
            'enemies',
            'Enemies & Rivals',
            <Sword className="w-5 h-5 text-red-400" />,
            <ArrayEditor
              items={data.enemies || []}
              onChange={(newItems) => updateField('enemies', newItems)}
              itemSchema={{
                key: 'enemy',
                type: 'object',
                label: 'Enemy',
                required: false,
                children: [
                  { key: 'name', type: 'string', label: 'Name', required: true },
                  { key: 'description', type: 'string', label: 'Description', required: true }
                ]
              }}
              label="Enemies"
            />
          )}

          {/* Notes */}
          {renderSection(
            'notes',
            'Additional Notes',
            <Info className="w-5 h-5 text-gray-400" />,
            <div className="space-y-4">
              <p className="text-sm text-gray-400">
                Add any additional notes about your character's background, relationships, or story elements.
              </p>
              {Object.entries(data.notes || {}).map(([key, value]) => (
                <div key={key} className="space-y-2">
                  <label className="block text-sm font-medium text-white capitalize">
                    {key.replace(/_/g, ' ')}
                  </label>
                  <textarea
                    value={value}
                    onChange={(e) => updateField(`notes.${key}`, e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-vertical"
                  />
                </div>
              ))}
              
              <button
                type="button"
                onClick={() => {
                  const newKey = `note_${Date.now()}`;
                  updateField(`notes.${newKey}`, '');
                }}
                className="flex items-center space-x-2 px-3 py-2 border-2 border-dashed border-gray-600 rounded-md text-gray-400 hover:border-purple-500 hover:text-purple-400 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>Add Note</span>
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};