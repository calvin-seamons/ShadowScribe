import { create } from 'zustand';

export type AppView = 'chat' | 'knowledge-base';

interface NavigationStore {
  currentView: AppView;
  isKnowledgeBaseEditorOpen: boolean;
  setCurrentView: (view: AppView) => void;
  openKnowledgeBaseEditor: () => void;
  closeKnowledgeBaseEditor: () => void;
  toggleKnowledgeBaseEditor: () => void;
}

export const useNavigationStore = create<NavigationStore>((set, get) => ({
  currentView: 'chat',
  isKnowledgeBaseEditorOpen: false,
  
  setCurrentView: (view) => set({ 
    currentView: view,
    isKnowledgeBaseEditorOpen: view === 'knowledge-base'
  }),
  
  openKnowledgeBaseEditor: () => set({ 
    currentView: 'knowledge-base',
    isKnowledgeBaseEditorOpen: true
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
      set({ currentView: 'knowledge-base', isKnowledgeBaseEditorOpen: true });
    }
  },
}));