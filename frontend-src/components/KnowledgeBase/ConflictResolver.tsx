/**
 * Conflict Resolver Component
 * 
 * Provides conflict detection and resolution UI for file operations including:
 * - Real-time conflict detection
 * - Conflict visualization and explanation
 * - Resolution recommendations
 * - Safe operation confirmation
 */

import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Info, 
  Clock, 
  FileText, 
  Users, 
  Shield,
  RefreshCw
} from 'lucide-react';
import {
  ConflictCheckResult,
  ConflictInfo,
  checkFileConflicts,
  getErrorMessage
} from '../../services/knowledgeBaseApi';

interface ConflictResolverProps {
  filename: string;
  onConflictResolved?: (canProceed: boolean) => void;
  onRefresh?: () => void;
  autoCheck?: boolean;
}

interface ConflictSeverityConfig {
  icon: React.ComponentType<any>;
  color: string;
  bgColor: string;
  borderColor: string;
}

const SEVERITY_CONFIG: Record<string, ConflictSeverityConfig> = {
  error: {
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200'
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200'
  },
  info: {
    icon: Info,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200'
  }
};

export const ConflictResolver: React.FC<ConflictResolverProps> = ({
  filename,
  onConflictResolved,
  onRefresh,
  autoCheck = true
}) => {
  const [conflictResult, setConflictResult] = useState<ConflictCheckResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  useEffect(() => {
    if (autoCheck && filename) {
      checkConflicts();
    }
  }, [filename, autoCheck]);

  const checkConflicts = async () => {
    if (!filename) return;

    try {
      setLoading(true);
      setError(null);
      
      const result = await checkFileConflicts(filename);
      setConflictResult(result);
      setLastChecked(new Date());
      
      // Notify parent component
      onConflictResolved?.(canProceedSafely(result));
      
    } catch (err) {
      setError(getErrorMessage(err));
      setConflictResult(null);
      onConflictResolved?.(false);
    } finally {
      setLoading(false);
    }
  };

  const canProceedSafely = (result: ConflictCheckResult): boolean => {
    if (!result.has_conflicts) return true;
    
    // Check if there are any error-level conflicts
    const hasErrors = result.conflicts.some(conflict => conflict.severity === 'error');
    return !hasErrors;
  };

  const getConflictTypeDescription = (type: string): string => {
    const descriptions: Record<string, string> = {
      recent_modification: 'File was recently modified by another process',
      large_file: 'File size is unusually large',
      validation_error: 'File contains validation errors',
      concurrent_access: 'Multiple users are editing this file',
      backup_failure: 'Recent backup operations failed',
      permission_issue: 'File permission conflicts detected'
    };
    
    return descriptions[type] || 'Unknown conflict type';
  };

  const getResolutionSteps = (conflict: ConflictInfo): string[] => {
    const steps: Record<string, string[]> = {
      recent_modification: [
        'Review recent changes in backup history',
        'Coordinate with other users if applicable',
        'Ensure your changes don\'t conflict with recent modifications'
      ],
      large_file: [
        'Verify file integrity',
        'Check for unexpected data growth',
        'Consider breaking large files into smaller components'
      ],
      validation_error: [
        'Fix validation errors before proceeding',
        'Use the validation panel to identify specific issues',
        'Restore from a valid backup if necessary'
      ],
      concurrent_access: [
        'Coordinate with other users',
        'Wait for other editing sessions to complete',
        'Use the backup system to merge changes if needed'
      ]
    };
    
    return steps[conflict.type] || ['Review the conflict and proceed with caution'];
  };

  const formatLastChecked = (): string => {
    if (!lastChecked) return 'Never';
    
    const now = new Date();
    const diffMs = now.getTime() - lastChecked.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    
    if (diffSeconds < 60) {
      return `${diffSeconds} second${diffSeconds !== 1 ? 's' : ''} ago`;
    } else if (diffMinutes < 60) {
      return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
    } else {
      return lastChecked.toLocaleTimeString();
    }
  };

  if (!filename) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 text-center">
        <FileText className="h-8 w-8 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-500">No file selected for conflict checking</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Shield className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">
              Conflict Detection
            </h3>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="text-sm text-gray-500">
              Last checked: {formatLastChecked()}
            </div>
            <button
              onClick={checkConflicts}
              disabled={loading}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              {loading ? 'Checking...' : 'Check Now'}
            </button>
          </div>
        </div>
        
        <div className="mt-2">
          <p className="text-sm text-gray-600">
            Checking: <span className="font-medium">{filename}</span>
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex">
              <XCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h4 className="text-sm font-medium text-red-800">
                  Conflict Check Failed
                </h4>
                <p className="mt-1 text-sm text-red-700">{error}</p>
                <button
                  onClick={() => setError(null)}
                  className="mt-2 text-sm text-red-600 hover:text-red-500"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        ) : loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-500">Checking for conflicts...</p>
          </div>
        ) : conflictResult ? (
          <div className="space-y-4">
            {/* Overall Status */}
            <div className={`rounded-lg p-4 ${
              !conflictResult.has_conflicts 
                ? 'bg-green-50 border border-green-200'
                : canProceedSafely(conflictResult)
                  ? 'bg-yellow-50 border border-yellow-200'
                  : 'bg-red-50 border border-red-200'
            }`}>
              <div className="flex items-center">
                {!conflictResult.has_conflicts ? (
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                ) : canProceedSafely(conflictResult) ? (
                  <AlertTriangle className="h-5 w-5 text-yellow-500 mr-3" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500 mr-3" />
                )}
                
                <div className="flex-1">
                  <h4 className={`text-sm font-medium ${
                    !conflictResult.has_conflicts 
                      ? 'text-green-800'
                      : canProceedSafely(conflictResult)
                        ? 'text-yellow-800'
                        : 'text-red-800'
                  }`}>
                    {!conflictResult.has_conflicts 
                      ? 'No Conflicts Detected'
                      : canProceedSafely(conflictResult)
                        ? 'Warnings Detected - Proceed with Caution'
                        : 'Conflicts Detected - Action Required'
                    }
                  </h4>
                  
                  <p className={`mt-1 text-sm ${
                    !conflictResult.has_conflicts 
                      ? 'text-green-700'
                      : canProceedSafely(conflictResult)
                        ? 'text-yellow-700'
                        : 'text-red-700'
                  }`}>
                    {conflictResult.message || 
                     (!conflictResult.has_conflicts 
                       ? 'File is safe to modify'
                       : `${conflictResult.conflicts.length} issue${conflictResult.conflicts.length !== 1 ? 's' : ''} found`
                     )
                    }
                  </p>
                </div>
              </div>
            </div>

            {/* File Information */}
            {conflictResult.file_info && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h5 className="text-sm font-medium text-gray-900 mb-3">File Information</h5>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Size:</span>
                    <span className="ml-2 text-gray-900">
                      {(conflictResult.file_info.size / 1024).toFixed(1)} KB
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Last Modified:</span>
                    <span className="ml-2 text-gray-900">
                      {new Date(conflictResult.file_info.last_modified).toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Recent Backups:</span>
                    <span className="ml-2 text-gray-900">
                      {conflictResult.file_info.recent_backups}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Conflicts List */}
            {conflictResult.has_conflicts && (
              <div className="space-y-3">
                <h5 className="text-sm font-medium text-gray-900">
                  Detected Issues ({conflictResult.conflicts.length})
                </h5>
                
                {conflictResult.conflicts.map((conflict, index) => {
                  const config = SEVERITY_CONFIG[conflict.severity] || SEVERITY_CONFIG.info;
                  const IconComponent = config.icon;
                  
                  return (
                    <div
                      key={index}
                      className={`rounded-lg border p-4 ${config.bgColor} ${config.borderColor}`}
                    >
                      <div className="flex items-start">
                        <IconComponent className={`h-5 w-5 ${config.color} mr-3 mt-0.5`} />
                        
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h6 className={`text-sm font-medium ${config.color}`}>
                              {getConflictTypeDescription(conflict.type)}
                            </h6>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              conflict.severity === 'error' 
                                ? 'bg-red-100 text-red-800'
                                : conflict.severity === 'warning'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-blue-100 text-blue-800'
                            }`}>
                              {conflict.severity}
                            </span>
                          </div>
                          
                          <p className={`mt-1 text-sm ${config.color.replace('600', '700')}`}>
                            {conflict.message}
                          </p>
                          
                          <div className="mt-3">
                            <p className={`text-sm font-medium ${config.color.replace('600', '800')}`}>
                              Recommended Actions:
                            </p>
                            <ul className={`mt-1 text-sm ${config.color.replace('600', '700')} list-disc list-inside space-y-1`}>
                              {getResolutionSteps(conflict).map((step, stepIndex) => (
                                <li key={stepIndex}>{step}</li>
                              ))}
                            </ul>
                          </div>
                          
                          {conflict.details && (
                            <div className="mt-3">
                              <details className="group">
                                <summary className={`cursor-pointer text-sm font-medium ${config.color} hover:underline`}>
                                  View Details
                                </summary>
                                <div className="mt-2 p-3 bg-white rounded border">
                                  <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                                    {JSON.stringify(conflict.details, null, 2)}
                                  </pre>
                                </div>
                              </details>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-200">
              <div className="flex items-center space-x-4">
                {onRefresh && (
                  <button
                    onClick={onRefresh}
                    className="text-sm text-blue-600 hover:text-blue-500"
                  >
                    Refresh File
                  </button>
                )}
              </div>
              
              <div className="flex items-center space-x-3">
                <div className={`text-sm ${
                  !conflictResult.has_conflicts 
                    ? 'text-green-600'
                    : canProceedSafely(conflictResult)
                      ? 'text-yellow-600'
                      : 'text-red-600'
                }`}>
                  {!conflictResult.has_conflicts 
                    ? 'Safe to proceed'
                    : canProceedSafely(conflictResult)
                      ? 'Proceed with caution'
                      : 'Resolve conflicts first'
                  }
                </div>
                
                {conflictResult.has_conflicts && !canProceedSafely(conflictResult) && (
                  <button
                    onClick={checkConflicts}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
                  >
                    Recheck After Resolution
                  </button>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Shield className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Click "Check Now" to scan for conflicts</p>
          </div>
        )}
      </div>
    </div>
  );
};