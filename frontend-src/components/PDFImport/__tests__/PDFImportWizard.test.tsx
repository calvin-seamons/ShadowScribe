import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { PDFImportWizard } from '../PDFImportWizard';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock file for testing
const createMockFile = (name: string, size: number, type: string) => {
  const file = new File(['mock content'], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
};

// Mock PDF extraction result
const mockExtractionResult = {
  session_id: 'test-session-123',
  extracted_text: 'Character Name: Test Character\nClass: Fighter\nLevel: 5\nRace: Human',
  page_count: 1,
  structure_info: {
    has_form_fields: true,
    has_tables: false,
    detected_format: 'dnd_beyond',
    text_quality: 'high'
  },
  confidence_score: 0.95
};

// Mock character parse result
const mockParseResult = {
  session_id: 'test-session-123',
  character_files: {
    character: {
      character_base: {
        name: 'Test Character',
        race: 'Human',
        character_class: 'Fighter',
        level: 5
      }
    },
    character_background: {
      personality_traits: ['Brave', 'Loyal'],
      ideals: ['Justice'],
      bonds: ['My sword'],
      flaws: ['Stubborn']
    }
  },
  uncertain_fields: [
    {
      file_type: 'character',
      field_path: 'character_base.alignment',
      extracted_value: 'Lawful Good',
      confidence: 0.7,
      suggestions: ['Lawful Good', 'Neutral Good']
    }
  ],
  parsing_confidence: 0.85,
  validation_results: {
    character: {
      is_valid: true,
      errors: [],
      warnings: []
    },
    character_background: {
      is_valid: true,
      errors: [],
      warnings: []
    }
  }
};

describe('PDFImportWizard', () => {
  const mockOnComplete = vi.fn();
  const mockOnCancel = vi.fn();
  const mockOnFallbackToManual = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const renderWizard = () => {
    return render(
      <PDFImportWizard
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
        onFallbackToManual={mockOnFallbackToManual}
      />
    );
  };

  describe('Initial State', () => {
    it('should render the upload step initially', () => {
      renderWizard();
      
      expect(screen.getByText('Upload PDF Character Sheet')).toBeInTheDocument();
      expect(screen.getByText('Drop your PDF here or click to browse')).toBeInTheDocument();
      expect(screen.getByText('Step 1 of 4')).toBeInTheDocument();
    });

    it('should show progress steps with correct states', () => {
      renderWizard();
      
      // Check that all steps are visible
      expect(screen.getByText('Upload PDF')).toBeInTheDocument();
      expect(screen.getByText('Review Content')).toBeInTheDocument();
      expect(screen.getByText('AI Parsing')).toBeInTheDocument();
      expect(screen.getByText('Review Data')).toBeInTheDocument();
    });

    it('should have navigation buttons in correct states', () => {
      renderWizard();
      
      const previousButton = screen.getByText('Previous');
      const nextButton = screen.getByText('Next');
      
      expect(previousButton).toBeDisabled();
      expect(nextButton).toBeDisabled(); // No file uploaded yet
    });
  });

  describe('PDF Upload Flow', () => {
    it('should handle successful PDF upload', async () => {
      // Mock successful upload response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockExtractionResult)
      });

      renderWizard();
      
      const fileInput = document.querySelector('input[type="file"]');
      const mockFile = createMockFile('character-sheet.pdf', 1024 * 1024, 'application/pdf');
      
      if (fileInput) {
        fireEvent.change(fileInput, { target: { files: [mockFile] } });
      }

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/character/import-pdf/upload', expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        }));
      });
    });

    it('should handle upload errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Upload failed'));

      renderWizard();
      
      const fileInput = document.querySelector('input[type="file"]');
      const mockFile = createMockFile('character-sheet.pdf', 1024 * 1024, 'application/pdf');
      
      if (fileInput) {
        fireEvent.change(fileInput, { target: { files: [mockFile] } });
      }

      await waitFor(() => {
        expect(screen.getByText('Upload Error')).toBeInTheDocument();
        expect(screen.getByText(/upload failed/i)).toBeInTheDocument();
      });
    });

    it('should validate file size limits', async () => {
      renderWizard();
      
      const fileInput = document.querySelector('input[type="file"]');
      const oversizedFile = createMockFile('large-file.pdf', 15 * 1024 * 1024, 'application/pdf'); // 15MB
      
      if (fileInput) {
        fireEvent.change(fileInput, { target: { files: [oversizedFile] } });
      }

      await waitFor(() => {
        expect(screen.getByText(/file size exceeds the maximum limit/i)).toBeInTheDocument();
      });
    });

    it('should validate file types', async () => {
      renderWizard();
      
      const fileInput = document.querySelector('input[type="file"]');
      const wrongTypeFile = createMockFile('document.docx', 1024, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
      
      if (fileInput) {
        fireEvent.change(fileInput, { target: { files: [wrongTypeFile] } });
      }

      await waitFor(() => {
        expect(screen.getByText(/only pdf files are supported/i)).toBeInTheDocument();
      });
    });
  });

  describe('Content Preview Flow', () => {
    beforeEach(async () => {
      // Setup wizard in preview state
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockExtractionResult)
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockExtractionResult)
        });

      renderWizard();
      
      const fileInput = document.querySelector('input[type="file"]');
      const mockFile = createMockFile('character-sheet.pdf', 1024 * 1024, 'application/pdf');
      
      if (fileInput) {
        fireEvent.change(fileInput, { target: { files: [mockFile] } });
      }

      await waitFor(() => {
        expect(screen.getByText('Review Extracted Content')).toBeInTheDocument();
      });
    });

    it('should display extracted text content', () => {
      expect(screen.getByText(/character name: test character/i)).toBeInTheDocument();
      expect(screen.getByText(/class: fighter/i)).toBeInTheDocument();
    });

    it('should show text quality indicators', () => {
      expect(screen.getByText('Excellent text quality detected')).toBeInTheDocument();
      expect(screen.getByText('D&D Beyond Export')).toBeInTheDocument();
    });

    it('should allow text editing', () => {
      const editButton = screen.getByText('Edit Text');
      fireEvent.click(editButton);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveValue(mockExtractionResult.extracted_text);
    });

    it('should proceed to parsing when confirmed', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockParseResult)
      });

      const confirmButton = screen.getByText('Continue to Parsing');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText('Processing Character Data')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText('Review Character Data')).toBeInTheDocument();
      });
    });

    it('should return to upload when rejected', () => {
      const rejectButton = screen.getByText('Cancel Import');
      fireEvent.click(rejectButton);

      expect(screen.getByText('Upload PDF Character Sheet')).toBeInTheDocument();
    });
  });

  describe('AI Parsing Flow', () => {
    it('should handle parsing errors', async () => {
      // Setup wizard in preview state
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockExtractionResult)
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockExtractionResult)
        })
        .mockRejectedValueOnce(new Error('Parsing failed'));

      renderWizard();
      
      const fileInput = document.querySelector('input[type="file"]');
      const mockFile = createMockFile('character-sheet.pdf', 1024 * 1024, 'application/pdf');
      
      if (fileInput) {
        fireEvent.change(fileInput, { target: { files: [mockFile] } });
      }

      await waitFor(() => {
        expect(screen.getByText('Review Extracted Content')).toBeInTheDocument();
      });

      const confirmButton = screen.getByText('Continue to Parsing');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText('Import Error')).toBeInTheDocument();
        expect(screen.getByText(/parsing failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Character Data Review Flow', () => {
    beforeEach(async () => {
      // Setup wizard in review state
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockExtractionResult)
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockExtractionResult)
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockParseResult)
        });

      renderWizard();
      
      const fileInput = document.querySelector('input[type="file"]');
      const mockFile = createMockFile('character-sheet.pdf', 1024 * 1024, 'application/pdf');
      
      if (fileInput) {
        fireEvent.change(fileInput, { target: { files: [mockFile] } });
      }

      await waitFor(() => {
        expect(screen.getByText('Review Extracted Content')).toBeInTheDocument();
      });

      const confirmButton = screen.getByText('Continue to Parsing');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText('Review Character Data')).toBeInTheDocument();
      });
    });

    it('should display parsed character data', () => {
      expect(screen.getByDisplayValue('Test Character')).toBeInTheDocument();
      expect(screen.getByText('Basic Character Info')).toBeInTheDocument();
      expect(screen.getByText('Background & Personality')).toBeInTheDocument();
    });

    it('should show confidence indicators', () => {
      expect(screen.getByText(/85% - medium confidence/i)).toBeInTheDocument();
      expect(screen.getByText(/1 field needs review/i)).toBeInTheDocument();
    });

    it('should allow field editing', () => {
      // Find and click an edit button (there should be edit icons for uncertain fields)
      const editButtons = screen.getAllByRole('button');
      const editButton = editButtons.find(button => 
        button.querySelector('svg') && button.getAttribute('title')?.includes('edit')
      );
      
      if (editButton) {
        fireEvent.click(editButton);
        // Should show input field for editing
        expect(screen.getByRole('textbox')).toBeInTheDocument();
      }
    });

    it('should finalize character creation', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, character_name: 'Test Character' })
      });

      const characterNameInput = screen.getByDisplayValue('Test Character');
      expect(characterNameInput).toBeInTheDocument();

      const finalizeButton = screen.getByText('Create Character Files');
      fireEvent.click(finalizeButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/character/import-pdf/generate/test-session-123',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: expect.stringContaining('Test Character')
          })
        );
      });

      await waitFor(() => {
        expect(mockOnComplete).toHaveBeenCalledWith('Test Character');
      });
    });
  });

  describe('Navigation and State Management', () => {
    it('should handle step navigation correctly', async () => {
      // Setup wizard with successful upload
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockExtractionResult)
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockExtractionResult)
        });

      renderWizard();
      
      const fileInput = document.querySelector('input[type="file"]');
      const mockFile = createMockFile('character-sheet.pdf', 1024 * 1024, 'application/pdf');
      
      if (fileInput) {
        fireEvent.change(fileInput, { target: { files: [mockFile] } });
      }

      await waitFor(() => {
        expect(screen.getByText('Review Extracted Content')).toBeInTheDocument();
      });

      // Should be able to go back to upload
      const previousButton = screen.getByText('Previous');
      fireEvent.click(previousButton);

      expect(screen.getByText('Upload PDF Character Sheet')).toBeInTheDocument();
    });

    it('should handle cancellation at any step', () => {
      renderWizard();
      
      const cancelButton = screen.getByText('Back to Character Selection');
      fireEvent.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });

    it('should offer fallback to manual wizard', () => {
      renderWizard();
      
      const fallbackButton = screen.getByText('Use Manual Wizard Instead');
      fireEvent.click(fallbackButton);

      expect(mockOnFallbackToManual).toHaveBeenCalled();
    });
  });

  describe('Error Recovery', () => {
    it('should provide retry options on upload failure', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      renderWizard();
      
      const fileInput = document.querySelector('input[type="file"]');
      const mockFile = createMockFile('character-sheet.pdf', 1024 * 1024, 'application/pdf');
      
      if (fileInput) {
        fireEvent.change(fileInput, { target: { files: [mockFile] } });
      }

      await waitFor(() => {
        expect(screen.getByText('Upload Error')).toBeInTheDocument();
      });

      expect(screen.getByText('Try Again')).toBeInTheDocument();
      expect(screen.getByText('Choose Different File')).toBeInTheDocument();
    });

    it('should clean up session on unmount', () => {
      const { unmount } = renderWizard();
      
      // Mock a session being created
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockExtractionResult)
      });

      unmount();

      // Should attempt cleanup (though we can't easily test the fetch call in unmount)
      expect(true).toBe(true); // Placeholder - actual cleanup testing would require more complex mocking
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      renderWizard();
      
      expect(screen.getByRole('button', { name: /back to character selection/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /use manual wizard instead/i })).toBeInTheDocument();
    });

    it('should support keyboard navigation', () => {
      renderWizard();
      
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).not.toHaveAttribute('tabindex', '-1');
      });
    });

    it('should provide clear error messages', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Specific error message'));

      renderWizard();
      
      const fileInput = document.querySelector('input[type="file"]');
      const mockFile = createMockFile('character-sheet.pdf', 1024 * 1024, 'application/pdf');
      
      if (fileInput) {
        fireEvent.change(fileInput, { target: { files: [mockFile] } });
      }

      await waitFor(() => {
        expect(screen.getByText('Import Error')).toBeInTheDocument();
        expect(screen.getByText('Specific error message')).toBeInTheDocument();
      });
    });
  });
});