import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { useValidation } from './ValidationProvider';
import { ValidationError } from '../../../services/knowledgeBaseApi';

interface ValidatedTextareaProps {
  fieldPath: string;
  label: string;
  value: any;
  onChange: (value: any) => void;
  required?: boolean;
  placeholder?: string;
  rows?: number;
  disabled?: boolean;
  className?: string;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  debounceMs?: number;
  maxLength?: number;
  showCharCount?: boolean;
}

export const ValidatedTextarea: React.FC<ValidatedTextareaProps> = ({
  fieldPath,
  label,
  value,
  onChange,
  required = false,
  placeholder,
  rows = 4,
  disabled = false,
  className = '',
  validateOnChange = true,
  validateOnBlur = true,
  debounceMs = 300,
  maxLength,
  showCharCount = false
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

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    
    // Enforce max length if specified
    if (maxLength && newValue.length > maxLength) {
      return;
    }
    
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
  const currentLength = String(localValue || '').length;

  const getTextareaClassName = () => {
    let baseClasses = 'w-full px-3 py-2 bg-gray-700 border rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 transition-colors resize-vertical';
    
    if (disabled) {
      baseClasses += ' bg-gray-600 text-gray-400 cursor-not-allowed resize-none';
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
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-white">
          {label}
          {required && <span className="text-red-400 ml-1">*</span>}
        </label>
        
        {/* Character Count */}
        {(showCharCount || maxLength) && (
          <div className="flex items-center space-x-2 text-xs text-gray-400">
            {getValidationIcon()}
            <span>
              {currentLength}
              {maxLength && `/${maxLength}`}
            </span>
          </div>
        )}
      </div>
      
      <div className="relative">
        <textarea
          value={String(localValue || '')}
          onChange={handleChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          placeholder={placeholder}
          rows={rows}
          disabled={disabled}
          className={getTextareaClassName()}
          name={fieldPath}
          maxLength={maxLength}
        />
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