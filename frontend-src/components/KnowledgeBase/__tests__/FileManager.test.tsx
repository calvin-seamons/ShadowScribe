/**
 * FileManager Component Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { FileManager } from '../FileManager';
import * as knowledgeBaseApi from '../../../services/knowledgeBaseApi';

// Mock the API
vi.mock('../../../services/knowledgeBaseApi', () => ({
  listKnowledgeBaseFiles: vi.fn(),
  listBackups: vi.fn(),
  restoreBackup: vi.fn(),
  duplicateFile: vi.fn(),
  exportFile: vi.fn(),
  importFile: vi.fn(),
  exportCharacter: vi.fn(),
  importCharacter: vi.fn(),
  deleteFile: vi.fn(),
  checkFileConflicts: vi.fn(),
  getErrorMessage: vi.fn((error) => error.message || 'Unknown error')
}));

const mockFiles = [
  {
    filename: 'test-character/character.json',
    file_type: 'character' as const,
    size: 1024,
    last_modified: '2024-01-01T12:00:00Z',
    is_editable: true
  },
  {
    filename: 'test-character/character_background.json',
    file_type: 'character_background' as const,
    size: 512,
    last_modified: '2024-01-01T12:00:00Z',
    is_editable: true
  }
];

const mockBackups = [
  {
    backup_id: 'backup-1',
    filename: 'test-character/character.json',
    created_at: '2024-01-01T11:00:00Z',
    size: 1000
  }
];

describe('FileManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (knowledgeBaseApi.listKnowledgeBaseFiles as any).mockResolvedValue(mockFiles);
    (knowledgeBaseApi.listBackups as any).mockResolvedValue(mockBackups);
  });

  it('renders file manager with tabs', async () => {
    render(<FileManager />);
    
    await waitFor(() => {
      expect(screen.getByText('File Manager')).toBeInTheDocument();
      expect(screen.getByText('Files (2)')).toBeInTheDocument();
      expect(screen.getByText('Backups (1)')).toBeInTheDocument();
    });
  });

  it('displays files list', async () => {
    render(<FileManager />);
    
    await waitFor(() => {
      expect(screen.getByText('test-character/character.json')).toBeInTheDocument();
      expect(screen.getByText('test-character/character_background.json')).toBeInTheDocument();
    });
  });

  it('switches to backups tab', async () => {
    render(<FileManager />);
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('Backups (1)'));
    });

    await waitFor(() => {
      expect(screen.getByText('test-character/character.json')).toBeInTheDocument();
      expect(screen.getByText('Restore')).toBeInTheDocument();
    });
  });

  it('handles file export', async () => {
    const mockExportData = { test: 'data' };
    (knowledgeBaseApi.exportFile as any).mockResolvedValue(mockExportData);
    
    // Mock URL.createObjectURL and related DOM methods
    global.URL.createObjectURL = vi.fn(() => 'mock-url');
    global.URL.revokeObjectURL = vi.fn();
    
    const mockLink = {
      href: '',
      download: '',
      click: vi.fn()
    };
    vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
    vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
    vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);

    render(<FileManager />);
    
    await waitFor(() => {
      const exportButtons = screen.getAllByTitle('Export file');
      fireEvent.click(exportButtons[0]);
    });

    await waitFor(() => {
      expect(knowledgeBaseApi.exportFile).toHaveBeenCalledWith('test-character/character.json');
      expect(mockLink.click).toHaveBeenCalled();
    });
  });

  it('handles file duplication', async () => {
    (knowledgeBaseApi.duplicateFile as any).mockResolvedValue(undefined);
    
    render(<FileManager />);
    
    await waitFor(() => {
      const duplicateButtons = screen.getAllByTitle('Duplicate file');
      fireEvent.click(duplicateButtons[0]);
    });

    // Should open duplicate modal
    await waitFor(() => {
      expect(screen.getByText('Duplicate File')).toBeInTheDocument();
      expect(screen.getByDisplayValue('test-character/character_copy.json')).toBeInTheDocument();
    });

    // Confirm duplication
    fireEvent.click(screen.getByText('Duplicate'));

    await waitFor(() => {
      expect(knowledgeBaseApi.duplicateFile).toHaveBeenCalledWith(
        'test-character/character.json',
        'test-character/character_copy.json'
      );
    });
  });

  it('handles file deletion with conflict check', async () => {
    const mockConflicts = {
      has_conflicts: false,
      conflicts: [],
      message: 'No conflicts detected'
    };
    (knowledgeBaseApi.checkFileConflicts as any).mockResolvedValue(mockConflicts);
    (knowledgeBaseApi.deleteFile as any).mockResolvedValue(undefined);
    
    render(<FileManager />);
    
    await waitFor(() => {
      const deleteButtons = screen.getAllByTitle('Delete file');
      fireEvent.click(deleteButtons[0]);
    });

    // Should open delete confirmation modal
    await waitFor(() => {
      expect(screen.getByText('Confirm Deletion')).toBeInTheDocument();
      expect(screen.getByText('No conflicts detected. Safe to delete.')).toBeInTheDocument();
    });

    // Confirm deletion
    fireEvent.click(screen.getByText('Delete'));

    await waitFor(() => {
      expect(knowledgeBaseApi.deleteFile).toHaveBeenCalledWith('test-character/character.json');
    });
  });

  it('handles character export', async () => {
    const mockExportPackage = { character_data: { test: 'data' } };
    (knowledgeBaseApi.exportCharacter as any).mockResolvedValue(mockExportPackage);
    
    // Mock URL.createObjectURL and related DOM methods
    global.URL.createObjectURL = vi.fn(() => 'mock-url');
    global.URL.revokeObjectURL = vi.fn();
    
    const mockLink = {
      href: '',
      download: '',
      click: vi.fn()
    };
    vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
    vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
    vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);

    render(<FileManager />);
    
    await waitFor(() => {
      const characterExportButton = screen.getByText('test-character');
      fireEvent.click(characterExportButton);
    });

    await waitFor(() => {
      expect(knowledgeBaseApi.exportCharacter).toHaveBeenCalledWith('test-character');
      expect(mockLink.click).toHaveBeenCalled();
    });
  });

  it('handles backup restoration', async () => {
    (knowledgeBaseApi.restoreBackup as any).mockResolvedValue(undefined);
    
    render(<FileManager />);
    
    // Switch to backups tab
    await waitFor(() => {
      fireEvent.click(screen.getByText('Backups (1)'));
    });

    // Click restore button
    await waitFor(() => {
      fireEvent.click(screen.getByText('Restore'));
    });

    await waitFor(() => {
      expect(knowledgeBaseApi.restoreBackup).toHaveBeenCalledWith('backup-1');
    });
  });

  it('handles import file', async () => {
    const mockFile = new File(['{"test": "data"}'], 'test.json', { type: 'application/json' });
    (knowledgeBaseApi.importFile as any).mockResolvedValue(undefined);
    
    render(<FileManager />);
    
    const fileInput = screen.getByLabelText('Import') as HTMLInputElement;
    
    // Mock FileReader
    const mockFileReader = {
      readAsText: vi.fn(),
      onload: null as any,
      result: '{"test": "data"}'
    };
    vi.spyOn(window, 'FileReader').mockImplementation(() => mockFileReader as any);
    
    fireEvent.change(fileInput, { target: { files: [mockFile] } });
    
    // Simulate FileReader onload
    mockFileReader.onload({ target: { result: '{"test": "data"}' } } as any);
    
    await waitFor(() => {
      expect(screen.getByText('Import File')).toBeInTheDocument();
    });

    // Confirm import
    fireEvent.click(screen.getByText('Import'));

    await waitFor(() => {
      expect(knowledgeBaseApi.importFile).toHaveBeenCalled();
    });
  });

  it('displays error messages', async () => {
    const errorMessage = 'Test error message';
    (knowledgeBaseApi.listKnowledgeBaseFiles as any).mockRejectedValue(new Error(errorMessage));
    
    render(<FileManager />);
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });
});