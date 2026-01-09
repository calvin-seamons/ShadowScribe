'use client'

import { useEffect } from 'react'
import { useChatStore } from '@/lib/stores/chatStore'
import MessageBubble from './MessageBubble'

interface StreamingMessageProps {
  onUpdate?: () => void
}

export default function StreamingMessage({ onUpdate }: StreamingMessageProps) {
  // Select only the streaming message content
  // This isolates the re-renders to this component during streaming
  const currentStreamingMessage = useChatStore(state => state.currentStreamingMessage)

  // Trigger scroll when content updates
  useEffect(() => {
    if (currentStreamingMessage && onUpdate) {
      onUpdate()
    }
  }, [currentStreamingMessage, onUpdate])

  if (!currentStreamingMessage) return null

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
