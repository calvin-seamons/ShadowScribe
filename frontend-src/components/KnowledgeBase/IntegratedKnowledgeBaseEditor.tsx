import React, { useState, useEffect } from 'react';
import { FileText, Plus, Save, AlertCircle, Settings, History, Shield, X, BookOpen } from 'lucide-react';
import { FileBrowser } from './FileBrowser';
import { DynamicForm } from './DynamicForm';
import { CharacterCreationWizard } from './CharacterCreationWizard';
import { CharacterSelector } from './CharacterSelector';
import { FileManager } from './FileManager';
import { BackupManager } from './BackupManager';
import { ConflictResolver } from './ConflictResolver';
import { 
  ValidationProvider, 
  ValidationSummary, 
  UnsavedChangesWarning
} from './validation';
import { useKnowledgeBaseStore } from '../../stores/knowledgeBaseStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { useKnowledgeBaseSession } from '../../hooks/useKnowledgeBaseSession';
import { useCharacterSync } from '../../hooks/useCharacterSync';
import { 
  KnowledgeBaseFile, 
  ValidationError,
  listKnowledgeBaseFiles,
  getFileContent,
  updateFileContent,
  getFileSchema,
  validateFileContent,
  getErrorMessage
} from '../../services/knowledgeBaseApi';

// Inner component that uses validation hooks within ValidationProvider context
const EditorContent: React.FC<{
  hasUnsavedChanges: boolean;
  selectedFile: KnowledgeBaseFile | null;
  fileContent: any;
  schema: Record<string, any> | null;
  validationErrors: ValidationError[];
  error: string | null;
  isLoading: boolean;
  isSaving: boolean;
  activeTab: 'editor' | 'manager' | 'backups' | 'conflicts';
  selectedCharacter: string | null;
  files: KnowledgeBaseFile[];
  onSave: () => void;
  onClose: () => void;
  onTabChange: (tab: 'editor' | 'manager' | 'backups' | 'conflicts') => void;
  onCreateNew: () => void;
  onCharacterSelect: (character: string | null) => void;
  onFileSelect: (file: KnowledgeBaseFile) => void;
  onContentChange: (content: any) => void;
  onLoadFiles: () => void;
}> = ({
  hasUnsavedChanges,
  selectedFile,
  fileContent,
  schema,
  validationErrors,
  error,
  isLoading,
  isSaving,
  activeTab,
  selectedCharacter,
  files,
  onSave,
  onClose,
  onTabChange,
  onCreateNew,
  onCharacterSelect,
  onFileSelect,
  onContentChange
}) => {
  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <BookOpen className="w-6 h-6 text-purple-400" />
            <h1 className="text-xl font-bold text-white">Knowledge Base Editor</h1>
            {hasUnsavedChanges && (
              <span className="text-xs bg-yellow-600 text-yellow-100 px-2 py-1 rounded">
                Unsaved Changes
              </span>
            )}
          </div>
          
          {/* Character Selector */}
          <div className="w-64">
            <CharacterSelector
              selectedCharacter={selectedCharacter}
              onCharacterSelect={onCharacterSelect}
              onCreateNew={onCreateNew}
            />
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={onCreateNew}
            className="flex items-center space-x-2 px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>New Character</span>
          </button>
          
          {selectedFile && (
            <button
              onClick={onSave}
              disabled={!hasUnsavedChanges || isSaving}
              className="flex items-center space-x-2 px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="w-4 h-4" />
              <span>{isSaving ? 'Saving...' : 'Save'}</span>
            </button>
          )}
          
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-md transition-colors"
            title="Close Editor"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-900/50 border-b border-red-700">
          <div className="flex items-center space-x-2 text-red-200">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Validation Summary */}
      {validationErrors.length > 0 && (
        <div className="border-b border-gray-700">
          <ValidationSummary />
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-700">
        <nav className="flex space-x-8 px-4">
          <button
            onClick={() => onTabChange('editor')}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'editor'
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            <FileText className="w-4 h-4 inline mr-2" />
            Editor
          </button>
          <button
            onClick={() => onTabChange('manager')}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'manager'
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            <Settings className="w-4 h-4 inline mr-2" />
            File Manager
          </button>
          <button
            onClick={() => onTabChange('backups')}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'backups'
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            <History className="w-4 h-4 inline mr-2" />
            Backups
          </button>
          <button
            onClick={() => onTabChange('conflicts')}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'conflicts'
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            <Shield className="w-4 h-4 inline mr-2" />
            Conflicts
          </button>
        </nav>
      </div>

      {/* Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {activeTab === 'editor' && (
          <>
            {/* File Browser */}
            <div className="w-80 border-r border-gray-700">
              <FileBrowser
                files={files}
                selectedFile={selectedFile}
                onFileSelect={onFileSelect}
                onRefresh={() => {}}
                isLoading={isLoading}
              />
            </div>

            {/* Editor */}
            <div className="flex-1 overflow-auto">
              {selectedFile && fileContent && schema ? (
                <DynamicForm
                  schema={schema}
                  data={fileContent.content}
                  onChange={onContentChange}
                  onValidationErrors={() => {}}
                  fileType={selectedFile.file_type}
                />
              ) : (
                <div className="h-full flex items-center justify-center text-gray-400">
                  <div className="text-center">
                    <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p className="text-lg">Select a file to edit</p>
                    <p className="text-sm">Choose a file from the browser to get started</p>
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'manager' && (
          <div className="flex-1 overflow-auto">
            <FileManager />
          </div>
        )}

        {activeTab === 'backups' && (
          <div className="flex-1 overflow-auto">
            <BackupManager />
          </div>
        )}

        {activeTab === 'conflicts' && (
          <div className="flex-1 overflow-auto">
            <ConflictResolver filename={selectedFile?.filename || ''} />
          </div>
        )}
      </div>

      {/* Unsaved Changes Warning */}
      <UnsavedChangesWarning />
    </div>
  );
};

export const IntegratedKnowledgeBaseEditor: React.FC = () => {
  const {
    files,
    selectedFile,
    fileContent,
    hasUnsavedChanges,
    isLoading,
    isSaving,
    error,
    setFiles,
    setSelectedFile,
    setFileContent,
    setHasUnsavedChanges,
    setIsLoading,
    setIsSaving,
    setError,
    markCharacterModified,
  } = useKnowledgeBaseStore();
  
  const { closeKnowledgeBaseEditor } = useNavigationStore();
  const { hasAccess, handleSessionCleanup, enableAutoSave } = useKnowledgeBaseSession();
  const { refreshCharacterData } = useCharacterSync();
  
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
  const [schema, setSchema] = useState<Record<string, any> | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [showWizard, setShowWizard] = useState(false);
  const [activeTab, setActiveTab] = useState<'editor' | 'manager' | 'backups' | 'conflicts'>('editor');

  // Load files when character selection changes
  useEffect(() => {
    loadFiles();
  }, [selectedCharacter]);

  // Check access and load files on component mount
  useEffect(() => {
    if (!hasAccess()) {
      setError('Access denied. Please ensure you have a valid session.');
      return;
    }
    
    // Enable auto-save
    const cleanupAutoSave = enableAutoSave(30000); // Auto-save every 30 seconds
    
    // Listen for auto-save events
    const handleAutoSave = () => {
      if (selectedFile && fileContent && hasUnsavedChanges) {
        console.log('Auto-saving file:', selectedFile.filename);
        handleSave();
      }
    };
    
    window.addEventListener('knowledge-base-auto-save', handleAutoSave);
    
    // Cleanup on unmount
    return () => {
      window.removeEventListener('knowledge-base-auto-save', handleAutoSave);
      if (cleanupAutoSave) cleanupAutoSave();
      handleSessionCleanup();
    };
  }, [hasAccess, enableAutoSave, handleSessionCleanup]);

  // Access control check
  if (!hasAccess()) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-900">
        <div className="text-center text-gray-400">
          <Shield className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <h2 className="text-xl font-semibold mb-2">Access Denied</h2>
          <p>You need a valid session to access the Knowledge Base Editor.</p>
          <button
            onClick={closeKnowledgeBaseEditor}
            className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
          >
            Return to Chat
          </button>
        </div>
      </div>
    );
  }

  const loadFiles = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const fileList = await listKnowledgeBaseFiles(selectedCharacter || undefined);
      setFiles(fileList);
      
      // Clear selected file if it's not in the new list
      if (selectedFile && !fileList.find(f => f.filename === selectedFile.filename)) {
        setSelectedFile(null);
        setFileContent(null);
        setSchema(null);
        setHasUnsavedChanges(false);
      }
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(`Failed to load files: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCharacterSelect = (characterName: string | null) => {
    if (hasUnsavedChanges) {
      const confirmDiscard = window.confirm(
        'You have unsaved changes. Are you sure you want to switch characters? Your changes will be lost.'
      );
      if (!confirmDiscard) return;
    }

    setSelectedCharacter(characterName);
    setSelectedFile(null);
    setFileContent(null);
    setSchema(null);
    setHasUnsavedChanges(false);
    setValidationErrors([]);
  };

  const handleFileSelect = async (file: KnowledgeBaseFile) => {
    if (hasUnsavedChanges) {
      const shouldContinue = window.confirm(
        'You have unsaved changes. Do you want to continue without saving?'
      );
      if (!shouldContinue) return;
    }

    setIsLoading(true);
    setError(null);
    setSelectedFile(file);
    
    try {
      const [content, fileSchema] = await Promise.all([
        getFileContent(file.filename),
        getFileSchema(file.file_type)
      ]);
      
      setFileContent(content);
      setSchema(fileSchema);
      setHasUnsavedChanges(false);
      setValidationErrors([]);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(`Failed to load file: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleContentChange = (newContent: any) => {
    if (fileContent) {
      setFileContent({
        ...fileContent,
        content: newContent
      });
      setHasUnsavedChanges(true);
    }
  };

  const handleSave = async () => {
    if (!selectedFile || !fileContent) return;

    setIsSaving(true);
    setError(null);

    try {
      // Validate before saving
      const validation = await validateFileContent(selectedFile.filename, fileContent.content);
      
      if (!validation.is_valid) {
        setValidationErrors(validation.errors);
        setError('Please fix validation errors before saving');
        return;
      }

      // Save the file
      await updateFileContent(selectedFile.filename, fileContent.content);
      
      setHasUnsavedChanges(false);
      setValidationErrors([]);
      
      // Mark character as modified for synchronization
      if (selectedFile.file_type === 'character') {
        markCharacterModified(selectedFile.filename);
        // Trigger character data refresh in the main application
        refreshCharacterData();
      }
      
      // Reload files to get updated metadata
      await loadFiles();
      
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(`Failed to save file: ${errorMessage}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleClose = () => {
    if (!handleSessionCleanup()) {
      return; // User cancelled the close operation
    }
    
    closeKnowledgeBaseEditor();
  };

  const handleWizardComplete = async (characterName: string) => {
    setShowWizard(false);
    
    // Switch to the newly created character
    setSelectedCharacter(characterName);
    
    // The useEffect will trigger loadFiles() when selectedCharacter changes
  };

  if (showWizard) {
    return (
      <ValidationProvider>
        <div className="h-full flex flex-col bg-gray-900">
          <div className="flex-1 overflow-hidden">
            <CharacterCreationWizard
              onComplete={handleWizardComplete}
              onCancel={() => setShowWizard(false)}
            />
          </div>
        </div>
      </ValidationProvider>
    );
  }

  return (
    <ValidationProvider>
      <EditorContent
        hasUnsavedChanges={hasUnsavedChanges}
        selectedFile={selectedFile}
        fileContent={fileContent}
        schema={schema}
        validationErrors={validationErrors}
        error={error}
        isLoading={isLoading}
        isSaving={isSaving}
        activeTab={activeTab}
        selectedCharacter={selectedCharacter}
        files={files}
        onSave={handleSave}
        onClose={handleClose}
        onTabChange={setActiveTab}
        onCreateNew={() => setShowWizard(true)}
        onCharacterSelect={handleCharacterSelect}
        onFileSelect={handleFileSelect}
        onContentChange={handleContentChange}
        onLoadFiles={loadFiles}
      />
    </ValidationProvider>
  );
};
