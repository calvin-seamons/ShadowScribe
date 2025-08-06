import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';

interface SessionState {
  sessionId: string;
  initializeSession: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  sessionId: '',
  initializeSession: () => {
    // Check if session exists in localStorage
    const existingSession = localStorage.getItem('shadowscribe_session');
    
    if (existingSession) {
      set({ sessionId: existingSession });
    } else {
      const newSessionId = uuidv4();
      localStorage.setItem('shadowscribe_session', newSessionId);
      set({ sessionId: newSessionId });
    }
  },
}));
