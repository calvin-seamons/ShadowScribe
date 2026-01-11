'use client'

import { useEffect, useRef } from 'react'
import { useCallback } from 'react'
import { useChatStore } from '@/lib/stores/chatStore'
import MessageBubble from './MessageBubble'
import StreamingMessage from './StreamingMessage'

export default function MessageList() {
  const messages = useChatStore(state => state.messages)
  const isStreaming = useChatStore(state => state.isStreaming)
  const error = useChatStore(state => state.error)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])
  
  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])
  
  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
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
        <StreamingMessage onUpdate={scrollToBottom} />
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
