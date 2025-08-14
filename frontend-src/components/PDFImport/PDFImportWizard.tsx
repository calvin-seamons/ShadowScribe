import React, { useState, useCallback, useEffect } from 'react';
import {
  Upload,
  FileText,
  Eye,
  CheckCircle,
  ArrowLeft,
  ArrowRight,
  Loader2,
  Home,
  AlertTriangle
} from 'lucide-react';
import { PDFUpload } from './PDFUpload';
import { PDFContentPreview } from './PDFContentPreview';
import { CharacterDataReview } from './CharacterDataReview';
import { 
  CharacterParseResult, 
  ParsedCharacterData,
  UncertainField,
  ImageData
} from '../../types';

interface WizardStep {
  id: string;
  title: string;
  icon: React.ReactNode;
  description: string;
  isComplete: boolean;
  isValid: boolean;
}

interface PDFImportWizardProps {
  onComplete: (characterName: string) => void;
  onCancel: () => void;
  onFallbackToManual?: () => void;
}

interface ImportState {
  sessionId: string | null;
  images: ImageData[];
  parsedData: ParsedCharacterData | null;
  uncertainFields: UncertainField[];
  error: string | null;
  isLoading: boolean;
  loadingMessage: string;
}

export const PDFImportWizard: React.FC<PDFImportWizardProps> = ({
  onComplete,
  onCancel,
  onFallbackToManual
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [importState, setImportState] = useState<ImportState>({
    sessionId: null,
    images: [],
    parsedData: null,
    uncertainFields: [],
    error: null,
    isLoading: false,
    loadingMessage: ''
  });

  // Define wizard steps in state
  const [steps, setSteps] = useState<WizardStep[]>([
    {
      id: 'upload',
      title: 'Upload PDF',
      icon: <Upload className="w-5 h-5" />,
      description: 'Upload your character sheet PDF file',
      isComplete: false,
      isValid: false
    },
    {
      id: 'preview',
      title: 'Review Images',
      icon: <Eye className="w-5 h-5" />,
      description: 'Review converted PDF images',
      isComplete: false,
      isValid: false
    },
    {
      id: 'parse',
      title: 'Vision Processing',
      icon: <FileText className="w-5 h-5" />,
      description: 'AI vision processes your character images',
      isComplete: false,
      isValid: false
    },
    {
      id: 'review',
      title: 'Review Data',
      icon: <CheckCircle className="w-5 h-5" />,
      description: 'Review and edit parsed character information',
      isComplete: false,
      isValid: false
    }
  ]);

  // Update step validity when import state changes
  useEffect(() => {
    console.log('Import state or current step changed:', {
      hasSessionId: !!importState.sessionId,
      hasImages: importState.images.length > 0,
      hasParsedData: !!importState.parsedData,
      isLoading: importState.isLoading,
      currentStep
    });
    
    setSteps(prevSteps => {
      const newSteps = [...prevSteps];
      
      newSteps[0].isComplete = !!importState.sessionId && importState.images.length > 0;
      newSteps[0].isValid = newSteps[0].isComplete;
      
      newSteps[1].isComplete = newSteps[0].isComplete && currentStep > 1;
      newSteps[1].isValid = newSteps[0].isComplete;
      
      newSteps[2].isComplete = !!importState.parsedData;
      newSteps[2].isValid = newSteps[2].isComplete;
      
      newSteps[3].isComplete = false; // Only complete when user finalizes
      newSteps[3].isValid = !!importState.parsedData;
      
      console.log('Updated steps validity:', newSteps.map(s => ({ id: s.id, isValid: s.isValid, isComplete: s.isComplete })));
      
      return newSteps;
    });
    
    // Auto-advance from upload step to preview step when upload is complete
    if (currentStep === 0 && importState.sessionId && importState.images.length > 0 && !importState.isLoading) {
      console.log('Auto-advancing from upload step to preview step');
      setCurrentStep(1);
    }
  }, [importState, currentStep]);
  // Navigation functions
  const canGoNext = useCallback((): boolean => {
    if (currentStep >= steps.length - 1) {
      console.log('canGoNext: false - at last step');
      return false;
    }
    const canGo = steps[currentStep].isValid && !importState.isLoading;
    console.log(`canGoNext: ${canGo} - step ${currentStep} isValid: ${steps[currentStep].isValid}, isLoading: ${importState.isLoading}`);
    return canGo;
  }, [currentStep, steps, importState.isLoading]);

  const canGoPrevious = useCallback((): boolean => {
    return currentStep > 0 && !importState.isLoading;
  }, [currentStep, importState.isLoading]);

  const goNext = useCallback(() => {
    console.log('goNext called, canGoNext():', canGoNext());
    if (canGoNext()) {
      console.log('Going to next step from', currentStep, 'to', currentStep + 1);
      setSteps(prevSteps => {
        const newSteps = [...prevSteps];
        newSteps[currentStep].isComplete = true;
        return newSteps;
      });
      setCurrentStep(prev => prev + 1);
    } else {
      console.log('Cannot go next - conditions not met');
    }
  }, [canGoNext, currentStep]);

  const goPrevious = useCallback(() => {
    if (canGoPrevious()) {
      setCurrentStep(prev => prev - 1);
    }
  }, [canGoPrevious]);

  // Error handling
  const handleError = useCallback((error: string, allowFallback: boolean = true) => {
    setImportState(prev => ({
      ...prev,
      error,
      isLoading: false,
      loadingMessage: ''
    }));

    // For critical errors, offer fallback to manual wizard
    if (allowFallback && onFallbackToManual) {
      setTimeout(() => {
        if (confirm(`${error}\n\nWould you like to use the manual character creation wizard instead?`)) {
          onFallbackToManual();
        }
      }, 1000);
    }
  }, [onFallbackToManual]);

  const clearError = useCallback(() => {
    setImportState(prev => ({ ...prev, error: null }));
  }, []);

  // PDF Upload handlers
  const handleUploadComplete = useCallback(async (sessionId: string, imageCount: number) => {
    try {
      console.log('Upload complete, sessionId:', sessionId, 'imageCount:', imageCount);
      
      // Get converted images from preview endpoint
      const response = await fetch(`/api/character/import-pdf/preview/${sessionId}`);
      if (!response.ok) {
        throw new Error('Failed to get converted images');
      }

      const previewData = await response.json();
      console.log('Preview data:', previewData);
      
      const images = previewData.images || [];
      
      console.log('Setting import state with sessionId and images');
      setImportState(prev => ({
        ...prev,
        sessionId,
        images,
        error: null
      }));

      // Don't call goNext() here - let the useEffect handle navigation
      // after state has been updated and steps validity has been recalculated
    } catch (error) {
      console.error('Error in handleUploadComplete:', error);
      handleError(error instanceof Error ? error.message : 'Failed to process uploaded PDF');
    }
  }, [handleError]);

  const handleUploadError = useCallback((error: string) => {
    handleError(error, true);
  }, [handleError]);

  // PDF Content Preview handlers
  const handlePreviewConfirm = useCallback(async (orderedImages: ImageData[]) => {
    // Prevent double-clicks by checking if already loading
    if (importState.isLoading) {
      console.log('Already processing, ignoring duplicate click');
      return;
    }

    if (!importState.sessionId) {
      handleError('No active session found');
      return;
    }

    // Update state and immediately move to processing step
    setImportState(prev => ({
      ...prev,
      isLoading: true,
      loadingMessage: 'AI vision is processing your character images...',
      images: orderedImages,
      error: null
    }));

    // Move to the Vision Processing step immediately
    setCurrentStep(2);

    try {
      const response = await fetch('/api/character/import-pdf/parse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: importState.sessionId,
          images: orderedImages.map(img => img.base64)
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Vision processing failed' }));
        throw new Error(errorData.detail || 'Failed to process character images');
      }

      const parseResult: CharacterParseResult = await response.json();
      
      setImportState(prev => ({
        ...prev,
        parsedData: {
          character_files: parseResult.character_files,
          uncertain_fields: parseResult.uncertain_fields,
          parsing_confidence: parseResult.parsing_confidence,
          validation_results: parseResult.validation_results
        },
        uncertainFields: parseResult.uncertain_fields,
        isLoading: false,
        loadingMessage: ''
      }));

      // Auto-advance to review step
      setCurrentStep(3);
    } catch (error) {
      console.error('Vision processing error:', error);
      // Make sure to set isLoading to false on error
      setImportState(prev => ({
        ...prev,
        isLoading: false,
        loadingMessage: ''
      }));
      // Go back to preview step on error
      setCurrentStep(1);
      handleError(error instanceof Error ? error.message : 'Failed to process character images', false);
    }
  }, [importState.sessionId, importState.isLoading, handleError]);

  const handlePreviewReject = useCallback(() => {
    // Only cleanup if not currently processing
    if (!importState.isLoading) {
      // Cleanup the session if it exists
      if (importState.sessionId) {
        fetch(`/api/character/import-pdf/cleanup/${importState.sessionId}`, {
          method: 'DELETE'
        }).catch(() => {
          // Ignore cleanup errors
        });
      }
      
      // Go back to upload step
      setCurrentStep(0);
      setImportState(prev => ({
        ...prev,
        sessionId: null,
        images: [],
        error: null
      }));
    }
  }, [importState.sessionId, importState.isLoading]);

  // Character Data Review handlers
  const handleFieldEdit = useCallback((filePath: string, fieldPath: string, value: any) => {
    if (!importState.parsedData) return;

    setImportState(prev => ({
      ...prev,
      parsedData: {
        ...prev.parsedData!,
        character_files: {
          ...prev.parsedData!.character_files,
          [filePath]: {
            ...prev.parsedData!.character_files[filePath],
            // Update nested field using field path
            ...setNestedValue(prev.parsedData!.character_files[filePath], fieldPath, value)
          }
        }
      }
    }));
  }, [importState.parsedData]);

  const handleFinalize = useCallback(async (characterName: string) => {
    if (!importState.sessionId || !importState.parsedData) {
      handleError('No character data to finalize');
      return;
    }

    setImportState(prev => ({
      ...prev,
      isLoading: true,
      loadingMessage: 'Creating character files...'
    }));

    try {
      const response = await fetch(`/api/character/import-pdf/generate/${importState.sessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          character_name: characterName,
          character_data: importState.parsedData.character_files
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to create character files' }));
        throw new Error(errorData.detail || 'Failed to create character files');
      }

      await response.json();
      
      // Clean up session
      await fetch(`/api/character/import-pdf/cleanup/${importState.sessionId}`, {
        method: 'DELETE'
      }).catch(() => {
        // Ignore cleanup errors
      });

      onComplete(characterName);
    } catch (error) {
      handleError(error instanceof Error ? error.message : 'Failed to create character files', false);
    }
  }, [importState.sessionId, importState.parsedData, onComplete, handleError]);

  const handleReparse = useCallback(async () => {
    if (!importState.sessionId || importState.images.length === 0) {
      handleError('No images to reprocess');
      return;
    }

    await handlePreviewConfirm(importState.images);
  }, [importState.sessionId, importState.images, handlePreviewConfirm]);

  // Cleanup session on unmount or cancel
  useEffect(() => {
    return () => {
      // Only cleanup if not currently processing to avoid race conditions
      if (importState.sessionId && !importState.isLoading) {
        fetch(`/api/character/import-pdf/cleanup/${importState.sessionId}`, {
          method: 'DELETE'
        }).catch(() => {
          // Ignore cleanup errors
        });
      }
    };
  }, [importState.sessionId]);

  const handleCancel = useCallback(() => {
    // Only cleanup if not currently processing
    if (importState.sessionId && !importState.isLoading) {
      fetch(`/api/character/import-pdf/cleanup/${importState.sessionId}`, {
        method: 'DELETE'
      }).catch(() => {
        // Ignore cleanup errors
      });
    }
    onCancel();
  }, [importState.sessionId, importState.isLoading, onCancel]);

  // Render step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <PDFUpload
            onUploadComplete={handleUploadComplete}
            onError={handleUploadError}
          />
        );
      case 1:
        return importState.images.length > 0 ? (
          <PDFContentPreview
            images={importState.images}
            onConfirm={handlePreviewConfirm}
            onReject={handlePreviewReject}
            isLoading={importState.isLoading}
          />
        ) : null;
      case 2:
        return (
          <div className="w-full max-w-2xl mx-auto p-6 text-center">
            <div className="space-y-6">
              <div className="flex items-center justify-center">
                <Loader2 className="h-12 w-12 text-purple-400 animate-spin" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Processing Character Images</h2>
                <p className="text-gray-400 mb-4">
                  Our AI vision system is analyzing your character sheet images and extracting the information...
                </p>
                <p className="text-sm text-purple-300">
                  {importState.loadingMessage || 'This may take a few moments...'}
                </p>
              </div>
            </div>
          </div>
        );
      case 3:
        return importState.parsedData ? (
          <CharacterDataReview
            parsedData={importState.parsedData}
            uncertainFields={importState.uncertainFields}
            onFieldEdit={handleFieldEdit}
            onFinalize={handleFinalize}
            onReparse={handleReparse}
            isLoading={importState.isLoading}
          />
        ) : null;
      default:
        return null;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white overflow-hidden">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex-shrink-0">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={handleCancel}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors"
            >
              <Home className="h-4 w-4 mr-2" />
              Back to Character Selection
            </button>
            <div className="h-6 w-px bg-gray-600" />
            <h1 className="text-xl font-bold text-white">PDF Character Import</h1>
          </div>
          
          {onFallbackToManual && (
            <button
              onClick={onFallbackToManual}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              Use Manual Wizard Instead
            </button>
          )}
        </div>
      </div>

      {/* Progress Steps */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex-shrink-0">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const isActive = index === currentStep;
              const isCompleted = step.isComplete;
              const isAccessible = index <= currentStep || step.isComplete;

              return (
                <div key={step.id} className="flex items-center">
                  <div className="flex items-center">
                    <button
                      onClick={() => isAccessible && !importState.isLoading && setCurrentStep(index)}
                      disabled={!isAccessible || importState.isLoading}
                      className={`
                        flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all
                        ${isActive 
                          ? 'border-purple-500 bg-purple-500 text-white' 
                          : isCompleted 
                            ? 'border-green-500 bg-green-500 text-white'
                            : isAccessible
                              ? 'border-gray-500 bg-gray-700 text-gray-300 hover:border-gray-400'
                              : 'border-gray-600 bg-gray-800 text-gray-500'
                        }
                        ${isAccessible && !importState.isLoading ? 'cursor-pointer' : 'cursor-not-allowed'}
                      `}
                    >
                      {isCompleted ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : (
                        step.icon
                      )}
                    </button>
                    <div className="ml-3 hidden md:block">
                      <p className={`text-sm font-medium ${isActive ? 'text-white' : 'text-gray-400'}`}>
                        {step.title}
                      </p>
                      <p className="text-xs text-gray-500">{step.description}</p>
                    </div>
                  </div>
                  
                  {index < steps.length - 1 && (
                    <div className={`hidden md:block w-16 h-px mx-4 ${
                      steps[index + 1].isComplete || index < currentStep ? 'bg-green-500' : 'bg-gray-600'
                    }`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {importState.error && (
        <div className="bg-red-900/20 border-b border-red-700 px-6 py-4 flex-shrink-0">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-start">
              <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5 mr-3 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-red-300 font-medium">Import Error</p>
                <p className="text-red-200 text-sm mt-1">{importState.error}</p>
                <div className="mt-3 flex space-x-3">
                  <button
                    onClick={clearError}
                    className="text-sm text-red-300 hover:text-red-200 underline"
                  >
                    Dismiss
                  </button>
                  {onFallbackToManual && (
                    <button
                      onClick={onFallbackToManual}
                      className="text-sm text-red-300 hover:text-red-200 underline"
                    >
                      Use Manual Wizard
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden">
        <div className="py-6 px-6">
          {renderStepContent()}
        </div>
      </div>

      {/* Navigation Footer */}
      {currentStep !== 2 && ( // Hide navigation during parsing step
        <div className="bg-gray-800 border-t border-gray-700 px-6 py-4 flex-shrink-0">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <button
              onClick={goPrevious}
              disabled={!canGoPrevious()}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Previous
            </button>

            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-400">
                Step {currentStep + 1} of {steps.length}
              </span>
              
              {currentStep < steps.length - 1 && (
                <button
                  onClick={goNext}
                  disabled={!canGoNext()}
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                  <ArrowRight className="h-4 w-4 ml-2" />
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper function to set nested object values using dot notation
function setNestedValue(obj: Record<string, any>, path: string, value: any): Record<string, any> {
  const keys = path.split('.');
  const result = { ...obj };
  let current = result;
  
  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];
    if (!(key in current) || typeof current[key] !== 'object') {
      current[key] = {};
    } else {
      current[key] = { ...current[key] };
    }
    current = current[key];
  }
  
  current[keys[keys.length - 1]] = value;
  return result;
}