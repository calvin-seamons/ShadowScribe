import React, { useState, useEffect } from 'react';
import { X, FileText, Save, AlertCircle, Settings, History } from 'lucide-react';
import { FileBrowser } from './FileBrowser';
import { DynamicForm } from './DynamicForm';
import { CharacterCreationWizard } from './CharacterCreationWizard';
import { CharacterSelector } from './CharacterSelector';
import { FileManager } from './FileManager';
import { BackupManager } from './BackupManager';
// Validation imports removed - using integrated editor instead
import { 
  KnowledgeBaseFile, 
  FileContent, 
  ValidationError,
  listKnowledgeBaseFiles,
  getFileContent,
  updateFileContent,
  getFileSchema,
  validateFileContent,
  getErrorMessage,
  isKnowledgeBaseApiError
} from '../../services/knowledgeBaseApi';

interface KnowledgeBaseEditorProps {
  onClose: () => void;
}

export const KnowledgeBaseEditor: React.FC<KnowledgeBaseEditorProps> = ({ onClose }) => {
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
  const [files, setFiles] = useState<KnowledgeBaseFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<KnowledgeBaseFile | null>(null);
  const [fileContent, setFileContent] = useState<FileContent | null>(null);
  const [schema, setSchema] = useState<Record<string, any> | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showWizard, setShowWizard] = useState(false);
  const [activeTab, setActiveTab] = useState<'editor' | 'manager' | 'backups'>('editor');

  // Load files when character selection changes
  useEffect(() => {
    loadFiles();
  }, [selectedCharacter]);

  const loadFiles = async () => {
    try {
      setIsLoading(true);
      setError(null);
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
      setError(getErrorMessage(err));
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
      const confirmDiscard = window.confirm(
        'You have unsaved changes. Are you sure you want to switch files? Your changes will be lost.'
      );
      if (!confirmDiscard) return;
    }

    try {
      setIsLoading(true);
      setError(null);
      setValidationErrors([]);
      
      // Load file content and schema
      const [content, fileSchema] = await Promise.all([
        getFileContent(file.filename),
        getFileSchema(file.file_type)
      ]);

      setSelectedFile(file);
      setFileContent(content);
      setSchema(fileSchema);
      setHasUnsavedChanges(false);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleContentChange = (newContent: Record<string, any>) => {
    if (fileContent) {
      setFileContent({
        ...fileContent,
        content: newContent
      });
      setHasUnsavedChanges(true);
      
      // Clear validation errors when content changes
      setValidationErrors([]);
    }
  };

  const handleValidationErrors = (errors: ValidationError[]) => {
    setValidationErrors(errors);
  };

  const handleSave = async () => {
    if (!selectedFile || !fileContent) return;

    try {
      setIsSaving(true);
      setError(null);

      // Validate content before saving
      const validationResult = await validateFileContent(selectedFile.filename, fileContent.content);
      
      if (!validationResult.is_valid) {
        setValidationErrors(validationResult.errors);
        setError('Please fix validation errors before saving.');
        return;
      }

      // Save the file
      await updateFileContent(selectedFile.filename, fileContent.content);
      
      setHasUnsavedChanges(false);
      setValidationErrors([]);
      
      // Refresh file list to update last modified time
      await loadFiles();
      
    } catch (err) {
      setError(getErrorMessage(err));
      
      // If it's a validation error, extract the validation details
      if (isKnowledgeBaseApiError(err) && err.details?.errors) {
        setValidationErrors(err.details.errors);
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateNew = () => {
    if (hasUnsavedChanges) {
      const confirmDiscard = window.confirm(
        'You have unsaved changes. Are you sure you want to create a new character? Your changes will be lost.'
      );
      if (!confirmDiscard) return;
    }
    setShowWizard(true);
  };

  const handleWizardComplete = async (characterName: string, filesCreated: string[]) => {
    setShowWizard(false);
    setError(null);
    
    // Switch to the newly created character
    setSelectedCharacter(characterName);
    
    // The useEffect will trigger loadFiles() when selectedCharacter changes
    // Then we can select the main character file
    setTimeout(async () => {
      const mainCharacterFile = filesCreated.find(filename => 
        filename.includes('character.json') && !filename.includes('background')
      );
      
      if (mainCharacterFile) {
        const file = files.find(f => f.filename === mainCharacterFile);
        if (file) {
          await handleFileSelect(file);
        }
      }
    }, 100); // Small delay to ensure files are loaded
  };

  const handleWizardCancel = () => {
    setShowWizard(false);
  };

  const handleClose = () => {
    if (hasUnsavedChanges) {
      const confirmClose = window.confirm(
        'You have unsaved changes. Are you sure you want to close? Your changes will be lost.'
      );
      if (!confirmClose) return;
    }
    onClose();
  };

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg shadow-xl w-full max-w-7xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center space-x-4">
<button onClick={handleClose} className="flex items-center space-x-2 p-2 -ml-2 rounded-lg hover:bg-gray-750 transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-purple-500">
              <FileText className="w-6 h-6 text-purple-400" />
              <h2 className="text-xl font-semibold text-white">Knowledge Base Editor</h2>
              {hasUnsavedChanges && (
                <span className="text-yellow-400 text-sm ml-2">• Unsaved changes</span>
              )}
            </button>
            
            {/* Character Selector */}
            <div className="w-64">
              <CharacterSelector
                selectedCharacter={selectedCharacter}
                onCharacterSelect={handleCharacterSelect}
                onCreateNew={handleCreateNew}
              />
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {selectedFile && activeTab === 'editor' && (
              <button
                onClick={handleSave}
                disabled={isSaving || !hasUnsavedChanges}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="w-4 h-4" />
                <span>{isSaving ? 'Saving...' : 'Save'}</span>
              </button>
            )}
            <button
              onClick={handleClose}
              className="p-2 text-gray-400 hover:text-white"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-700">
          <nav className="flex space-x-8 px-4">
            <button
              onClick={() => setActiveTab('editor')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'editor'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              <FileText className="h-4 w-4 inline mr-2" />
              Editor
            </button>
            <button
              onClick={() => setActiveTab('manager')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'manager'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              <Settings className="h-4 w-4 inline mr-2" />
              File Manager
            </button>
            <button
              onClick={() => setActiveTab('backups')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'backups'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              <History className="h-4 w-4 inline mr-2" />
              Backups
            </button>
          </nav>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mx-4 mt-4 p-3 bg-red-900 border border-red-700 rounded-md flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <span className="text-red-200">{error}</span>
          </div>
        )}

        {/* Validation Errors */}
        {validationErrors.length > 0 && (
          <div className="mx-4 mt-4 p-3 bg-yellow-900 border border-yellow-700 rounded-md">
            <div className="flex items-center space-x-2 mb-2">
              <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0" />
              <span className="text-yellow-200 font-medium">Validation Errors:</span>
            </div>
            <ul className="text-yellow-200 text-sm space-y-1">
              {validationErrors.map((error, index) => (
                <li key={index}>
                  <strong>{error.field_path}:</strong> {error.message}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* File Browser Sidebar - Only show for editor tab */}
          {activeTab === 'editor' && (
            <div className="w-80 border-r border-gray-700 flex flex-col">
              <div className="flex-1 overflow-hidden">
                <FileBrowser
                  files={files}
                  selectedFile={selectedFile}
                  onFileSelect={handleFileSelect}
                  onRefresh={loadFiles}
                  isLoading={isLoading}
                />
              </div>
            </div>
          )}

          {/* Content Area */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {activeTab === 'editor' && (
              <>
                {isLoading ? (
                  <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-4"></div>
                      <p className="text-gray-400">Loading...</p>
                    </div>
                  </div>
                ) : selectedFile && fileContent && schema ? (
                  <div className="flex-1 overflow-hidden">
                    <DynamicForm
                      schema={schema}
                      data={fileContent.content}
                      onChange={handleContentChange}
                      onValidationErrors={handleValidationErrors}
                      fileType={selectedFile.file_type}
                    />
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center">
                    <div className="text-center text-gray-400">
                      <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
                      <p className="text-lg">Select a file to start editing</p>
                      <p className="text-sm">Choose a file from the sidebar to view and edit its contents</p>
                    </div>
                  </div>
                )}
              </>
            )}

            {activeTab === 'manager' && (
              <div className="flex-1 overflow-auto p-4">
                <FileManager
                  selectedFile={selectedFile?.filename}
                  onFileSelect={(filename) => {
                    const file = files.find(f => f.filename === filename);
                    if (file) {
                      setActiveTab('editor');
                      handleFileSelect(file);
                    }
                  }}
                  onFileChange={loadFiles}
                />
              </div>
            )}

            {activeTab === 'backups' && (
              <div className="flex-1 overflow-auto p-4">
                <BackupManager
                  filename={selectedFile?.filename}
                  onRestore={() => {
                    loadFiles();
                    if (selectedFile) {
                      handleFileSelect(selectedFile);
                    }
                  }}
                />
              </div>
            )}
          </div>
        </div>
        </div>
      </div>

      {/* Character Creation Wizard */}
      {showWizard && (
        <CharacterCreationWizard
          onComplete={handleWizardComplete}
          onCancel={handleWizardCancel}
        />
      )}
    </>
  );
};