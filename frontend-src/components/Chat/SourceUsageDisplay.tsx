import { useState } from 'react';
import { ChevronDown, ChevronRight, Book, User, ScrollText, Database, Info } from 'lucide-react';
import clsx from 'clsx';
import type { QuerySourceUsage } from '../../types/index';

interface SourceUsageDisplayProps {
  sourceUsage: QuerySourceUsage;
  className?: string;
}

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

const sourceColors = {
  dnd_rulebook: 'text-amber-400 bg-amber-400/10 border-amber-400/30',
  character_data: 'text-blue-400 bg-blue-400/10 border-blue-400/30',
  session_notes: 'text-purple-400 bg-purple-400/10 border-purple-400/30',
} as const;

export const SourceUsageDisplay: React.FC<SourceUsageDisplayProps> = ({ 
  sourceUsage, 
  className 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());

  const toggleExpanded = () => {
    console.log('Toggling expanded state:', !isExpanded);
    setIsExpanded(!isExpanded);
  };

  const toggleSourceExpanded = (source: string) => {
    console.log('Toggling source expanded:', source);
    const newExpanded = new Set(expandedSources);
    if (newExpanded.has(source)) {
      newExpanded.delete(source);
    } else {
      newExpanded.add(source);
    }
    setExpandedSources(newExpanded);
  };

  const formatTargets = (targets: any, source: string) => {
    try {
      if (!targets || !targets[source]) return [];
      
      const sourceTargets = targets[source];
      
      // Handle different target formats
      if (Array.isArray(sourceTargets)) {
        return sourceTargets;
      } else if (typeof sourceTargets === 'object') {
        // For character data with file-specific targets
        return Object.entries(sourceTargets).map(([file, fieldArray]) => {
          if (Array.isArray(fieldArray)) {
            return `${file}: ${fieldArray.join(', ')}`;
          }
          return `${file}: ${fieldArray}`;
        });
      }
      
      return [String(sourceTargets)];
    } catch (error) {
      console.error('Error formatting targets:', error, { targets, source });
      return [`Error formatting targets for ${source}`];
    }
  };

  const getSourceIcon = (source: string) => {
    const Icon = sourceIcons[source as keyof typeof sourceIcons] || Database;
    return <Icon className="w-4 h-4" />;
  };

  const getSourceDisplayName = (source: string) => {
    return sourceDisplayNames[source as keyof typeof sourceDisplayNames] || 
           source.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getSourceColorClass = (source: string) => {
    return sourceColors[source as keyof typeof sourceColors] || 
           'text-gray-400 bg-gray-400/10 border-gray-400/30';
  };

  if (!sourceUsage || !sourceUsage.sources?.length) {
    console.log('SourceUsageDisplay: No source usage data or empty sources', sourceUsage);
    return null;
  }

  console.log('SourceUsageDisplay rendering with data:', sourceUsage);

  return (
    <div className={clsx(
      "mt-4 rounded-lg border border-gray-600/50 bg-gray-800/50 transition-all duration-200 hover:shadow-lg",
      className
    )}>
      {/* Header */}
      <button
        onClick={toggleExpanded}
        className="w-full px-4 py-3 flex items-center justify-between text-sm text-gray-300 hover:text-white hover:bg-gray-700/30 transition-colors rounded-t-lg"
      >
        <div className="flex items-center space-x-2">
          <Info className="w-4 h-4 text-blue-400" />
          <span className="font-medium">Sources Used</span>
          <span className="text-xs text-gray-500 bg-gray-700 px-2 py-1 rounded-full">
            {sourceUsage.sources.length}
          </span>
        </div>
        <div className="transition-transform duration-200">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </div>
      </button>

      {/* Source Pills (Always Visible) */}
      <div className="px-4 pb-2 flex flex-wrap gap-2">
        {sourceUsage.sources.map((source) => (
          <div
            key={source}
            className={clsx(
              "flex items-center space-x-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-all duration-200 hover:scale-105",
              getSourceColorClass(source)
            )}
          >
            {getSourceIcon(source)}
            <span>{getSourceDisplayName(source)}</span>
          </div>
        ))}
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-gray-600/50 bg-gray-800/30">
          <div className="p-4 space-y-4">
            {sourceUsage.sources.map((source) => {
              const targets = formatTargets(sourceUsage.targets, source);
              const isSourceExpanded = expandedSources.has(source);
              
              return (
                <div 
                  key={source} 
                  className="space-y-2"
                >
                  <button
                    onClick={() => toggleSourceExpanded(source)}
                    className="w-full text-left transition-all duration-200"
                  >
                    <div className={clsx(
                      "flex items-center justify-between p-3 rounded-lg border transition-all duration-200 hover:scale-[1.02] hover:shadow-lg",
                      getSourceColorClass(source),
                      "hover:bg-opacity-20"
                    )}>
                      <div className="flex items-center space-x-3">
                        {getSourceIcon(source)}
                        <div>
                          <div className="font-medium text-sm">
                            {getSourceDisplayName(source)}
                          </div>
                          <div className="text-xs opacity-75">
                            {targets.length} {targets.length === 1 ? 'target' : 'targets'}
                          </div>
                        </div>
                      </div>
                      <div className="transition-transform duration-200">
                        {isSourceExpanded ? (
                          <ChevronDown className="w-4 h-4" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                      </div>
                    </div>
                  </button>

                  {/* Source Details */}
                  {isSourceExpanded && targets.length > 0 && (
                    <div className="ml-4 pl-4 border-l-2 border-gray-600/30 space-y-2">
                      <div className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                        Specific Content Retrieved:
                      </div>
                      <div className="space-y-1">
                        {targets.map((target, targetIndex) => (
                          <div
                            key={targetIndex}
                            className="text-sm text-gray-300 bg-gray-700/50 px-3 py-2 rounded border border-gray-600/30 transition-all duration-200 hover:bg-gray-700/70 hover:border-gray-500/50"
                          >
                            <code className="text-xs font-mono text-gray-200">
                              {target}
                            </code>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* Content Summary */}
            {sourceUsage.content && (
              <div className="pt-3 border-t border-gray-600/30">
                <div className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
                  Content Summary:
                </div>
                <div className="text-sm text-gray-300 bg-gray-700/30 p-3 rounded border border-gray-600/30 leading-relaxed transition-all duration-200 hover:bg-gray-700/40">
                  {(() => {
                    console.log('Content type:', typeof sourceUsage.content, sourceUsage.content);
                    
                    if (typeof sourceUsage.content === 'string') {
                      return sourceUsage.content.length > 200 
                        ? `${sourceUsage.content.substring(0, 200)}...` 
                        : sourceUsage.content;
                    } else if (typeof sourceUsage.content === 'object' && sourceUsage.content !== null) {
                      return (
                        <div className="space-y-2">
                          {Object.entries(sourceUsage.content).map(([key, value]) => (
                            <div key={key} className="text-xs">
                              <div className="text-gray-400 uppercase tracking-wide mb-1">
                                {key.replace(/_/g, ' ')}:
                              </div>
                              <div className="text-gray-200 font-mono bg-gray-800/50 px-2 py-1 rounded">
                                {Array.isArray(value) ? value.join(', ') : String(value)}
                              </div>
                            </div>
                          ))}
                        </div>
                      );
                    } else {
                      return 'No content summary available';
                    }
                  })()}
                </div>
              </div>
            )}

            {/* Timestamp */}
            <div className="pt-2 border-t border-gray-600/30 text-xs text-gray-500">
              Sources retrieved: {sourceUsage.retrievedAt.toLocaleString()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SourceUsageDisplay;
