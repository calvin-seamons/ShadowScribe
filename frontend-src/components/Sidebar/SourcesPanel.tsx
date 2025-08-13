import { useEffect, useState } from 'react';
import { Book, User, ScrollText, Zap, CheckCircle } from 'lucide-react';
import clsx from 'clsx';
import { getAvailableSources } from '../../services/api';
import type { SourceDetails, Progress } from '../../types/index';

const sourceIcons = {
  dnd_rulebook: Book,
  character_data: User,
  session_notes: ScrollText,
} as const;

const sourceDisplayNames = {
  dnd_rulebook: 'D&D 5e Rulebook',
  character_data: 'Character Data',
  session_notes: 'Session Notes',
} as const;

interface SourcesData {
  sources: Record<string, SourceDetails>;
}

interface SourcesPanelProps {
  currentProgress?: Progress | null;
  activeSources?: string[];
  lastUsedSources?: string[];
}

export const SourcesPanel: React.FC<SourcesPanelProps> = ({ 
  currentProgress, 
  activeSources = [],
  lastUsedSources = []
}) => {
  const [sources, setSources] = useState<Record<string, SourceDetails>>({});
  const [loading, setLoading] = useState(true);
  const [usedSources, setUsedSources] = useState<Set<string>>(new Set());

  useEffect(() => {
    const loadSources = async () => {
      try {
        const data: SourcesData = await getAvailableSources();
        setSources(data.sources);
      } catch (error) {
        console.error('Failed to load sources:', error);
      } finally {
        setLoading(false);
      }
    };

    loadSources();
  }, []);

  // Track used sources - prioritize current progress, then fall back to last used sources
  useEffect(() => {
    if (currentProgress?.metadata?.sources) {
      // Update used sources from current progress
      setUsedSources(new Set(currentProgress.metadata.sources));
    } else if (lastUsedSources.length > 0) {
      // Keep showing last used sources when no current progress
      setUsedSources(new Set(lastUsedSources));
    } else {
      // Only reset when explicitly no sources available
      setUsedSources(new Set());
    }
  }, [currentProgress, lastUsedSources]);

  const getSourceStatus = (sourceKey: string) => {
    if (usedSources.has(sourceKey)) {
      return 'used';
    }
    if (activeSources.includes(sourceKey)) {
      return 'active';
    }
    return 'available';
  };

  if (loading) {
    return (
      <div className="p-4 border-b border-gray-700">
        <div className="animate-pulse">
          <div className="h-5 bg-gray-700 rounded mb-3"></div>
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-8 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 border-b border-gray-700">
      <h3 className="text-sm font-semibold text-gray-400 uppercase mb-3">
        Knowledge Sources
      </h3>
      <div className="space-y-2">
        {Object.entries(sources).map(([key, details]) => {
          const Icon = sourceIcons[key as keyof typeof sourceIcons] || Book;
          const displayName = sourceDisplayNames[key as keyof typeof sourceDisplayNames] || 
                             key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          const count = details?.count || 'Available';
          const status = getSourceStatus(key);
          
          return (
            <div
              key={key}
              className={clsx(
                "flex items-center space-x-3 p-2 rounded transition-all duration-300",
                status === 'used' && "bg-green-800/30 border border-green-600/50",
                status === 'active' && "bg-blue-800/30 border border-blue-600/50 animate-pulse",
                status === 'available' && "hover:bg-gray-800"
              )}
            >
              <div className="relative">
                <Icon className={clsx(
                  "w-4 h-4 transition-colors",
                  status === 'used' && "text-green-400",
                  status === 'active' && "text-blue-400",
                  status === 'available' && "text-purple-500"
                )} />
                
                {/* Status indicator */}
                {status === 'used' && (
                  <CheckCircle className="w-3 h-3 text-green-400 absolute -top-1 -right-1 bg-gray-900 rounded-full" />
                )}
                {status === 'active' && (
                  <Zap className="w-3 h-3 text-blue-400 absolute -top-1 -right-1 bg-gray-900 rounded-full animate-pulse" />
                )}
              </div>
              
              <div className="flex-1">
                <div className={clsx(
                  "text-sm transition-colors",
                  status === 'used' && "text-green-200",
                  status === 'active' && "text-blue-200",
                  status === 'available' && "text-white"
                )}>
                  {displayName}
                </div>
                <div className={clsx(
                  "text-xs transition-colors",
                  status === 'used' && "text-green-400",
                  status === 'active' && "text-blue-400", 
                  status === 'available' && "text-gray-500"
                )}>
                  {status === 'used' ? 'Used in response' : 
                   status === 'active' ? 'Processing...' : 
                   `${count} items`}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Active processing indicator */}
      {currentProgress && (currentProgress.status === 'starting' || currentProgress.status === 'active') && (
        <div className="mt-3 pt-3 border-t border-gray-600/50">
          <div className="text-xs text-blue-400 font-medium flex items-center space-x-2">
            <Zap className="w-3 h-3 animate-pulse" />
            <span>{currentProgress.message}</span>
          </div>
        </div>
      )}
    </div>
  );
};
