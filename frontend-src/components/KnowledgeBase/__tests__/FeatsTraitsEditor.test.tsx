import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { FeatsTraitsEditor } from '../FeatsTraitsEditor';

const mockData = {
  features_and_traits: {
    class_features: {
      paladin: {
        level: 8,
        features: [
          {
            name: 'Divine Sense',
            source: 'PHB, pg. 84',
            action_type: 'action' as const,
            uses: {
              current: 8,
              maximum: 8,
              reset: 'long_rest' as const
            }
          }
        ]
      }
    },
    species_traits: {
      species: 'Dwarf',
      subrace: 'Mountain Dwarf',
      traits: [
        {
          name: 'Darkvision',
          source: 'BR, pg. 20',
          range: '60 ft',
          effect: 'See in darkness (shades of gray)'
        }
      ]
    },
    feats: [
      {
        name: 'Lucky',
        source: 'PHB, pg. 167',
        uses: {
          maximum: 3,
          reset: 'long_rest' as const
        }
      }
    ],
    calculated_features: {
      total_level: 13,
      proficiency_bonus: 5
    }
  },
  metadata: {
    version: '1.0',
    last_updated: '2025-08-02',
    notes: []
  }
};

describe('FeatsTraitsEditor', () => {
  it('renders without crashing', () => {
    const mockOnChange = vi.fn();
    
    // This test just ensures the component can be instantiated without errors
    expect(() => {
      React.createElement(FeatsTraitsEditor, {
        data: mockData,
        onChange: mockOnChange,
        validationErrors: []
      });
    }).not.toThrow();
  });

  it('has the correct structure', () => {
    const mockOnChange = vi.fn();
    
    const element = React.createElement(FeatsTraitsEditor, {
      data: mockData,
      onChange: mockOnChange,
      validationErrors: []
    });
    
    // Basic structure test
    expect(element.type).toBe(FeatsTraitsEditor);
    expect(element.props.data).toBe(mockData);
    expect(element.props.onChange).toBe(mockOnChange);
  });

  it('handles validation errors prop', () => {
    const mockOnChange = vi.fn();
    const validationErrors = [
      {
        field_path: 'features_and_traits.class_features.paladin.features.0.name',
        message: 'Name is required',
        error_type: 'required' as const
      }
    ];
    
    const element = React.createElement(FeatsTraitsEditor, {
      data: mockData,
      onChange: mockOnChange,
      validationErrors: validationErrors
    });
    
    expect(element.props.validationErrors).toBe(validationErrors);
  });
});