import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle, X } from 'lucide-react';
import { useValidation } from './ValidationProvider';

interface ValidationSummaryProps {
  onClose?: () => void;
  showWhenValid?: boolean;
  className?: string;
}

export const ValidationSummary: React.FC<ValidationSummaryProps> = ({
  onClose,
  showWhenValid = false,
  className = ''
}) => {
  const { validationState, hasErrors, hasWarnings } = useValidation();
  const { errors, warnings, isValidating, hasUnsavedChanges, lastValidated } = validationState;

  // Don't show if no errors/warnings and showWhenValid is false
  if (!hasErrors && !hasWarnings && !showWhenValid && !hasUnsavedChanges) {
    return null;
  }

  const getStatusIcon = () => {
    if (isValidating) {
      return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-400" />;
    }
    if (hasErrors) {
      return <AlertCircle className="w-5 h-5 text-red-400" />;
    }
    if (hasWarnings) {
      return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
    }
    return <CheckCircle className="w-5 h-5 text-green-400" />;
  };

  const getStatusText = () => {
    if (isValidating) {
      return 'Validating...';
    }
    if (hasErrors) {
      return `${errors.length} error${errors.length !== 1 ? 's' : ''} found`;
    }
    if (hasWarnings) {
      return `${warnings.length} warning${warnings.length !== 1 ? 's' : ''} found`;
    }
    return 'All validations passed';
  };

  const getStatusColor = () => {
    if (isValidating) return 'border-blue-500 bg-blue-900/20';
    if (hasErrors) return 'border-red-500 bg-red-900/20';
    if (hasWarnings) return 'border-yellow-500 bg-yellow-900/20';
    return 'border-green-500 bg-green-900/20';
  };

  const scrollToField = (fieldPath: string) => {
    // Try to find and scroll to the field with error
    const element = document.querySelector(`[data-field-path="${fieldPath}"]`) ||
                   document.querySelector(`input[name="${fieldPath}"]`) ||
                   document.querySelector(`select[name="${fieldPath}"]`) ||
                   document.querySelector(`textarea[name="${fieldPath}"]`);
    
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Focus the element if it's focusable
      if (element instanceof HTMLInputElement || 
          element instanceof HTMLSelectElement || 
          element instanceof HTMLTextAreaElement) {
        element.focus();
      }
    }
  };

  return (
    <div className={`border rounded-lg p-4 ${getStatusColor()} ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <h3 className="text-sm font-medium text-white">
              {getStatusText()}
            </h3>
            {hasUnsavedChanges && (
              <p className="text-xs text-gray-400 mt-1">
                You have unsaved changes
              </p>
            )}
            {lastValidated && !isValidating && (
              <p className="text-xs text-gray-400 mt-1">
                Last validated: {lastValidated.toLocaleTimeString()}
              </p>
            )}
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Error List */}
      {hasErrors && (
        <div className="space-y-2 mb-3">
          <h4 className="text-sm font-medium text-red-400 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4" />
            <span>Errors</span>
          </h4>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {errors.map((error, index) => (
              <div
                key={index}
                className="flex items-start space-x-2 text-sm text-red-300 cursor-pointer hover:text-red-200 transition-colors"
                onClick={() => scrollToField(error.field_path)}
              >
                <span className="text-red-400 mt-0.5">•</span>
                <div>
                  <span className="font-medium">{getFieldLabel(error.field_path)}:</span>
                  <span className="ml-1">{error.message}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Warning List */}
      {hasWarnings && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-yellow-400 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4" />
            <span>Warnings</span>
          </h4>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {warnings.map((warning, index) => (
              <div
                key={index}
                className="flex items-start space-x-2 text-sm text-yellow-300"
              >
                <span className="text-yellow-400 mt-0.5">•</span>
                <span>{warning}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Success State */}
      {!hasErrors && !hasWarnings && showWhenValid && !isValidating && (
        <div className="text-sm text-green-300">
          All fields are valid and ready to save.
        </div>
      )}
    </div>
  );
};

// Helper function to get a human-readable field label
function getFieldLabel(fieldPath: string): string {
  const parts = fieldPath.split('.');
  const lastPart = parts[parts.length - 1];
  
  // Convert snake_case to Title Case
  return lastPart
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}