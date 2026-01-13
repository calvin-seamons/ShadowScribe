'use client'

import { useEffect, useRef } from 'react'
import { useChatStore } from '@/lib/stores/chatStore'
import MessageBubble from './MessageBubble'

export default function StreamingMessage() {
  const isStreaming = useChatStore(state => state.isStreaming)
  const currentStreamingMessage = useChatStore(state => state.currentStreamingMessage)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isStreaming && currentStreamingMessage) {
      endRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [isStreaming, currentStreamingMessage])

  if (!isStreaming || !currentStreamingMessage) {
    return null
  }

  return (
    <>
      <MessageBubble
        message={{
          id: 'streaming',
          role: 'assistant',
          content: currentStreamingMessage,
          timestamp: new Date(),
        }}
        isStreaming
      />
      <div ref={endRef} />
    </>
  )
}
