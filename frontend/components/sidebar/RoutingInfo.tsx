/**
 * Displays routing information (tools selected and intentions)
 * Shows both primary and local classifier results in comparison mode
 */
'use client';

import { RoutingMetadata, ToolInfo } from '@/lib/types/metadata';
import { Database, Book, ScrollText, Bot, Cpu } from 'lucide-react';

interface RoutingInfoProps {
  routing: RoutingMetadata;
}

function ToolList({ tools, colorMap, iconMap }: {
  tools: ToolInfo[];
  colorMap: Record<string, string>;
  iconMap: Record<string, typeof Database>;
}) {
  return (
    <div className="space-y-3">
      {tools.map((tool, idx) => {
        const Icon = iconMap[tool.tool] || Database;
        const colorClass = colorMap[tool.tool] || 'bg-gray-100 text-gray-700';

        return (
          <div key={idx} className="space-y-2">
            <div className="flex items-center gap-2">
              <div className={`p-1.5 rounded ${colorClass}`}>
                <Icon className="w-4 h-4" />
              </div>
              <span className="text-sm font-medium capitalize">
                {tool.tool.replace('_', ' ')}
              </span>
            </div>

            <div className="ml-9 space-y-1">
              <div className="text-xs text-muted-foreground">
                <span className="font-medium">Intention:</span> {tool.intention}
              </div>

              <div className="flex items-center gap-2">
                <div className="flex-1 bg-muted rounded-full h-1.5">
                  <div
                    className={`h-full rounded-full ${colorClass.split(' ')[0]}`}
                    style={{ width: `${tool.confidence * 100}%` }}
                  />
                </div>
                <span className="text-xs text-muted-foreground">
                  {(tool.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function RoutingInfo({ routing }: RoutingInfoProps) {
  const toolIcons: Record<string, typeof Database> = {
    character_data: Database,
    rulebook: Book,
    session_notes: ScrollText,
  };

  const toolColors: Record<string, string> = {
    character_data: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    rulebook: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    session_notes: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  };

  const hasLocalComparison = routing.local_tools_needed && routing.local_tools_needed.length > 0;
  const backendLabel = routing.classifier_backend === 'llm' ? 'Haiku' : 'Local';
  const BackendIcon = routing.classifier_backend === 'llm' ? Bot : Cpu;

  return (
    <div className="space-y-4">
      {/* Primary classifier results */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <BackendIcon className="w-3.5 h-3.5" />
          <span>{backendLabel} (Primary)</span>
        </div>
        <ToolList tools={routing.tools_needed} colorMap={toolColors} iconMap={toolIcons} />
      </div>

      {/* Local classifier comparison (only shown in comparison mode) */}
      {hasLocalComparison && (
        <div className="space-y-2 pt-3 border-t border-border/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <Cpu className="w-3.5 h-3.5" />
              <span>Local Classifier (Comparison)</span>
            </div>
            {routing.local_inference_time_ms && (
              <span className="text-xs text-muted-foreground">
                {routing.local_inference_time_ms.toFixed(0)}ms
              </span>
            )}
          </div>
          <ToolList tools={routing.local_tools_needed!} colorMap={toolColors} iconMap={toolIcons} />
        </div>
      )}

      {/* Show normalized query if available */}
      {routing.normalized_query && (
        <div className="pt-3 border-t border-border/50">
          <div className="text-xs font-medium text-muted-foreground mb-1">Normalized Query</div>
          <div className="text-xs text-muted-foreground/80 font-mono bg-muted/50 p-2 rounded">
            {routing.normalized_query}
          </div>
        </div>
      )}
    </div>
  );
}
