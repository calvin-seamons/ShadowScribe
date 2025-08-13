import { useEffect, useState } from 'react';
import { CheckCircle, Circle, Loader, XCircle } from 'lucide-react';
import type { Progress } from '../../types/index';

interface ProgressIndicatorProps {
  progress: Progress | null;
}

const passes = [
  { number: 1, name: 'Source Selection', description: 'Identifying relevant knowledge sources' },
  { number: 2, name: 'Content Targeting', description: 'Pinpointing specific information' },
  { number: 3, name: 'Content Retrieval', description: 'Fetching data from sources' },
  { number: 4, name: 'Response Generation', description: 'Crafting your answer' },
];

export default function ProgressIndicator({ progress }: ProgressIndicatorProps) {
  const [completedPasses, setCompletedPasses] = useState<Set<number>>(new Set());
  const [erroredPasses, setErroredPasses] = useState<Set<number>>(new Set());
  const [currentPass, setCurrentPass] = useState<number>(0);
  const [animatingPass, setAnimatingPass] = useState<number | null>(null);

  useEffect(() => {
    if (progress) {
      if (progress.status === 'complete') {
        setCompletedPasses(prev => {
          const newCompleted = new Set([...prev, progress.pass]);
          return newCompleted;
        });
        setAnimatingPass(progress.pass);
        setTimeout(() => setAnimatingPass(null), 500);
        
        // When a pass completes, clear the current pass
        // The next pass will be set when it starts
        setCurrentPass(0);
      } else if (progress.status === 'error') {
        setErroredPasses(prev => {
          const newErrored = new Set([...prev, progress.pass]);
          return newErrored;
        });
        setAnimatingPass(progress.pass);
        setTimeout(() => setAnimatingPass(null), 500);
        
        // Clear current pass so next one can start
        setCurrentPass(0);
      } else if (progress.status === 'starting' || progress.status === 'active') {
        setCurrentPass(progress.pass);
      }
    }
  }, [progress]);

  // Reset state when new query starts (when progress resets to pass 1 starting)
  useEffect(() => {
    if (progress?.status === 'starting' && progress.pass === 1) {
      setCompletedPasses(new Set());
      setErroredPasses(new Set());
      setCurrentPass(1);
      setAnimatingPass(null);
    }
  }, [progress]);

  const getPassStatus = (passNumber: number) => {
    if (erroredPasses.has(passNumber)) return 'error';
    if (completedPasses.has(passNumber)) return 'complete';
    if (currentPass === passNumber) return 'active';
    // If we haven't started yet but we're processing, show pass 1 as preparing
    if (currentPass === 0 && passNumber === 1 && !progress) return 'preparing';
    return 'pending';
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-300">Processing Query</h3>
      </div>

      <div className="space-y-2">
        {passes.map((pass) => {
          const status = getPassStatus(pass.number);
          const isAnimating = animatingPass === pass.number;

          return (
            <div
              key={pass.number}
              className={`flex items-start space-x-3 transition-all duration-300 ${
                isAnimating ? 'scale-105' : ''
              }`}
            >
              {/* Status Icon */}
              <div className="flex-shrink-0 mt-0.5">
                {status === 'complete' ? (
                  <CheckCircle
                    className={`w-5 h-5 text-green-500 ${
                      isAnimating ? 'animate-bounce-right' : ''
                    }`}
                  />
                ) : status === 'error' ? (
                  <XCircle
                    className={`w-5 h-5 text-red-500 ${
                      isAnimating ? 'animate-bounce-right' : ''
                    }`}
                  />
                ) : status === 'active' || status === 'preparing' ? (
                  <Loader className="w-5 h-5 text-purple-500 animate-spin" />
                ) : (
                  <Circle className="w-5 h-5 text-gray-600" />
                )}
              </div>

              {/* Pass Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline justify-between">
                  <h4
                    className={`text-sm font-medium transition-colors ${
                      status === 'complete'
                        ? 'text-green-400'
                        : status === 'error'
                        ? 'text-red-400'
                        : status === 'active' || status === 'preparing'
                        ? 'text-purple-400'
                        : 'text-gray-500'
                    }`}
                  >
                    Pass {pass.number}: {pass.name}
                  </h4>
                </div>

                <p className="text-xs text-gray-500 mt-0.5">{pass.description}</p>

                {/* Show details for current pass */}
                {(status === 'active' || status === 'preparing') && (
                  <div className="mt-1 text-xs text-gray-400 animate-fade-in">
                    {status === 'preparing' ? 'Preparing...' : progress?.details || progress?.message}
                  </div>
                )}

                {/* Show error details for errored passes */}
                {status === 'error' && (
                  <div className="mt-1 text-xs text-red-400 animate-fade-in">
                    <div className="font-medium">Error: {progress?.message}</div>
                    {progress?.details && progress.details !== progress.message && (
                      <div className="mt-0.5 text-red-300">{progress.details}</div>
                    )}
                    {progress?.metadata?.error && (
                      <div className="mt-0.5 text-red-300 font-mono text-xs">{progress.metadata.error}</div>
                    )}
                  </div>
                )}

                {/* Show metadata for completed passes */}
                {status === 'complete' && (
                  <div className="mt-1 text-xs text-gray-400">
                    {pass.number === 1 && (
                      <span>Sources identified</span>
                    )}
                    {pass.number === 3 && (
                      <span>Content retrieved</span>
                    )}
                  </div>
                )}
              </div>

              {/* Progress Bar for Active Pass */}
              {(status === 'active' || status === 'preparing') && (
                <div className="absolute left-0 right-0 bottom-0 h-0.5 bg-gray-700">
                  <div className="h-full bg-purple-500 animate-progress" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Overall Progress Bar */}
      <div className="mt-4 pt-3 border-t border-gray-700">
        <div className="h-1 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-purple-500 to-purple-600 transition-all duration-500"
            style={{ width: `${(completedPasses.size / 4) * 100}%` }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-500">
            {completedPasses.size} of 4 passes complete
          </span>
          <span className="text-xs text-gray-500">
            {Math.round((completedPasses.size / 4) * 100)}%
          </span>
        </div>
      </div>

      <style>{`
        @keyframes progress {
          0% {
            width: 0%;
          }
          100% {
            width: 100%;
          }
        }

        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(-4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes bounce-right {
          0%, 20%, 53%, 80%, 100% {
            transform: translateX(0);
          }
          40%, 43% {
            transform: translateX(8px);
          }
          70% {
            transform: translateX(4px);
          }
          90% {
            transform: translateX(2px);
          }
        }

        .animate-progress {
          animation: progress 2s ease-in-out infinite;
        }

        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }

        .animate-bounce-right {
          animation: bounce-right 0.5s ease-in-out;
        }
      `}</style>
    </div>
  );
}