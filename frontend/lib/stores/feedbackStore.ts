/**
 * Zustand store for routing feedback state
 */
import { create } from 'zustand';
import type { RoutingRecord, ToolIntentionOptions, FeedbackStats, ToolCorrection } from '../types/feedback';

interface FeedbackState {
  // Current query feedback (for inline feedback UI)
  currentFeedbackId: string | null;
  currentPredictedTools: ToolCorrection[];
  
  // Tool options (cached)
  toolIntentions: ToolIntentionOptions | null;
  
  // Feedback modal state
  showFeedbackModal: boolean;
  selectedRecord: RoutingRecord | null;
  
  // User's current corrections
  corrections: ToolCorrection[];
  feedbackNotes: string;
  
  // Stats
  stats: FeedbackStats | null;
  
  // Actions
  setCurrentFeedback: (feedbackId: string, predictedTools: ToolCorrection[]) => void;
  clearCurrentFeedback: () => void;
  setToolIntentions: (options: ToolIntentionOptions) => void;
  openFeedbackModal: (record: RoutingRecord) => void;
  closeFeedbackModal: () => void;
  setCorrections: (corrections: ToolCorrection[]) => void;
  addCorrection: (tool: string, intention: string) => void;
  removeCorrection: (index: number) => void;
  updateCorrection: (index: number, tool: string, intention: string) => void;
  setFeedbackNotes: (notes: string) => void;
  setStats: (stats: FeedbackStats) => void;
  resetForm: () => void;
}

export const useFeedbackStore = create<FeedbackState>((set) => ({
  // Initial state
  currentFeedbackId: null,
  currentPredictedTools: [],
  toolIntentions: null,
  showFeedbackModal: false,
  selectedRecord: null,
  corrections: [],
  feedbackNotes: '',
  stats: null,
  
  // Actions
  setCurrentFeedback: (feedbackId, predictedTools) => set({
    currentFeedbackId: feedbackId,
    currentPredictedTools: predictedTools
  }),
  
  clearCurrentFeedback: () => set({
    currentFeedbackId: null,
    currentPredictedTools: []
  }),
  
  setToolIntentions: (options) => set({ toolIntentions: options }),
  
  openFeedbackModal: (record) => set({
    showFeedbackModal: true,
    selectedRecord: record,
    // Pre-populate corrections with predicted tools
    corrections: record.predicted_tools.map(t => ({
      tool: t.tool,
      intention: t.intention
    })),
    feedbackNotes: ''
  }),
  
  closeFeedbackModal: () => set({
    showFeedbackModal: false,
    selectedRecord: null,
    corrections: [],
    feedbackNotes: ''
  }),
  
  setCorrections: (corrections) => set({ corrections }),
  
  addCorrection: (tool, intention) => set((state) => ({
    corrections: [...state.corrections, { tool, intention }]
  })),
  
  removeCorrection: (index) => set((state) => ({
    corrections: state.corrections.filter((_, i) => i !== index)
  })),
  
  updateCorrection: (index, tool, intention) => set((state) => ({
    corrections: state.corrections.map((c, i) => 
      i === index ? { tool, intention } : c
    )
  })),
  
  setFeedbackNotes: (notes) => set({ feedbackNotes: notes }),
  
  setStats: (stats) => set({ stats }),
  
  resetForm: () => set({
    corrections: [],
    feedbackNotes: ''
  })
}));
