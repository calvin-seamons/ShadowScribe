'use client'

import { useState } from 'react'
import { useFeedbackStore } from '@/lib/stores/feedbackStore'
import { feedbackService } from '@/lib/services/feedbackService'
import type { ToolPrediction } from '@/lib/types/feedback'
import { ThumbsUp, ThumbsDown, Check } from 'lucide-react'

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
        <Check className="w-3 h-3" />
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
        aria-label="Mark routing as correct"
      >
        <ThumbsUp className="w-4 h-4" />
      </button>
      
      {/* Thumbs down - opens modal */}
      <button
        onClick={handleThumbsDown}
        disabled={isSubmitting}
        className="p-1 text-muted-foreground hover:text-red-500 transition-colors disabled:opacity-50"
        title="Suggest better routing"
        aria-label="Suggest better routing"
      >
        <ThumbsDown className="w-4 h-4" />
      </button>
    </div>
  )
}
