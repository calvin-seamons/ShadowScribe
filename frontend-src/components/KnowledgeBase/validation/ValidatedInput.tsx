import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { useValidation } from './ValidationProvider';
import { ValidationError } from '../../../services/knowledgeBaseApi';

interface ValidatedInputProps {
  fieldPath: string;
  label: string;
  value: any;
  onChange: (value: any) => void;
  type?: 'text' | 'number' | 'email' | 'password' | 'tel' | 'url';
  required?: boolean;
  placeholder?: string;
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  className?: string;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  debounceMs?: number;
}

export const ValidatedInput: React.FC<ValidatedInputProps> = ({
  fieldPath,
  label,
  value,
  onChange,
  type = 'text',
  required = false,
  placeholder,
  min,
  max,
  step,
  disabled = false,
  className = '',
  validateOnChange = true,
  validateOnBlur = true,
  debounceMs = 300
}) => {
  const { validateField, getFieldErrors, setUnsavedChanges } = useValidation();
  const [localValue, setLocalValue] = useState(value);
  const [isValidating, setIsValidating] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<ValidationError[]>([]);
  const [touched, setTouched] = useState(false);

  // Debounced validation
  const [validationTimeout, setValidationTimeout] = useState<NodeJS.Timeout | null>(null);

  // Update local value when prop value changes
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  // Get current field errors from validation context
  useEffect(() => {
    const errors = getFieldErrors(fieldPath);
    setFieldErrors(errors);
  }, [fieldPath, getFieldErrors]);

  const performValidation = useCallback((valueToValidate: any) => {
    if (!touched && !validateOnChange) return;

    setIsValidating(true);
    const errors = validateField(fieldPath, valueToValidate);
    setFieldErrors(errors);
    setIsValidating(false);
  }, [fieldPath, validateField, touched, validateOnChange]);

  const debouncedValidation = useCallback((valueToValidate: any) => {
    if (validationTimeout) {
      clearTimeout(validationTimeout);
    }

    const timeout = setTimeout(() => {
      performValidation(valueToValidate);
    }, debounceMs);

    setValidationTimeout(timeout);
  }, [performValidation, debounceMs, validationTimeout]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = type === 'number' 
      ? (e.target.value ? Number(e.target.value) : '') 
      : e.target.value;
    
    setLocalValue(newValue);
    onChange(newValue);
    setUnsavedChanges(true);

    if (validateOnChange) {
      debouncedValidation(newValue);
    }
  };

  const handleBlur = () => {
    setTouched(true);
    if (validateOnBlur) {
      performValidation(localValue);
    }
  };

  const handleFocus = () => {
    setTouched(true);
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (validationTimeout) {
        clearTimeout(validationTimeout);
      }
    };
  }, [validationTimeout]);

  const hasErrors = fieldErrors.length > 0;
  const showValidation = touched || validateOnChange;

  const getInputClassName = () => {
    let baseClasses = 'w-full px-3 py-2 bg-gray-700 border rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 transition-colors';
    
    if (disabled) {
      baseClasses += ' bg-gray-600 text-gray-400 cursor-not-allowed';
    } else if (showValidation) {
      if (hasErrors) {
        baseClasses += ' border-red-500 focus:ring-red-500';
      } else if (touched && !isValidating) {
        baseClasses += ' border-green-500 focus:ring-green-500';
      } else {
        baseClasses += ' border-gray-600 focus:ring-purple-500';
      }
    } else {
      baseClasses += ' border-gray-600 focus:ring-purple-500';
    }

    return `${baseClasses} ${className}`;
  };

  const getValidationIcon = () => {
    if (!showValidation) return null;
    
    if (isValidating) {
      return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
    }
    
    if (hasErrors) {
      return <AlertCircle className="w-4 h-4 text-red-400" />;
    }
    
    if (touched && !isValidating) {
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    }
    
    return null;
  };

  return (
    <div className="space-y-2" data-field-path={fieldPath}>
      <label className="block text-sm font-medium text-white">
        {label}
        {required && <span className="text-red-400 ml-1">*</span>}
      </label>
      
      <div className="relative">
        <input
          type={type}
          value={String(localValue || '')}
          onChange={handleChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          placeholder={placeholder}
          min={min}
          max={max}
          step={step}
          disabled={disabled}
          className={getInputClassName()}
          name={fieldPath}
        />
        
        {/* Validation Icon */}
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          {getValidationIcon()}
        </div>
      </div>

      {/* Error Messages */}
      {showValidation && hasErrors && (
        <div className="space-y-1">
          {fieldErrors.map((error, index) => (
            <div key={index} className="flex items-center space-x-2 text-sm text-red-400">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};