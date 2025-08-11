import { useState, useCallback, useEffect, useRef } from 'react';
import { 
  ValidationError, 
  ValidationResult, 
  validateFileContent, 
  getFileSchema 
} from '../services/knowledgeBaseApi';

interface ValidationState {
  errors: ValidationError[];
  warnings: string[];
  isValidating: boolean;
  lastValidated: Date | null;
  schema: Record<string, any> | null;
}

interface UseValidationOptions {
  filename?: string;
  fileType?: string;
  validateOnChange?: boolean;
  debounceMs?: number;
  enableClientSideValidation?: boolean;
}

export function useValidation({
  filename,
  fileType,
  validateOnChange = true,
  debounceMs = 500,
  enableClientSideValidation = true
}: UseValidationOptions = {}) {
  const [validationState, setValidationState] = useState<ValidationState>({
    errors: [],
    warnings: [],
    isValidating: false,
    lastValidated: null,
    schema: null
  });

  const validationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isValidatingRef = useRef(false);

  // Load schema when filename or fileType changes
  useEffect(() => {
    if (fileType) {
      getFileSchema(fileType)
        .then(schema => {
          setValidationState(prev => ({ ...prev, schema }));
        })
        .catch(error => {
          console.error('Failed to load schema:', error);
        });
    }
  }, [fileType]);

  // Client-side field validation using JSON schema
  const validateField = useCallback((fieldPath: string, value: any): ValidationError[] => {
    if (!enableClientSideValidation || !validationState.schema) {
      return [];
    }

    const errors: ValidationError[] = [];
    const schema = validationState.schema;

    // Navigate to the field schema
    const pathParts = fieldPath.split('.');
    let currentSchema = schema;
    
    for (const part of pathParts) {
      if (currentSchema?.properties?.[part]) {
        currentSchema = currentSchema.properties[part];
      } else if (currentSchema?.items?.properties?.[part]) {
        currentSchema = currentSchema.items.properties[part];
      } else {
        // Schema path not found, skip validation
        return errors;
      }
    }

    // Required field validation
    if (currentSchema?.required && (value === null || value === undefined || value === '')) {
      errors.push({
        field_path: fieldPath,
        message: `${getFieldLabel(fieldPath)} is required`,
        error_type: 'required'
      });
      return errors;
    }

    // Skip other validations if field is empty and not required
    if (value === null || value === undefined || value === '') {
      return errors;
    }

    // Type validation
    const expectedType = currentSchema?.type;
    const actualType = Array.isArray(value) ? 'array' : typeof value;

    if (expectedType && expectedType !== actualType) {
      errors.push({
        field_path: fieldPath,
        message: `${getFieldLabel(fieldPath)} must be of type ${expectedType}`,
        error_type: 'type'
      });
      return errors; // Don't continue with other validations if type is wrong
    }

    // Number validations
    if (expectedType === 'number' && typeof value === 'number') {
      if (currentSchema.minimum !== undefined && value < currentSchema.minimum) {
        errors.push({
          field_path: fieldPath,
          message: `${getFieldLabel(fieldPath)} must be at least ${currentSchema.minimum}`,
          error_type: 'custom'
        });
      }
      if (currentSchema.maximum !== undefined && value > currentSchema.maximum) {
        errors.push({
          field_path: fieldPath,
          message: `${getFieldLabel(fieldPath)} must be at most ${currentSchema.maximum}`,
          error_type: 'custom'
        });
      }
      if (currentSchema.multipleOf !== undefined && value % currentSchema.multipleOf !== 0) {
        errors.push({
          field_path: fieldPath,
          message: `${getFieldLabel(fieldPath)} must be a multiple of ${currentSchema.multipleOf}`,
          error_type: 'custom'
        });
      }
    }

    // String validations
    if (expectedType === 'string' && typeof value === 'string') {
      if (currentSchema.minLength !== undefined && value.length < currentSchema.minLength) {
        errors.push({
          field_path: fieldPath,
          message: `${getFieldLabel(fieldPath)} must be at least ${currentSchema.minLength} characters`,
          error_type: 'custom'
        });
      }
      if (currentSchema.maxLength !== undefined && value.length > currentSchema.maxLength) {
        errors.push({
          field_path: fieldPath,
          message: `${getFieldLabel(fieldPath)} must be at most ${currentSchema.maxLength} characters`,
          error_type: 'custom'
        });
      }
      if (currentSchema.pattern) {
        try {
          const regex = new RegExp(currentSchema.pattern);
          if (!regex.test(value)) {
            errors.push({
              field_path: fieldPath,
              message: `${getFieldLabel(fieldPath)} format is invalid`,
              error_type: 'format'
            });
          }
        } catch (e) {
          console.warn('Invalid regex pattern in schema:', currentSchema.pattern);
        }
      }
    }

    // Array validations
    if (expectedType === 'array' && Array.isArray(value)) {
      if (currentSchema.minItems !== undefined && value.length < currentSchema.minItems) {
        errors.push({
          field_path: fieldPath,
          message: `${getFieldLabel(fieldPath)} must have at least ${currentSchema.minItems} items`,
          error_type: 'custom'
        });
      }
      if (currentSchema.maxItems !== undefined && value.length > currentSchema.maxItems) {
        errors.push({
          field_path: fieldPath,
          message: `${getFieldLabel(fieldPath)} must have at most ${currentSchema.maxItems} items`,
          error_type: 'custom'
        });
      }
    }

    // Enum validation
    if (currentSchema.enum && !currentSchema.enum.includes(value)) {
      errors.push({
        field_path: fieldPath,
        message: `${getFieldLabel(fieldPath)} must be one of: ${currentSchema.enum.join(', ')}`,
        error_type: 'custom'
      });
    }

    return errors;
  }, [validationState.schema, enableClientSideValidation]);

  // Server-side validation
  const validateWithServer = useCallback(async (data: Record<string, any>): Promise<ValidationResult> => {
    if (!filename) {
      throw new Error('Filename is required for server validation');
    }

    setValidationState(prev => ({ ...prev, isValidating: true }));
    isValidatingRef.current = true;

    try {
      const result = await validateFileContent(filename, data);
      
      setValidationState(prev => ({
        ...prev,
        errors: result.errors,
        warnings: result.warnings,
        isValidating: false,
        lastValidated: new Date()
      }));

      isValidatingRef.current = false;
      return result;
    } catch (error) {
      console.error('Server validation failed:', error);
      
      const fallbackResult: ValidationResult = {
        is_valid: false,
        errors: [{
          field_path: 'root',
          message: 'Validation service unavailable',
          error_type: 'custom'
        }],
        warnings: []
      };

      setValidationState(prev => ({
        ...prev,
        errors: fallbackResult.errors,
        warnings: fallbackResult.warnings,
        isValidating: false,
        lastValidated: new Date()
      }));

      isValidatingRef.current = false;
      return fallbackResult;
    }
  }, [filename]);

  // Debounced server validation
  const debouncedServerValidation = useCallback((data: Record<string, any>) => {
    if (validationTimeoutRef.current) {
      clearTimeout(validationTimeoutRef.current);
    }

    validationTimeoutRef.current = setTimeout(() => {
      if (!isValidatingRef.current) {
        validateWithServer(data);
      }
    }, debounceMs);
  }, [validateWithServer, debounceMs]);

  // Combined validation (client + server)
  const validate = useCallback(async (data: Record<string, any>, useServer: boolean = true): Promise<ValidationResult> => {
    // Always do client-side validation first for immediate feedback
    const clientErrors: ValidationError[] = [];
    
    if (enableClientSideValidation && validationState.schema) {
      // Validate all fields in the data
      const validateObject = (obj: any, basePath: string = '') => {
        Object.entries(obj).forEach(([key, value]) => {
          const fieldPath = basePath ? `${basePath}.${key}` : key;
          
          if (value && typeof value === 'object' && !Array.isArray(value)) {
            validateObject(value, fieldPath);
          } else {
            const fieldErrors = validateField(fieldPath, value);
            clientErrors.push(...fieldErrors);
          }
        });
      };

      validateObject(data);
    }

    // Update state with client-side errors immediately
    setValidationState(prev => ({
      ...prev,
      errors: clientErrors,
      warnings: prev.warnings // Keep existing warnings
    }));

    // If server validation is requested and we have a filename
    if (useServer && filename) {
      if (validateOnChange) {
        // Use debounced validation for real-time updates
        debouncedServerValidation(data);
        // Return client-side result immediately
        return {
          is_valid: clientErrors.length === 0,
          errors: clientErrors,
          warnings: validationState.warnings
        };
      } else {
        // Use immediate server validation
        return await validateWithServer(data);
      }
    }

    // Return client-side validation result
    return {
      is_valid: clientErrors.length === 0,
      errors: clientErrors,
      warnings: validationState.warnings
    };
  }, [
    enableClientSideValidation,
    validationState.schema,
    validationState.warnings,
    validateField,
    filename,
    validateOnChange,
    debouncedServerValidation,
    validateWithServer
  ]);

  // Get errors for a specific field
  const getFieldErrors = useCallback((fieldPath: string): ValidationError[] => {
    return validationState.errors.filter(error => error.field_path === fieldPath);
  }, [validationState.errors]);

  // Clear all validation state
  const clearValidation = useCallback(() => {
    setValidationState(prev => ({
      ...prev,
      errors: [],
      warnings: [],
      lastValidated: null
    }));

    if (validationTimeoutRef.current) {
      clearTimeout(validationTimeoutRef.current);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (validationTimeoutRef.current) {
        clearTimeout(validationTimeoutRef.current);
      }
    };
  }, []);

  return {
    // State
    errors: validationState.errors,
    warnings: validationState.warnings,
    isValidating: validationState.isValidating,
    lastValidated: validationState.lastValidated,
    schema: validationState.schema,
    hasErrors: validationState.errors.length > 0,
    hasWarnings: validationState.warnings.length > 0,
    isValid: validationState.errors.length === 0,

    // Methods
    validate,
    validateField,
    validateWithServer,
    getFieldErrors,
    clearValidation
  };
}

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