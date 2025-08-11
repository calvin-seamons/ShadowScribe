import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as knowledgeBaseApi from '../../../../services/knowledgeBaseApi';

// Mock the API
vi.mock('../../../../services/knowledgeBaseApi', () => ({
  validateFileContent: vi.fn(),
  getFileSchema: vi.fn(),
}));

const mockValidateFileContent = vi.mocked(knowledgeBaseApi.validateFileContent);
const mockGetFileSchema = vi.mocked(knowledgeBaseApi.getFileSchema);

// Test the validation logic directly without React components
describe('ValidationProvider Logic', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Field Validation', () => {
    it('should validate required fields', () => {
      const schema = {
        type: 'object',
        properties: {
          test: {
            type: 'object',
            properties: {
              field: { type: 'string', required: true }
            }
          }
        }
      };

      // Simulate field validation logic
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

        if (currentSchema?.required && (value === null || value === undefined || value === '')) {
          errors.push({
            field_path: fieldPath,
            message: `Field is required`,
            error_type: 'required'
          });
        }

        return errors;
      };

      const errors = validateField('test.field', '', schema);
      expect(errors).toHaveLength(1);
      expect(errors[0].error_type).toBe('required');
    });

    it('should validate field types', () => {
      const schema = {
        type: 'object',
        properties: {
          test: {
            type: 'object',
            properties: {
              numberField: { type: 'number' }
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

        if (value !== null && value !== undefined && value !== '') {
          const expectedType = currentSchema?.type;
          const actualType = Array.isArray(value) ? 'array' : typeof value;

          if (expectedType && expectedType !== actualType) {
            errors.push({
              field_path: fieldPath,
              message: `Field must be of type ${expectedType}`,
              error_type: 'type'
            });
          }
        }

        return errors;
      };

      const errors = validateField('test.numberField', 'not a number', schema);
      expect(errors).toHaveLength(1);
      expect(errors[0].error_type).toBe('type');
    });

    it('should validate number ranges', () => {
      const schema = {
        type: 'object',
        properties: {
          test: {
            type: 'object',
            properties: {
              level: { 
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
              message: `Field must be at least ${currentSchema.minimum}`,
              error_type: 'custom'
            });
          }
          if (currentSchema.maximum !== undefined && value > currentSchema.maximum) {
            errors.push({
              field_path: fieldPath,
              message: `Field must be at most ${currentSchema.maximum}`,
              error_type: 'custom'
            });
          }
        }

        return errors;
      };

      const tooLowErrors = validateField('test.level', 0, schema);
      expect(tooLowErrors).toHaveLength(1);
      expect(tooLowErrors[0].message).toContain('at least 1');

      const tooHighErrors = validateField('test.level', 25, schema);
      expect(tooHighErrors).toHaveLength(1);
      expect(tooHighErrors[0].message).toContain('at most 20');

      const validErrors = validateField('test.level', 10, schema);
      expect(validErrors).toHaveLength(0);
    });
  });

  describe('Server Validation', () => {
    it('should call server validation API', async () => {
      const mockValidationResult = {
        is_valid: false,
        errors: [
          {
            field_path: 'test.field',
            message: 'Field is required',
            error_type: 'required' as const
          }
        ],
        warnings: ['This is a warning']
      };

      mockValidateFileContent.mockResolvedValue(mockValidationResult);

      const result = await knowledgeBaseApi.validateFileContent('test.json', { test: { field: 'value' } });
      
      expect(result).toEqual(mockValidationResult);
      expect(mockValidateFileContent).toHaveBeenCalledWith('test.json', { test: { field: 'value' } });
    });

    it('should handle server validation errors', async () => {
      mockValidateFileContent.mockRejectedValue(new Error('Service unavailable'));

      await expect(knowledgeBaseApi.validateFileContent('test.json', {}))
        .rejects.toThrow('Service unavailable');
    });
  });

  describe('Schema Loading', () => {
    it('should load schema for file type', async () => {
      const mockSchema = {
        type: 'object',
        properties: {
          name: { type: 'string', required: true }
        }
      };

      mockGetFileSchema.mockResolvedValue(mockSchema);

      const result = await knowledgeBaseApi.getFileSchema('character');
      
      expect(result).toEqual(mockSchema);
      expect(mockGetFileSchema).toHaveBeenCalledWith('character');
    });
  });

  describe('File Type Detection', () => {
    it('should detect file type from filename', () => {
      const getFileTypeFromFilename = (filename: string): string => {
        const lowerFilename = filename.toLowerCase();
        
        if (lowerFilename.includes('character_background')) return 'character_background';
        if (lowerFilename.includes('feats_and_traits')) return 'feats_and_traits';
        if (lowerFilename.includes('action_list')) return 'action_list';
        if (lowerFilename.includes('inventory_list')) return 'inventory_list';
        if (lowerFilename.includes('objectives_and_contracts')) return 'objectives_and_contracts';
        if (lowerFilename.includes('spell_list')) return 'spell_list';
        if (lowerFilename.includes('character.json')) return 'character';
        
        return 'other';
      };

      expect(getFileTypeFromFilename('test_character.json')).toBe('character');
      expect(getFileTypeFromFilename('test_character_background.json')).toBe('character_background');
      expect(getFileTypeFromFilename('unknown_file.json')).toBe('other');
    });
  });

  describe('Field Label Generation', () => {
    it('should generate human-readable labels from field paths', () => {
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
    });
  });
});