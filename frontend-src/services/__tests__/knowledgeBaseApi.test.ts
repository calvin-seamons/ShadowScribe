/**
 * Tests for Knowledge Base API Service
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  listCharacters,
  listKnowledgeBaseFiles,
  getFileContent,
  updateFileContent,
  createFile,
  deleteFile,
  validateFileContent,
  getFileSchema,
  getFileTemplate,
  getSupportedFileTypes,
  createNewCharacter,
  listBackups,
  restoreBackup,
  executeBatchFileOperations,
  KnowledgeBaseApiError,
  isKnowledgeBaseApiError,
  getErrorMessage,
  getFileTypeFromFilename,
  FILE_TYPES,
} from '../knowledgeBaseApi';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Knowledge Base API Service', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('Character Management', () => {
    it('should list characters successfully', async () => {
      const mockResponse = {
        characters: ['Aragorn', 'Legolas', 'Gimli'],
        count: 3,
        status: 'success'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await listCharacters();
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/knowledge-base/characters'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual({
        characters: ['Aragorn', 'Legolas', 'Gimli'],
        count: 3,
        status: 'success'
      });
    });
  });

  describe('File CRUD Operations', () => {
    it('should list knowledge base files', async () => {
      const mockFiles = [
        {
          filename: 'characters/aragorn/character.json',
          file_type: 'character',
          size: 1024,
          last_modified: '2024-01-01T00:00:00Z',
          is_editable: true
        }
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ files: mockFiles, status: 'success' }),
      });

      const result = await listKnowledgeBaseFiles();
      
      expect(result).toEqual(mockFiles);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/knowledge-base/files'),
        expect.any(Object)
      );
    });

    it('should list files filtered by character name', async () => {
      const characterName = 'aragorn';
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ files: [], status: 'success' }),
      });

      await listKnowledgeBaseFiles(characterName);
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`?character_name=${characterName}`),
        expect.any(Object)
      );
    });

    it('should get file content', async () => {
      const mockContent = {
        filename: 'test.json',
        content: { name: 'Test Character' },
        schema_version: '1.0'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ content: mockContent, status: 'success' }),
      });

      const result = await getFileContent('test.json');
      
      expect(result).toEqual(mockContent);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/knowledge-base/files/test.json'),
        expect.any(Object)
      );
    });

    it('should update file content', async () => {
      const content = { name: 'Updated Character' };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'success' }),
      });

      await updateFileContent('test.json', content);
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/knowledge-base/files/test.json'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ content }),
        })
      );
    });

    it('should create new file', async () => {
      const filename = 'new-character.json';
      const content = { name: 'New Character' };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'success' }),
      });

      await createFile(filename, content);
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/knowledge-base/files'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ filename, content }),
        })
      );
    });

    it('should delete file', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'success' }),
      });

      await deleteFile('test.json');
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/knowledge-base/files/test.json'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });

  describe('Validation Functions', () => {
    it('should validate file content', async () => {
      const mockValidation = {
        is_valid: true,
        errors: [],
        warnings: []
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ result: mockValidation, status: 'success' }),
      });

      const result = await validateFileContent('test.json', { name: 'Test' });
      
      expect(result).toEqual(mockValidation);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/knowledge-base/validate/test.json'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ content: { name: 'Test' } }),
        })
      );
    });
  });

  describe('Schema and Template Functions', () => {
    it('should get file schema', async () => {
      const mockSchema = { type: 'object', properties: {} };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ json_schema: mockSchema, file_type: 'character', status: 'success' }),
      });

      const result = await getFileSchema('character');
      
      expect(result).toEqual(mockSchema);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/knowledge-base/schema/character'),
        expect.any(Object)
      );
    });

    it('should get file template', async () => {
      const mockTemplate = { name: '', level: 1 };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ template: mockTemplate, file_type: 'character', status: 'success' }),
      });

      const result = await getFileTemplate('character');
      
      expect(result).toEqual(mockTemplate);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/knowledge-base/template/character'),
        expect.any(Object)
      );
    });

    it('should get supported file types', async () => {
      const mockTypes = { 'character.json': 'character' };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ supported_types: mockTypes, status: 'success' }),
      });

      const result = await getSupportedFileTypes();
      
      expect(result).toEqual(mockTypes);
    });
  });

  describe('Character Creation', () => {
    it('should create new character', async () => {
      const request = {
        character_name: 'Aragorn',
        race: 'Human',
        character_class: 'Ranger',
        level: 1
      };

      const mockResponse = {
        character_name: 'Aragorn',
        files_created: ['character.json', 'character_background.json'],
        status: 'success',
        message: 'Character created successfully'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await createNewCharacter(request);
      
      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/knowledge-base/character/new'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(request),
        })
      );
    });
  });

  describe('Backup Management', () => {
    it('should list backups', async () => {
      const mockBackups = [
        {
          backup_id: 'backup-123',
          filename: 'test.json',
          created_at: '2024-01-01T00:00:00Z',
          size: 1024
        }
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ backups: mockBackups, status: 'success' }),
      });

      const result = await listBackups();
      
      expect(result).toEqual(mockBackups);
    });

    it('should restore backup', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'success' }),
      });

      await restoreBackup('backup-123');
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/knowledge-base/backups/backup-123/restore'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('Batch Operations', () => {
    it('should execute batch file operations', async () => {
      const operations = [
        { filename: 'file1.json', content: { name: 'Test1' }, operation: 'create' as const },
        { filename: 'file2.json', content: { name: 'Test2' }, operation: 'update' as const }
      ];

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ status: 'success' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ status: 'success' }),
        });

      await executeBatchFileOperations(operations);
      
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Error Handling', () => {
    it('should handle HTTP errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ detail: 'File not found' }),
      });

      await expect(getFileContent('nonexistent.json')).rejects.toThrow(KnowledgeBaseApiError);
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(getFileContent('test.json')).rejects.toThrow(KnowledgeBaseApiError);
    });

    it('should identify KnowledgeBaseApiError', () => {
      const error = new KnowledgeBaseApiError('Test error');
      expect(isKnowledgeBaseApiError(error)).toBe(true);
      expect(isKnowledgeBaseApiError(new Error('Regular error'))).toBe(false);
    });

    it('should get error message', () => {
      const kbError = new KnowledgeBaseApiError('KB error');
      const regularError = new Error('Regular error');
      const unknownError = 'string error';

      expect(getErrorMessage(kbError)).toBe('KB error');
      expect(getErrorMessage(regularError)).toBe('Regular error');
      expect(getErrorMessage(unknownError)).toBe('An unknown error occurred');
    });
  });

  describe('File Type Utilities', () => {
    it('should identify file types from filenames', () => {
      expect(getFileTypeFromFilename('character.json')).toBe(FILE_TYPES.CHARACTER);
      expect(getFileTypeFromFilename('character_background.json')).toBe(FILE_TYPES.CHARACTER_BACKGROUND);
      expect(getFileTypeFromFilename('feats_and_traits.json')).toBe(FILE_TYPES.FEATS_AND_TRAITS);
      expect(getFileTypeFromFilename('action_list.json')).toBe(FILE_TYPES.ACTION_LIST);
      expect(getFileTypeFromFilename('inventory_list.json')).toBe(FILE_TYPES.INVENTORY_LIST);
      expect(getFileTypeFromFilename('objectives_and_contracts.json')).toBe(FILE_TYPES.OBJECTIVES_AND_CONTRACTS);
      expect(getFileTypeFromFilename('spell_list.json')).toBe(FILE_TYPES.SPELL_LIST);
      expect(getFileTypeFromFilename('unknown_file.json')).toBe('other');
    });

    it('should handle case insensitive filenames', () => {
      expect(getFileTypeFromFilename('CHARACTER.JSON')).toBe(FILE_TYPES.CHARACTER);
      expect(getFileTypeFromFilename('Character_Background.json')).toBe(FILE_TYPES.CHARACTER_BACKGROUND);
    });
  });
});