import { useEffect, useState } from 'react';
import { Book, User, ScrollText } from 'lucide-react';
import { getAvailableSources } from '../../services/api';
import type { SourceDetails } from '../../types/index';

const sourceIcons = {
  dnd_rulebook: Book,
  character_data: User,
  session_notes: ScrollText,
} as const;

interface SourcesData {
  sources: Record<string, SourceDetails>;
}

export const SourcesPanel: React.FC = () => {
  const [sources, setSources] = useState<Record<string, SourceDetails>>({});
  const [loading, setLoading] = useState(true);

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
          const count = details?.count || 'Available';
          
          return (
            <div
              key={key}
              className="flex items-center space-x-3 p-2 rounded hover:bg-gray-800 transition-colors"
            >
              <Icon className="w-4 h-4 text-purple-500" />
              <div className="flex-1">
                <div className="text-sm text-white">
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </div>
                <div className="text-xs text-gray-500">{count} items</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
