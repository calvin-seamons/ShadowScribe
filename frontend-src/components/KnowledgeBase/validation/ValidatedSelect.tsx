import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, CheckCircle, ChevronDown } from 'lucide-react';
import { useValidation } from './ValidationProvider';
import { ValidationError } from '../../../services/knowledgeBaseApi';

interface ValidatedSelectProps {
  fieldPath: string;
  label: string;
  value: any;
  onChange: (value: any) => void;
  options: Array<{ value: string | number; label: string }> | string[];
  required?: boolean;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
}

export const ValidatedSelect: React.FC<ValidatedSelectProps> = ({
  fieldPath,
  label,
  value,
  onChange,
  options,
  required = false,
  placeholder = 'Select...',
  disabled = false,
  className = '',
  validateOnChange = true,
  validateOnBlur = true
}) => {
  const { validateField, getFieldErrors, setUnsavedChanges } = useValidation();
  const [fieldErrors, setFieldErrors] = useState<ValidationError[]>([]);
  const [touched, setTouched] = useState(false);

  // Get current field errors from validation context
  useEffect(() => {
    const errors = getFieldErrors(fieldPath);
    setFieldErrors(errors);
  }, [fieldPath, getFieldErrors]);

  const performValidation = useCallback((valueToValidate: any) => {
    if (!touched && !validateOnChange) return;

    const errors = validateField(fieldPath, valueToValidate);
    setFieldErrors(errors);
  }, [fieldPath, validateField, touched, validateOnChange]);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    setUnsavedChanges(true);

    if (validateOnChange) {
      performValidation(newValue);
    }
  };

  const handleBlur = () => {
    setTouched(true);
    if (validateOnBlur) {
      performValidation(value);
    }
  };

  const handleFocus = () => {
    setTouched(true);
  };

  const hasErrors = fieldErrors.length > 0;
  const showValidation = touched || validateOnChange;

  const getSelectClassName = () => {
    let baseClasses = 'w-full px-3 py-2 bg-gray-700 border rounded-md text-white focus:outline-none focus:ring-2 transition-colors appearance-none';
    
    if (disabled) {
      baseClasses += ' bg-gray-600 text-gray-400 cursor-not-allowed';
    } else if (showValidation) {
      if (hasErrors) {
        baseClasses += ' border-red-500 focus:ring-red-500';
      } else if (touched) {
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
    
    if (hasErrors) {
      return <AlertCircle className="w-4 h-4 text-red-400" />;
    }
    
    if (touched) {
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    }
    
    return null;
  };

  // Normalize options to consistent format
  const normalizedOptions = options.map(option => 
    typeof option === 'string' 
      ? { value: option, label: option }
      : option
  );

  return (
    <div className="space-y-2" data-field-path={fieldPath}>
      <label className="block text-sm font-medium text-white">
        {label}
        {required && <span className="text-red-400 ml-1">*</span>}
      </label>
      
      <div className="relative">
        <select
          value={String(value || '')}
          onChange={handleChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          disabled={disabled}
          className={getSelectClassName()}
          name={fieldPath}
        >
          <option value="">{placeholder}</option>
          {normalizedOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        
        {/* Dropdown Icon and Validation Icon */}
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          <div className="flex items-center space-x-1">
            {getValidationIcon()}
            <ChevronDown className="w-4 h-4 text-gray-400" />
          </div>
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