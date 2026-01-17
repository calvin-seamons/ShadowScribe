'use client'

import { memo } from 'react'
import { useChatStore } from '@/lib/stores/chatStore'
import MessageBubble from './MessageBubble'

function StreamingMessage() {
  // Subscribe only to the streaming content to prevent parent re-renders
  const content = useChatStore(state => state.currentStreamingMessage)

  return (
    <MessageBubble
      message={{
        id: 'streaming',
        role: 'assistant',
        content: content,
        timestamp: new Date()
      }}
      isStreaming={true}
    />
  )
}

export default memo(StreamingMessage)
