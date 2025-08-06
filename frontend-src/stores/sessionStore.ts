import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';

interface SessionStore {
  sessionId: string;
  setSessionId: (id: string) => void;
  initializeSession: () => void;
}

export const useSessionStore = create<SessionStore>((set) => ({
  sessionId: generateSessionId(),
  setSessionId: (id) => set({ sessionId: id }),
  initializeSession: () => {
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

function generateSessionId(): string {
  return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
