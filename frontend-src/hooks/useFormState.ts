import { useState, useEffect, useCallback, useRef } from 'react';
import { ValidationError } from '../services/knowledgeBaseApi';

interface FormState<T> {
  data: T;
  originalData: T;
  errors: ValidationError[];
  isValid: boolean;
  isDirty: boolean;
  isSubmitting: boolean;
  hasUnsavedChanges: boolean;
}

interface UseFormStateOptions<T> {
  initialData: T;
  onValidate?: (data: T) => ValidationError[] | Promise<ValidationError[]>;
  onSubmit?: (data: T) => Promise<void> | void;
  validateOnChange?: boolean;
  debounceMs?: number;
}

export function useFormState<T extends Record<string, any>>({
  initialData,
  onValidate,
  onSubmit,
  validateOnChange = true,
  debounceMs = 300
}: UseFormStateOptions<T>) {
  const [formState, setFormState] = useState<FormState<T>>({
    data: initialData,
    originalData: initialData,
    errors: [],
    isValid: true,
    isDirty: false,
    isSubmitting: false,
    hasUnsavedChanges: false
  });

  const validationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isValidatingRef = useRef(false);

  // Deep comparison helper
  const deepEqual = useCallback((obj1: any, obj2: any): boolean => {
    if (obj1 === obj2) return true;
    if (obj1 == null || obj2 == null) return false;
    if (typeof obj1 !== typeof obj2) return false;

    if (typeof obj1 !== 'object') return obj1 === obj2;

    if (Array.isArray(obj1) !== Array.isArray(obj2)) return false;

    const keys1 = Object.keys(obj1);
    const keys2 = Object.keys(obj2);

    if (keys1.length !== keys2.length) return false;

    for (const key of keys1) {
      if (!keys2.includes(key)) return false;
      if (!deepEqual(obj1[key], obj2[key])) return false;
    }

    return true;
  }, []);

  // Validate data
  const validateData = useCallback(async (data: T): Promise<ValidationError[]> => {
    if (!onValidate) return [];

    try {
      const result = await onValidate(data);
      return result;
    } catch (error) {
      console.error('Validation error:', error);
      return [{
        field_path: 'root',
        message: 'Validation failed',
        error_type: 'custom'
      }];
    }
  }, [onValidate]);

  // Debounced validation
  const debouncedValidation = useCallback(async (data: T) => {
    if (validationTimeoutRef.current) {
      clearTimeout(validationTimeoutRef.current);
    }

    validationTimeoutRef.current = setTimeout(async () => {
      if (isValidatingRef.current) return;
      
      isValidatingRef.current = true;
      const errors = await validateData(data);
      
      setFormState(prev => ({
        ...prev,
        errors,
        isValid: errors.length === 0
      }));
      
      isValidatingRef.current = false;
    }, debounceMs);
  }, [validateData, debounceMs]);

  // Update form data
  const updateData = useCallback((newData: T | ((prev: T) => T)) => {
    setFormState(prev => {
      const updatedData = typeof newData === 'function' ? newData(prev.data) : newData;
      const isDirty = !deepEqual(updatedData, prev.originalData);
      const hasUnsavedChanges = isDirty;

      // Trigger validation if enabled
      if (validateOnChange && onValidate) {
        debouncedValidation(updatedData);
      }

      return {
        ...prev,
        data: updatedData,
        isDirty,
        hasUnsavedChanges
      };
    });
  }, [deepEqual, validateOnChange, onValidate, debouncedValidation]);

  // Update a specific field
  const updateField = useCallback((fieldPath: string, value: any) => {
    updateData(prev => {
      const keys = fieldPath.split('.');
      const newData = { ...prev };
      let current: any = newData;

      // Navigate to the parent of the target field
      for (let i = 0; i < keys.length - 1; i++) {
        if (current[keys[i]] === null || current[keys[i]] === undefined) {
          current[keys[i]] = {};
        } else {
          current[keys[i]] = { ...current[keys[i]] };
        }
        current = current[keys[i]];
      }

      // Set the field value
      current[keys[keys.length - 1]] = value;
      return newData;
    });
  }, [updateData]);

  // Reset form to original state
  const reset = useCallback(() => {
    setFormState(prev => ({
      ...prev,
      data: prev.originalData,
      errors: [],
      isValid: true,
      isDirty: false,
      isSubmitting: false,
      hasUnsavedChanges: false
    }));

    if (validationTimeoutRef.current) {
      clearTimeout(validationTimeoutRef.current);
    }
  }, []);

  // Reset with new data
  const resetWithData = useCallback((newData: T) => {
    setFormState({
      data: newData,
      originalData: newData,
      errors: [],
      isValid: true,
      isDirty: false,
      isSubmitting: false,
      hasUnsavedChanges: false
    });

    if (validationTimeoutRef.current) {
      clearTimeout(validationTimeoutRef.current);
    }
  }, []);

  // Submit form
  const submit = useCallback(async () => {
    if (!onSubmit) return;

    setFormState(prev => ({ ...prev, isSubmitting: true }));

    try {
      // Validate before submit
      const errors = await validateData(formState.data);
      
      if (errors.length > 0) {
        setFormState(prev => ({
          ...prev,
          errors,
          isValid: false,
          isSubmitting: false
        }));
        return false;
      }

      // Submit data
      await onSubmit(formState.data);

      // Update original data and reset dirty state
      setFormState(prev => ({
        ...prev,
        originalData: prev.data,
        errors: [],
        isValid: true,
        isDirty: false,
        isSubmitting: false,
        hasUnsavedChanges: false
      }));

      return true;
    } catch (error) {
      console.error('Submit error:', error);
      setFormState(prev => ({
        ...prev,
        errors: [{
          field_path: 'root',
          message: error instanceof Error ? error.message : 'Submit failed',
          error_type: 'custom'
        }],
        isValid: false,
        isSubmitting: false
      }));
      return false;
    }
  }, [onSubmit, validateData, formState.data]);

  // Manual validation trigger
  const validate = useCallback(async () => {
    const errors = await validateData(formState.data);
    setFormState(prev => ({
      ...prev,
      errors,
      isValid: errors.length === 0
    }));
    return errors;
  }, [validateData, formState.data]);

  // Get field value
  const getFieldValue = useCallback((fieldPath: string) => {
    const keys = fieldPath.split('.');
    let current: any = formState.data;

    for (const key of keys) {
      if (current === null || current === undefined) return undefined;
      current = current[key];
    }

    return current;
  }, [formState.data]);

  // Get field errors
  const getFieldErrors = useCallback((fieldPath: string): ValidationError[] => {
    return formState.errors.filter(error => error.field_path === fieldPath);
  }, [formState.errors]);

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
    ...formState,
    
    // Actions
    updateData,
    updateField,
    reset,
    resetWithData,
    submit,
    validate,
    
    // Helpers
    getFieldValue,
    getFieldErrors
  };
}