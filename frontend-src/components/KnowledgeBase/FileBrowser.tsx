import React from 'react';
import { 
  FileText, 
  User, 
  Scroll, 
  Sword, 
  Package, 
  Target, 
  Sparkles, 
  RefreshCw,
  Calendar,
  HardDrive
} from 'lucide-react';
import { KnowledgeBaseFile } from '../../services/knowledgeBaseApi';

interface FileBrowserProps {
  files: KnowledgeBaseFile[];
  selectedFile: KnowledgeBaseFile | null;
  onFileSelect: (file: KnowledgeBaseFile) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const FileBrowser: React.FC<FileBrowserProps> = ({
  files,
  selectedFile,
  onFileSelect,
  onRefresh,
  isLoading
}) => {
  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'character':
        return <User className="w-4 h-4" />;
      case 'character_background':
        return <Scroll className="w-4 h-4" />;
      case 'feats_and_traits':
        return <Sparkles className="w-4 h-4" />;
      case 'action_list':
        return <Sword className="w-4 h-4" />;
      case 'inventory_list':
        return <Package className="w-4 h-4" />;
      case 'objectives_and_contracts':
        return <Target className="w-4 h-4" />;
      case 'spell_list':
        return <Sparkles className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  const getFileTypeLabel = (fileType: string) => {
    switch (fileType) {
      case 'character':
        return 'Character';
      case 'character_background':
        return 'Background';
      case 'feats_and_traits':
        return 'Feats & Traits';
      case 'action_list':
        return 'Actions';
      case 'inventory_list':
        return 'Inventory';
      case 'objectives_and_contracts':
        return 'Objectives';
      case 'spell_list':
        return 'Spells';
      default:
        return 'Other';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return 'Unknown';
    }
  };

  // Group files by character name (extracted from filename)
  const groupedFiles = files.reduce((groups, file) => {
    // Extract character name from filename (assuming format like "character_name_file_type.json")
    const parts = file.filename.replace('.json', '').split('_');
    let characterName = 'Unknown';
    
    if (parts.length >= 2) {
      // For files like "john_doe_character.json", take everything except the last part
      characterName = parts.slice(0, -1).join('_');
    } else {
      characterName = parts[0] || 'Unknown';
    }

    if (!groups[characterName]) {
      groups[characterName] = [];
    }
    groups[characterName].push(file);
    return groups;
  }, {} as Record<string, KnowledgeBaseFile[]>);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-medium text-white">Files</h3>
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-1 text-gray-400 hover:text-white disabled:opacity-50"
            title="Refresh file list"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        <p className="text-sm text-gray-400">
          {files.length} file{files.length !== 1 ? 's' : ''} found
        </p>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500 mx-auto mb-2"></div>
            <p className="text-sm text-gray-400">Loading files...</p>
          </div>
        ) : files.length === 0 ? (
          <div className="p-4 text-center">
            <FileText className="w-12 h-12 text-gray-600 mx-auto mb-2" />
            <p className="text-sm text-gray-400">No files found</p>
            <p className="text-xs text-gray-500 mt-1">
              Create a new character to get started
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {Object.entries(groupedFiles).map(([characterName, characterFiles]) => (
              <div key={characterName} className="px-4">
                {/* Character Group Header */}
                <div className="mb-2">
                  <h4 className="text-sm font-medium text-purple-300 capitalize">
                    {characterName.replace(/_/g, ' ')}
                  </h4>
                  <div className="h-px bg-gray-700 mt-1"></div>
                </div>

                {/* Files for this character */}
                <div className="space-y-1">
                  {characterFiles
                    .sort((a, b) => {
                      // Sort by file type priority
                      const typePriority = {
                        'character': 0,
                        'character_background': 1,
                        'feats_and_traits': 2,
                        'action_list': 3,
                        'inventory_list': 4,
                        'objectives_and_contracts': 5,
                        'spell_list': 6,
                        'other': 7
                      };
                      return (typePriority[a.file_type as keyof typeof typePriority] || 7) - 
                             (typePriority[b.file_type as keyof typeof typePriority] || 7);
                    })
                    .map((file) => (
                      <button
                        key={file.filename}
                        onClick={() => onFileSelect(file)}
                        className={`w-full text-left p-3 rounded-md transition-colors ${
                          selectedFile?.filename === file.filename
                            ? 'bg-purple-600 text-white'
                            : 'text-gray-300 hover:bg-gray-700'
                        }`}
                      >
                        <div className="flex items-start space-x-3">
                          <div className={`mt-0.5 ${
                            selectedFile?.filename === file.filename
                              ? 'text-purple-200'
                              : 'text-gray-400'
                          }`}>
                            {getFileIcon(file.file_type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <p className="text-sm font-medium truncate">
                                {getFileTypeLabel(file.file_type)}
                              </p>
                              {!file.is_editable && (
                                <span className="text-xs text-yellow-400 ml-2">
                                  Read-only
                                </span>
                              )}
                            </div>
                            <p className="text-xs opacity-75 truncate mt-1">
                              {file.filename}
                            </p>
                            <div className="flex items-center space-x-3 mt-2 text-xs opacity-60">
                              <div className="flex items-center space-x-1">
                                <HardDrive className="w-3 h-3" />
                                <span>{formatFileSize(file.size)}</span>
                              </div>
                              <div className="flex items-center space-x-1">
                                <Calendar className="w-3 h-3" />
                                <span>{formatDate(file.last_modified)}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </button>
                    ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};