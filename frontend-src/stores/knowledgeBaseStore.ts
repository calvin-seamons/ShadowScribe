import { create } from 'zustand';
import { KnowledgeBaseFile, FileContent } from '../services/knowledgeBaseApi';

interface KnowledgeBaseStore {
  // File management
  files: KnowledgeBaseFile[];
  selectedFile: KnowledgeBaseFile | null;
  fileContent: FileContent | null;
  
  // Editor state
  hasUnsavedChanges: boolean;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  
  // Character data synchronization
  lastModifiedCharacter: string | null;
  characterDataVersion: number;
  
  // Actions
  setFiles: (files: KnowledgeBaseFile[]) => void;
  setSelectedFile: (file: KnowledgeBaseFile | null) => void;
  setFileContent: (content: FileContent | null) => void;
  setHasUnsavedChanges: (hasChanges: boolean) => void;
  setIsLoading: (loading: boolean) => void;
  setIsSaving: (saving: boolean) => void;
  setError: (error: string | null) => void;
  
  // Character synchronization
  markCharacterModified: (characterName: string) => void;
  incrementCharacterDataVersion: () => void;
  
  // Reset state
  resetState: () => void;
}

export const useKnowledgeBaseStore = create<KnowledgeBaseStore>((set, get) => ({
  // Initial state
  files: [],
  selectedFile: null,
  fileContent: null,
  hasUnsavedChanges: false,
  isLoading: false,
  isSaving: false,
  error: null,
  lastModifiedCharacter: null,
  characterDataVersion: 0,
  
  // Actions
  setFiles: (files) => set({ files }),
  setSelectedFile: (file) => set({ selectedFile: file }),
  setFileContent: (content) => set({ fileContent: content }),
  setHasUnsavedChanges: (hasChanges) => set({ hasUnsavedChanges: hasChanges }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  setIsSaving: (saving) => set({ isSaving: saving }),
  setError: (error) => set({ error }),
  
  // Character synchronization
  markCharacterModified: (characterName) => {
    set({ 
      lastModifiedCharacter: characterName,
      characterDataVersion: get().characterDataVersion + 1
    });
  },
  
  incrementCharacterDataVersion: () => {
    set({ characterDataVersion: get().characterDataVersion + 1 });
  },
  
  // Reset state
  resetState: () => set({
    files: [],
    selectedFile: null,
    fileContent: null,
    hasUnsavedChanges: false,
    isLoading: false,
    isSaving: false,
    error: null,
    lastModifiedCharacter: null,
    characterDataVersion: 0,
  }),
}));