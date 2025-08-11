# Real-time Validation System

This validation system provides comprehensive client-side and server-side validation for knowledge base editing with immediate feedback, error highlighting, and unsaved changes detection.

## Features

- **Real-time validation** with debounced server calls
- **Client-side validation** using JSON schemas for immediate feedback
- **Field-level validation** with visual indicators
- **Form state management** with unsaved changes detection
- **Error display components** with clear messaging
- **Validation summary** showing all current errors and warnings
- **Unsaved changes warnings** with browser navigation protection

## Components

### ValidationProvider

The main context provider that manages validation state and provides validation methods.

```tsx
import { ValidationProvider } from './validation';

<ValidationProvider filename="character.json" fileType="character">
  <YourFormComponent />
</ValidationProvider>
```

**Props:**
- `filename?: string` - File name for server validation
- `fileType?: string` - File type for schema loading
- `schema?: Record<string, any>` - Pre-loaded JSON schema
- `children: React.ReactNode` - Child components

### ValidatedInput

A text/number input with built-in validation and error display.

```tsx
import { ValidatedInput } from './validation';

<ValidatedInput
  fieldPath="character_base.name"
  label="Character Name"
  value={data.character_base.name}
  onChange={(value) => updateField('character_base.name', value)}
  required
  placeholder="Enter character name"
/>
```

**Props:**
- `fieldPath: string` - Dot-notation path to the field
- `label: string` - Field label
- `value: any` - Current field value
- `onChange: (value: any) => void` - Change handler
- `type?: 'text' | 'number' | 'email' | 'password' | 'tel' | 'url'` - Input type
- `required?: boolean` - Whether field is required
- `placeholder?: string` - Placeholder text
- `min?: number` - Minimum value (for numbers)
- `max?: number` - Maximum value (for numbers)
- `step?: number` - Step value (for numbers)
- `disabled?: boolean` - Whether input is disabled
- `validateOnChange?: boolean` - Validate on every change (default: true)
- `validateOnBlur?: boolean` - Validate on blur (default: true)
- `debounceMs?: number` - Debounce delay for validation (default: 300ms)

### ValidatedSelect

A select dropdown with validation and error display.

```tsx
import { ValidatedSelect } from './validation';

<ValidatedSelect
  fieldPath="character_base.race"
  label="Race"
  value={data.character_base.race}
  onChange={(value) => updateField('character_base.race', value)}
  options={['Human', 'Elf', 'Dwarf']}
  required
  placeholder="Select race"
/>
```

**Props:**
- `fieldPath: string` - Dot-notation path to the field
- `label: string` - Field label
- `value: any` - Current field value
- `onChange: (value: any) => void` - Change handler
- `options: Array<{ value: string | number; label: string }> | string[]` - Select options
- `required?: boolean` - Whether field is required
- `placeholder?: string` - Placeholder text
- `disabled?: boolean` - Whether select is disabled
- `validateOnChange?: boolean` - Validate on change (default: true)
- `validateOnBlur?: boolean` - Validate on blur (default: true)

### ValidatedTextarea

A textarea with validation, character counting, and error display.

```tsx
import { ValidatedTextarea } from './validation';

<ValidatedTextarea
  fieldPath="description"
  label="Character Description"
  value={data.description}
  onChange={(value) => updateField('description', value)}
  rows={6}
  maxLength={1000}
  showCharCount
/>
```

**Props:**
- `fieldPath: string` - Dot-notation path to the field
- `label: string` - Field label
- `value: any` - Current field value
- `onChange: (value: any) => void` - Change handler
- `required?: boolean` - Whether field is required
- `placeholder?: string` - Placeholder text
- `rows?: number` - Number of rows (default: 4)
- `disabled?: boolean` - Whether textarea is disabled
- `maxLength?: number` - Maximum character length
- `showCharCount?: boolean` - Show character count
- `validateOnChange?: boolean` - Validate on change (default: true)
- `validateOnBlur?: boolean` - Validate on blur (default: true)
- `debounceMs?: number` - Debounce delay for validation (default: 300ms)

### ValidationSummary

Displays a summary of all validation errors and warnings.

```tsx
import { ValidationSummary } from './validation';

<ValidationSummary 
  showWhenValid 
  onClose={() => setShowSummary(false)}
/>
```

**Props:**
- `onClose?: () => void` - Close handler
- `showWhenValid?: boolean` - Show summary even when valid (default: false)
- `className?: string` - Additional CSS classes

### UnsavedChangesWarning

Shows a warning when there are unsaved changes with save/discard options.

```tsx
import { UnsavedChangesWarning } from './validation';

<UnsavedChangesWarning
  onSave={handleSave}
  onDiscard={handleDiscard}
  position="floating"
/>
```

**Props:**
- `onSave?: () => void` - Save handler
- `onDiscard?: () => void` - Discard changes handler
- `onDismiss?: () => void` - Dismiss warning handler
- `showSaveButton?: boolean` - Show save button (default: true)
- `showDiscardButton?: boolean` - Show discard button (default: true)
- `position?: 'top' | 'bottom' | 'floating'` - Warning position (default: 'floating')

## Hooks

### useValidation

Access validation context and methods.

```tsx
import { useValidation } from './validation';

const {
  validationState,
  validateField,
  validateForm,
  clearValidation,
  setUnsavedChanges,
  getFieldErrors,
  hasErrors,
  hasWarnings
} = useValidation();
```

**Returns:**
- `validationState: ValidationState` - Current validation state
- `validateField: (fieldPath: string, value: any) => ValidationError[]` - Validate single field
- `validateForm: (filename: string, data: Record<string, any>) => Promise<ValidationResult>` - Validate entire form
- `clearValidation: () => void` - Clear all validation state
- `setUnsavedChanges: (hasChanges: boolean) => void` - Set unsaved changes flag
- `getFieldErrors: (fieldPath: string) => ValidationError[]` - Get errors for specific field
- `hasErrors: boolean` - Whether there are any errors
- `hasWarnings: boolean` - Whether there are any warnings

### useUnsavedChangesWarning

Hook for programmatic unsaved changes warning.

```tsx
import { useUnsavedChangesWarning } from './validation';

const hasUnsavedChanges = useUnsavedChangesWarning('Custom warning message');
```

## Usage Examples

### Basic Form with Validation

```tsx
import React, { useState } from 'react';
import { 
  ValidationProvider, 
  ValidationSummary, 
  ValidatedInput,
  UnsavedChangesWarning 
} from './validation';

const MyForm = () => {
  const [data, setData] = useState({ name: '', level: 1 });

  const updateField = (fieldPath: string, value: any) => {
    // Update nested field logic
    setData(prev => ({ ...prev, [fieldPath]: value }));
  };

  return (
    <ValidationProvider filename="character.json" fileType="character">
      <div className="space-y-6">
        <ValidationSummary showWhenValid />
        
        <ValidatedInput
          fieldPath="name"
          label="Character Name"
          value={data.name}
          onChange={(value) => updateField('name', value)}
          required
        />
        
        <ValidatedInput
          fieldPath="level"
          label="Level"
          type="number"
          value={data.level}
          onChange={(value) => updateField('level', value)}
          min={1}
          max={20}
          required
        />
        
        <UnsavedChangesWarning
          onSave={() => console.log('Save')}
          onDiscard={() => setData({ name: '', level: 1 })}
        />
      </div>
    </ValidationProvider>
  );
};
```

### Custom Validation Logic

```tsx
import { useValidation } from './validation';

const CustomComponent = () => {
  const { validateField, getFieldErrors } = useValidation();

  const handleCustomValidation = (value: string) => {
    const errors = validateField('custom.field', value);
    
    // Add custom validation logic
    if (value.includes('forbidden')) {
      errors.push({
        field_path: 'custom.field',
        message: 'Value contains forbidden text',
        error_type: 'custom'
      });
    }
    
    return errors;
  };

  // Component implementation...
};
```

## Validation Rules

The system supports various validation rules through JSON schemas:

### Required Fields
```json
{
  "type": "string",
  "required": true
}
```

### Type Validation
```json
{
  "type": "number"  // string, boolean, array, object
}
```

### Number Ranges
```json
{
  "type": "number",
  "minimum": 1,
  "maximum": 20,
  "multipleOf": 5
}
```

### String Length
```json
{
  "type": "string",
  "minLength": 2,
  "maxLength": 50
}
```

### Pattern Matching
```json
{
  "type": "string",
  "pattern": "^[A-Za-z]+$"
}
```

### Enum Values
```json
{
  "type": "string",
  "enum": ["option1", "option2", "option3"]
}
```

### Array Validation
```json
{
  "type": "array",
  "minItems": 1,
  "maxItems": 10,
  "items": {
    "type": "string"
  }
}
```

## Error Types

- `required` - Field is required but empty
- `type` - Value doesn't match expected type
- `format` - Value doesn't match expected format/pattern
- `custom` - Custom validation rule failed

## Best Practices

1. **Use ValidationProvider** at the top level of your form
2. **Set appropriate debounce delays** to balance responsiveness and performance
3. **Provide clear field labels** for better error messages
4. **Use client-side validation** for immediate feedback
5. **Always validate on the server** for security
6. **Handle validation errors gracefully** with user-friendly messages
7. **Show validation summary** for complex forms
8. **Warn users about unsaved changes** before navigation

## Testing

The validation system includes comprehensive tests for:
- Field validation logic
- Server integration
- Error handling
- Schema loading
- Utility functions

Run tests with:
```bash
npm test -- --run frontend-src/components/KnowledgeBase/validation/__tests__/
```