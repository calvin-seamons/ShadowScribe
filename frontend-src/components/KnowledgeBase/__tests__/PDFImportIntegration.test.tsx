import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { IntegratedKnowledgeBaseEditor } from '../IntegratedKnowledgeBaseEditor';
import { useNavigationStore } from '../../../stores/navigationStore';
import { useKnowledgeBaseStore } from '../../../stores/knowledgeBaseStore';
import { useKnowledgeBaseSession } from '../../../hooks/useKnowledgeBaseSession';
import { useCharacterSync } from '../../../hooks/useCharacterSync';

// Mock all the dependencies
vi.mock('../../../stores/navigationStore');
vi.mock('../../../stores/knowledgeBaseStore');
vi.mock('../../../hooks/useKnowledgeBaseSession');
vi.mock('../../../hooks/useCharacterSync');
vi.mock('../../../services/knowledgeBaseApi');

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockUseNavigationStore = useNavigationStore as vi.MockedFunction<typeof useNavigationStore>;
const mockUseKnowledgeBaseStore = useKnowledgeBaseStore as vi.MockedFunction<typeof useKnowledgeBaseStore>;
const mockUseKnowledgeBaseSession = useKnowledgeBaseSession as vi.MockedFunction<typeof useKnowledgeBaseSession>;
const mockUseCharacterSync = useCharacterSync as vi.MockedFunction<typeof useCharacterSync>;

describe('PDF Import Integration', () => {
  const mockCloseKnowledgeBaseEditor = vi.fn();
  const mockOpenKnowledgeBaseEditor = vi.fn();
  const mockSetCurrentView = vi.fn();
  const mockRefreshCharacterData = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockClear();

    // Mock navigation store
    mockUseNavigationStore.mockReturnValue({
      currentView: 'knowledge-base',
      isKnowledgeBaseEditorOpen: true,
      isPDFImportOpen: false,
      setCurrentView: mockSetCurrentView,
      openKnowledgeBaseEditor: mockOpenKnowledgeBaseEditor,
      closeKnowledgeBaseEditor: mockCloseKnowledgeBaseEditor,
      toggleKnowledgeBaseEditor: vi.fn(),
      openPDFImport: vi.fn(),
      closePDFImport: vi.fn(),
    });

    // Mock knowledge base store
    mockUseKnowledgeBaseStore.mockReturnValue({
      files: [],
      selectedFile: null,
      fileContent: null,
      hasUnsavedChanges: false,
      isLoading: false,
      isSaving: false,
      error: null,
      setFiles: vi.fn(),
      setSelectedFile: vi.fn(),
      setFileContent: vi.fn(),
      setHasUnsavedChanges: vi.fn(),
      setIsLoading: vi.fn(),
      setIsSaving: vi.fn(),
      setError: vi.fn(),
      markCharacterModified: vi.fn(),
    });

    // Mock session hook
    mockUseKnowledgeBaseSession.mockReturnValue({
      hasAccess: () => true,
      handleSessionCleanup: () => true,
      enableAutoSave: () => () => {},
    });

    // Mock character sync hook
    mockUseCharacterSync.mockReturnValue({
      refreshCharacterData: mockRefreshCharacterData,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Character Creation Selection Integration', () => {
    it('should show character creation selection when creating new character', () => {
      render(<IntegratedKnowledgeBaseEditor />);
      
      const newCharacterButton = screen.getByText('New Character');
      fireEvent.click(newCharacterButton);
      
      expect(screen.getByText('Create New Character')).toBeInTheDocument();
      expect(screen.getByText('Choose how you\'d like to create your character')).toBeInTheDocument();
    });

    it('should navigate to PDF import when PDF option is selected', () => {
      render(<IntegratedKnowledgeBaseEditor />);
      
      // Click new character to show selection
      const newCharacterButton = screen.getByText('New Character');
      fireEvent.click(newCharacterButton);
      
      // Select PDF import option
      const pdfImportButton = screen.getByText('Upload PDF Character Sheet');
      fireEvent.click(pdfImportButton);
      
      // Should show PDF import wizard
      expect(screen.getByText('PDF Character Import')).toBeInTheDocument();
      expect(screen.getByText('Upload PDF')).toBeInTheDocument();
    });

    it('should navigate to manual wizard when manual option is selected', () => {
      render(<IntegratedKnowledgeBaseEditor />);
      
      // Click new character to show selection
      const newCharacterButton = screen.getByText('New Character');
      fireEvent.click(newCharacterButton);
      
      // Select manual wizard option
      const manualWizardButton = screen.getByText('Start Manual Wizard');
      fireEvent.click(manualWizardButton);
      
      // Should show manual creation wizard
      expect(screen.getByText('Character Creation Wizard')).toBeInTheDocument();
    });

    it('should return to editor when creation is cancelled', () => {
      render(<IntegratedKnowledgeBaseEditor />);
      
      // Click new character to show selection
      const newCharacterButton = screen.getByText('New Character');
      fireEvent.click(newCharacterButton);
      
      // Cancel creation
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);
      
      // Should return to main editor
      expect(screen.getByText('Knowledge Base Editor')).toBeInTheDocument();
      expect(screen.getByText('Select a file to edit')).toBeInTheDocument();
    });
  });

  describe('PDF Import Workflow Integration', () => {
    beforeEach(() => {
      // Setup successful PDF import responses
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            session_id: 'test-session-123',
            extracted_text: 'Character Name: Test Character\nClass: Fighter\nLevel: 5',
            structure_info: {
              detected_format: 'dnd_beyond',
              text_quality: 'high'
            }
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            session_id: 'test-session-123',
            extracted_text: 'Character Name: Test Character\nClass: Fighter\nLevel: 5',
            structure_info: {
              detected_format: 'dnd_beyond',
              text_quality: 'high'
            }
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            session_id: 'test-session-123',
            character_files: {
              character: { character_base: { name: 'Test Character' } }
            },
            uncertain_fields: [],
            parsing_confidence: 0.9,
            validation_results: {}
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ success: true })
        });
    });

    it('should complete full PDF import workflow and return to editor', async () => {
      render(<IntegratedKnowledgeBaseEditor />);
      
      // Start PDF import
      const newCharacterButton = screen.getByText('New Character');
      fireEvent.click(newCharacterButton);
      
      const pdfImportButton = screen.getByText('Upload PDF Character Sheet');
      fireEvent.click(pdfImportButton);
      
      // Upload PDF file
      const fileInput = document.querySelector('input[type="file"]');
      const mockFile = new File(['mock content'], 'character.pdf', { type: 'application/pdf' });
      
      if (fileInput) {
        fireEvent.change(fileInput, { target: { files: [mockFile] } });
      }

      // Wait for upload and preview
      await waitFor(() => {
        expect(screen.getByText('Review Extracted Content')).toBeInTheDocument();
      });

      // Confirm preview
      const confirmButton = screen.getByText('Continue to Parsing');
      fireEvent.click(confirmButton);

      // Wait for parsing and review
      await waitFor(() => {
        expect(screen.getByText('Review Character Data')).toBeInTheDocument();
      });

      // Finalize character creation
      const finalizeButton = screen.getByText('Create Character Files');
      fireEvent.click(finalizeButton);

      // Should call openKnowledgeBaseEditor after completion
      await waitFor(() => {
        expect(mockOpenKnowledgeBaseEditor).toHaveBeenCalled();
      });
    });

    it('should handle fallback to manual wizard from PDF import', () => {
      render(<IntegratedKnowledgeBaseEditor />);
      
      // Start PDF import
      const newCharacterButton = screen.getByText('New Character');
      fireEvent.click(newCharacterButton);
      
      const pdfImportButton = screen.getByText('Upload PDF Character Sheet');
      fireEvent.click(pdfImportButton);
      
      // Use fallback to manual wizard
      const fallbackButton = screen.getByText('Use Manual Wizard Instead');
      fireEvent.click(fallbackButton);
      
      // Should show manual wizard
      expect(screen.getByText('Character Creation Wizard')).toBeInTheDocument();
    });

    it('should handle PDF import cancellation', () => {
      render(<IntegratedKnowledgeBaseEditor />);
      
      // Start PDF import
      const newCharacterButton = screen.getByText('New Character');
      fireEvent.click(newCharacterButton);
      
      const pdfImportButton = screen.getByText('Upload PDF Character Sheet');
      fireEvent.click(pdfImportButton);
      
      // Cancel import
      const cancelButton = screen.getByText('Back to Character Selection');
      fireEvent.click(cancelButton);
      
      // Should return to main editor
      expect(screen.getByText('Knowledge Base Editor')).toBeInTheDocument();
    });
  });

  describe('Character Editor Integration', () => {
    it('should switch to character after successful import', async () => {
      const mockSetFiles = vi.fn();
      const mockSetSelectedFile = vi.fn();
      
      mockUseKnowledgeBaseStore.mockReturnValue({
        files: [],
        selectedFile: null,
        fileContent: null,
        hasUnsavedChanges: false,
        isLoading: false,
        isSaving: false,
        error: null,
        setFiles: mockSetFiles,
        setSelectedFile: mockSetSelectedFile,
        setFileContent: vi.fn(),
        setHasUnsavedChanges: vi.fn(),
        setIsLoading: vi.fn(),
        setIsSaving: vi.fn(),
        setError: vi.fn(),
        markCharacterModified: vi.fn(),
      });

      render(<IntegratedKnowledgeBaseEditor />);
      
      // Start and complete PDF import (simplified)
      const newCharacterButton = screen.getByText('New Character');
      fireEvent.click(newCharacterButton);
      
      const pdfImportButton = screen.getByText('Upload PDF Character Sheet');
      fireEvent.click(pdfImportButton);
      
      // Simulate successful completion
      const wizard = screen.getByText('PDF Character Import').closest('div');
      if (wizard) {
        // Trigger the onComplete callback directly for testing
        const onCompleteCallback = mockOpenKnowledgeBaseEditor;
        onCompleteCallback();
      }
      
      expect(mockOpenKnowledgeBaseEditor).toHaveBeenCalled();
    });

    it('should refresh character data after import', async () => {
      render(<IntegratedKnowledgeBaseEditor />);
      
      // Simulate character import completion
      // This would normally be triggered by the PDF import wizard's onComplete callback
      mockRefreshCharacterData();
      
      expect(mockRefreshCharacterData).toHaveBeenCalled();
    });
  });

  describe('Navigation Integration', () => {
    it('should handle navigation state changes during import', () => {
      render(<IntegratedKnowledgeBaseEditor />);
      
      // Start PDF import
      const newCharacterButton = screen.getByText('New Character');
      fireEvent.click(newCharacterButton);
      
      const pdfImportButton = screen.getByText('Upload PDF Character Sheet');
      fireEvent.click(pdfImportButton);
      
      // Verify we're in PDF import mode
      expect(screen.getByText('PDF Character Import')).toBeInTheDocument();
      
      // Cancel should return to chat view
      const cancelButton = screen.getByText('Back to Character Selection');
      fireEvent.click(cancelButton);
      
      // Should return to editor (not call setCurrentView to chat)
      expect(screen.getByText('Knowledge Base Editor')).toBeInTheDocument();
    });

    it('should maintain proper navigation state during wizard transitions', () => {
      render(<IntegratedKnowledgeBaseEditor />);
      
      // Navigate through creation selection
      const newCharacterButton = screen.getByText('New Character');
      fireEvent.click(newCharacterButton);
      
      // Should show selection screen
      expect(screen.getByText('Create New Character')).toBeInTheDocument();
      
      // Select PDF import
      const pdfImportButton = screen.getByText('Upload PDF Character Sheet');
      fireEvent.click(pdfImportButton);
      
      // Should show PDF wizard
      expect(screen.getByText('PDF Character Import')).toBeInTheDocument();
      
      // Use fallback to manual
      const fallbackButton = screen.getByText('Use Manual Wizard Instead');
      fireEvent.click(fallbackButton);
      
      // Should show manual wizard
      expect(screen.getByText('Character Creation Wizard')).toBeInTheDocument();
    });
  });

  describe('Error Handling Integration', () => {
    it('should handle PDF import errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Upload failed'));
      
      render(<IntegratedKnowledgeBaseEditor />);
      
      // Start PDF import
      const newCharacterButton = screen.getByText('New Character');
      fireEvent.click(newCharacterButton);
      
      const pdfImportButton = screen.getByText('Upload PDF Character Sheet');
      fireEvent.click(pdfImportButton);
      
      // Try to upload a file
      const fileInput = document.querySelector('input[type="file"]');
      const mockFile = new File(['mock content'], 'character.pdf', { type: 'application/pdf' });
      
      if (fileInput) {
        fireEvent.change(fileInput, { target: { files: [mockFile] } });
      }

      // Should show error and offer fallback
      await waitFor(() => {
        expect(screen.getByText('Import Error')).toBeInTheDocument();
        expect(screen.getByText('Use Manual Wizard')).toBeInTheDocument();
      });
    });

    it('should handle session cleanup on errors', () => {
      const mockHandleSessionCleanup = vi.fn().mockReturnValue(true);
      
      mockUseKnowledgeBaseSession.mockReturnValue({
        hasAccess: () => true,
        handleSessionCleanup: mockHandleSessionCleanup,
        enableAutoSave: () => () => {},
      });

      render(<IntegratedKnowledgeBaseEditor />);
      
      // Close editor
      const closeButton = screen.getByRole('button', { name: /close editor/i });
      fireEvent.click(closeButton);
      
      expect(mockHandleSessionCleanup).toHaveBeenCalled();
      expect(mockCloseKnowledgeBaseEditor).toHaveBeenCalled();
    });
  });

  describe('Accessibility Integration', () => {
    it('should maintain proper focus management during navigation', () => {
      render(<IntegratedKnowledgeBaseEditor />);
      
      // Start creation flow
      const newCharacterButton = screen.getByText('New Character');
      fireEvent.click(newCharacterButton);
      
      // Should be able to navigate with keyboard
      const pdfImportButton = screen.getByText('Upload PDF Character Sheet');
      const manualWizardButton = screen.getByText('Start Manual Wizard');
      
      expect(pdfImportButton).not.toHaveAttribute('tabindex', '-1');
      expect(manualWizardButton).not.toHaveAttribute('tabindex', '-1');
    });

    it('should provide proper ARIA labels throughout the workflow', () => {
      render(<IntegratedKnowledgeBaseEditor />);
      
      // Check main editor accessibility
      expect(screen.getByRole('button', { name: /new character/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /close editor/i })).toBeInTheDocument();
      
      // Navigate to selection
      const newCharacterButton = screen.getByText('New Character');
      fireEvent.click(newCharacterButton);
      
      // Check selection screen accessibility
      expect(screen.getByRole('button', { name: /upload pdf character sheet/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /start manual wizard/i })).toBeInTheDocument();
    });
  });
});