/**
 * Metadata store for RAG pipeline visualization
 */
import { create } from 'zustand';
import type { QueryMetadata, ToolInfo } from '../types/metadata';

interface MetadataState {
  currentMetadata: QueryMetadata | null;
  messageMetadata: Map<string, QueryMetadata>;
  sidebarVisible: boolean;
  
  // Feedback tracking
  currentFeedbackId: string | null;
  currentRoutingTools: ToolInfo[];
  messageFeedbackIds: Map<string, string>;  // messageId -> feedbackId
  
  setCurrentMetadata: (metadata: QueryMetadata) => void;
  updateCurrentMetadata: (partial: Partial<QueryMetadata>) => void;
  saveMessageMetadata: (messageId: string, metadata: QueryMetadata) => void;
  getMessageMetadata: (messageId: string) => QueryMetadata | undefined;
  toggleSidebar: () => void;
  setSidebarVisible: (visible: boolean) => void;
  clearCurrentMetadata: () => void;
  
  // Feedback actions
  setCurrentFeedbackId: (feedbackId: string) => void;
  saveFeedbackIdForMessage: (messageId: string, feedbackId: string) => void;
  getFeedbackIdForMessage: (messageId: string) => string | undefined;
  getRoutingToolsForMessage: (messageId: string) => ToolInfo[];
}

export const useMetadataStore = create<MetadataState>((set, get) => ({
  currentMetadata: null,
  messageMetadata: new Map(),
  sidebarVisible: true,
  currentFeedbackId: null,
  currentRoutingTools: [],
  messageFeedbackIds: new Map(),
  
  setCurrentMetadata: (metadata) => set({ currentMetadata: metadata }),
  
  updateCurrentMetadata: (partial) => set((state) => {
    const newMetadata = state.currentMetadata 
      ? { ...state.currentMetadata, ...partial }
      : partial as QueryMetadata;
    
    // Also track routing tools for feedback
    const routingTools = partial.routing?.tools_needed || state.currentRoutingTools;
    
    return {
      currentMetadata: newMetadata,
      currentRoutingTools: routingTools
    };
  }),
  
  saveMessageMetadata: (messageId, metadata) => set((state) => {
    const newMap = new Map(state.messageMetadata);
    newMap.set(messageId, metadata);
    
    // Also save feedback ID if we have one
    const newFeedbackMap = new Map(state.messageFeedbackIds);
    if (state.currentFeedbackId) {
      newFeedbackMap.set(messageId, state.currentFeedbackId);
    }
    
    return { 
      messageMetadata: newMap,
      messageFeedbackIds: newFeedbackMap
    };
  }),
  
  getMessageMetadata: (messageId) => {
    return get().messageMetadata.get(messageId);
  },
  
  toggleSidebar: () => set((state) => ({ sidebarVisible: !state.sidebarVisible })),
  
  setSidebarVisible: (visible) => set({ sidebarVisible: visible }),
  
  clearCurrentMetadata: () => set({ 
    currentMetadata: null,
    currentFeedbackId: null,
    currentRoutingTools: []
  }),
  
  setCurrentFeedbackId: (feedbackId) => set({ currentFeedbackId: feedbackId }),
  
  saveFeedbackIdForMessage: (messageId, feedbackId) => set((state) => {
    const newMap = new Map(state.messageFeedbackIds);
    newMap.set(messageId, feedbackId);
    return { messageFeedbackIds: newMap };
  }),
  
  getFeedbackIdForMessage: (messageId) => {
    return get().messageFeedbackIds.get(messageId);
  },
  
  getRoutingToolsForMessage: (messageId) => {
    const metadata = get().messageMetadata.get(messageId);
    return metadata?.routing?.tools_needed || [];
  }
}));
