import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { ValidationError, ValidationResult, validateFileContent, getFileSchema } from '../../../services/knowledgeBaseApi';

interface ValidationState {
  errors: ValidationError[];
  warnings: string[];
  isValidating: boolean;
  hasUnsavedChanges: boolean;
  lastValidated: Date | null;
}

interface ValidationContextType {
  validationState: ValidationState;
  validateField: (fieldPath: string, value: any, schema?: any) => ValidationError[];
  validateForm: (filename: string, data: Record<string, any>) => Promise<ValidationResult>;
  clearValidation: () => void;
  setUnsavedChanges: (hasChanges: boolean) => void;
  getFieldErrors: (fieldPath: string) => ValidationError[];
  hasErrors: boolean;
  hasWarnings: boolean;
}

const ValidationContext = createContext<ValidationContextType | null>(null);

export const useValidation = () => {
  const context = useContext(ValidationContext);
  if (!context) {
    throw new Error('useValidation must be used within a ValidationProvider');
  }
  return context;
};

interface ValidationProviderProps {
  children: React.ReactNode;
  filename?: string;
  schema?: Record<string, any>;
}

export const ValidationProvider: React.FC<ValidationProviderProps> = ({
  children,
  filename,
  schema: initialSchema
}) => {
  const [validationState, setValidationState] = useState<ValidationState>({
    errors: [],
    warnings: [],
    isValidating: false,
    hasUnsavedChanges: false,
    lastValidated: null
  });

  const [schema, setSchema] = useState<Record<string, any> | null>(initialSchema || null);

  // Load schema if filename is provided and schema is not already loaded
  useEffect(() => {
    if (filename && !schema) {
      const fileType = getFileTypeFromFilename(filename);
      if (fileType !== 'other') {
        getFileSchema(fileType)
          .then(setSchema)
          .catch(console.error);
      }
    }
  }, [filename, schema]);

  const validateField = useCallback((fieldPath: string, value: any, fieldSchema?: any): ValidationError[] => {
    const errors: ValidationError[] = [];
    const currentSchema = fieldSchema || schema;

    if (!currentSchema) return errors;

    // Navigate to the field schema
    const pathParts = fieldPath.split('.');
    let currentSchemaNode = currentSchema;
    
    for (const part of pathParts) {
      if (currentSchemaNode?.properties?.[part]) {
        currentSchemaNode = currentSchemaNode.properties[part];
      } else if (currentSchemaNode?.items?.properties?.[part]) {
        currentSchemaNode = currentSchemaNode.items.properties[part];
      } else {
        // Schema path not found, skip validation
        return errors;
      }
    }

    // Required field validation
    if (currentSchemaNode?.required && (value === null || value === undefined || value === '')) {
      errors.push({
        field_path: fieldPath,
        message: `${getFieldLabel(fieldPath)} is required`,
        error_type: 'required'
      });
      return errors; // Don't continue with other validations if required field is empty
    }

    // Type validation
    if (value !== null && value !== undefined && value !== '') {
      const expectedType = currentSchemaNode?.type;
      const actualType = Array.isArray(value) ? 'array' : typeof value;

      if (expectedType && expectedType !== actualType) {
        errors.push({
          field_path: fieldPath,
          message: `${getFieldLabel(fieldPath)} must be of type ${expectedType}`,
          error_type: 'type'
        });
      }

      // Number range validation
      if (expectedType === 'number' && typeof value === 'number') {
        if (currentSchemaNode.minimum !== undefined && value < currentSchemaNode.minimum) {
          errors.push({
            field_path: fieldPath,
            message: `${getFieldLabel(fieldPath)} must be at least ${currentSchemaNode.minimum}`,
            error_type: 'custom'
          });
        }
        if (currentSchemaNode.maximum !== undefined && value > currentSchemaNode.maximum) {
          errors.push({
            field_path: fieldPath,
            message: `${getFieldLabel(fieldPath)} must be at most ${currentSchemaNode.maximum}`,
            error_type: 'custom'
          });
        }
      }

      // String length validation
      if (expectedType === 'string' && typeof value === 'string') {
        if (currentSchemaNode.minLength !== undefined && value.length < currentSchemaNode.minLength) {
          errors.push({
            field_path: fieldPath,
            message: `${getFieldLabel(fieldPath)} must be at least ${currentSchemaNode.minLength} characters`,
            error_type: 'custom'
          });
        }
        if (currentSchemaNode.maxLength !== undefined && value.length > currentSchemaNode.maxLength) {
          errors.push({
            field_path: fieldPath,
            message: `${getFieldLabel(fieldPath)} must be at most ${currentSchemaNode.maxLength} characters`,
            error_type: 'custom'
          });
        }
      }

      // Pattern validation
      if (currentSchemaNode.pattern && typeof value === 'string') {
        const regex = new RegExp(currentSchemaNode.pattern);
        if (!regex.test(value)) {
          errors.push({
            field_path: fieldPath,
            message: `${getFieldLabel(fieldPath)} format is invalid`,
            error_type: 'format'
          });
        }
      }

      // Enum validation
      if (currentSchemaNode.enum && !currentSchemaNode.enum.includes(value)) {
        errors.push({
          field_path: fieldPath,
          message: `${getFieldLabel(fieldPath)} must be one of: ${currentSchemaNode.enum.join(', ')}`,
          error_type: 'custom'
        });
      }
    }

    return errors;
  }, [schema]);

  const validateForm = useCallback(async (filename: string, data: Record<string, any>): Promise<ValidationResult> => {
    setValidationState(prev => ({ ...prev, isValidating: true }));

    try {
      const result = await validateFileContent(filename, data);
      
      setValidationState(prev => ({
        ...prev,
        errors: result.errors,
        warnings: result.warnings,
        isValidating: false,
        lastValidated: new Date()
      }));

      return result;
    } catch (error) {
      console.error('Validation failed:', error);
      
      setValidationState(prev => ({
        ...prev,
        errors: [{
          field_path: 'root',
          message: 'Validation service unavailable',
          error_type: 'custom'
        }],
        warnings: [],
        isValidating: false,
        lastValidated: new Date()
      }));

      return {
        is_valid: false,
        errors: [{
          field_path: 'root',
          message: 'Validation service unavailable',
          error_type: 'custom'
        }],
        warnings: []
      };
    }
  }, []);

  const clearValidation = useCallback(() => {
    setValidationState({
      errors: [],
      warnings: [],
      isValidating: false,
      hasUnsavedChanges: false,
      lastValidated: null
    });
  }, []);

  const setUnsavedChanges = useCallback((hasChanges: boolean) => {
    setValidationState(prev => ({
      ...prev,
      hasUnsavedChanges: hasChanges
    }));
  }, []);

  const getFieldErrors = useCallback((fieldPath: string): ValidationError[] => {
    return validationState.errors.filter(error => error.field_path === fieldPath);
  }, [validationState.errors]);

  const hasErrors = validationState.errors.length > 0;
  const hasWarnings = validationState.warnings.length > 0;

  const contextValue: ValidationContextType = {
    validationState,
    validateField,
    validateForm,
    clearValidation,
    setUnsavedChanges,
    getFieldErrors,
    hasErrors,
    hasWarnings
  };

  return (
    <ValidationContext.Provider value={contextValue}>
      {children}
    </ValidationContext.Provider>
  );
};

// Helper function to get a human-readable field label
function getFieldLabel(fieldPath: string): string {
  const parts = fieldPath.split('.');
  const lastPart = parts[parts.length - 1];
  
  // Convert snake_case to Title Case
  return lastPart
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Helper function to determine file type from filename
function getFileTypeFromFilename(filename: string): string {
  const lowerFilename = filename.toLowerCase();
  
  if (lowerFilename.includes('character_background')) return 'character_background';
  if (lowerFilename.includes('feats_and_traits')) return 'feats_and_traits';
  if (lowerFilename.includes('action_list')) return 'action_list';
  if (lowerFilename.includes('inventory_list')) return 'inventory_list';
  if (lowerFilename.includes('objectives_and_contracts')) return 'objectives_and_contracts';
  if (lowerFilename.includes('spell_list')) return 'spell_list';
  if (lowerFilename.includes('character.json')) return 'character';
  
  return 'other';
}