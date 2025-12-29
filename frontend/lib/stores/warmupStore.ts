import { create } from 'zustand'

type WarmupStatus = 'idle' | 'checking' | 'warming' | 'ready' | 'error'

interface WarmupState {
  status: WarmupStatus
  error: string | null

  setStatus: (status: WarmupStatus) => void
  setError: (error: string) => void
  setReady: () => void
  reset: () => void
}

export const useWarmupStore = create<WarmupState>((set) => ({
  status: 'idle',
  error: null,

  setStatus: (status) => set({ status, error: null }),

  setError: (error) => set({ status: 'error', error }),

  setReady: () => set({ status: 'ready', error: null }),

  reset: () => set({ status: 'idle', error: null }),
}))
