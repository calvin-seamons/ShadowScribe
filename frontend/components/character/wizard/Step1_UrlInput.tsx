/**
 * Step 1: URL Input
 *
 * User enters D&D Beyond character URL to fetch character data.
 * Uses wizard store directly - no props needed.
 */

'use client'

import { useState } from 'react'
import { ExternalLink, Loader2, AlertTriangle, HelpCircle, Link2 } from 'lucide-react'
import { useWizardStore } from '@/lib/stores/wizardStore'
import { useWizardWebSocket } from '@/lib/hooks/useWizardWebSocket'

export function Step1_UrlInput() {
  const { dndbeyondUrl, setUrl, error, isCreating } = useWizardStore()
  const { createCharacter } = useWizardWebSocket()
  const [localError, setLocalError] = useState<string | null>(null)

  // Use default URL for testing if none set
  const [inputUrl, setInputUrl] = useState(dndbeyondUrl || 'https://www.dndbeyond.com/characters/152248393')

  const handleFetch = async () => {
    if (!inputUrl.trim()) {
      setLocalError('Please enter a D&D Beyond URL')
      return
    }

    // Basic URL validation
    if (!inputUrl.includes('dndbeyond.com/characters/')) {
      setLocalError('Invalid D&D Beyond URL. Expected format: https://dndbeyond.com/characters/{id}')
      return
    }

    setLocalError(null)

    try {
      await createCharacter(inputUrl)
      // Navigation handled by useWizardWebSocket
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Failed to fetch character')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isCreating) {
      handleFetch()
    }
  }

  const displayError = localError || error

  return (
    <div className="p-8 md:p-12">
      <div className="max-w-xl mx-auto">
        {/* Step header */}
        <div className="text-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-5 glow-gold-sm">
            <Link2 className="w-8 h-8 text-primary" />
          </div>
          <h2 className="text-2xl md:text-3xl font-display tracking-wide text-gradient-gold text-shadow-sm mb-2">
            Import from D&D Beyond
          </h2>
          <p className="text-muted-foreground">
            Enter your character&apos;s URL to begin the import process
          </p>
        </div>

        {/* URL Input */}
        <div className="space-y-6">
          <div>
            <label htmlFor="dndbeyond-url" className="block text-sm font-medium text-foreground mb-2">
              Character URL
            </label>
            <div className="relative">
              <input
                id="dndbeyond-url"
                type="url"
                value={inputUrl}
                onChange={(e) => setInputUrl(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="https://dndbeyond.com/characters/..."
                className="input-arcane pr-12"
                disabled={isCreating}
              />
              <ExternalLink className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground/50" />
            </div>
          </div>

          {/* Error Display */}
          {displayError && (
            <div className="flex items-start gap-3 p-4 rounded-xl bg-destructive/10 border border-destructive/20">
              <AlertTriangle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-destructive">Import Failed</p>
                <p className="text-sm text-destructive/80 mt-1">{displayError}</p>
              </div>
            </div>
          )}

          {/* Action Button */}
          <button
            onClick={handleFetch}
            disabled={isCreating || !inputUrl.trim()}
            className="btn-primary w-full py-4 text-lg"
          >
            {isCreating ? (
              <span className="flex items-center justify-center gap-3">
                <Loader2 className="w-5 h-5 animate-spin" />
                Fetching Character...
              </span>
            ) : (
              'Fetch Character'
            )}
          </button>
        </div>

        {/* Help Section */}
        <div className="mt-10 p-5 rounded-xl bg-muted/30 border border-border/50">
          <div className="flex items-start gap-3">
            <HelpCircle className="w-5 h-5 text-muted-foreground flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-foreground mb-2">How to find your character URL</h3>
              <ol className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 rounded-full bg-primary/10 text-primary text-xs flex items-center justify-center flex-shrink-0 mt-0.5">1</span>
                  <span>Go to D&D Beyond and open your character sheet</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 rounded-full bg-primary/10 text-primary text-xs flex items-center justify-center flex-shrink-0 mt-0.5">2</span>
                  <span>Copy the URL from your browser&apos;s address bar</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 rounded-full bg-primary/10 text-primary text-xs flex items-center justify-center flex-shrink-0 mt-0.5">3</span>
                  <span>Paste it above and click &quot;Fetch Character&quot;</span>
                </li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
