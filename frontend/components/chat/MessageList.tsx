'use client'

import { useEffect, useRef } from 'react'
import { useChatStore } from '@/lib/stores/chatStore'
import MessageBubble from './MessageBubble'
import StreamingMessage from './StreamingMessage'

export default function MessageList() {
  // Use granular selectors to avoid re-renders when currentStreamingMessage changes
  const messages = useChatStore(state => state.messages)
  const isStreaming = useChatStore(state => state.isStreaming)
  const error = useChatStore(state => state.error)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
  
  // Only scroll when messages list changes (e.g. new message added)
  // Streaming updates are handled by StreamingMessage component
  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {/* Show empty state only when no messages AND not streaming */}
      {messages.length === 0 && !isStreaming && (
        <div className="flex h-full items-center justify-center">
          <div className="text-center text-muted-foreground">
            <p className="text-lg">No messages yet</p>
            <p className="text-sm mt-2">Start a conversation by typing a message below</p>
          </div>
        </div>
      )}
      
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      
      {isStreaming && (
        <StreamingMessage />
      )}
      
      {error && (
        <div className="rounded-lg bg-destructive/10 border border-destructive p-4 text-destructive">
          <p className="font-semibold">Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  )
}
