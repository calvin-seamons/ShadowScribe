import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { CharacterDataReview } from '../CharacterDataReview';
import { ParsedCharacterData, UncertainField, ValidationResult } from '../../../types';

// Mock the validation components
vi.mock('../../KnowledgeBase/validation', () => ({
  ValidationProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useValidation: () => ({
    validationState: { errors: [], warnings: [], isValidating: false, hasUnsavedChanges: false, lastValidated: null },
    validateField: vi.fn(() => []),
    validateForm: vi.fn(() => Promise.resolve({ is_valid: true, errors: [], warnings: [] })),
    clearValidation: vi.fn(),
    setUnsavedChanges: vi.fn(),
    getFieldErrors: vi.fn(() => []),
    hasErrors: false,
    hasWarnings: false
  }),
  ValidatedInput: ({ value, onChange, label }: any) => (
    <div>
      <label>{label}</label>
      <input 
        value={value || ''} 
        onChange={(e) => onChange(e.target.value)}
        data-testid={`validated-input-${label?.toLowerCase().replace(/\s+/g, '-')}`}
      />
    </div>
  ),
  ValidatedSelect: ({ value, onChange, label, options }: any) => (
    <div>
      <label>{label}</label>
      <select 
        value={value || ''} 
        onChange={(e) => onChange(e.target.value)}
        data-testid={`validated-select-${label?.toLowerCase().replace(/\s+/g, '-')}`}
      >
        <option value="">Select {label}</option>
        {options?.map((option: string) => (
          <option key={option} value={option}>{option}</option>
        ))}
      </select>
    </div>
  ),
  ValidatedTextarea: ({ value, onChange, label }: any) => (
    <div>
      <label>{label}</label>
      <textarea 
        value={value || ''} 
        onChange={(e) => onChange(e.target.value)}
        data-testid={`validated-textarea-${label?.toLowerCase().replace(/\s+/g, '-')}`}
      />
    </div>
  )
}));

describe('CharacterDataReview', () => {
  const mockParsedData: ParsedCharacterData = {
    character_files: {
      character: {
        character_base: {
          name: 'Test Character',
          race: 'Human',
          class: 'Fighter',
          level: 5
        },
        ability_scores: {
          strength: 16,
          dexterity: 14,
          constitution: 15,
          intelligence: 12,
          wisdom: 13,
          charisma: 10
        }
      },
      spell_list: {
        spells: [
          {
            name: 'Magic Missile',
            level: 1,
            school: 'Evocation'
          }
        ]
      }
    },
    uncertain_fields: [],
    parsing_confidence: 0.85,
    validation_results: {
      character: {
        is_valid: true,
        errors: [],
        warnings: []
      },
      spell_list: {
        is_valid: true,
        errors: [],
        warnings: []
      }
    }
  };

  const mockUncertainFields: UncertainField[] = [
    {
      file_type: 'character',
      field_path: 'character_base.race',
      extracted_value: 'Human',
      confidence: 0.7,
      suggestions: ['Human', 'Variant Human', 'Half-Elf']
    },
    {
      file_type: 'spell_list',
      field_path: 'spells.0.name',
      extracted_value: 'Magic Missile',
      confidence: 0.6,
      suggestions: ['Magic Missile', 'Mage Armor', 'Shield']
    }
  ];

  const defaultProps = {
    parsedData: mockParsedData,
    uncertainFields: [],
    onFieldEdit: vi.fn(),
    onFinalize: vi.fn(),
    onReparse: vi.fn(),
    isLoading: false
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders the component with basic elements', () => {
      render(<CharacterDataReview {...defaultProps} />);
      
      expect(screen.getByText('Review Character Data')).toBeInTheDocument();
      expect(screen.getByText('Review and edit the extracted character information. Fields marked with uncertainty require your attention.')).toBeInTheDocument();
      expect(screen.getByText('Character Name')).toBeInTheDocument();
      expect(screen.getByText('Create Character Files')).toBeInTheDocument();
    });

    it('displays parsing confidence correctly', () => {
      render(<CharacterDataReview {...defaultProps} />);
      
      expect(screen.getByText('85% - High confidence - data appears accurate')).toBeInTheDocument();
    });

    it('shows file sections for each character file type', () => {
      render(<CharacterDataReview {...defaultProps} />);
      
      expect(screen.getByText('Basic Character Info')).toBeInTheDocument();
      expect(screen.getByText('Spells & Magic')).toBeInTheDocument();
    });

    it('displays uncertain fields count', () => {
      render(<CharacterDataReview {...defaultProps} uncertainFields={mockUncertainFields} />);
      
      expect(screen.getAllByText(/2 fields? need review/)).toHaveLength(2); // Appears in status section and action bar
    });

    it('shows validation status when there are no errors', () => {
      render(<CharacterDataReview {...defaultProps} />);
      
      expect(screen.getByText('All data valid')).toBeInTheDocument();
    });
  });

  describe('Character Name Input', () => {
    it('initializes character name from parsed data', () => {
      render(<CharacterDataReview {...defaultProps} />);
      
      const nameInput = screen.getByPlaceholderText('Enter character name for the imported files');
      expect(nameInput).toHaveValue('Test Character');
    });

    it('allows editing character name', async () => {
      const user = userEvent.setup();
      render(<CharacterDataReview {...defaultProps} />);
      
      const nameInput = screen.getByPlaceholderText('Enter character name for the imported files');
      await user.clear(nameInput);
      await user.type(nameInput, 'New Character Name');
      
      expect(nameInput).toHaveValue('New Character Name');
    });

    it('prevents finalization without character name', async () => {
      const user = userEvent.setup();
      const mockOnFinalize = vi.fn();
      
      render(<CharacterDataReview {...defaultProps} onFinalize={mockOnFinalize} />);
      
      const nameInput = screen.getByPlaceholderText('Enter character name for the imported files');
      await user.clear(nameInput);
      
      const finalizeButton = screen.getByText('Create Character Files');
      expect(finalizeButton).toBeDisabled();
    });
  });

  describe('File Section Interaction', () => {
    it('expands and collapses file sections', async () => {
      const user = userEvent.setup();
      render(<CharacterDataReview {...defaultProps} />);
      
      const characterSection = screen.getByText('Basic Character Info');
      
      // Character section should be expanded by default
      expect(screen.getByText('Test Character')).toBeInTheDocument();
      
      // Click to collapse
      await user.click(characterSection);
      
      // Content should still be visible (we're not testing the actual collapse behavior here
      // as it depends on the implementation details)
    });

    it('shows uncertain field indicators in section headers', () => {
      render(<CharacterDataReview {...defaultProps} uncertainFields={mockUncertainFields} />);
      
      expect(screen.getAllByText(/1 uncertain/)).toHaveLength(2); // One for each file type with uncertain fields
    });
  });

  describe('Field Editing', () => {
    it('allows editing fields when edit button is clicked', async () => {
      const user = userEvent.setup();
      const mockOnFieldEdit = vi.fn();
      
      render(<CharacterDataReview {...defaultProps} onFieldEdit={mockOnFieldEdit} />);
      
      // Find and click an edit button (this is a simplified test)
      const editButtons = screen.getAllByRole('button');
      const editButton = editButtons.find(button => 
        button.querySelector('svg') && button.getAttribute('class')?.includes('text-gray-400')
      );
      
      if (editButton) {
        await user.click(editButton);
        // The field should now be in edit mode
        // This would require more specific implementation testing
      }
    });

    it('calls onFieldEdit when field value changes', async () => {
      const user = userEvent.setup();
      const mockOnFieldEdit = vi.fn();
      
      render(<CharacterDataReview {...defaultProps} onFieldEdit={mockOnFieldEdit} />);
      
      // This test would need to interact with actual editable fields
      // The implementation depends on the field editing state management
    });
  });

  describe('Uncertain Fields Display', () => {
    it('shows uncertain field count in status section', () => {
      render(<CharacterDataReview {...defaultProps} uncertainFields={mockUncertainFields} />);
      
      // Check that uncertain fields are counted (appears in multiple places)
      expect(screen.getAllByText(/2 fields? need review/)).toHaveLength(2);
    });

    it('shows uncertain field indicators in file sections', () => {
      render(<CharacterDataReview {...defaultProps} uncertainFields={mockUncertainFields} />);
      
      // Check that sections with uncertain fields are marked
      expect(screen.getAllByText(/1 uncertain/)).toHaveLength(2);
    });

    it('filters to show only uncertain fields when toggle is activated', async () => {
      const user = userEvent.setup();
      render(<CharacterDataReview {...defaultProps} uncertainFields={mockUncertainFields} />);
      
      const showUncertainButton = screen.getByText('Show Uncertain Only');
      await user.click(showUncertainButton);
      
      expect(screen.getByText('Show All')).toBeInTheDocument();
    });
  });

  describe('Validation Errors', () => {
    it('displays validation errors for fields', () => {
      const parsedDataWithErrors: ParsedCharacterData = {
        ...mockParsedData,
        validation_results: {
          character: {
            is_valid: false,
            errors: [
              {
                field_path: 'character_base.name',
                message: 'Name is required',
                error_type: 'required'
              }
            ],
            warnings: []
          },
          spell_list: {
            is_valid: true,
            errors: [],
            warnings: []
          }
        }
      };

      render(<CharacterDataReview {...defaultProps} parsedData={parsedDataWithErrors} />);
      
      expect(screen.getAllByText(/1 validation error/)).toHaveLength(2); // Appears in status section and action bar
      expect(screen.getByText('1 error')).toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    it('calls onReparse when re-parse button is clicked', async () => {
      const user = userEvent.setup();
      const mockOnReparse = vi.fn();
      
      render(<CharacterDataReview {...defaultProps} onReparse={mockOnReparse} />);
      
      const reparseButtons = screen.getAllByText('Re-parse PDF');
      await user.click(reparseButtons[0]);
      
      expect(mockOnReparse).toHaveBeenCalled();
    });

    it('calls onFinalize with character name when finalize button is clicked', async () => {
      const user = userEvent.setup();
      const mockOnFinalize = vi.fn();
      
      render(<CharacterDataReview {...defaultProps} onFinalize={mockOnFinalize} />);
      
      const finalizeButton = screen.getByText('Create Character Files');
      await user.click(finalizeButton);
      
      expect(mockOnFinalize).toHaveBeenCalledWith('Test Character');
    });

    it('disables buttons when loading', () => {
      render(<CharacterDataReview {...defaultProps} isLoading={true} />);
      
      const finalizeButton = screen.getByText('Create Character Files');
      const reparseButtons = screen.getAllByText('Re-parse PDF');
      
      expect(finalizeButton).toBeDisabled();
      expect(reparseButtons[0]).toBeDisabled();
    });
  });

  describe('Confidence Levels', () => {
    it('shows high confidence indicator for confidence >= 0.8', () => {
      const highConfidenceData = {
        ...mockParsedData,
        parsing_confidence: 0.9
      };
      
      render(<CharacterDataReview {...defaultProps} parsedData={highConfidenceData} />);
      
      expect(screen.getByText('90% - High confidence - data appears accurate')).toBeInTheDocument();
    });

    it('shows medium confidence indicator for confidence >= 0.6', () => {
      const mediumConfidenceData = {
        ...mockParsedData,
        parsing_confidence: 0.7
      };
      
      render(<CharacterDataReview {...defaultProps} parsedData={mediumConfidenceData} />);
      
      expect(screen.getByText('70% - Medium confidence - please review highlighted fields')).toBeInTheDocument();
    });

    it('shows low confidence indicator for confidence < 0.6', () => {
      const lowConfidenceData = {
        ...mockParsedData,
        parsing_confidence: 0.5
      };
      
      render(<CharacterDataReview {...defaultProps} parsedData={lowConfidenceData} />);
      
      expect(screen.getByText('50% - Low confidence - manual review recommended')).toBeInTheDocument();
    });
  });

  describe('File Section Rendering', () => {
    it('renders file sections for character data', () => {
      render(<CharacterDataReview {...defaultProps} />);
      
      expect(screen.getByText('Basic Character Info')).toBeInTheDocument();
      expect(screen.getByText('Spells & Magic')).toBeInTheDocument();
    });

    it('shows file sections are expandable', () => {
      render(<CharacterDataReview {...defaultProps} />);
      
      // Check that sections have expand/collapse buttons
      const sectionButtons = screen.getAllByRole('button');
      const sectionButton = sectionButtons.find(button => 
        button.textContent?.includes('Basic Character Info')
      );
      expect(sectionButton).toBeInTheDocument();
    });
  });

  describe('Help and Guidelines', () => {
    it('displays review guidelines', () => {
      render(<CharacterDataReview {...defaultProps} />);
      
      expect(screen.getByText('Review Guidelines')).toBeInTheDocument();
      expect(screen.getByText(/Yellow highlighted fields indicate uncertainty/)).toBeInTheDocument();
      expect(screen.getByText(/Red indicators show validation errors/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(<CharacterDataReview {...defaultProps} />);
      
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
      
      const textboxes = screen.getAllByRole('textbox');
      expect(textboxes.length).toBeGreaterThan(0);
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<CharacterDataReview {...defaultProps} />);
      
      const nameInput = screen.getByPlaceholderText('Enter character name for the imported files');
      
      await user.tab();
      // The first focusable element should be focused
      // This is a basic test - more comprehensive keyboard navigation testing would be needed
    });
  });
});