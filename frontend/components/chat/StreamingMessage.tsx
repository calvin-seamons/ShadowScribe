'use client'

import { useChatStore } from '@/lib/stores/chatStore'
import MessageBubble from './MessageBubble'

export default function StreamingMessage() {
  // Granular selectors to ensure this component only re-renders when streaming state changes
  const isStreaming = useChatStore(state => state.isStreaming)
  const currentStreamingMessage = useChatStore(state => state.currentStreamingMessage)

  if (!isStreaming || !currentStreamingMessage) {
    return null
  }

  return (
    <MessageBubble
      message={{
        id: 'streaming',
        role: 'assistant',
        content: currentStreamingMessage,
        timestamp: new Date()
      }}
      isStreaming
    />
  )
}
