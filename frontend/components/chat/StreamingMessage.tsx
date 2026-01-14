'use client'

import { useEffect, useRef, useMemo } from 'react'
import { useChatStore } from '@/lib/stores/chatStore'
import MessageBubble from './MessageBubble'

export function StreamingMessage() {
  const currentStreamingMessage = useChatStore(state => state.currentStreamingMessage)
  const ref = useRef<HTMLDivElement>(null)

  // Use a stable timestamp for the duration of this component's mount
  const timestamp = useMemo(() => new Date(), [])

  useEffect(() => {
    if (currentStreamingMessage) {
      ref.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [currentStreamingMessage])

  if (!currentStreamingMessage) return null

  return (
    <div ref={ref}>
      <MessageBubble
        message={{
          id: 'streaming',
          role: 'assistant',
          content: currentStreamingMessage,
          timestamp: timestamp
        }}
        isStreaming
      />
    </div>
  )
}
