/**
 * Backup Manager Component
 * 
 * Provides detailed backup management functionality including:
 * - Version history with detailed metadata
 * - Backup restoration with preview
 * - Backup comparison and diff viewing
 * - Backup cleanup and management
 */

import React, { useState, useEffect } from 'react';
import { 
  History, 
  RotateCcw, 
  Eye, 
  Calendar, 
  HardDrive, 
  FileText,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';
import {
  BackupInfo,
  FileContent,
  listBackups,
  restoreBackup,
  getFileContent,
  getErrorMessage
} from '../../services/knowledgeBaseApi';

interface BackupManagerProps {
  filename?: string;
  onRestore?: () => void;
}

interface BackupWithPreview extends BackupInfo {
  isExpanded?: boolean;
  previewContent?: any;
  isLoadingPreview?: boolean;
}

export const BackupManager: React.FC<BackupManagerProps> = ({
  filename,
  onRestore
}) => {
  const [backups, setBackups] = useState<BackupWithPreview[]>([]);
  const [currentContent, setCurrentContent] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [restoreConfirmation, setRestoreConfirmation] = useState<string | null>(null);

  useEffect(() => {
    loadBackups();
    if (filename) {
      loadCurrentContent();
    }
  }, [filename]);

  const loadBackups = async () => {
    try {
      setLoading(true);
      const backupList = await listBackups(filename);
      setBackups(backupList.map(backup => ({ ...backup, isExpanded: false })));
      setError(null);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const loadCurrentContent = async () => {
    if (!filename) return;
    
    try {
      const content = await getFileContent(filename);
      setCurrentContent(content.content);
    } catch (err) {
      // File might not exist, that's okay
      setCurrentContent(null);
    }
  };

  const toggleBackupExpansion = async (backupId: string) => {
    const backup = backups.find(b => b.backup_id === backupId);
    if (!backup) return;

    if (backup.isExpanded) {
      // Collapse
      setBackups(backups.map(b => 
        b.backup_id === backupId 
          ? { ...b, isExpanded: false, previewContent: undefined }
          : b
      ));
    } else {
      // Expand and load preview
      setBackups(backups.map(b => 
        b.backup_id === backupId 
          ? { ...b, isExpanded: true, isLoadingPreview: true }
          : b
      ));

      try {
        // For now, we'll show a placeholder since we don't have a direct API to get backup content
        // In a real implementation, you'd want to add an endpoint to get backup content without restoring
        setBackups(backups.map(b => 
          b.backup_id === backupId 
            ? { 
                ...b, 
                isExpanded: true, 
                isLoadingPreview: false,
                previewContent: { message: "Preview not available - restore to view content" }
              }
            : b
        ));
      } catch (err) {
        setBackups(backups.map(b => 
          b.backup_id === backupId 
            ? { ...b, isExpanded: true, isLoadingPreview: false }
            : b
        ));
      }
    }
  };

  const handleRestoreClick = (backupId: string) => {
    setRestoreConfirmation(backupId);
  };

  const confirmRestore = async () => {
    if (!restoreConfirmation) return;

    try {
      await restoreBackup(restoreConfirmation);
      setRestoreConfirmation(null);
      await loadBackups();
      await loadCurrentContent();
      onRestore?.();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) {
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getBackupAge = (dateString: string): 'recent' | 'old' | 'ancient' => {
    const date = new Date(dateString);
    const now = new Date();
    const diffHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffHours < 24) return 'recent';
    if (diffHours < 24 * 7) return 'old';
    return 'ancient';
  };

  const groupBackupsByFile = () => {
    const grouped: { [filename: string]: BackupWithPreview[] } = {};
    
    backups.forEach(backup => {
      if (!grouped[backup.filename]) {
        grouped[backup.filename] = [];
      }
      grouped[backup.filename].push(backup);
    });

    return grouped;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-500">Loading backups...</p>
        </div>
      </div>
    );
  }

  const groupedBackups = filename ? { [filename]: backups } : groupBackupsByFile();

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <History className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">
              Backup History
              {filename && (
                <span className="text-sm font-normal text-gray-500 ml-2">
                  for {filename}
                </span>
              )}
            </h3>
          </div>
          <div className="text-sm text-gray-500">
            {backups.length} backup{backups.length !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border-l-4 border-red-400">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
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
        {Object.keys(groupedBackups).length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <History className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>No backups found</p>
            {filename && (
              <p className="text-sm mt-2">
                Backups will be created automatically when you modify this file
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedBackups).map(([fileName, fileBackups]) => (
              <div key={fileName}>
                {!filename && (
                  <div className="flex items-center mb-4">
                    <FileText className="h-5 w-5 text-gray-400 mr-2" />
                    <h4 className="text-md font-medium text-gray-900">{fileName}</h4>
                    <span className="ml-2 text-sm text-gray-500">
                      ({fileBackups.length} backup{fileBackups.length !== 1 ? 's' : ''})
                    </span>
                  </div>
                )}
                
                <div className="space-y-3">
                  {fileBackups.map((backup, index) => {
                    const age = getBackupAge(backup.created_at);
                    const isLatest = index === 0;
                    
                    return (
                      <div
                        key={backup.backup_id}
                        className={`border rounded-lg ${
                          isLatest 
                            ? 'border-green-200 bg-green-50' 
                            : age === 'recent' 
                              ? 'border-blue-200 bg-blue-50'
                              : 'border-gray-200 bg-white'
                        }`}
                      >
                        <div className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center flex-1">
                              <button
                                onClick={() => toggleBackupExpansion(backup.backup_id)}
                                className="mr-2 p-1 hover:bg-gray-100 rounded"
                              >
                                {backup.isExpanded ? (
                                  <ChevronDown className="h-4 w-4 text-gray-400" />
                                ) : (
                                  <ChevronRight className="h-4 w-4 text-gray-400" />
                                )}
                              </button>
                              
                              <div className="flex-1">
                                <div className="flex items-center">
                                  {isLatest && (
                                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                                  )}
                                  <Clock className="h-4 w-4 text-gray-400 mr-2" />
                                  <span className="text-sm font-medium text-gray-900">
                                    {formatDate(backup.created_at)}
                                  </span>
                                  {isLatest && (
                                    <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                      Latest
                                    </span>
                                  )}
                                </div>
                                
                                <div className="mt-1 flex items-center text-xs text-gray-500">
                                  <HardDrive className="h-3 w-3 mr-1" />
                                  {formatFileSize(backup.size)}
                                  <span className="mx-2">•</span>
                                  <span className="truncate">ID: {backup.backup_id.slice(-8)}</span>
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => toggleBackupExpansion(backup.backup_id)}
                                className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-xs leading-4 font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                              >
                                <Eye className="h-3 w-3 mr-1" />
                                {backup.isExpanded ? 'Hide' : 'Preview'}
                              </button>
                              
                              <button
                                onClick={() => handleRestoreClick(backup.backup_id)}
                                className="inline-flex items-center px-3 py-1 border border-transparent shadow-sm text-xs leading-4 font-medium rounded text-white bg-blue-600 hover:bg-blue-700"
                              >
                                <RotateCcw className="h-3 w-3 mr-1" />
                                Restore
                              </button>
                            </div>
                          </div>
                          
                          {/* Expanded Preview */}
                          {backup.isExpanded && (
                            <div className="mt-4 border-t pt-4">
                              {backup.isLoadingPreview ? (
                                <div className="text-center py-4">
                                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                                  <p className="mt-2 text-sm text-gray-500">Loading preview...</p>
                                </div>
                              ) : (
                                <div className="bg-gray-50 rounded p-3">
                                  <h5 className="text-sm font-medium text-gray-900 mb-2">
                                    Backup Preview
                                  </h5>
                                  <div className="text-xs text-gray-600 font-mono bg-white p-2 rounded border max-h-40 overflow-y-auto">
                                    {backup.previewContent ? (
                                      <pre>{JSON.stringify(backup.previewContent, null, 2)}</pre>
                                    ) : (
                                      <p className="text-gray-500 italic">
                                        Preview not available. Restore backup to view content.
                                      </p>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Restore Confirmation Modal */}
      {restoreConfirmation && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center">
                <RotateCcw className="h-6 w-6 text-blue-600 mr-3" />
                <h3 className="text-lg font-medium text-gray-900">
                  Confirm Restore
                </h3>
              </div>
              
              <div className="mt-4">
                <p className="text-sm text-gray-500">
                  Are you sure you want to restore this backup? This will overwrite the current file content.
                </p>
                
                <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-md p-3">
                  <div className="flex">
                    <AlertCircle className="h-5 w-5 text-yellow-400" />
                    <div className="ml-3">
                      <p className="text-sm text-yellow-700">
                        <strong>Warning:</strong> This action cannot be undone. The current file content will be backed up before restoration.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setRestoreConfirmation(null)}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmRestore}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Restore Backup
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};