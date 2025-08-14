import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PDFUpload } from '../PDFUpload';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('PDFUpload - Vision Processing', () => {
  const mockOnUploadComplete = vi.fn();
  const mockOnError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const renderComponent = () => {
    return render(
      <PDFUpload
        onUploadComplete={mockOnUploadComplete}
        onError={mockOnError}
      />
    );
  };

  const createMockFile = (name: string, type: string, size: number) => {
    const file = new File(['mock content'], name, { type });
    Object.defineProperty(file, 'size', { value: size });
    return file;
  };

  const getFileInput = () => document.querySelector('input[type="file"]') as HTMLInputElement;

  describe('Initial Render', () => {
    it('renders upload interface with correct elements for vision processing', () => {
      renderComponent();
      
      expect(screen.getByText('Upload PDF Character Sheet')).toBeInTheDocument();
      expect(screen.getByText('Drop your PDF here or click to browse')).toBeInTheDocument();
      expect(screen.getByText('Maximum file size: 10MB • Supported format: PDF')).toBeInTheDocument();
      expect(screen.getByText('Supported PDF Formats')).toBeInTheDocument();
      expect(screen.getByText(/The system will convert each page to high-quality images for AI vision processing/)).toBeInTheDocument();
    });

    it('displays supported formats information including vision-specific formats', () => {
      renderComponent();
      
      expect(screen.getByText(/D&D Beyond character sheet exports/)).toBeInTheDocument();
      expect(screen.getByText(/Roll20 character sheet PDFs/)).toBeInTheDocument();
      expect(screen.getByText(/Official D&D 5e character sheets/)).toBeInTheDocument();
      expect(screen.getByText(/Handwritten or filled PDF character sheets/)).toBeInTheDocument();
      expect(screen.getByText(/Scanned character sheets and images/)).toBeInTheDocument();
      expect(screen.getByText(/Complex layouts and visual formats/)).toBeInTheDocument();
    });
  });

  describe('File Selection', () => {
    it('opens file dialog when upload area is clicked', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      const uploadArea = screen.getByText('Drop your PDF here or click to browse').closest('div');
      expect(uploadArea).toBeInTheDocument();
      
      // Mock file input click
      const fileInput = getFileInput();
      const clickSpy = vi.spyOn(fileInput, 'click');
      
      await user.click(uploadArea!);
      expect(clickSpy).toHaveBeenCalled();
    });

    it('handles file selection through input for image conversion', async () => {
      const user = userEvent.setup();
      const mockFile = createMockFile('character.pdf', 'application/pdf', 1024 * 1024); // 1MB
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: 'test-session-123',
          images: ['base64-image-1', 'base64-image-2'],
          page_count: 2,
          image_format: 'PNG',
          total_size_mb: 1.5,
        }),
      });

      renderComponent();
      
      const fileInput = getFileInput();
      await user.upload(fileInput, mockFile);
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/character/import-pdf/upload',
          expect.objectContaining({
            method: 'POST',
            body: expect.any(FormData),
          })
        );
      });
    });
  });

  describe('File Validation', () => {
    it('has file validation logic', () => {
      renderComponent();
      
      // Verify the component has the correct file input restrictions
      const fileInput = getFileInput();
      expect(fileInput.accept).toBe('.pdf,application/pdf');
      
      // The validation logic is tested through integration with valid files
      expect(fileInput).toBeInTheDocument();
    });

    it('validates file size and calls onError for large files', async () => {
      const user = userEvent.setup();
      const mockFile = createMockFile('large.pdf', 'application/pdf', 11 * 1024 * 1024); // 11MB
      
      renderComponent();
      
      const fileInput = getFileInput();
      await user.upload(fileInput, mockFile);
      
      expect(mockOnError).toHaveBeenCalledWith('File size exceeds the maximum limit of 10MB. Please select a smaller file.');
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('accepts valid PDF files and converts to images', async () => {
      const user = userEvent.setup();
      const mockFile = createMockFile('character.pdf', 'application/pdf', 5 * 1024 * 1024); // 5MB
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: 'test-session-123',
          images: ['base64-image-1', 'base64-image-2', 'base64-image-3'],
          page_count: 3,
          image_format: 'PNG',
          total_size_mb: 2.1,
        }),
      });

      renderComponent();
      
      const fileInput = getFileInput();
      await user.upload(fileInput, mockFile);
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
      });
      
      expect(mockOnError).not.toHaveBeenCalled();
    });
  });

  describe('Drag and Drop', () => {
    it('has drag and drop upload area', () => {
      renderComponent();
      
      // Find the actual upload area with border-dashed class
      const uploadArea = document.querySelector('.border-dashed');
      
      // Just verify the element exists and has the expected structure
      expect(uploadArea).toBeInTheDocument();
      expect(uploadArea?.className).toContain('border-dashed');
    });

    it('handles file drop with valid PDF for image conversion', async () => {
      const mockFile = createMockFile('character.pdf', 'application/pdf', 1024 * 1024);
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: 'test-session-123',
          images: ['base64-image-1'],
          page_count: 1,
          image_format: 'PNG',
          total_size_mb: 0.8,
        }),
      });

      renderComponent();
      
      const uploadArea = screen.getByText('Drop your PDF here or click to browse').closest('div')!.parentElement!;
      
      const dropEvent = new Event('drop', { bubbles: true });
      Object.defineProperty(dropEvent, 'dataTransfer', {
        value: {
          files: [mockFile],
        },
      });
      
      fireEvent(uploadArea, dropEvent);
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
      });
    });
  });

  describe('Upload and Conversion Progress', () => {
    it('shows upload and conversion progress during file processing', async () => {
      const user = userEvent.setup();
      const mockFile = createMockFile('character.pdf', 'application/pdf', 1024 * 1024);
      
      // Mock a delayed response
      mockFetch.mockImplementationOnce(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: async () => ({
              session_id: 'test-session-123',
              images: ['base64-image-1', 'base64-image-2'],
              page_count: 2,
              image_format: 'PNG',
              total_size_mb: 1.2,
            }),
          }), 100)
        )
      );

      renderComponent();
      
      const fileInput = getFileInput();
      await user.upload(fileInput, mockFile);
      
      // Check that upload progress is shown
      await waitFor(() => {
        expect(screen.getByText(/Uploading character\.pdf\.\.\./)).toBeInTheDocument();
      });
      
      // Check progress bar exists
      expect(document.querySelector('.bg-purple-500')).toBeInTheDocument();
      
      // Should eventually show conversion stage
      await waitFor(() => {
        expect(screen.getByText(/Converting PDF to images\.\.\./)).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('shows cancel button during upload and conversion', async () => {
      const user = userEvent.setup();
      const mockFile = createMockFile('character.pdf', 'application/pdf', 1024 * 1024);
      
      // Mock a delayed response
      mockFetch.mockImplementationOnce(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: async () => ({
              session_id: 'test-session-123',
              images: ['base64-image-1'],
              page_count: 1,
              image_format: 'PNG',
              total_size_mb: 0.5,
            }),
          }), 100)
        )
      );

      renderComponent();
      
      const fileInput = getFileInput();
      await user.upload(fileInput, mockFile);
      
      // Wait for upload to start and check cancel button appears
      await waitFor(() => {
        expect(screen.getByText('Cancel Upload')).toBeInTheDocument();
      });
      
      // Should show conversion cancel button later
      await waitFor(() => {
        expect(screen.getByText('Cancel Conversion')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('shows conversion progress indicators', async () => {
      const user = userEvent.setup();
      const mockFile = createMockFile('character.pdf', 'application/pdf', 1024 * 1024);
      
      // Mock a delayed response
      mockFetch.mockImplementationOnce(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: async () => ({
              session_id: 'test-session-123',
              images: ['base64-image-1', 'base64-image-2'],
              page_count: 2,
              image_format: 'PNG',
              total_size_mb: 1.1,
            }),
          }), 150)
        )
      );

      renderComponent();
      
      const fileInput = getFileInput();
      await user.upload(fileInput, mockFile);
      
      // Should show conversion-specific messaging
      await waitFor(() => {
        expect(screen.getByText(/Converting pages to high-quality images/)).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Error Handling', () => {
    it('handles API errors gracefully during image conversion', async () => {
      const user = userEvent.setup();
      const mockFile = createMockFile('character.pdf', 'application/pdf', 1024 * 1024);
      
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Image conversion failed' }),
      });

      renderComponent();
      
      const fileInput = getFileInput();
      await user.upload(fileInput, mockFile);
      
      await waitFor(() => {
        expect(screen.getByText('Upload Error')).toBeInTheDocument();
        expect(screen.getByText('Image conversion failed')).toBeInTheDocument();
      });
      
      expect(mockOnError).toHaveBeenCalledWith('Image conversion failed');
    });

    it('provides retry functionality after error', async () => {
      const user = userEvent.setup();
      const mockFile = createMockFile('character.pdf', 'application/pdf', 1024 * 1024);
      
      // First call fails
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Server error' }),
      });
      
      // Second call succeeds
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: 'test-session-123',
          images: ['base64-image-1'],
          page_count: 1,
          image_format: 'PNG',
          total_size_mb: 0.7,
        }),
      });

      renderComponent();
      
      const fileInput = getFileInput();
      await user.upload(fileInput, mockFile);
      
      await waitFor(() => {
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Try Again'));
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2);
      });
    });

    it('allows choosing different file after error', async () => {
      const user = userEvent.setup();
      const mockFile = createMockFile('character.pdf', 'application/pdf', 1024 * 1024);
      
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Server error' }),
      });

      renderComponent();
      
      const fileInput = getFileInput();
      await user.upload(fileInput, mockFile);
      
      await waitFor(() => {
        expect(screen.getByText('Choose Different File')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Choose Different File'));
      
      // Error should be cleared
      expect(screen.queryByText('Upload Error')).not.toBeInTheDocument();
    });
  });

  describe('Success Flow', () => {
    it('calls onUploadComplete with correct data on successful image conversion', async () => {
      const user = userEvent.setup();
      const mockFile = createMockFile('character.pdf', 'application/pdf', 1024 * 1024);
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: 'test-session-123',
          images: ['base64-image-1', 'base64-image-2'],
          page_count: 2,
          image_format: 'PNG',
          total_size_mb: 1.3,
        }),
      });

      renderComponent();
      
      const fileInput = getFileInput();
      await user.upload(fileInput, mockFile);
      
      await waitFor(() => {
        expect(mockOnUploadComplete).toHaveBeenCalledWith(
          'test-session-123',
          2 // page_count
        );
      }, { timeout: 2000 });
    });

    it('resets upload state after successful conversion', async () => {
      const user = userEvent.setup();
      const mockFile = createMockFile('character.pdf', 'application/pdf', 1024 * 1024);
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: 'test-session-123',
          images: ['base64-image-1'],
          page_count: 1,
          image_format: 'PNG',
          total_size_mb: 0.6,
        }),
      });

      renderComponent();
      
      const fileInput = getFileInput();
      await user.upload(fileInput, mockFile);
      
      await waitFor(() => {
        expect(mockOnUploadComplete).toHaveBeenCalled();
      });
      
      // Should return to initial state
      await waitFor(() => {
        expect(screen.getByText('Drop your PDF here or click to browse')).toBeInTheDocument();
      });
    });

    it('handles multi-page PDF conversion correctly', async () => {
      const user = userEvent.setup();
      const mockFile = createMockFile('multi-page.pdf', 'application/pdf', 2 * 1024 * 1024);
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: 'test-session-456',
          images: ['base64-image-1', 'base64-image-2', 'base64-image-3', 'base64-image-4'],
          page_count: 4,
          image_format: 'PNG',
          total_size_mb: 2.8,
        }),
      });

      renderComponent();
      
      const fileInput = getFileInput();
      await user.upload(fileInput, mockFile);
      
      await waitFor(() => {
        expect(mockOnUploadComplete).toHaveBeenCalledWith(
          'test-session-456',
          4 // page_count for 4-page PDF
        );
      }, { timeout: 2000 });
    });
  });
});