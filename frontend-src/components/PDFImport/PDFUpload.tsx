import React, { useState, useRef, useCallback } from 'react';
import { Upload, X, FileText, AlertCircle, CheckCircle } from 'lucide-react';

interface PDFUploadProps {
  onUploadComplete: (sessionId: string, extractedText: string) => void;
  onError: (error: string) => void;
}

interface UploadState {
  isDragOver: boolean;
  isUploading: boolean;
  progress: number;
  error: string | null;
  file: File | null;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ACCEPTED_TYPES = ['application/pdf'];

export const PDFUpload: React.FC<PDFUploadProps> = ({ onUploadComplete, onError }) => {
  const [uploadState, setUploadState] = useState<UploadState>({
    isDragOver: false,
    isUploading: false,
    progress: 0,
    error: null,
    file: null,
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const validateFile = useCallback((file: File): string | null => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return 'Only PDF files are supported. Please select a valid PDF file.';
    }
    
    if (file.size > MAX_FILE_SIZE) {
      return `File size exceeds the maximum limit of ${MAX_FILE_SIZE / (1024 * 1024)}MB. Please select a smaller file.`;
    }
    
    return null;
  }, []);

  const resetUploadState = useCallback(() => {
    setUploadState({
      isDragOver: false,
      isUploading: false,
      progress: 0,
      error: null,
      file: null,
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const uploadFile = useCallback(async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setUploadState(prev => ({ ...prev, error: validationError }));
      onError(validationError);
      return;
    }

    setUploadState(prev => ({ 
      ...prev, 
      isUploading: true, 
      progress: 0, 
      error: null, 
      file 
    }));

    try {
      // Create abort controller for cancellation
      abortControllerRef.current = new AbortController();

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/character/import-pdf/upload', {
        method: 'POST',
        body: formData,
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(errorData.detail || 'Upload failed');
      }

      // Simulate progress for better UX (since we don't have real progress from fetch)
      const progressInterval = setInterval(() => {
        setUploadState(prev => {
          const newProgress = Math.min(prev.progress + 10, 90);
          return { ...prev, progress: newProgress };
        });
      }, 100);

      const result = await response.json();
      
      clearInterval(progressInterval);
      setUploadState(prev => ({ ...prev, progress: 100 }));

      // Small delay to show 100% progress
      setTimeout(() => {
        onUploadComplete(result.session_id, ''); // Pass empty string for extracted_text since it will be fetched later
        resetUploadState();
      }, 500);

    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          setUploadState(prev => ({ ...prev, error: 'Upload cancelled', isUploading: false }));
        } else {
          const errorMessage = error.message || 'Failed to upload PDF file';
          setUploadState(prev => ({ ...prev, error: errorMessage, isUploading: false }));
          onError(errorMessage);
        }
      }
    }
  }, [validateFile, onUploadComplete, onError, resetUploadState]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setUploadState(prev => ({ ...prev, isDragOver: true }));
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setUploadState(prev => ({ ...prev, isDragOver: false }));
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setUploadState(prev => ({ ...prev, isDragOver: false }));

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      uploadFile(files[0]);
    }
  }, [uploadFile]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      uploadFile(files[0]);
    }
  }, [uploadFile]);

  const handleCancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    resetUploadState();
  }, [resetUploadState]);

  const handleRetry = useCallback(() => {
    if (uploadState.file) {
      uploadFile(uploadState.file);
    } else {
      resetUploadState();
    }
  }, [uploadState.file, uploadFile, resetUploadState]);

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Upload PDF Character Sheet</h2>
        <p className="text-gray-400">
          Upload your D&D character sheet in PDF format. Supported sources include D&D Beyond exports, 
          Roll20 sheets, and other PDF character sheets.
        </p>
      </div>

      {/* Upload Area */}
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200
          ${uploadState.isDragOver 
            ? 'border-purple-400 bg-purple-900/20' 
            : 'border-gray-600 hover:border-gray-500'
          }
          ${uploadState.isUploading ? 'pointer-events-none' : 'cursor-pointer'}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !uploadState.isUploading && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileSelect}
          className="hidden"
          disabled={uploadState.isUploading}
        />

        {uploadState.isUploading ? (
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              <FileText className="h-12 w-12 text-purple-400" />
            </div>
            <div>
              <p className="text-white font-medium mb-2">
                Uploading {uploadState.file?.name}...
              </p>
              <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                <div 
                  className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadState.progress}%` }}
                />
              </div>
              <p className="text-sm text-gray-400">{uploadState.progress}% complete</p>
            </div>
            <button
              onClick={handleCancel}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors"
            >
              <X className="h-4 w-4 mr-2" />
              Cancel Upload
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              <Upload className="h-12 w-12 text-gray-400" />
            </div>
            <div>
              <p className="text-white font-medium mb-2">
                Drop your PDF here or click to browse
              </p>
              <p className="text-sm text-gray-400">
                Maximum file size: 10MB • Supported format: PDF
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Error Display */}
      {uploadState.error && (
        <div className="mt-4 p-4 bg-red-900/20 border border-red-700 rounded-lg">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-red-400 mt-0.5 mr-3 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-red-300 font-medium">Upload Error</p>
              <p className="text-red-200 text-sm mt-1">{uploadState.error}</p>
              <div className="mt-3 flex space-x-3">
                <button
                  onClick={handleRetry}
                  className="text-sm text-red-300 hover:text-red-200 underline"
                >
                  Try Again
                </button>
                <button
                  onClick={resetUploadState}
                  className="text-sm text-gray-400 hover:text-gray-300 underline"
                >
                  Choose Different File
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* File Requirements */}
      <div className="mt-6 p-4 bg-gray-800 rounded-lg">
        <h3 className="text-white font-medium mb-2 flex items-center">
          <CheckCircle className="h-4 w-4 text-green-400 mr-2" />
          Supported PDF Formats
        </h3>
        <ul className="text-sm text-gray-300 space-y-1">
          <li>• D&D Beyond character sheet exports</li>
          <li>• Roll20 character sheet PDFs</li>
          <li>• Official D&D 5e character sheets</li>
          <li>• Handwritten or filled PDF character sheets</li>
        </ul>
        <p className="text-xs text-gray-400 mt-2">
          Note: Scanned images or heavily formatted sheets may require manual review after upload.
        </p>
      </div>
    </div>
  );
};