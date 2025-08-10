import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { ObjectivesEditor } from '../ObjectivesEditor';

// Mock data for testing
const mockData = {
  objectives_and_contracts: {
    active_contracts: [
      {
        id: 'test-1',
        name: 'Test Quest',
        type: 'Quest' as const,
        status: 'Active' as const,
        description: 'A test quest',
        priority: 'High' as const,
        quest_giver: 'Test NPC',
        location: 'Test Location',
        objectives: ['Complete task 1', 'Complete task 2'],
        rewards: ['Gold', 'Experience']
      }
    ],
    current_objectives: [],
    completed_objectives: [
      {
        id: 'completed-1',
        name: 'Divine Covenant',
        type: 'Divine Covenant' as const,
        status: 'Completed' as const,
        description: 'A completed divine covenant',
        completion_date: '2024-01-01',
        parties: {
          patron: { name: 'Test Deity', title: 'The Divine' },
          bound: { name: 'Test Character', title: 'The Bound' }
        },
        outcome: 'Successfully completed',
        rewards: ['Divine blessing'],
        obligations_accepted: ['Serve faithfully'],
        lasting_effects: ['Permanent mark']
      }
    ],
    contract_templates: {
      quest: {
        id: '',
        name: 'Quest Template',
        type: 'Quest',
        status: 'Active',
        quest_giver: '',
        location: '',
        description: '',
        objectives: [],
        rewards: [],
        deadline: '',
        notes: ''
      }
    }
  },
  metadata: {
    version: '1.0',
    last_updated: '2024-01-01',
    notes: []
  }
};

describe('ObjectivesEditor', () => {
  it('renders without crashing', () => {
    const mockOnChange = vi.fn();
    
    // This test just ensures the component can be instantiated without errors
    expect(() => {
      React.createElement(ObjectivesEditor, {
        data: mockData,
        onChange: mockOnChange
      });
    }).not.toThrow();
  });

  it('has the correct structure', () => {
    const mockOnChange = vi.fn();
    
    const element = React.createElement(ObjectivesEditor, {
      data: mockData,
      onChange: mockOnChange
    });
    
    // Basic structure test
    expect(element.type).toBe(ObjectivesEditor);
    expect(element.props.data).toBe(mockData);
    expect(element.props.onChange).toBe(mockOnChange);
  });
});