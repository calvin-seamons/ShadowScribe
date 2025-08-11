import React, { useEffect, useCallback } from 'react';
import { AlertTriangle, Save, X } from 'lucide-react';
import { useValidation } from './ValidationProvider';

interface UnsavedChangesWarningProps {
  onSave?: () => void;
  onDiscard?: () => void;
  onDismiss?: () => void;
  showSaveButton?: boolean;
  showDiscardButton?: boolean;
  className?: string;
  position?: 'top' | 'bottom' | 'floating';
}

export const UnsavedChangesWarning: React.FC<UnsavedChangesWarningProps> = ({
  onSave,
  onDiscard,
  onDismiss,
  showSaveButton = true,
  showDiscardButton = true,
  className = '',
  position = 'floating'
}) => {
  const { validationState, hasErrors } = useValidation();
  const { hasUnsavedChanges } = validationState;

  // Warn user before leaving page with unsaved changes
  const handleBeforeUnload = useCallback((e: BeforeUnloadEvent) => {
    if (hasUnsavedChanges) {
      e.preventDefault();
      e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
      return e.returnValue;
    }
  }, [hasUnsavedChanges]);

  useEffect(() => {
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [handleBeforeUnload]);

  // Don't show if no unsaved changes
  if (!hasUnsavedChanges) {
    return null;
  }

  const getPositionClasses = () => {
    switch (position) {
      case 'top':
        return 'sticky top-0 z-50';
      case 'bottom':
        return 'sticky bottom-0 z-50';
      case 'floating':
        return 'fixed bottom-4 right-4 z-50 max-w-md';
      default:
        return '';
    }
  };

  const getContainerClasses = () => {
    const baseClasses = 'bg-yellow-900/90 border border-yellow-500 rounded-lg p-4 backdrop-blur-sm';
    return `${baseClasses} ${getPositionClasses()} ${className}`;
  };

  return (
    <div className={getContainerClasses()}>
      <div className="flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
        
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-yellow-200">
            Unsaved Changes
          </h3>
          <p className="text-sm text-yellow-300 mt-1">
            You have unsaved changes that will be lost if you navigate away.
          </p>
          
          {hasErrors && (
            <p className="text-sm text-red-300 mt-1">
              Please fix validation errors before saving.
            </p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2 flex-shrink-0">
          {showSaveButton && onSave && (
            <button
              onClick={onSave}
              disabled={hasErrors}
              className={`inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                hasErrors
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-green-600 text-white hover:bg-green-700'
              }`}
              title={hasErrors ? 'Fix validation errors before saving' : 'Save changes'}
            >
              <Save className="w-4 h-4 mr-1" />
              Save
            </button>
          )}
          
          {showDiscardButton && onDiscard && (
            <button
              onClick={onDiscard}
              className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-red-200 bg-red-900/50 hover:bg-red-900/70 rounded-md transition-colors"
            >
              <X className="w-4 h-4 mr-1" />
              Discard
            </button>
          )}
          
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-yellow-400 hover:text-yellow-300 transition-colors"
              title="Dismiss warning"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Hook for programmatic unsaved changes warning
export const useUnsavedChangesWarning = (message?: string) => {
  const { validationState } = useValidation();
  const { hasUnsavedChanges } = validationState;

  const defaultMessage = 'You have unsaved changes. Are you sure you want to leave?';

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = message || defaultMessage;
        return e.returnValue;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [hasUnsavedChanges, message, defaultMessage]);

  return hasUnsavedChanges;
};