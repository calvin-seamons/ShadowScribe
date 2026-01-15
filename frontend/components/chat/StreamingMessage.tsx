'use client'

import { useEffect, useRef } from 'react'
import { useChatStore } from '@/lib/stores/chatStore'
import MessageBubble from './MessageBubble'

interface StreamingMessageProps {
  onUpdate?: () => void
}

export default function StreamingMessage({ onUpdate }: StreamingMessageProps) {
  // Subscribe ONLY to currentStreamingMessage
  // This ensures this component re-renders on every token, but the parent (MessageList) does not.
  const currentStreamingMessage = useChatStore(state => state.currentStreamingMessage)

  // Keep timestamp stable during a single streaming session to avoid unnecessary prop changes
  // though content change will trigger re-render anyway.
  const timestampRef = useRef(new Date())

  useEffect(() => {
    onUpdate?.()
  }, [currentStreamingMessage, onUpdate])

  if (!currentStreamingMessage) return null

  return (
    <MessageBubble
      message={{
        id: 'streaming',
        role: 'assistant',
        content: currentStreamingMessage,
        timestamp: timestampRef.current
      }}
      isStreaming
    />
  )
}
