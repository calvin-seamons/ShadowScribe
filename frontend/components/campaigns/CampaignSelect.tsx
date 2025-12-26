'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';

interface Campaign {
    id: string;
    name: string;
    description?: string;
    created_at?: string;
}

interface CampaignSelectProps {
    value: string | null;
    onChange: (campaignId: string | null) => void;
    disabled?: boolean;
}

export function CampaignSelect({ value, onChange, disabled }: CampaignSelectProps) {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { token } = useAuth();

    useEffect(() => {
        fetchCampaigns();
    }, []);

    const fetchCampaigns = async () => {
        setLoading(true);
        setError(null);

        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json'
            };

            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch('/api/campaigns', { headers });

            if (!response.ok) {
                throw new Error('Failed to fetch campaigns');
            }

            const data = await response.json();
            setCampaigns(data.campaigns || []);
        } catch (err) {
            setError('Unable to load campaigns');
            console.error('Error fetching campaigns:', err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="animate-pulse">
                <div className="h-10 bg-gray-700 rounded-lg"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-red-400 text-sm p-3 bg-red-900/20 rounded-lg">
                {error}
                <button
                    onClick={fetchCampaigns}
                    className="ml-2 underline hover:no-underline"
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">
                Select Campaign
            </label>
            <select
                value={value || ''}
                onChange={(e) => onChange(e.target.value || null)}
                disabled={disabled}
                className="w-full px-4 py-2.5 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <option value="">No Campaign (Solo Play)</option>
                {campaigns.map((campaign) => (
                    <option key={campaign.id} value={campaign.id}>
                        {campaign.name}
                    </option>
                ))}
            </select>
            {campaigns.length === 0 && (
                <p className="text-gray-500 text-sm">
                    No campaigns available. Characters can be created without a campaign.
                </p>
            )}
        </div>
    );
}

// Campaign card for display in lists
export function CampaignCard({ campaign, selected, onSelect }: {
    campaign: Campaign;
    selected: boolean;
    onSelect: () => void;
}) {
    return (
        <button
            onClick={onSelect}
            className={`w-full p-4 rounded-xl text-left transition-all ${selected
                    ? 'bg-purple-600/30 border-2 border-purple-500 shadow-lg shadow-purple-500/20'
                    : 'bg-gray-800/50 border border-gray-700 hover:border-gray-600'
                }`}
        >
            <h3 className="font-semibold text-white">{campaign.name}</h3>
            {campaign.description && (
                <p className="text-gray-400 text-sm mt-1 line-clamp-2">
                    {campaign.description}
                </p>
            )}
        </button>
    );
}

// Campaign selection grid
export function CampaignGrid({
    selectedId,
    onSelect
}: {
    selectedId: string | null;
    onSelect: (id: string | null) => void;
}) {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [loading, setLoading] = useState(true);
    const { token } = useAuth();

    useEffect(() => {
        const fetchCampaigns = async () => {
            try {
                const headers: Record<string, string> = {};
                if (token) {
                    headers['Authorization'] = `Bearer ${token}`;
                }

                const response = await fetch('/api/campaigns', { headers });
                if (response.ok) {
                    const data = await response.json();
                    setCampaigns(data.campaigns || []);
                }
            } catch (err) {
                console.error('Error fetching campaigns:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchCampaigns();
    }, [token]);

    if (loading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="h-24 bg-gray-800 rounded-xl animate-pulse"></div>
                ))}
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* No Campaign Option */}
            <button
                onClick={() => onSelect(null)}
                className={`w-full p-4 rounded-xl text-left transition-all ${selectedId === null
                        ? 'bg-gray-600/30 border-2 border-gray-500'
                        : 'bg-gray-800/50 border border-gray-700 hover:border-gray-600'
                    }`}
            >
                <h3 className="font-semibold text-white">Solo Play</h3>
                <p className="text-gray-400 text-sm mt-1">
                    Create a character without joining a campaign
                </p>
            </button>

            {/* Campaign Options */}
            {campaigns.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {campaigns.map((campaign) => (
                        <CampaignCard
                            key={campaign.id}
                            campaign={campaign}
                            selected={selectedId === campaign.id}
                            onSelect={() => onSelect(campaign.id)}
                        />
                    ))}
                </div>
            )}

            {campaigns.length === 0 && (
                <p className="text-center text-gray-500 py-4">
                    No campaigns available yet. You can create a character in solo mode.
                </p>
            )}
        </div>
    );
}
