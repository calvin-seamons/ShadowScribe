/**
 * Knowledge Base API Service
 * 
 * This service provides TypeScript functions for all knowledge base CRUD operations,
 * including error handling, response typing, templates, schemas, and batch operations.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api';
const KB_API_BASE = `${API_BASE_URL}/knowledge-base`;

// Types for API responses and requests
export interface KnowledgeBaseFile {
  filename: string;
  file_type: 'character' | 'character_background' | 'feats_and_traits' | 'action_list' | 'inventory_list' | 'objectives_and_contracts' | 'spell_list' | 'other';
  size: number;
  last_modified: string;
  is_editable: boolean;
}

export interface FileContent {
  filename: string;
  content: Record<string, any>;
  schema_version?: string;
}

export interface ValidationError {
  field_path: string;
  message: string;
  error_type: 'required' | 'type' | 'format' | 'custom';
}

export interface ValidationResult {
  is_valid: boolean;
  errors: ValidationError[];
  warnings: string[];
}

export interface BackupInfo {
  backup_id: string;
  filename: string;
  created_at: string;
  size: number;
}



// API Response wrappers
export interface ApiResponse<T> {
  status: string;
  data?: T;
  error?: string;
}

export interface FileListResponse {
  files: KnowledgeBaseFile[];
  status: string;
}

export interface FileContentResponse {
  content: FileContent;
  status: string;
}

export interface ValidationResponse {
  result: ValidationResult;
  status: string;
}

export interface SchemaResponse {
  json_schema: Record<string, any>;
  file_type: string;
  status: string;
}

export interface TemplateResponse {
  template: Record<string, any>;
  file_type: string;
  status: string;
}

export interface BackupListResponse {
  backups: BackupInfo[];
  status: string;
}

// Error handling utility
class KnowledgeBaseApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'KnowledgeBaseApiError';
  }
}

// Generic API request handler with error handling
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  try {
    const response = await fetch(`${KB_API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      let errorDetails;

      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
        errorDetails = errorData;
      } catch {
        // If we can't parse the error response, use the default message
      }

      throw new KnowledgeBaseApiError(errorMessage, response.status, errorDetails);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof KnowledgeBaseApiError) {
      throw error;
    }
    
    // Network or other errors
    throw new KnowledgeBaseApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      0,
      error
    );
  }
}

// Character Management Functions
export async function listCharacters(): Promise<{ characters: string[]; count: number }> {
  return apiRequest<{ characters: string[]; count: number }>('/characters');
}

// File CRUD Operations
export async function listKnowledgeBaseFiles(characterName?: string): Promise<KnowledgeBaseFile[]> {
  const params = characterName ? `?character_name=${encodeURIComponent(characterName)}` : '';
  const response = await apiRequest<FileListResponse>(`/files${params}`);
  return response.files;
}

export async function getFileContent(filename: string): Promise<FileContent> {
  const response = await apiRequest<FileContentResponse>(`/files/${encodeURIComponent(filename)}`);
  return response.content;
}

export async function updateFileContent(filename: string, content: Record<string, any>): Promise<void> {
  await apiRequest(`/files/${encodeURIComponent(filename)}`, {
    method: 'PUT',
    body: JSON.stringify({ content }),
  });
}

export async function createFile(filename: string, content: Record<string, any>): Promise<void> {
  await apiRequest('/files', {
    method: 'POST',
    body: JSON.stringify({ filename, content }),
  });
}

export async function deleteFile(filename: string): Promise<void> {
  await apiRequest(`/files/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });
}

// Validation Functions
export async function validateFileContent(
  filename: string, 
  content: Record<string, any>
): Promise<ValidationResult> {
  const response = await apiRequest<ValidationResponse>(`/validate/${encodeURIComponent(filename)}`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
  return response.result;
}

// Schema and Template Functions
export async function getFileSchema(fileType: string): Promise<Record<string, any>> {
  const response = await apiRequest<SchemaResponse>(`/schema/${encodeURIComponent(fileType)}`);
  return response.json_schema;
}

export async function getFileTemplate(fileType: string): Promise<Record<string, any>> {
  const response = await apiRequest<TemplateResponse>(`/template/${encodeURIComponent(fileType)}`);
  return response.template;
}

export async function getSupportedFileTypes(): Promise<Record<string, string>> {
  const response = await apiRequest<{ supported_types: Record<string, string> }>('/supported-types');
  return response.supported_types;
}



// Backup Management Functions
export async function listBackups(filename?: string): Promise<BackupInfo[]> {
  const params = filename ? `?filename=${encodeURIComponent(filename)}` : '';
  const response = await apiRequest<BackupListResponse>(`/backups${params}`);
  return response.backups;
}

export async function restoreBackup(backupId: string): Promise<void> {
  await apiRequest(`/backups/${encodeURIComponent(backupId)}/restore`, {
    method: 'POST',
  });
}

// Batch Operations for Character Creation Workflow
export interface BatchFileOperation {
  filename: string;
  content: Record<string, any>;
  operation: 'create' | 'update';
}

export async function executeBatchFileOperations(operations: BatchFileOperation[]): Promise<void> {
  const promises = operations.map(async (op) => {
    if (op.operation === 'create') {
      return createFile(op.filename, op.content);
    } else {
      return updateFileContent(op.filename, op.content);
    }
  });

  await Promise.all(promises);
}

// Utility Functions for Error Handling
export function isKnowledgeBaseApiError(error: any): error is KnowledgeBaseApiError {
  return error instanceof KnowledgeBaseApiError;
}

export function getErrorMessage(error: any): string {
  if (isKnowledgeBaseApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unknown error occurred';
}

// File Type Utilities
export const FILE_TYPES = {
  CHARACTER: 'character',
  CHARACTER_BACKGROUND: 'character_background',
  FEATS_AND_TRAITS: 'feats_and_traits',
  ACTION_LIST: 'action_list',
  INVENTORY_LIST: 'inventory_list',
  OBJECTIVES_AND_CONTRACTS: 'objectives_and_contracts',
  SPELL_LIST: 'spell_list',
} as const;

export type FileType = typeof FILE_TYPES[keyof typeof FILE_TYPES];

export function getFileTypeFromFilename(filename: string): FileType | 'other' {
  const lowerFilename = filename.toLowerCase();
  
  if (lowerFilename.includes('character_background')) return FILE_TYPES.CHARACTER_BACKGROUND;
  if (lowerFilename.includes('feats_and_traits')) return FILE_TYPES.FEATS_AND_TRAITS;
  if (lowerFilename.includes('action_list')) return FILE_TYPES.ACTION_LIST;
  if (lowerFilename.includes('inventory_list')) return FILE_TYPES.INVENTORY_LIST;
  if (lowerFilename.includes('objectives_and_contracts')) return FILE_TYPES.OBJECTIVES_AND_CONTRACTS;
  if (lowerFilename.includes('spell_list')) return FILE_TYPES.SPELL_LIST;
  if (lowerFilename.includes('character.json')) return FILE_TYPES.CHARACTER;
  
  return 'other';
}

// File Management Functions
export async function duplicateFile(filename: string, newFilename: string): Promise<void> {
  await apiRequest(`/files/${encodeURIComponent(filename)}/duplicate?new_filename=${encodeURIComponent(newFilename)}`, {
    method: 'POST',
  });
}

export async function exportFile(filename: string): Promise<any> {
  const response = await apiRequest<{ export_data: any; filename: string }>(`/files/${encodeURIComponent(filename)}/export`);
  return response.export_data;
}

export async function importFile(exportData: any, filename?: string, overwrite: boolean = false): Promise<void> {
  await apiRequest('/files/import', {
    method: 'POST',
    body: JSON.stringify({
      export_data: exportData,
      filename,
      overwrite,
    }),
  });
}

export async function exportCharacter(characterName: string): Promise<any> {
  const response = await apiRequest<{ export_package: any; character_name: string }>(`/characters/${encodeURIComponent(characterName)}/export`);
  return response.export_package;
}

export async function importCharacter(exportPackage: any, characterName?: string, overwrite: boolean = false): Promise<{ imported_files: string[]; failed_files: string[] }> {
  const response = await apiRequest<{ imported_files: string[]; failed_files: string[] }>('/characters/import', {
    method: 'POST',
    body: JSON.stringify({
      export_package: exportPackage,
      character_name: characterName,
      overwrite,
    }),
  });
  return response;
}

export interface ConflictInfo {
  type: string;
  message: string;
  severity: 'warning' | 'error';
  recommendation: string;
  details?: any;
}

export interface ConflictCheckResult {
  has_conflicts: boolean;
  conflicts: ConflictInfo[];
  file_info?: {
    filename: string;
    size: number;
    last_modified: string;
    recent_backups: number;
  };
  message?: string;
}

export async function checkFileConflicts(filename: string): Promise<ConflictCheckResult> {
  const response = await apiRequest<ConflictCheckResult>(`/files/${encodeURIComponent(filename)}/conflicts`);
  return response;
}

// Export the error class for external use
export { KnowledgeBaseApiError };