'use client'

import { Message } from '@/lib/types/conversation'
import { format } from 'date-fns'
import { cn } from '@/lib/utils'
import { MarkdownRenderer } from '@/components/markdown/MarkdownRenderer'
import { useMetadataStore } from '@/lib/stores/metadataStore'
import FeedbackButton from './FeedbackButton'
import { User, Sparkles } from 'lucide-react'

interface MessageBubbleProps {
  message: Message
  isStreaming?: boolean
}

export default function MessageBubble({ message, isStreaming = false }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const { getFeedbackIdForMessage, getRoutingToolsForMessage } = useMetadataStore()

  // Get feedback info for this message
  const feedbackId = !isUser ? getFeedbackIdForMessage(message.id) : undefined
  const routingTools = !isUser ? getRoutingToolsForMessage(message.id) : []

  return (
    <div
      className={cn(
        'flex gap-3 animate-fade-in-up',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center',
          isUser
            ? 'bg-primary/20 text-primary'
            : 'bg-secondary text-secondary-foreground'
        )}
      >
        {isUser ? (
          <User className="w-5 h-5" />
        ) : (
          <Sparkles className="w-5 h-5" />
        )}
      </div>

      {/* Message content */}
      <div
        className={cn(
          'group relative max-w-[75%] rounded-2xl px-4 py-3',
          isUser
            ? 'bg-gradient-to-br from-primary to-primary/90 text-primary-foreground rounded-tr-sm'
            : 'bg-card border border-border/50 text-card-foreground rounded-tl-sm shadow-sm'
        )}
      >
        {/* Subtle glow effect for assistant messages */}
        {!isUser && (
          <div className="absolute inset-0 rounded-2xl rounded-tl-sm bg-gradient-to-br from-primary/5 to-transparent pointer-events-none" />
        )}

        {/* Message text */}
        <div className="relative">
          {isUser ? (
            <div className="whitespace-pre-wrap text-[15px] leading-relaxed">
              {message.content}
            </div>
          ) : (
            <div className="prose-arcane text-[15px]">
              <MarkdownRenderer content={message.content} />
              {isStreaming && (
                <span className="inline-block w-2 h-5 ml-1 bg-primary/70 cursor-blink rounded-sm" />
              )}
            </div>
          )}
        </div>

        {/* Footer: timestamp and feedback */}
        <div
          className={cn(
            'flex items-center gap-3 mt-2 pt-2 border-t',
            isUser
              ? 'border-primary-foreground/20 justify-end'
              : 'border-border/50 justify-between'
          )}
        >
          {/* Timestamp */}
          <span
            className={cn(
              'text-xs',
              isUser ? 'text-primary-foreground/70' : 'text-muted-foreground'
            )}
          >
            {format(message.timestamp, 'HH:mm')}
          </span>

          {/* Feedback button for assistant messages (not during streaming) */}
          {!isUser && !isStreaming && feedbackId && (
            <FeedbackButton
              feedbackId={feedbackId}
              predictedTools={routingTools.map((t) => ({
                tool: t.tool,
                intention: t.intention,
                confidence: t.confidence,
              }))}
            />
          )}
        </div>
      </div>
    </div>
  )
}
