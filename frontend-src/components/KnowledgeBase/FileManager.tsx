/**
 * File Manager Component
 * 
 * Provides comprehensive file management functionality including:
 * - File conflict detection and resolution
 * - Backup restoration with version history
 * - File export/import for portability
 * - File deletion with safety checks
 * - File duplication for character variants
 */

import React, { useState, useEffect } from 'react';
import { 
  Trash2, 
  Copy, 
  Download, 
  Upload, 
  History, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  FileText,
  User,
  Calendar,
  HardDrive
} from 'lucide-react';
import {
  KnowledgeBaseFile,
  BackupInfo,
  ConflictCheckResult,
  listKnowledgeBaseFiles,
  listBackups,
  restoreBackup,
  duplicateFile,
  exportFile,
  importFile,
  exportCharacter,
  importCharacter,
  deleteFile,
  checkFileConflicts,
  getErrorMessage
} from '../../services/knowledgeBaseApi';

interface FileManagerProps {
  selectedFile?: string;
  onFileSelect?: (filename: string) => void;
  onFileChange?: () => void;
}

interface DeleteConfirmationState {
  filename: string;
  conflicts: ConflictCheckResult | null;
  isLoading: boolean;
}

interface DuplicateState {
  filename: string;
  newName: string;
  isLoading: boolean;
}

interface ImportState {
  isVisible: boolean;
  importData: any;
  filename: string;
  overwrite: boolean;
  isLoading: boolean;
}

export const FileManager: React.FC<FileManagerProps> = ({
  selectedFile,
  onFileSelect,
  onFileChange
}) => {
  const [files, setFiles] = useState<KnowledgeBaseFile[]>([]);
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'files' | 'backups'>('files');
  
  // State for various operations
  const [deleteConfirmation, setDeleteConfirmation] = useState<DeleteConfirmationState | null>(null);
  const [duplicateState, setDuplicateState] = useState<DuplicateState | null>(null);
  const [importState, setImportState] = useState<ImportState>({
    isVisible: false,
    importData: null,
    filename: '',
    overwrite: false,
    isLoading: false
  });

  // Load files and backups
  useEffect(() => {
    loadFiles();
    loadBackups();
  }, []);

  const loadFiles = async () => {
    try {
      setLoading(true);
      const fileList = await listKnowledgeBaseFiles();
      setFiles(fileList);
      setError(null);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const loadBackups = async () => {
    try {
      const backupList = await listBackups();
      setBackups(backupList);
    } catch (err) {
      console.error('Failed to load backups:', err);
    }
  };

  // File deletion with conflict checking
  const handleDeleteClick = async (filename: string) => {
    try {
      setDeleteConfirmation({ filename, conflicts: null, isLoading: true });
      
      // Check for conflicts before deletion
      const conflicts = await checkFileConflicts(filename);
      
      setDeleteConfirmation({ filename, conflicts, isLoading: false });
    } catch (err) {
      setError(getErrorMessage(err));
      setDeleteConfirmation(null);
    }
  };

  const confirmDelete = async () => {
    if (!deleteConfirmation) return;

    try {
      await deleteFile(deleteConfirmation.filename);
      setDeleteConfirmation(null);
      await loadFiles();
      await loadBackups();
      onFileChange?.();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  // File duplication
  const handleDuplicateClick = (filename: string) => {
    const baseName = filename.replace(/\.json$/, '');
    const newName = `${baseName}_copy.json`;
    setDuplicateState({ filename, newName, isLoading: false });
  };

  const confirmDuplicate = async () => {
    if (!duplicateState) return;

    try {
      setDuplicateState({ ...duplicateState, isLoading: true });
      await duplicateFile(duplicateState.filename, duplicateState.newName);
      setDuplicateState(null);
      await loadFiles();
      onFileChange?.();
    } catch (err) {
      setError(getErrorMessage(err));
      setDuplicateState({ ...duplicateState, isLoading: false });
    }
  };

  // File export
  const handleExport = async (filename: string) => {
    try {
      const exportData = await exportFile(filename);
      
      // Create download
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
        type: 'application/json' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename.replace(/[\/\\]/g, '_')}_export.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  // Character export
  const handleCharacterExport = async (characterName: string) => {
    try {
      const exportPackage = await exportCharacter(characterName);
      
      // Create download
      const blob = new Blob([JSON.stringify(exportPackage, null, 2)], { 
        type: 'application/json' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${characterName}_character_export.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  // File import
  const handleImportFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importData = JSON.parse(e.target?.result as string);
        setImportState({
          isVisible: true,
          importData,
          filename: '',
          overwrite: false,
          isLoading: false
        });
      } catch (err) {
        setError('Invalid JSON file');
      }
    };
    reader.readAsText(file);
  };

  const confirmImport = async () => {
    if (!importState.importData) return;

    try {
      setImportState({ ...importState, isLoading: true });
      
      if (importState.importData.character_data) {
        // Character import
        await importCharacter(
          importState.importData, 
          importState.filename || undefined, 
          importState.overwrite
        );
      } else {
        // Single file import
        await importFile(
          importState.importData, 
          importState.filename || undefined, 
          importState.overwrite
        );
      }
      
      setImportState({
        isVisible: false,
        importData: null,
        filename: '',
        overwrite: false,
        isLoading: false
      });
      
      await loadFiles();
      onFileChange?.();
    } catch (err) {
      setError(getErrorMessage(err));
      setImportState({ ...importState, isLoading: false });
    }
  };

  // Backup restoration
  const handleRestoreBackup = async (backupId: string) => {
    try {
      await restoreBackup(backupId);
      await loadFiles();
      await loadBackups();
      onFileChange?.();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  // Get unique character names from files
  const getCharacterNames = (): string[] => {
    const characters = new Set<string>();
    files.forEach(file => {
      if (file.filename.includes('/')) {
        const characterName = file.filename.split('/')[0];
        characters.add(characterName);
      }
    });
    return Array.from(characters).sort();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">File Manager</h3>
          <div className="flex items-center space-x-2">
            <input
              type="file"
              accept=".json"
              onChange={handleImportFile}
              className="hidden"
              id="import-file"
            />
            <label
              htmlFor="import-file"
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 cursor-pointer"
            >
              <Upload className="h-4 w-4 mr-2" />
              Import
            </label>
          </div>
        </div>
        
        {/* Tabs */}
        <div className="mt-4">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('files')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'files'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <FileText className="h-4 w-4 inline mr-2" />
              Files ({files.length})
            </button>
            <button
              onClick={() => setActiveTab('backups')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'backups'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <History className="h-4 w-4 inline mr-2" />
              Backups ({backups.length})
            </button>
          </nav>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border-l-4 border-red-400">
          <div className="flex">
            <XCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
              <button
                onClick={() => setError(null)}
                className="mt-2 text-sm text-red-600 hover:text-red-500"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-500">Loading...</p>
          </div>
        ) : (
          <>
            {/* Files Tab */}
            {activeTab === 'files' && (
              <div className="space-y-4">
                {/* Character Export Section */}
                {getCharacterNames().length > 0 && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Export Characters</h4>
                    <div className="flex flex-wrap gap-2">
                      {getCharacterNames().map(characterName => (
                        <button
                          key={characterName}
                          onClick={() => handleCharacterExport(characterName)}
                          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                        >
                          <User className="h-4 w-4 mr-2" />
                          {characterName}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Files List */}
                <div className="space-y-2">
                  {files.map(file => (
                    <div
                      key={file.filename}
                      className={`border rounded-lg p-4 ${
                        selectedFile === file.filename
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div 
                          className="flex-1 cursor-pointer"
                          onClick={() => onFileSelect?.(file.filename)}
                        >
                          <div className="flex items-center">
                            <FileText className="h-5 w-5 text-gray-400 mr-3" />
                            <div>
                              <p className="text-sm font-medium text-gray-900">
                                {file.filename}
                              </p>
                              <p className="text-xs text-gray-500">
                                {file.file_type} • {formatFileSize(file.size)} • 
                                Modified {formatDate(file.last_modified)}
                              </p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleDuplicateClick(file.filename)}
                            className="p-2 text-gray-400 hover:text-gray-600"
                            title="Duplicate file"
                          >
                            <Copy className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleExport(file.filename)}
                            className="p-2 text-gray-400 hover:text-gray-600"
                            title="Export file"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteClick(file.filename)}
                            className="p-2 text-red-400 hover:text-red-600"
                            title="Delete file"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {files.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                      <p>No files found</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Backups Tab */}
            {activeTab === 'backups' && (
              <div className="space-y-2">
                {backups.map(backup => (
                  <div
                    key={backup.backup_id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-gray-300"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center">
                          <History className="h-5 w-5 text-gray-400 mr-3" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {backup.filename}
                            </p>
                            <p className="text-xs text-gray-500">
                              <Calendar className="h-3 w-3 inline mr-1" />
                              {formatDate(backup.created_at)} • 
                              <HardDrive className="h-3 w-3 inline ml-2 mr-1" />
                              {formatFileSize(backup.size)}
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      <button
                        onClick={() => handleRestoreBackup(backup.backup_id)}
                        className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                      >
                        <History className="h-4 w-4 mr-2" />
                        Restore
                      </button>
                    </div>
                  </div>
                ))}
                
                {backups.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <History className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>No backups found</p>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirmation && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center">
                <AlertTriangle className="h-6 w-6 text-red-600 mr-3" />
                <h3 className="text-lg font-medium text-gray-900">
                  Confirm Deletion
                </h3>
              </div>
              
              <div className="mt-4">
                <p className="text-sm text-gray-500">
                  Are you sure you want to delete "{deleteConfirmation.filename}"?
                </p>
                
                {deleteConfirmation.isLoading ? (
                  <div className="mt-4 text-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-2 text-sm text-gray-500">Checking for conflicts...</p>
                  </div>
                ) : deleteConfirmation.conflicts?.has_conflicts ? (
                  <div className="mt-4 space-y-2">
                    <p className="text-sm font-medium text-red-600">
                      Potential issues detected:
                    </p>
                    {deleteConfirmation.conflicts.conflicts.map((conflict, index) => (
                      <div key={index} className="text-sm text-gray-600 bg-yellow-50 p-2 rounded">
                        <p className="font-medium">{conflict.message}</p>
                        <p className="text-xs text-gray-500">{conflict.recommendation}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="mt-4 flex items-center text-sm text-green-600">
                    <CheckCircle className="h-4 w-4 mr-2" />
                    No conflicts detected. Safe to delete.
                  </div>
                )}
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setDeleteConfirmation(null)}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDelete}
                  disabled={deleteConfirmation.isLoading}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Duplicate Modal */}
      {duplicateState && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Duplicate File
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Original File
                  </label>
                  <p className="mt-1 text-sm text-gray-500">{duplicateState.filename}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    New File Name
                  </label>
                  <input
                    type="text"
                    value={duplicateState.newName}
                    onChange={(e) => setDuplicateState({ ...duplicateState, newName: e.target.value })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setDuplicateState(null)}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDuplicate}
                  disabled={duplicateState.isLoading || !duplicateState.newName}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {duplicateState.isLoading ? 'Duplicating...' : 'Duplicate'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Import Modal */}
      {importState.isVisible && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Import File
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Import Type
                  </label>
                  <p className="mt-1 text-sm text-gray-500">
                    {importState.importData?.character_data ? 'Character Package' : 'Single File'}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    File/Character Name (optional)
                  </label>
                  <input
                    type="text"
                    value={importState.filename}
                    onChange={(e) => setImportState({ ...importState, filename: e.target.value })}
                    placeholder="Leave empty to use original name"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>
                
                <div className="flex items-center">
                  <input
                    id="overwrite"
                    type="checkbox"
                    checked={importState.overwrite}
                    onChange={(e) => setImportState({ ...importState, overwrite: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="overwrite" className="ml-2 block text-sm text-gray-900">
                    Overwrite existing files
                  </label>
                </div>
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setImportState({ ...importState, isVisible: false })}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmImport}
                  disabled={importState.isLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {importState.isLoading ? 'Importing...' : 'Import'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};