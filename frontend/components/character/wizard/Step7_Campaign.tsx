/**
 * Step 7: Campaign Selection
 *
 * Select which campaign this character belongs to.
 * All characters must be assigned to a campaign.
 */

'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { Users, Loader2, Plus } from 'lucide-react'
import { useWizardStore } from '@/lib/stores/wizardStore'
import { StepLayout, EditorCard } from './StepLayout'
import { useAuth } from '@/lib/auth-context'

interface Campaign {
    id: string
    name: string
    description?: string
    created_at?: string
}

export function Step7_Campaign() {
    const { selectedCampaignId, setSelectedCampaignId, prevStep, nextStep } = useWizardStore()
    const [campaigns, setCampaigns] = useState<Campaign[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const { token } = useAuth()

    const fetchCampaigns = useCallback(async () => {
        setLoading(true)
        setError(null)

        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json'
            }

            if (token) {
                headers['Authorization'] = `Bearer ${token}`
            }

            const response = await fetch('/api/campaigns', { headers })

            if (!response.ok) {
                throw new Error('Failed to fetch campaigns')
            }

            const data = await response.json()
            setCampaigns(data.campaigns || [])
        } catch (err) {
            setError('Unable to load campaigns')
            console.error('Error fetching campaigns:', err)
        } finally {
            setLoading(false)
        }
    }, [token])

    useEffect(() => {
        fetchCampaigns()
    }, [fetchCampaigns])

    const handleContinue = () => {
        if (!selectedCampaignId) {
            return // Don't continue without a campaign
        }
        nextStep()
    }

    const canContinue = !!selectedCampaignId

    return (
        <StepLayout
            stepNumber={7}
            title="Select Campaign"
            subtitle="Choose which campaign this character belongs to"
            icon={Users}
            onBack={prevStep}
            onContinue={handleContinue}
            continueLabel="Continue to Review"
            canContinue={canContinue}
        >
            <div className="max-w-2xl mx-auto">
                <EditorCard title="Available Campaigns" icon={Users} variant="default">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center py-12">
                            <Loader2 className="w-8 h-8 text-primary animate-spin mb-4" />
                            <p className="text-muted-foreground">Loading campaigns...</p>
                        </div>
                    ) : error ? (
                        <div className="text-center py-8">
                            <p className="text-red-400 mb-4">{error}</p>
                            <button
                                onClick={fetchCampaigns}
                                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                            >
                                Retry
                            </button>
                        </div>
                    ) : campaigns.length === 0 ? (
                        <div className="text-center py-12">
                            <Users className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
                            <p className="text-muted-foreground mb-2">No campaigns available</p>
                            <p className="text-sm text-muted-foreground/70 mb-4">
                                Create a campaign first to organize your characters.
                            </p>
                            <Link
                                href="/campaigns/new"
                                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                            >
                                <Plus className="w-4 h-4" />
                                Create Campaign
                            </Link>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {campaigns.map((campaign) => {
                                const isSelected = selectedCampaignId === campaign.id
                                return (
                                    <button
                                        key={campaign.id}
                                        onClick={() => setSelectedCampaignId(campaign.id)}
                                        className={`w-full p-4 rounded-xl text-left transition-all ${isSelected
                                            ? 'bg-primary/20 border-2 border-primary shadow-lg shadow-primary/10'
                                            : 'bg-card/50 border border-border/50 hover:border-primary/30 hover:bg-card'
                                            }`}
                                    >
                                        <div className="flex items-start gap-3">
                                            <div
                                                className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors ${isSelected
                                                    ? 'border-primary bg-primary'
                                                    : 'border-muted-foreground/30'
                                                    }`}
                                            >
                                                {isSelected && (
                                                    <div className="w-2 h-2 rounded-full bg-primary-foreground" />
                                                )}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h3 className={`font-display text-lg ${isSelected ? 'text-primary' : 'text-foreground'}`}>
                                                    {campaign.name}
                                                </h3>
                                                {campaign.description && (
                                                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                                        {campaign.description}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    </button>
                                )
                            })}
                        </div>
                    )}
                </EditorCard>

                {!canContinue && campaigns.length > 0 && (
                    <p className="text-center text-amber-400 text-sm mt-4">
                        Please select a campaign to continue
                    </p>
                )}
            </div>
        </StepLayout>
    )
}
