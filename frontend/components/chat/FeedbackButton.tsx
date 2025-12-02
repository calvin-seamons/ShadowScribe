'use client'

import { useState } from 'react'
import { useFeedbackStore } from '@/lib/stores/feedbackStore'
import { feedbackService } from '@/lib/services/feedbackService'
import type { RoutingRecord, ToolPrediction } from '@/lib/types/feedback'

interface FeedbackButtonProps {
  feedbackId: string;
  predictedTools: ToolPrediction[];
  onOpenModal?: () => void;
}

/**
 * Compact inline feedback button that appears on assistant messages.
 * Shows thumbs up/down for quick feedback or opens modal for corrections.
 */
export default function FeedbackButton({ feedbackId, predictedTools, onOpenModal }: FeedbackButtonProps) {
  const { openFeedbackModal, setToolIntentions } = useFeedbackStore()
  const [status, setStatus] = useState<'idle' | 'correct' | 'incorrect' | 'submitted'>('idle')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleThumbsUp = async () => {
    if (status !== 'idle') return
    
    setIsSubmitting(true)
    try {
      await feedbackService.submitFeedback(feedbackId, {
        is_correct: true
      })
      setStatus('correct')
    } catch (err) {
      console.error('Failed to submit feedback:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleThumbsDown = async () => {
    if (status !== 'idle') return
    
    // Load tool intentions and open modal
    try {
      const options = await feedbackService.getToolIntentions()
      setToolIntentions(options)
      
      // Get full record for modal
      const record = await feedbackService.getRecord(feedbackId)
      openFeedbackModal(record)
      onOpenModal?.()
    } catch (err) {
      console.error('Failed to open feedback modal:', err)
    }
  }

  if (status === 'correct') {
    return (
      <span className="text-xs text-green-500 flex items-center gap-1">
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
        Thanks!
      </span>
    )
  }

  if (status === 'submitted') {
    return (
      <span className="text-xs text-blue-500">Feedback submitted</span>
    )
  }

  return (
    <div className="flex items-center gap-1 opacity-50 hover:opacity-100 transition-opacity">
      <span className="text-xs text-muted-foreground mr-1">Routing ok?</span>
      
      {/* Thumbs up */}
      <button
        onClick={handleThumbsUp}
        disabled={isSubmitting}
        className="p-1 text-muted-foreground hover:text-green-500 transition-colors disabled:opacity-50"
        title="Routing was correct"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
        </svg>
      </button>
      
      {/* Thumbs down - opens modal */}
      <button
        onClick={handleThumbsDown}
        disabled={isSubmitting}
        className="p-1 text-muted-foreground hover:text-red-500 transition-colors disabled:opacity-50"
        title="Suggest better routing"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
        </svg>
      </button>
    </div>
  )
}
