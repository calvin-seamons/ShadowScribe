import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';

interface SessionStore {
  sessionId: string;
  setSessionId: (id: string) => void;
  initializeSession: () => void;
}

export const useSessionStore = create<SessionStore>((set) => ({
  sessionId: getInitialSessionId(),
  setSessionId: (id) => {
    console.log('[SessionStore] Setting sessionId to:', id);
    set({ sessionId: id });
  },
  initializeSession: () => {
    const existingSession = localStorage.getItem('shadowscribe_session');
    if (existingSession) {
      console.log('[SessionStore] Using existing session:', existingSession);
      set({ sessionId: existingSession });
    } else {
      const newSessionId = uuidv4();
      console.log('[SessionStore] Creating new session:', newSessionId);
      localStorage.setItem('shadowscribe_session', newSessionId);
      set({ sessionId: newSessionId });
    }
  },
}));

function getInitialSessionId(): string {
  // Force a fresh session for debugging - clear any existing session
  localStorage.removeItem('shadowscribe_session');
  
  const sessionId = uuidv4();
  console.log('[SessionStore] FORCING FRESH SESSION:', sessionId);
  localStorage.setItem('shadowscribe_session', sessionId);
  return sessionId;
}
