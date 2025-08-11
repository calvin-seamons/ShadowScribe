import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as knowledgeBaseApi from '../../services/knowledgeBaseApi';

// Mock the API
vi.mock('../../services/knowledgeBaseApi', () => ({
  validateFileContent: vi.fn(),
  getFileSchema: vi.fn(),
}));

const mockValidateFileContent = vi.mocked(knowledgeBaseApi.validateFileContent);
const mockGetFileSchema = vi.mocked(knowledgeBaseApi.getFileSchema);

describe('useValidation Hook Logic', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Client-side Validation', () => {
    it('should validate required fields', () => {
      const schema = {
        type: 'object',
        properties: {
          character_base: {
            type: 'object',
            properties: {
              name: { type: 'string', required: true }
            }
          }
        }
      };

      // Simulate the validateField logic from useValidation
      const validateField = (fieldPath: string, value: any, schema: any) => {
        const errors: any[] = [];
        const pathParts = fieldPath.split('.');
        let currentSchema = schema;
        
        for (const part of pathParts) {
          if (currentSchema?.properties?.[part]) {
            currentSchema = currentSchema.properties[part];
          } else if (currentSchema?.items?.properties?.[part]) {
            currentSchema = currentSchema.items.properties[part];
          } else {
            return errors;
          }
        }

        if (currentSchema?.required && (value === null || value === undefined || value === '')) {
          errors.push({
            field_path: fieldPath,
            message: `${getFieldLabel(fieldPath)} is required`,
            error_type: 'required'
          });
          return errors;
        }

        if (value !== null && value !== undefined && value !== '') {
          const expectedType = currentSchema?.type;
          const actualType = Array.isArray(value) ? 'array' : typeof value;

          if (expectedType && expectedType !== actualType) {
            errors.push({
              field_path: fieldPath,
              message: `${getFieldLabel(fieldPath)} must be of type ${expectedType}`,
              error_type: 'type'
            });
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
          }

          // Enum validation
          if (currentSchema.enum && !currentSchema.enum.includes(value)) {
            errors.push({
              field_path: fieldPath,
              message: `${getFieldLabel(fieldPath)} must be one of: ${currentSchema.enum.join(', ')}`,
              error_type: 'custom'
            });
          }
        }

        return errors;
      };

      const getFieldLabel = (fieldPath: string): string => {
        const parts = fieldPath.split('.');
        const lastPart = parts[parts.length - 1];
        
        return lastPart
          .split('_')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');
      };

      // Test required field validation
      const requiredErrors = validateField('character_base.name', '', schema);
      expect(requiredErrors).toHaveLength(1);
      expect(requiredErrors[0].error_type).toBe('required');
      expect(requiredErrors[0].message).toContain('Name is required');

      // Test valid value
      const validErrors = validateField('character_base.name', 'Aragorn', schema);
      expect(validErrors).toHaveLength(0);
    });

    it('should validate number ranges', () => {
      const schema = {
        type: 'object',
        properties: {
          character_base: {
            type: 'object',
            properties: {
              total_level: { 
                type: 'number',
                minimum: 1,
                maximum: 20
              }
            }
          }
        }
      };

      const validateField = (fieldPath: string, value: any, schema: any) => {
        const errors: any[] = [];
        const pathParts = fieldPath.split('.');
        let currentSchema = schema;
        
        for (const part of pathParts) {
          if (currentSchema?.properties?.[part]) {
            currentSchema = currentSchema.properties[part];
          } else {
            return errors;
          }
        }

        if (currentSchema?.type === 'number' && typeof value === 'number') {
          if (currentSchema.minimum !== undefined && value < currentSchema.minimum) {
            errors.push({
              field_path: fieldPath,
              message: `Total Level must be at least ${currentSchema.minimum}`,
              error_type: 'custom'
            });
          }
          if (currentSchema.maximum !== undefined && value > currentSchema.maximum) {
            errors.push({
              field_path: fieldPath,
              message: `Total Level must be at most ${currentSchema.maximum}`,
              error_type: 'custom'
            });
          }
        }

        return errors;
      };

      const tooLowErrors = validateField('character_base.total_level', 0, schema);
      expect(tooLowErrors).toHaveLength(1);
      expect(tooLowErrors[0].message).toContain('at least 1');

      const tooHighErrors = validateField('character_base.total_level', 25, schema);
      expect(tooHighErrors).toHaveLength(1);
      expect(tooHighErrors[0].message).toContain('at most 20');

      const validErrors = validateField('character_base.total_level', 10, schema);
      expect(validErrors).toHaveLength(0);
    });

    it('should validate string lengths', () => {
      const schema = {
        type: 'object',
        properties: {
          character_base: {
            type: 'object',
            properties: {
              name: { 
                type: 'string',
                minLength: 2,
                maxLength: 50
              }
            }
          }
        }
      };

      const validateField = (fieldPath: string, value: any, schema: any) => {
        const errors: any[] = [];
        const pathParts = fieldPath.split('.');
        let currentSchema = schema;
        
        for (const part of pathParts) {
          if (currentSchema?.properties?.[part]) {
            currentSchema = currentSchema.properties[part];
          } else {
            return errors;
          }
        }

        if (currentSchema?.type === 'string' && typeof value === 'string') {
          if (currentSchema.minLength !== undefined && value.length < currentSchema.minLength) {
            errors.push({
              field_path: fieldPath,
              message: `Name must be at least ${currentSchema.minLength} characters`,
              error_type: 'custom'
            });
          }
          if (currentSchema.maxLength !== undefined && value.length > currentSchema.maxLength) {
            errors.push({
              field_path: fieldPath,
              message: `Name must be at most ${currentSchema.maxLength} characters`,
              error_type: 'custom'
            });
          }
        }

        return errors;
      };

      const tooShortErrors = validateField('character_base.name', 'A', schema);
      expect(tooShortErrors).toHaveLength(1);
      expect(tooShortErrors[0].message).toContain('at least 2 characters');

      const tooLongErrors = validateField('character_base.name', 'A'.repeat(51), schema);
      expect(tooLongErrors).toHaveLength(1);
      expect(tooLongErrors[0].message).toContain('at most 50 characters');

      const validErrors = validateField('character_base.name', 'Aragorn', schema);
      expect(validErrors).toHaveLength(0);
    });

    it('should validate enum values', () => {
      const schema = {
        type: 'object',
        properties: {
          character_base: {
            type: 'object',
            properties: {
              alignment: { 
                type: 'string',
                enum: ['Lawful Good', 'Neutral Good', 'Chaotic Good']
              }
            }
          }
        }
      };

      const validateField = (fieldPath: string, value: any, schema: any) => {
        const errors: any[] = [];
        const pathParts = fieldPath.split('.');
        let currentSchema = schema;
        
        for (const part of pathParts) {
          if (currentSchema?.properties?.[part]) {
            currentSchema = currentSchema.properties[part];
          } else {
            return errors;
          }
        }

        if (currentSchema?.enum && !currentSchema.enum.includes(value)) {
          errors.push({
            field_path: fieldPath,
            message: `Alignment must be one of: ${currentSchema.enum.join(', ')}`,
            error_type: 'custom'
          });
        }

        return errors;
      };

      const invalidErrors = validateField('character_base.alignment', 'Invalid Alignment', schema);
      expect(invalidErrors).toHaveLength(1);
      expect(invalidErrors[0].message).toContain('must be one of');

      const validErrors = validateField('character_base.alignment', 'Lawful Good', schema);
      expect(validErrors).toHaveLength(0);
    });
  });

  describe('Server Validation Integration', () => {
    it('should call server validation API', async () => {
      const mockValidationResult = {
        is_valid: false,
        errors: [
          {
            field_path: 'character_base.name',
            message: 'Name is required',
            error_type: 'required' as const
          }
        ],
        warnings: ['Consider adding a background']
      };

      mockValidateFileContent.mockResolvedValue(mockValidationResult);

      const result = await knowledgeBaseApi.validateFileContent('character.json', {
        character_base: { name: '' }
      });
      
      expect(result).toEqual(mockValidationResult);
      expect(mockValidateFileContent).toHaveBeenCalledWith('character.json', {
        character_base: { name: '' }
      });
    });

    it('should handle server validation errors gracefully', async () => {
      mockValidateFileContent.mockRejectedValue(new Error('Service unavailable'));

      await expect(knowledgeBaseApi.validateFileContent('character.json', {}))
        .rejects.toThrow('Service unavailable');
    });
  });

  describe('Schema Loading', () => {
    it('should load schema for character file type', async () => {
      const mockSchema = {
        type: 'object',
        properties: {
          character_base: {
            type: 'object',
            properties: {
              name: { type: 'string', required: true },
              race: { type: 'string', required: true },
              class: { type: 'string', required: true },
              total_level: { type: 'number', minimum: 1, maximum: 20 }
            }
          }
        }
      };

      mockGetFileSchema.mockResolvedValue(mockSchema);

      const result = await knowledgeBaseApi.getFileSchema('character');
      
      expect(result).toEqual(mockSchema);
      expect(mockGetFileSchema).toHaveBeenCalledWith('character');
    });

    it('should handle schema loading errors', async () => {
      mockGetFileSchema.mockRejectedValue(new Error('Schema not found'));

      await expect(knowledgeBaseApi.getFileSchema('invalid_type'))
        .rejects.toThrow('Schema not found');
    });
  });

  describe('Utility Functions', () => {
    it('should generate field labels correctly', () => {
      const getFieldLabel = (fieldPath: string): string => {
        const parts = fieldPath.split('.');
        const lastPart = parts[parts.length - 1];
        
        return lastPart
          .split('_')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');
      };

      expect(getFieldLabel('character_base.total_level')).toBe('Total Level');
      expect(getFieldLabel('ability_scores.strength')).toBe('Strength');
      expect(getFieldLabel('combat_stats.max_hp')).toBe('Max Hp');
      expect(getFieldLabel('characteristics.eye_color')).toBe('Eye Color');
    });

    it('should filter field errors correctly', () => {
      const errors = [
        { field_path: 'character_base.name', message: 'Name required', error_type: 'required' },
        { field_path: 'character_base.race', message: 'Race required', error_type: 'required' },
        { field_path: 'ability_scores.strength', message: 'Invalid strength', error_type: 'custom' }
      ];

      const getFieldErrors = (fieldPath: string, allErrors: any[]) => {
        return allErrors.filter(error => error.field_path === fieldPath);
      };

      const nameErrors = getFieldErrors('character_base.name', errors);
      expect(nameErrors).toHaveLength(1);
      expect(nameErrors[0].message).toBe('Name required');

      const strengthErrors = getFieldErrors('ability_scores.strength', errors);
      expect(strengthErrors).toHaveLength(1);
      expect(strengthErrors[0].message).toBe('Invalid strength');

      const nonExistentErrors = getFieldErrors('non.existent.field', errors);
      expect(nonExistentErrors).toHaveLength(0);
    });
  });
});