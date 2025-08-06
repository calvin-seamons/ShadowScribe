import { useEffect, useState } from 'react';
import { Clock } from 'lucide-react';
import { getSessionHistory } from '../../services/api';
import type { HistoryItem } from '../../types/index';

interface SessionHistoryProps {
  sessionId: string;
}

interface SessionHistoryData {
  history: HistoryItem[];
}

export const SessionHistory: React.FC<SessionHistoryProps> = ({ sessionId }) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadHistory = async () => {
      if (!sessionId) return;
      
      try {
        const data: SessionHistoryData = await getSessionHistory(sessionId);
        setHistory(data.history);
      } catch (error) {
        console.error('Failed to load history:', error);
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
    
    // Refresh history periodically
    const interval = setInterval(loadHistory, 30000);
    return () => clearInterval(interval);
  }, [sessionId]);

  if (loading) {
    return (
      <div className="flex-1 p-4 overflow-y-auto">
        <div className="animate-pulse">
          <div className="h-5 bg-gray-700 rounded mb-3"></div>
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-16 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-4 overflow-y-auto">
      <h3 className="text-sm font-semibold text-gray-400 uppercase mb-3">
        Recent Queries
      </h3>
      
      {history.length === 0 ? (
        <p className="text-sm text-gray-500">No queries yet. Start a conversation!</p>
      ) : (
        <div className="space-y-3">
          {history.slice(-5).reverse().map((item, index) => (
            <div key={index} className="bg-gray-800 rounded p-3">
              <div className="flex items-start space-x-2">
                <Clock className="w-3 h-3 text-gray-500 mt-1" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{item.query}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(item.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
