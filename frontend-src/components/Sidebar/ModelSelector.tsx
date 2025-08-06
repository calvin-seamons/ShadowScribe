import { useState, useEffect } from 'react';
import { getModels, updateModel } from '../../services/api';
import type { ModelInfo } from '../../types/index';

export const ModelSelector: React.FC = () => {
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getModels();
      setModelInfo(data);
    } catch (err) {
      setError('Failed to load model information');
      console.error('Error loading models:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleModelChange = async (newModel: string) => {
    if (!modelInfo || newModel === modelInfo.current_model) return;

    try {
      setUpdating(true);
      setError(null);
      const data = await updateModel(newModel);
      setModelInfo(data);
    } catch (err) {
      setError('Failed to update model');
      console.error('Error updating model:', err);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-300 mb-2">AI Model</h3>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !modelInfo) {
    return (
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-300 mb-2">AI Model</h3>
        <div className="text-red-400 text-xs">
          {error || 'Unable to load models'}
        </div>
        <button
          onClick={loadModels}
          className="mt-2 text-xs text-blue-400 hover:text-blue-300"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 border-b border-gray-700">
      <h3 className="text-sm font-semibold text-gray-300 mb-2">AI Model</h3>
      
      <select
        value={modelInfo.current_model}
        onChange={(e) => handleModelChange(e.target.value)}
        disabled={updating}
        className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {modelInfo.available_models.map((model) => (
          <option key={model} value={model}>
            {model}
          </option>
        ))}
      </select>
      
      {updating && (
        <div className="mt-2 text-xs text-blue-400 flex items-center">
          <div className="animate-spin rounded-full h-3 w-3 border-b border-blue-400 mr-2"></div>
          Updating model...
        </div>
      )}
      
      {error && (
        <div className="mt-2 text-xs text-red-400">
          {error}
        </div>
      )}
      
      <div className="mt-2 text-xs text-gray-400">
        Current: {modelInfo.current_model}
      </div>
    </div>
  );
};
