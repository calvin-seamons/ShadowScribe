import { create } from 'zustand'
import { Message } from '@/lib/types/conversation'

interface ChatState {
  messages: Message[]
  isStreaming: boolean
  error: string | null
  currentStreamingMessage: string
  pendingMessageId: string | null  // Track the expected message ID for metadata association
  
  addMessage: (message: Message) => void
  setMessages: (messages: Message[]) => void
  startStreaming: (messageId?: string) => void  // Accept optional message ID
  appendToStreamingMessage: (chunk: string) => void
  completeStreaming: () => void
  setError: (error: string | null) => void
  clearMessages: () => void
  clearHistory: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  error: null,
  currentStreamingMessage: '',
  pendingMessageId: null,
  
  addMessage: (message) => 
    set((state) => ({
      messages: [...state.messages, message]
    })),
  
  setMessages: (messages) =>
    set({ messages }),
  
  startStreaming: (messageId?: string) => 
    set({ 
      isStreaming: true, 
      currentStreamingMessage: '',
      pendingMessageId: messageId || null,
      error: null 
    }),
  
  appendToStreamingMessage: (chunk) => 
    set((state) => ({
      currentStreamingMessage: state.currentStreamingMessage + chunk
    })),
  
  completeStreaming: () => 
    set((state) => {
      // Use pending message ID if available, otherwise generate new one
      const messageId = state.pendingMessageId || Date.now().toString()
      const assistantMessage: Message = {
        id: messageId,
        role: 'assistant',
        content: state.currentStreamingMessage,
        timestamp: new Date()
      }
      return {
        isStreaming: false,
        currentStreamingMessage: '',
        pendingMessageId: null,
        messages: [...state.messages, assistantMessage]
      }
    }),
  
  setError: (error) => 
    set({ 
      error, 
      isStreaming: false,
      currentStreamingMessage: '',
      pendingMessageId: null
    }),
  
  clearMessages: () => 
    set({ 
      messages: [], 
      currentStreamingMessage: '',
      isStreaming: false,
      pendingMessageId: null,
      error: null 
    }),
  
  clearHistory: () => 
    set({ 
      messages: [],
      currentStreamingMessage: '',
      isStreaming: false,
      pendingMessageId: null,
      error: null
    })
}))
