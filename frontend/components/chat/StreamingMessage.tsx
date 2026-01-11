'use client'

import { useEffect } from 'react'
import { useChatStore } from '@/lib/stores/chatStore'
import MessageBubble from './MessageBubble'

interface StreamingMessageProps {
  onUpdate: () => void
}

export default function StreamingMessage({ onUpdate }: StreamingMessageProps) {
  const currentStreamingMessage = useChatStore(state => state.currentStreamingMessage)

  // Trigger onUpdate (scroll) when content changes
  useEffect(() => {
    if (currentStreamingMessage) {
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
