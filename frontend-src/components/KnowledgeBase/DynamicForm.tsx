import React, { useState, useEffect, useCallback } from 'react';
import { ChevronDown, ChevronRight, AlertCircle, Info } from 'lucide-react';
import { ArrayEditor } from './ArrayEditor';
import { FeatsTraitsEditor } from './FeatsTraitsEditor';
import { ActionListEditor } from './ActionListEditor';
import { InventoryEditor } from './InventoryEditor';
import { ObjectivesEditor } from './ObjectivesEditor';
import { SpellListEditor } from './SpellListEditor';
import { ValidationError } from '../../services/knowledgeBaseApi';

interface FormField {
  key: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  label: string;
  required: boolean;
  description?: string;
  validation?: ValidationRule[];
  children?: FormField[];
  items?: FormField; // For array items
  enum?: string[]; // For enum values
  minimum?: number;
  maximum?: number;
  pattern?: string;
}

interface ValidationRule {
  type: 'required' | 'min' | 'max' | 'pattern' | 'custom';
  value?: any;
  message: string;
}

interface DynamicFormProps {
  schema: Record<string, any>;
  data: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
  onValidationErrors: (errors: ValidationError[]) => void;
  fileType: string;
}

export const DynamicForm: React.FC<DynamicFormProps> = ({
  schema,
  data,
  onChange,
  onValidationErrors,
  fileType
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['root']));
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);

  // Convert JSON schema to form fields
  const convertSchemaToFields = useCallback((
    schemaObj: any, 
    parentKey: string = ''
  ): FormField[] => {
    if (!schemaObj || typeof schemaObj !== 'object') return [];

    const properties = schemaObj.properties || {};
    const required = schemaObj.required || [];

    return Object.entries(properties).map(([key, prop]: [string, any]) => {
      const fullKey = parentKey ? `${parentKey}.${key}` : key;
      const isRequired = required.includes(key);

      let fieldType: FormField['type'] = 'string';
      let children: FormField[] | undefined;
      let items: FormField | undefined;

      if (prop.type === 'object' && prop.properties) {
        fieldType = 'object';
        children = convertSchemaToFields(prop, fullKey);
      } else if (prop.type === 'array') {
        fieldType = 'array';
        if (prop.items) {
          if (prop.items.type === 'object' && prop.items.properties) {
            items = {
              key: `${fullKey}[]`,
              type: 'object',
              label: 'Item',
              required: false,
              children: convertSchemaToFields(prop.items, `${fullKey}[]`)
            };
          } else {
            items = {
              key: `${fullKey}[]`,
              type: prop.items.type || 'string',
              label: 'Item',
              required: false,
              enum: prop.items.enum
            };
          }
        }
      } else if (prop.type === 'number' || prop.type === 'integer') {
        fieldType = 'number';
      } else if (prop.type === 'boolean') {
        fieldType = 'boolean';
      }

      return {
        key: fullKey,
        type: fieldType,
        label: prop.title || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        required: isRequired,
        description: prop.description,
        children,
        items,
        enum: prop.enum,
        minimum: prop.minimum,
        maximum: prop.maximum,
        pattern: prop.pattern
      };
    });
  }, []);

  const [formFields, setFormFields] = useState<FormField[]>([]);

  useEffect(() => {
    const fields = convertSchemaToFields(schema);
    setFormFields(fields);
  }, [schema, convertSchemaToFields]);

  // Get nested value from object using dot notation
  const getNestedValue = (obj: any, path: string): any => {
    return path.split('.').reduce((current, key) => {
      return current && current[key] !== undefined ? current[key] : undefined;
    }, obj);
  };

  // Set nested value in object using dot notation
  const setNestedValue = (obj: any, path: string, value: any): any => {
    const keys = path.split('.');
    const result = { ...obj };
    let current = result;

    for (let i = 0; i < keys.length - 1; i++) {
      const key = keys[i];
      if (!current[key] || typeof current[key] !== 'object') {
        current[key] = {};
      } else {
        current[key] = { ...current[key] };
      }
      current = current[key];
    }

    const lastKey = keys[keys.length - 1];
    if (value === undefined || value === '') {
      delete current[lastKey];
    } else {
      current[lastKey] = value;
    }

    return result;
  };

  const handleFieldChange = (fieldKey: string, value: any) => {
    const newData = setNestedValue(data, fieldKey, value);
    onChange(newData);
  };

  const toggleSection = (sectionKey: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionKey)) {
      newExpanded.delete(sectionKey);
    } else {
      newExpanded.add(sectionKey);
    }
    setExpandedSections(newExpanded);
  };

  const validateField = (field: FormField, value: any): ValidationError[] => {
    const errors: ValidationError[] = [];

    if (field.required && (value === undefined || value === null || value === '')) {
      errors.push({
        field_path: field.key,
        message: `${field.label} is required`,
        error_type: 'required'
      });
    }

    if (value !== undefined && value !== null && value !== '') {
      if (field.type === 'number') {
        const numValue = Number(value);
        if (isNaN(numValue)) {
          errors.push({
            field_path: field.key,
            message: `${field.label} must be a valid number`,
            error_type: 'type'
          });
        } else {
          if (field.minimum !== undefined && numValue < field.minimum) {
            errors.push({
              field_path: field.key,
              message: `${field.label} must be at least ${field.minimum}`,
              error_type: 'custom'
            });
          }
          if (field.maximum !== undefined && numValue > field.maximum) {
            errors.push({
              field_path: field.key,
              message: `${field.label} must be at most ${field.maximum}`,
              error_type: 'custom'
            });
          }
        }
      }

      if (field.type === 'string' && field.pattern) {
        const regex = new RegExp(field.pattern);
        if (!regex.test(String(value))) {
          errors.push({
            field_path: field.key,
            message: `${field.label} format is invalid`,
            error_type: 'format'
          });
        }
      }

      if (field.enum && !field.enum.includes(value)) {
        errors.push({
          field_path: field.key,
          message: `${field.label} must be one of: ${field.enum.join(', ')}`,
          error_type: 'custom'
        });
      }
    }

    return errors;
  };

  // Validate all fields and update errors
  useEffect(() => {
    const validateAllFields = (fields: FormField[], currentData: any): ValidationError[] => {
      let allErrors: ValidationError[] = [];

      fields.forEach(field => {
        const value = getNestedValue(currentData, field.key);
        const fieldErrors = validateField(field, value);
        allErrors = [...allErrors, ...fieldErrors];

        if (field.children) {
          const childErrors = validateAllFields(field.children, currentData);
          allErrors = [...allErrors, ...childErrors];
        }
      });

      return allErrors;
    };

    const errors = validateAllFields(formFields, data);
    setValidationErrors(errors);
    onValidationErrors(errors);
  }, [data, formFields, onValidationErrors]);

  const renderField = (field: FormField, level: number = 0): React.ReactNode => {
    const value = getNestedValue(data, field.key);
    const hasError = validationErrors.some(error => error.field_path === field.key);
    const fieldErrors = validationErrors.filter(error => error.field_path === field.key);

    const baseClasses = "w-full px-3 py-2 bg-gray-700 border rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500";
    const errorClasses = hasError ? "border-red-500" : "border-gray-600";

    if (field.type === 'object' && field.children) {
      const isExpanded = expandedSections.has(field.key);
      return (
        <div key={field.key} className="space-y-2">
          <button
            type="button"
            onClick={() => toggleSection(field.key)}
            className="flex items-center space-x-2 text-left w-full p-2 rounded-md hover:bg-gray-700 transition-colors"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-400" />
            )}
            <span className="font-medium text-white">{field.label}</span>
            {field.required && <span className="text-red-400">*</span>}
          </button>
          
          {field.description && (
            <div className="flex items-start space-x-2 text-sm text-gray-400 ml-6">
              <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <p>{field.description}</p>
            </div>
          )}

          {isExpanded && field.children && (
            <div className="ml-6 space-y-4 border-l border-gray-600 pl-4">
              {field.children.map(childField => renderField(childField, level + 1))}
            </div>
          )}
        </div>
      );
    }

    if (field.type === 'array') {
      return (
        <div key={field.key} className="space-y-2">
          <label className="block text-sm font-medium text-white">
            {field.label}
            {field.required && <span className="text-red-400 ml-1">*</span>}
          </label>
          
          {field.description && (
            <div className="flex items-start space-x-2 text-sm text-gray-400">
              <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <p>{field.description}</p>
            </div>
          )}

          <ArrayEditor
            items={value || []}
            onChange={(newItems) => handleFieldChange(field.key, newItems)}
            itemSchema={field.items}
            label={field.label}
          />

          {fieldErrors.map((error, index) => (
            <div key={index} className="flex items-center space-x-2 text-sm text-red-400">
              <AlertCircle className="w-4 h-4" />
              <span>{error.message}</span>
            </div>
          ))}
        </div>
      );
    }

    return (
      <div key={field.key} className="space-y-2">
        <label className="block text-sm font-medium text-white">
          {field.label}
          {field.required && <span className="text-red-400 ml-1">*</span>}
        </label>

        {field.description && (
          <div className="flex items-start space-x-2 text-sm text-gray-400">
            <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <p>{field.description}</p>
          </div>
        )}

        {field.type === 'boolean' ? (
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={value || false}
              onChange={(e) => handleFieldChange(field.key, e.target.checked)}
              className="rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500"
            />
            <span className="text-sm text-gray-300">Enable {field.label}</span>
          </label>
        ) : field.enum ? (
          <select
            value={value || ''}
            onChange={(e) => handleFieldChange(field.key, e.target.value)}
            className={`${baseClasses} ${errorClasses}`}
          >
            <option value="">Select {field.label}</option>
            {field.enum.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        ) : field.type === 'number' ? (
          <input
            type="number"
            value={value || ''}
            onChange={(e) => handleFieldChange(field.key, e.target.value ? Number(e.target.value) : undefined)}
            min={field.minimum}
            max={field.maximum}
            className={`${baseClasses} ${errorClasses}`}
            placeholder={`Enter ${field.label.toLowerCase()}`}
          />
        ) : (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleFieldChange(field.key, e.target.value)}
            pattern={field.pattern}
            className={`${baseClasses} ${errorClasses}`}
            placeholder={`Enter ${field.label.toLowerCase()}`}
          />
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

  // Use specialized editor for feats_and_traits
  if (fileType === 'feats_and_traits') {
    return (
      <div className="h-full flex flex-col">
        <div className="flex-1 overflow-y-auto p-4">
          <FeatsTraitsEditor
            data={data as any}
            onChange={onChange}
            validationErrors={validationErrors}
          />
        </div>
      </div>
    );
  }

  // Use specialized editor for action_list
  if (fileType === 'action_list') {
    return (
      <div className="h-full flex flex-col">
        <div className="flex-1 overflow-y-auto p-4">
          <ActionListEditor
            data={data as any}
            onChange={onChange}
            validationErrors={validationErrors}
          />
        </div>
      </div>
    );
  }

  // Use specialized editor for inventory_list
  if (fileType === 'inventory_list') {
    return (
      <div className="h-full flex flex-col">
        <div className="flex-1 overflow-y-auto p-4">
          <InventoryEditor
            data={data as any}
            onChange={onChange}
            validationErrors={validationErrors}
          />
        </div>
      </div>
    );
  }

  // Use specialized editor for objectives_and_contracts
  if (fileType === 'objectives_and_contracts') {
    return (
      <div className="h-full flex flex-col">
        <div className="flex-1 overflow-y-auto p-4">
          <ObjectivesEditor
            data={data as any}
            onChange={onChange}
            validationErrors={validationErrors}
          />
        </div>
      </div>
    );
  }

  // Use specialized editor for spell_list
  if (fileType === 'spell_list') {
    return (
      <div className="h-full flex flex-col">
        <div className="flex-1 overflow-y-auto p-4">
          <SpellListEditor
            data={data as any}
            onChange={onChange}
            validationErrors={validationErrors}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-medium text-white capitalize">
          {fileType.replace(/_/g, ' ')} Editor
        </h3>
        <p className="text-sm text-gray-400 mt-1">
          Edit the fields below. Required fields are marked with *
        </p>
      </div>

      {/* Form Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-6 max-w-4xl">
          {formFields.map(field => renderField(field))}
        </div>
      </div>
    </div>
  );
};