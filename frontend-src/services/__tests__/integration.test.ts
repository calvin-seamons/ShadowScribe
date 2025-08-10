/**
 * Integration tests for Knowledge Base API Service
 * 
 * These tests verify the API service works with the actual backend endpoints.
 * They are designed to be run against a running backend server.
 */

import { describe, it, expect, beforeAll } from 'vitest';
import {
  getSupportedFileTypes,
  getFileSchema,
  getFileTemplate,
  listCharacters,
  KnowledgeBaseApiError,
  isKnowledgeBaseApiError
} from '../knowledgeBaseApi';

// Skip integration tests by default - they require a running backend
const runIntegrationTests = process.env.RUN_INTEGRATION_TESTS === 'true';

describe.skipIf(!runIntegrationTests)('Knowledge Base API Integration Tests', () => {
  beforeAll(() => {
    console.log('Running integration tests against backend...');
  });

  it('should get supported file types from backend', async () => {
    try {
      const supportedTypes = await getSupportedFileTypes();
      
      expect(supportedTypes).toBeDefined();
      expect(typeof supportedTypes).toBe('object');
      
      // Should include the core file types
      const expectedTypes = [
        'character.json',
        'character_background.json',
        'feats_and_traits.json',
        'action_list.json',
        'inventory_list.json',
        'objectives_and_contracts.json',
        'spell_list.json'
      ];
      
      expectedTypes.forEach(type => {
        expect(supportedTypes).toHaveProperty(type);
      });
      
    } catch (error) {
      if (isKnowledgeBaseApiError(error) && error.status === 0) {
        console.warn('Backend not available for integration test');
        return;
      }
      throw error;
    }
  });

  it('should get schema for character file type', async () => {
    try {
      const schema = await getFileSchema('character');
      
      expect(schema).toBeDefined();
      expect(typeof schema).toBe('object');
      expect(schema).toHaveProperty('type');
      
    } catch (error) {
      if (isKnowledgeBaseApiError(error) && error.status === 0) {
        console.warn('Backend not available for integration test');
        return;
      }
      throw error;
    }
  });

  it('should get template for character file type', async () => {
    try {
      const template = await getFileTemplate('character');
      
      expect(template).toBeDefined();
      expect(typeof template).toBe('object');
      
    } catch (error) {
      if (isKnowledgeBaseApiError(error) && error.status === 0) {
        console.warn('Backend not available for integration test');
        return;
      }
      throw error;
    }
  });

  it('should list characters from backend', async () => {
    try {
      const result = await listCharacters();
      
      expect(result).toBeDefined();
      expect(result).toHaveProperty('characters');
      expect(result).toHaveProperty('count');
      expect(Array.isArray(result.characters)).toBe(true);
      expect(typeof result.count).toBe('number');
      
    } catch (error) {
      if (isKnowledgeBaseApiError(error) && error.status === 0) {
        console.warn('Backend not available for integration test');
        return;
      }
      throw error;
    }
  });

  it('should handle 404 errors gracefully', async () => {
    try {
      await getFileSchema('nonexistent_file_type');
      expect.fail('Should have thrown an error');
    } catch (error) {
      if (isKnowledgeBaseApiError(error)) {
        expect(error.status).toBe(400); // Backend returns 400 for invalid file types
        expect(error.message).toContain('Invalid file type');
      } else if (error instanceof Error && error.message.includes('Network error')) {
        console.warn('Backend not available for integration test');
      } else {
        throw error;
      }
    }
  });
});

// Instructions for running integration tests
if (!runIntegrationTests) {
  console.log(`
Integration tests are skipped by default.
To run integration tests:
1. Start the backend server: npm run backend
2. Run tests with: RUN_INTEGRATION_TESTS=true npm run test
  `);
}