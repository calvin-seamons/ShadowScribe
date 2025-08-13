import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
  FileText,
  Edit3,
  Check,
  AlertTriangle,
  CheckCircle,
  Info,
  ChevronDown,
  ChevronRight,
  Eye,
  EyeOff,
  RefreshCw,
  Save,
  AlertCircle
} from 'lucide-react';
import { ParsedCharacterData, UncertainField, ValidationError, ValidationResult } from '../../types';
import { 
  ValidationProvider
} from '../KnowledgeBase/validation';

interface CharacterDataReviewProps {
  parsedData: ParsedCharacterData;
  uncertainFields: UncertainField[];
  onFieldEdit: (filePath: string, fieldPath: string, value: any) => void;
  onFinalize: (characterName: string) => void;
  onReparse: () => void;
  isLoading?: boolean;
}

interface FileSection {
  fileType: string;
  displayName: string;
  icon: React.ReactNode;
  data: Record<string, any>;
  validationResult: ValidationResult;
  uncertainFieldsInFile: UncertainField[];
}

interface ConfidenceIndicator {
  level: 'high' | 'medium' | 'low';
  color: string;
  bgColor: string;
  icon: React.ReactNode;
  message: string;
}

const FILE_TYPE_DISPLAY_NAMES: Record<string, string> = {
  'character': 'Basic Character Info',
  'character_background': 'Background & Personality',
  'feats_and_traits': 'Feats & Traits',
  'action_list': 'Actions & Abilities',
  'inventory_list': 'Equipment & Inventory',
  'objectives_and_contracts': 'Objectives & Contracts',
  'spell_list': 'Spells & Magic'
};

const CONFIDENCE_INDICATORS: Record<string, ConfidenceIndicator> = {
  high: {
    level: 'high',
    color: 'text-green-400',
    bgColor: 'bg-green-900/20 border-green-700',
    icon: <CheckCircle className="h-4 w-4" />,
    message: 'High confidence - data appears accurate'
  },
  medium: {
    level: 'medium',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-900/20 border-yellow-700',
    icon: <AlertTriangle className="h-4 w-4" />,
    message: 'Medium confidence - please review highlighted fields'
  },
  low: {
    level: 'low',
    color: 'text-red-400',
    bgColor: 'bg-red-900/20 border-red-700',
    icon: <AlertCircle className="h-4 w-4" />,
    message: 'Low confidence - manual review recommended'
  }
};

export const CharacterDataReview: React.FC<CharacterDataReviewProps> = ({
  parsedData,
  uncertainFields,
  onFieldEdit,
  onFinalize,
  onReparse,
  isLoading = false
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['character']));
  const [editingFields, setEditingFields] = useState<Set<string>>(new Set());
  const [characterName, setCharacterName] = useState<string>('');
  const [showUncertainOnly, setShowUncertainOnly] = useState(false);

  // Extract character name from parsed data
  useEffect(() => {
    const characterData = parsedData.character_files?.character;
    if (characterData?.character_base?.name) {
      setCharacterName(characterData.character_base.name);
    }
  }, [parsedData]);

  // Organize data by file sections
  const fileSections: FileSection[] = useMemo(() => {
    const sections: FileSection[] = [];
    
    Object.entries(parsedData.character_files || {}).forEach(([fileType, data]) => {
      const validationResult = parsedData.validation_results?.[fileType] || {
        is_valid: true,
        errors: [],
        warnings: []
      };
      
      const uncertainFieldsInFile = uncertainFields.filter(field => field.file_type === fileType);
      
      sections.push({
        fileType,
        displayName: FILE_TYPE_DISPLAY_NAMES[fileType] || fileType,
        icon: getFileTypeIcon(fileType),
        data: data || {},
        validationResult,
        uncertainFieldsInFile
      });
    });
    
    return sections.sort((a, b) => {
      const order = ['character', 'character_background', 'feats_and_traits', 'action_list', 'inventory_list', 'spell_list', 'objectives_and_contracts'];
      return order.indexOf(a.fileType) - order.indexOf(b.fileType);
    });
  }, [parsedData, uncertainFields]);

  // Calculate overall confidence
  const overallConfidence: ConfidenceIndicator = useMemo(() => {
    const confidence = parsedData.parsing_confidence || 0;
    if (confidence >= 0.8) return CONFIDENCE_INDICATORS.high;
    if (confidence >= 0.6) return CONFIDENCE_INDICATORS.medium;
    return CONFIDENCE_INDICATORS.low;
  }, [parsedData.parsing_confidence]);

  const toggleSection = useCallback((sectionKey: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionKey)) {
      newExpanded.delete(sectionKey);
    } else {
      newExpanded.add(sectionKey);
    }
    setExpandedSections(newExpanded);
  }, [expandedSections]);

  const toggleFieldEdit = useCallback((fieldKey: string) => {
    const newEditing = new Set(editingFields);
    if (newEditing.has(fieldKey)) {
      newEditing.delete(fieldKey);
    } else {
      newEditing.add(fieldKey);
    }
    setEditingFields(newEditing);
  }, [editingFields]);

  const handleFieldChange = useCallback((fileType: string, fieldPath: string, value: any) => {
    onFieldEdit(fileType, fieldPath, value);
  }, [onFieldEdit]);

  const handleFinalize = useCallback(() => {
    if (!characterName.trim()) {
      alert('Please enter a character name before finalizing.');
      return;
    }
    onFinalize(characterName.trim());
  }, [characterName, onFinalize]);

  const getFieldValue = useCallback((data: Record<string, any>, fieldPath: string): any => {
    return fieldPath.split('.').reduce((obj, key) => obj?.[key], data);
  }, []);

  const isFieldUncertain = useCallback((fileType: string, fieldPath: string): UncertainField | undefined => {
    return uncertainFields.find(field => field.file_type === fileType && field.field_path === fieldPath);
  }, [uncertainFields]);

  const hasValidationErrors = useMemo(() => {
    return fileSections.some(section => section.validationResult.errors.length > 0);
  }, [fileSections]);

  const totalUncertainFields = uncertainFields.length;
  const totalValidationErrors = fileSections.reduce((sum, section) => sum + section.validationResult.errors.length, 0);

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Review Character Data</h2>
          <p className="text-gray-400">
            Review and edit the extracted character information. Fields marked with uncertainty require your attention.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowUncertainOnly(!showUncertainOnly)}
            className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
              showUncertainOnly 
                ? 'bg-yellow-600 hover:bg-yellow-700 text-white' 
                : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
            }`}
          >
            {showUncertainOnly ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
            {showUncertainOnly ? 'Show All' : 'Show Uncertain Only'}
          </button>
          <button
            onClick={onReparse}
            disabled={isLoading}
            className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Re-parse PDF
          </button>
        </div>
      </div>

      {/* Overall Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Parsing Confidence */}
        <div className={`p-4 rounded-lg border ${overallConfidence.bgColor}`}>
          <div className="flex items-center mb-2">
            <div className={overallConfidence.color}>
              {overallConfidence.icon}
            </div>
            <h3 className="text-white font-medium ml-2">Parsing Confidence</h3>
          </div>
          <p className={`text-sm mb-1 ${overallConfidence.color}`}>
            {Math.round((parsedData.parsing_confidence || 0) * 100)}% - {overallConfidence.message}
          </p>
        </div>

        {/* Uncertain Fields */}
        <div className={`p-4 rounded-lg border ${
          totalUncertainFields > 0 ? 'bg-yellow-900/20 border-yellow-700' : 'bg-green-900/20 border-green-700'
        }`}>
          <div className="flex items-center mb-2">
            <AlertTriangle className={`h-4 w-4 ${totalUncertainFields > 0 ? 'text-yellow-400' : 'text-green-400'}`} />
            <h3 className="text-white font-medium ml-2">Uncertain Fields</h3>
          </div>
          <p className={`text-sm ${totalUncertainFields > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
            {totalUncertainFields} field{totalUncertainFields !== 1 ? 's' : ''} need{totalUncertainFields === 1 ? 's' : ''} review
          </p>
        </div>

        {/* Validation Status */}
        <div className={`p-4 rounded-lg border ${
          hasValidationErrors ? 'bg-red-900/20 border-red-700' : 'bg-green-900/20 border-green-700'
        }`}>
          <div className="flex items-center mb-2">
            {hasValidationErrors ? (
              <AlertCircle className="h-4 w-4 text-red-400" />
            ) : (
              <CheckCircle className="h-4 w-4 text-green-400" />
            )}
            <h3 className="text-white font-medium ml-2">Validation Status</h3>
          </div>
          <p className={`text-sm ${hasValidationErrors ? 'text-red-400' : 'text-green-400'}`}>
            {hasValidationErrors ? `${totalValidationErrors} validation error${totalValidationErrors !== 1 ? 's' : ''}` : 'All data valid'}
          </p>
        </div>
      </div>

      {/* Character Name Input */}
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center mb-3">
          <FileText className="h-5 w-5 text-purple-400" />
          <h3 className="text-white font-medium ml-2">Character Name</h3>
        </div>
        <input
          type="text"
          value={characterName}
          onChange={(e) => setCharacterName(e.target.value)}
          placeholder="Enter character name for the imported files"
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          required
        />
        <p className="text-xs text-gray-400 mt-1">
          This will be used as the base name for all generated character files.
        </p>
      </div>

      {/* File Sections */}
      <div className="space-y-4">
        {fileSections.map((section) => {
          const isExpanded = expandedSections.has(section.fileType);
          const shouldShowSection = !showUncertainOnly || section.uncertainFieldsInFile.length > 0;
          
          if (!shouldShowSection) return null;

          return (
            <ValidationProvider key={section.fileType} filename={`${section.fileType}.json`}>
              <FileSection
                section={section}
                isExpanded={isExpanded}
                onToggle={() => toggleSection(section.fileType)}
                onFieldChange={handleFieldChange}
                editingFields={editingFields}
                onToggleEdit={toggleFieldEdit}
                getFieldValue={getFieldValue}
                isFieldUncertain={isFieldUncertain}
                showUncertainOnly={showUncertainOnly}
              />
            </ValidationProvider>
          );
        })}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-6 border-t border-gray-700">
        <button
          onClick={onReparse}
          disabled={isLoading}
          className="inline-flex items-center px-6 py-3 text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Re-parse PDF
        </button>

        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-400">
            {totalUncertainFields > 0 && (
              <span className="text-yellow-400">
                {totalUncertainFields} field{totalUncertainFields !== 1 ? 's' : ''} need review
              </span>
            )}
            {hasValidationErrors && (
              <span className="text-red-400 ml-3">
                {totalValidationErrors} validation error{totalValidationErrors !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          <button
            onClick={handleFinalize}
            disabled={!characterName.trim() || isLoading}
            className="inline-flex items-center px-6 py-3 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="h-4 w-4 mr-2" />
            Create Character Files
          </button>
        </div>
      </div>

      {/* Help Text */}
      <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
        <div className="flex items-start">
          <Info className="h-5 w-5 text-blue-400 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <p className="text-blue-300 font-medium mb-1">Review Guidelines</p>
            <ul className="text-blue-200 text-sm space-y-1">
              <li>• Yellow highlighted fields indicate uncertainty - please verify these values</li>
              <li>• Red indicators show validation errors that must be fixed</li>
              <li>• Click the edit icon next to any field to modify its value</li>
              <li>• Use "Show Uncertain Only" to focus on fields that need attention</li>
              <li>• All character files will be created with the name you specify above</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper component for individual file sections
interface FileSectionProps {
  section: FileSection;
  isExpanded: boolean;
  onToggle: () => void;
  onFieldChange: (fileType: string, fieldPath: string, value: any) => void;
  editingFields: Set<string>;
  onToggleEdit: (fieldKey: string) => void;
  getFieldValue: (data: Record<string, any>, fieldPath: string) => any;
  isFieldUncertain: (fileType: string, fieldPath: string) => UncertainField | undefined;
  showUncertainOnly: boolean;
}

const FileSection: React.FC<FileSectionProps> = ({
  section,
  isExpanded,
  onToggle,
  onFieldChange,
  editingFields,
  onToggleEdit,
  getFieldValue,
  isFieldUncertain,
  showUncertainOnly
}) => {
  const hasErrors = section.validationResult.errors.length > 0;
  const hasUncertainFields = section.uncertainFieldsInFile.length > 0;

  return (
    <div className="border border-gray-600 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 bg-gray-750 hover:bg-gray-700 transition-colors"
      >
        <div className="flex items-center space-x-3">
          {section.icon}
          <h3 className="text-lg font-medium text-white">{section.displayName}</h3>
          {hasErrors && (
            <span className="px-2 py-1 text-xs bg-red-900/30 text-red-300 rounded">
              {section.validationResult.errors.length} error{section.validationResult.errors.length !== 1 ? 's' : ''}
            </span>
          )}
          {hasUncertainFields && (
            <span className="px-2 py-1 text-xs bg-yellow-900/30 text-yellow-300 rounded">
              {section.uncertainFieldsInFile.length} uncertain
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronRight className="w-5 h-5 text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="p-4 bg-gray-800 border-t border-gray-600">
          <FieldRenderer
            data={section.data}
            fileType={section.fileType}
            parentPath=""
            onFieldChange={onFieldChange}
            editingFields={editingFields}
            onToggleEdit={onToggleEdit}
            getFieldValue={getFieldValue}
            isFieldUncertain={isFieldUncertain}
            validationErrors={section.validationResult.errors}
            showUncertainOnly={showUncertainOnly}
          />
        </div>
      )}
    </div>
  );
};

// Helper component for rendering fields recursively
interface FieldRendererProps {
  data: Record<string, any>;
  fileType: string;
  parentPath: string;
  onFieldChange: (fileType: string, fieldPath: string, value: any) => void;
  editingFields: Set<string>;
  onToggleEdit: (fieldKey: string) => void;
  getFieldValue: (data: Record<string, any>, fieldPath: string) => any;
  isFieldUncertain: (fileType: string, fieldPath: string) => UncertainField | undefined;
  validationErrors: ValidationError[];
  showUncertainOnly: boolean;
}

const FieldRenderer: React.FC<FieldRendererProps> = ({
  data,
  fileType,
  parentPath,
  onFieldChange,
  editingFields,
  onToggleEdit,
  isFieldUncertain,
  validationErrors,
  showUncertainOnly
}) => {
  const renderField = (key: string, value: any, currentPath: string) => {
    const fieldPath = currentPath ? `${currentPath}.${key}` : key;
    const fieldKey = `${fileType}.${fieldPath}`;
    const isEditing = editingFields.has(fieldKey);
    const uncertainField = isFieldUncertain(fileType, fieldPath);
    const fieldErrors = validationErrors.filter(error => error.field_path === fieldPath);
    const hasError = fieldErrors.length > 0;
    
    // Skip field if showing uncertain only and field is not uncertain
    if (showUncertainOnly && !uncertainField) {
      return null;
    }

    if (value && typeof value === 'object' && !Array.isArray(value)) {
      // Render nested object
      return (
        <div key={fieldPath} className="space-y-2">
          <div className="flex items-center space-x-2">
            <h4 className="text-sm font-medium text-white capitalize">
              {key.replace(/_/g, ' ')}
            </h4>
            {uncertainField && (
              <span className="px-2 py-1 text-xs bg-yellow-900/30 text-yellow-300 rounded">
                Uncertain
              </span>
            )}
          </div>
          <div className="ml-4 space-y-2 border-l border-gray-600 pl-4">
            {Object.entries(value).map(([nestedKey, nestedValue]) =>
              renderField(nestedKey, nestedValue, fieldPath)
            )}
          </div>
        </div>
      );
    }

    if (Array.isArray(value)) {
      // Render array
      return (
        <div key={fieldPath} className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <h4 className="text-sm font-medium text-white capitalize">
                {key.replace(/_/g, ' ')} ({value.length} items)
              </h4>
              {uncertainField && (
                <span className="px-2 py-1 text-xs bg-yellow-900/30 text-yellow-300 rounded">
                  Uncertain
                </span>
              )}
            </div>
          </div>
          <div className="ml-4 space-y-2">
            {value.map((item, index) => (
              <div key={index} className="p-2 bg-gray-700 rounded border-l-2 border-gray-600">
                {typeof item === 'object' ? (
                  Object.entries(item).map(([itemKey, itemValue]) => (
                    <div key={itemKey} className="text-sm">
                      <span className="text-gray-400">{itemKey}:</span>
                      <span className="text-white ml-2">{String(itemValue)}</span>
                    </div>
                  ))
                ) : (
                  <span className="text-white text-sm">{String(item)}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      );
    }

    // Render primitive field
    return (
      <div key={fieldPath} className={`space-y-2 ${uncertainField ? 'bg-yellow-900/10 p-2 rounded border border-yellow-700' : ''}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-white capitalize">
              {key.replace(/_/g, ' ')}
            </label>
            {uncertainField && (
              <div className="flex items-center space-x-1">
                <span className="px-2 py-1 text-xs bg-yellow-900/30 text-yellow-300 rounded">
                  {Math.round(uncertainField.confidence * 100)}% confident
                </span>
                <div title={`Suggestions: ${uncertainField.suggestions.join(', ')}`}>
                  <Info className="h-3 w-3 text-yellow-400" />
                </div>
              </div>
            )}
            {hasError && (
              <AlertCircle className="h-4 w-4 text-red-400" />
            )}
          </div>
          <button
            onClick={() => onToggleEdit(fieldKey)}
            className="text-gray-400 hover:text-white transition-colors"
          >
            {isEditing ? <Check className="h-4 w-4" /> : <Edit3 className="h-4 w-4" />}
          </button>
        </div>

        {isEditing ? (
          <input
            type={typeof value === 'number' ? 'number' : 'text'}
            value={value || ''}
            onChange={(e) => {
              const newValue = typeof value === 'number' ? Number(e.target.value) : e.target.value;
              onFieldChange(fileType, fieldPath, newValue);
            }}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        ) : (
          <div className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white">
            {value !== null && value !== undefined ? String(value) : <span className="text-gray-400 italic">Not set</span>}
          </div>
        )}

        {uncertainField && uncertainField.suggestions.length > 0 && (
          <div className="text-xs text-yellow-300">
            <span className="font-medium">Suggestions:</span> {uncertainField.suggestions.join(', ')}
          </div>
        )}

        {fieldErrors.map((error, index) => (
          <div key={index} className="flex items-center space-x-2 text-sm text-red-400">
            <AlertCircle className="w-4 h-4" />
            <span>{error.message}</span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {Object.entries(data).map(([key, value]) => renderField(key, value, parentPath))}
    </div>
  );
};

// Helper function to get appropriate icon for file type
function getFileTypeIcon(fileType: string): React.ReactNode {
  const iconMap: Record<string, React.ReactNode> = {
    character: <FileText className="w-5 h-5 text-purple-400" />,
    character_background: <FileText className="w-5 h-5 text-blue-400" />,
    feats_and_traits: <FileText className="w-5 h-5 text-green-400" />,
    action_list: <FileText className="w-5 h-5 text-red-400" />,
    inventory_list: <FileText className="w-5 h-5 text-yellow-400" />,
    spell_list: <FileText className="w-5 h-5 text-indigo-400" />,
    objectives_and_contracts: <FileText className="w-5 h-5 text-orange-400" />
  };
  
  return iconMap[fileType] || <FileText className="w-5 h-5 text-gray-400" />;
}