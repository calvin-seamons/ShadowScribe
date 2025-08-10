import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { CharacterCreationWizard } from '../CharacterCreationWizard';
import * as knowledgeBaseApi from '../../../services/knowledgeBaseApi';

// Mock the API
vi.mock('../../../services/knowledgeBaseApi', () => ({
  createNewCharacter: vi.fn(),
  getFileTemplate: vi.fn(),
}));

const mockCreateNewCharacter = vi.mocked(knowledgeBaseApi.createNewCharacter);
const mockGetFileTemplate = vi.mocked(knowledgeBaseApi.getFileTemplate);

describe('CharacterCreationWizard', () => {
  const mockOnComplete = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    expect(() => {
      React.createElement(CharacterCreationWizard, {
        onComplete: mockOnComplete,
        onCancel: mockOnCancel
      });
    }).not.toThrow();
  });

  it('has the correct structure', () => {
    const element = React.createElement(CharacterCreationWizard, {
      onComplete: mockOnComplete,
      onCancel: mockOnCancel
    });
    
    expect(element.type).toBe(CharacterCreationWizard);
    expect(element.props.onComplete).toBe(mockOnComplete);
    expect(element.props.onCancel).toBe(mockOnCancel);
  });

  it('handles props correctly', () => {
    const element = React.createElement(CharacterCreationWizard, {
      onComplete: mockOnComplete,
      onCancel: mockOnCancel
    });
    
    expect(typeof element.props.onComplete).toBe('function');
    expect(typeof element.props.onCancel).toBe('function');
  });

  it('can be instantiated with required props', () => {
    const props = {
      onComplete: vi.fn(),
      onCancel: vi.fn()
    };
    
    const element = React.createElement(CharacterCreationWizard, props);
    expect(element.props).toEqual(props);
  });

  it('has correct component type', () => {
    const element = React.createElement(CharacterCreationWizard, {
      onComplete: mockOnComplete,
      onCancel: mockOnCancel
    });
    
    expect(element.type.name).toBe('CharacterCreationWizard');
  });
});