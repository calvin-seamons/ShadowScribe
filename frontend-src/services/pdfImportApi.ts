import { PDFExtractionResult, CharacterParseResult, PDFImportSession } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api';

export class PDFImportError extends Error {
  constructor(message: string, public statusCode?: number) {
    super(message);
    this.name = 'PDFImportError';
  }
}

/**
 * Upload PDF file and extract text content
 */
export async function uploadPDF(file: File, signal?: AbortSignal): Promise<PDFExtractionResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/character/import-pdf/upload`, {
    method: 'POST',
    body: formData,
    signal,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new PDFImportError(errorData.detail || 'Failed to upload PDF', response.status);
  }

  return response.json();
}

/**
 * Get extracted PDF text for preview
 */
export async function getPDFPreview(sessionId: string): Promise<{ extracted_text: string }> {
  const response = await fetch(`${API_BASE_URL}/character/import-pdf/preview/${sessionId}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to get preview' }));
    throw new PDFImportError(errorData.detail || 'Failed to get PDF preview', response.status);
  }

  return response.json();
}

/**
 * Parse extracted text using LLM
 */
export async function parsePDFContent(sessionId: string, extractedText?: string): Promise<CharacterParseResult> {
  const response = await fetch(`${API_BASE_URL}/character/import-pdf/parse`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      extracted_text: extractedText,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Parsing failed' }));
    throw new PDFImportError(errorData.detail || 'Failed to parse PDF content', response.status);
  }

  return response.json();
}

/**
 * Generate character files from parsed data
 */
export async function generateCharacterFiles(
  sessionId: string, 
  characterName: string, 
  parsedData?: Record<string, any>
): Promise<{ character_name: string; files_created: string[]; status: string; message: string }> {
  const response = await fetch(`${API_BASE_URL}/character/import-pdf/generate/${sessionId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      character_name: characterName,
      parsed_data: parsedData,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Generation failed' }));
    throw new PDFImportError(errorData.detail || 'Failed to generate character files', response.status);
  }

  return response.json();
}

/**
 * Clean up temporary files and session data
 */
export async function cleanupPDFSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/character/import-pdf/cleanup/${sessionId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    // Don't throw error for cleanup failures, just log
    console.warn('Failed to cleanup PDF session:', sessionId);
  }
}

/**
 * Get current session status and data
 */
export async function getPDFImportSession(sessionId: string): Promise<PDFImportSession> {
  const response = await fetch(`${API_BASE_URL}/character/import-pdf/session/${sessionId}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to get session' }));
    throw new PDFImportError(errorData.detail || 'Failed to get import session', response.status);
  }

  return response.json();
}