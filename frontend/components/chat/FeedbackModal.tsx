'use client'

import { useEffect, useState } from 'react'
import { useFeedbackStore } from '@/lib/stores/feedbackStore'
import { feedbackService } from '@/lib/services/feedbackService'
import type { ToolCorrection } from '@/lib/types/feedback'

interface FeedbackModalProps {
  onClose?: () => void;
  onSubmit?: () => void;
}

export default function FeedbackModal({ onClose, onSubmit }: FeedbackModalProps) {
  const {
    showFeedbackModal,
    selectedRecord,
    toolIntentions,
    corrections,
    feedbackNotes,
    setToolIntentions,
    closeFeedbackModal,
    addCorrection,
    removeCorrection,
    updateCorrection,
    setFeedbackNotes,
    resetForm
  } = useFeedbackStore()

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load tool intentions on mount
  useEffect(() => {
    if (!toolIntentions) {
      feedbackService.getToolIntentions()
        .then(setToolIntentions)
        .catch(console.error)
    }
  }, [toolIntentions, setToolIntentions])

  if (!showFeedbackModal || !selectedRecord) {
    return null
  }

  const handleMarkCorrect = async () => {
    if (!selectedRecord) return
    
    setIsSubmitting(true)
    setError(null)
    
    try {
      await feedbackService.submitFeedback(selectedRecord.id, {
        is_correct: true
      })
      closeFeedbackModal()
      onSubmit?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSubmitCorrection = async () => {
    if (!selectedRecord || corrections.length === 0) return
    
    setIsSubmitting(true)
    setError(null)
    
    try {
      await feedbackService.submitFeedback(selectedRecord.id, {
        is_correct: false,
        corrected_tools: corrections,
        feedback_notes: feedbackNotes || undefined
      })
      closeFeedbackModal()
      onSubmit?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    resetForm()
    closeFeedbackModal()
    onClose?.()
  }

  const tools = toolIntentions?.tools || {}
  const toolNames = Object.keys(tools)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card border border-border rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-border">
          <h2 className="text-lg font-semibold">Routing Feedback</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Help improve the model by providing feedback on this routing decision
          </p>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[60vh]">
          {/* Query */}
          <div className="mb-4">
            <label className="text-sm font-medium text-muted-foreground">User Query</label>
            <div className="mt-1 p-3 bg-muted rounded-lg">
              <p className="text-sm">{selectedRecord.user_query}</p>
            </div>
          </div>

          {/* Model's Prediction */}
          <div className="mb-4">
            <label className="text-sm font-medium text-muted-foreground">Model's Routing</label>
            <div className="mt-1 space-y-2">
              {selectedRecord.predicted_tools.map((tool, index) => (
                <div key={index} className="flex items-center gap-2 p-2 bg-muted rounded-lg">
                  <span className="px-2 py-1 bg-primary/20 text-primary rounded text-xs font-medium">
                    {tool.tool}
                  </span>
                  <span className="text-sm">{tool.intention}</span>
                  <span className="text-xs text-muted-foreground ml-auto">
                    {(tool.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Correction Form */}
          <div className="mb-4">
            <label className="text-sm font-medium text-muted-foreground">
              Correct Routing (modify if incorrect)
            </label>
            <div className="mt-2 space-y-2">
              {corrections.map((correction, index) => (
                <div key={index} className="flex items-center gap-2">
                  {/* Tool selector */}
                  <select
                    value={correction.tool}
                    onChange={(e) => {
                      const newTool = e.target.value
                      const newIntentions = tools[newTool] || []
                      updateCorrection(index, newTool, newIntentions[0] || '')
                    }}
                    className="flex-1 px-3 py-2 bg-background border border-border rounded-lg text-sm"
                  >
                    {toolNames.map(tool => (
                      <option key={tool} value={tool}>{tool}</option>
                    ))}
                  </select>

                  {/* Intention selector */}
                  <select
                    value={correction.intention}
                    onChange={(e) => updateCorrection(index, correction.tool, e.target.value)}
                    className="flex-1 px-3 py-2 bg-background border border-border rounded-lg text-sm"
                  >
                    {(tools[correction.tool] || []).map(intention => (
                      <option key={intention} value={intention}>{intention}</option>
                    ))}
                  </select>

                  {/* Remove button */}
                  <button
                    onClick={() => removeCorrection(index)}
                    className="p-2 text-muted-foreground hover:text-destructive transition-colors"
                    title="Remove"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}

              {/* Add tool button */}
              <button
                onClick={() => {
                  const firstTool = toolNames[0] || 'character_data'
                  const firstIntention = tools[firstTool]?.[0] || ''
                  addCorrection(firstTool, firstIntention)
                }}
                className="w-full py-2 border border-dashed border-border rounded-lg text-sm text-muted-foreground hover:border-primary hover:text-primary transition-colors"
              >
                + Add Tool
              </button>
            </div>
          </div>

          {/* Notes */}
          <div className="mb-4">
            <label className="text-sm font-medium text-muted-foreground">
              Notes (optional)
            </label>
            <textarea
              value={feedbackNotes}
              onChange={(e) => setFeedbackNotes(e.target.value)}
              placeholder="Any additional context about this query..."
              className="mt-1 w-full px-3 py-2 bg-background border border-border rounded-lg text-sm resize-none"
              rows={2}
            />
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border flex items-center justify-between">
          <button
            onClick={handleClose}
            disabled={isSubmitting}
            className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Cancel
          </button>
          
          <div className="flex gap-2">
            <button
              onClick={handleMarkCorrect}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              ✓ Routing Correct
            </button>
            <button
              onClick={handleSubmitCorrection}
              disabled={isSubmitting || corrections.length === 0}
              className="px-4 py-2 text-sm bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors disabled:opacity-50"
            >
              Submit Correction
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
