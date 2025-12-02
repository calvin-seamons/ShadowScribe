'use client'

import { useState, useRef, useEffect } from 'react'
import { useChatStore } from '@/lib/stores/chatStore'
import { Send, Loader2 } from 'lucide-react'

interface MessageInputProps {
  onSendMessage: (content: string) => void
}

export default function MessageInput({ onSendMessage }: MessageInputProps) {
  const [input, setInput] = useState('')
  const { isStreaming } = useChatStore()
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`
    }
  }, [input])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim() || isStreaming) return

    onSendMessage(input.trim())
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="p-4">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-end gap-3 p-2 rounded-2xl bg-input border-2 border-border/50 focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/20 transition-all">
          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your character, spells, or the rules..."
            disabled={isStreaming}
            className="flex-1 bg-transparent px-3 py-2 text-[15px] resize-none focus:outline-none disabled:opacity-50 placeholder:text-muted-foreground/60 min-h-[44px] max-h-[150px]"
            rows={1}
          />

          {/* Send button */}
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="flex-shrink-0 w-10 h-10 rounded-xl bg-primary text-primary-foreground flex items-center justify-center transition-all hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed hover:scale-105 active:scale-95 disabled:hover:scale-100"
            aria-label="Send message"
          >
            {isStreaming ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Helper text */}
        <div className="flex items-center justify-between mt-2 px-2 text-xs text-muted-foreground/60">
          <span>Press Enter to send, Shift+Enter for new line</span>
          {isStreaming && (
            <span className="flex items-center gap-1.5 text-primary">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              Generating response...
            </span>
          )}
        </div>
      </form>
    </div>
  )
}
