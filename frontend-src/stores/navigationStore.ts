import { create } from 'zustand';

export type AppView = 'chat' | 'knowledge-base' | 'pdf-import';

interface NavigationStore {
  currentView: AppView;
  isKnowledgeBaseEditorOpen: boolean;
  isPDFImportOpen: boolean;
  setCurrentView: (view: AppView) => void;
  openKnowledgeBaseEditor: () => void;
  closeKnowledgeBaseEditor: () => void;
  toggleKnowledgeBaseEditor: () => void;
  openPDFImport: () => void;
  closePDFImport: () => void;
}

export const useNavigationStore = create<NavigationStore>((set, get) => ({
  currentView: 'chat',
  isKnowledgeBaseEditorOpen: false,
  isPDFImportOpen: false,
  
  setCurrentView: (view) => set({ 
    currentView: view,
    isKnowledgeBaseEditorOpen: view === 'knowledge-base',
    isPDFImportOpen: view === 'pdf-import'
  }),
  
  openKnowledgeBaseEditor: () => set({ 
    currentView: 'knowledge-base',
    isKnowledgeBaseEditorOpen: true,
    isPDFImportOpen: false
  }),
  
  closeKnowledgeBaseEditor: () => set({ 
    currentView: 'chat',
    isKnowledgeBaseEditorOpen: false 
  }),
  
  toggleKnowledgeBaseEditor: () => {
    const { isKnowledgeBaseEditorOpen } = get();
    if (isKnowledgeBaseEditorOpen) {
      set({ currentView: 'chat', isKnowledgeBaseEditorOpen: false });
    } else {
      set({ currentView: 'knowledge-base', isKnowledgeBaseEditorOpen: true, isPDFImportOpen: false });
    }
  },

  openPDFImport: () => set({
    currentView: 'pdf-import',
    isPDFImportOpen: true,
    isKnowledgeBaseEditorOpen: false
  }),

  closePDFImport: () => set({
    currentView: 'chat',
    isPDFImportOpen: false
  }),
}));