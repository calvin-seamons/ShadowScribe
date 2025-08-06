import { Loader2, CheckCircle } from 'lucide-react';
import clsx from 'clsx';
import type { Progress } from '../../types/index';

interface ProgressIndicatorProps {
  progress: Progress;
}

const passNames = [
  'Source Selection',
  'Content Targeting',
  'Content Retrieval',
  'Response Generation'
];

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ progress }) => {
  const currentPass = progress.pass;
  const isComplete = progress.status.includes('COMPLETE');

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center space-x-2 mb-3">
        <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
        <span className="text-sm text-gray-300">Processing query...</span>
      </div>
      
      <div className="space-y-2">
        {passNames.map((name, index) => {
          const passNumber = index + 1;
          const isActive = passNumber === currentPass;
          const isCompleted = passNumber < currentPass || (passNumber === currentPass && isComplete);
          
          return (
            <div
              key={passNumber}
              className={clsx(
                'flex items-center space-x-3 text-sm',
                isActive && 'text-purple-400',
                isCompleted && 'text-green-400',
                !isActive && !isCompleted && 'text-gray-500'
              )}
            >
              <div className="flex-shrink-0">
                {isCompleted ? (
                  <CheckCircle className="w-4 h-4" />
                ) : isActive ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <div className="w-4 h-4 rounded-full border border-gray-600" />
                )}
              </div>
              <div className="flex-1">
                <div className="font-medium">Pass {passNumber}: {name}</div>
                {isActive && (
                  <div className="text-xs text-gray-400 mt-1">{progress.details}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
