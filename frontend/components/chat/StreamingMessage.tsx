'use client'

import { useEffect } from 'react'
import { useChatStore } from '@/lib/stores/chatStore'
import MessageBubble from './MessageBubble'

interface StreamingMessageProps {
  onUpdate?: () => void
}

export default function StreamingMessage({ onUpdate }: StreamingMessageProps) {
  // Granular subscription to prevent parent re-renders
  const isStreaming = useChatStore(state => state.isStreaming)
  const currentStreamingMessage = useChatStore(state => state.currentStreamingMessage)

  // Trigger update (scrolling) when streaming message changes
  useEffect(() => {
    if (isStreaming && currentStreamingMessage && onUpdate) {
      onUpdate()
    }
  }, [isStreaming, currentStreamingMessage, onUpdate])

  if (!isStreaming || !currentStreamingMessage) return null

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
