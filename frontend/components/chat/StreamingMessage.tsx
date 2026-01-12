'use client'

import { useEffect, useRef } from 'react'
import { useChatStore } from '@/lib/stores/chatStore'
import MessageBubble from './MessageBubble'

export default function StreamingMessage() {
  const currentStreamingMessage = useChatStore(state => state.currentStreamingMessage)
  const ref = useRef<HTMLDivElement>(null)
  // Use a stable timestamp for the duration of the stream
  const timestamp = useRef(new Date()).current

  useEffect(() => {
    ref.current?.scrollIntoView({ behavior: 'smooth' })
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
