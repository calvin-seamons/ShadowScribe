/**
 * Metadata sidebar displaying RAG pipeline information
 */
'use client';

import { useMetadataStore } from '@/lib/stores/metadataStore';
import { ChevronDown, ChevronRight, X, Sparkles, Eye } from 'lucide-react';
import { useState } from 'react';
import { RoutingInfo } from './RoutingInfo';
import { EntityList } from './EntityList';
import { ContextSources } from './ContextSources';
import { PerformanceMetrics } from './PerformanceMetrics';
import { cn } from '@/lib/utils';

export function MetadataSidebar() {
  const { currentMetadata, sidebarVisible, toggleSidebar } = useMetadataStore();
  const [expandedSections, setExpandedSections] = useState({
    routing: true,
    entities: true,
    sources: true,
    performance: false,
  });

  if (!sidebarVisible) {
    return null;
  }

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  return (
    <div className="w-80 border-l border-border/50 bg-card/50 backdrop-blur-sm flex flex-col h-full overflow-hidden animate-slide-in-left">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-border/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <Eye className="w-4 h-4 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold text-foreground">Query Analysis</h2>
              <p className="text-xs text-muted-foreground">RAG Pipeline Insights</p>
            </div>
          </div>
          <button
            onClick={toggleSidebar}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
            aria-label="Close sidebar"
          >
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {!currentMetadata ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mb-4">
              <Sparkles className="w-8 h-8 text-muted-foreground/40" />
            </div>
            <p className="text-sm text-muted-foreground">
              Send a message to see
            </p>
            <p className="text-sm text-muted-foreground">
              query analysis
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Routing Info */}
            {currentMetadata.routing && (
              <Section
                title="Tools & Intentions"
                subtitle="Routing decisions"
                expanded={expandedSections.routing}
                onToggle={() => toggleSection('routing')}
                accentColor="primary"
              >
                <RoutingInfo routing={currentMetadata.routing} />
              </Section>
            )}

            {/* Entities */}
            {currentMetadata.entities && (
              <Section
                title="Entities Extracted"
                subtitle="Named entities found"
                expanded={expandedSections.entities}
                onToggle={() => toggleSection('entities')}
                accentColor="accent"
              >
                <EntityList entities={currentMetadata.entities} />
              </Section>
            )}

            {/* Context Sources */}
            {currentMetadata.sources && (
              <Section
                title="Context Sources"
                subtitle="RAG data sources"
                expanded={expandedSections.sources}
                onToggle={() => toggleSection('sources')}
                accentColor="secondary"
              >
                <ContextSources sources={currentMetadata.sources} />
              </Section>
            )}

            {/* Performance */}
            {currentMetadata.performance && (
              <Section
                title="Performance"
                subtitle="Timing breakdown"
                expanded={expandedSections.performance}
                onToggle={() => toggleSection('performance')}
                accentColor="muted"
              >
                <PerformanceMetrics performance={currentMetadata.performance} />
              </Section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

interface SectionProps {
  title: string;
  subtitle?: string;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  accentColor?: 'primary' | 'accent' | 'secondary' | 'muted';
}

function Section({ title, subtitle, expanded, onToggle, children, accentColor = 'primary' }: SectionProps) {
  const accentClasses = {
    primary: 'border-primary/20 hover:border-primary/30',
    accent: 'border-accent/20 hover:border-accent/30',
    secondary: 'border-secondary/30 hover:border-secondary/40',
    muted: 'border-border/50 hover:border-border',
  };

  const iconClasses = {
    primary: 'text-primary',
    accent: 'text-accent',
    secondary: 'text-secondary-foreground',
    muted: 'text-muted-foreground',
  };

  return (
    <div className={cn(
      'rounded-xl border bg-card/50 overflow-hidden transition-colors',
      accentClasses[accentColor]
    )}>
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 p-3 hover:bg-muted/30 transition-colors"
      >
        <div className={cn(
          'w-5 h-5 flex items-center justify-center transition-transform',
          expanded ? 'rotate-0' : '-rotate-90'
        )}>
          <ChevronDown className={cn('w-4 h-4', iconClasses[accentColor])} />
        </div>
        <div className="flex-1 text-left">
          <span className="font-medium text-sm text-foreground">{title}</span>
          {subtitle && (
            <span className="text-xs text-muted-foreground ml-2">{subtitle}</span>
          )}
        </div>
      </button>
      {expanded && (
        <div className="px-3 pb-3 pt-0 border-t border-border/30">
          <div className="pt-3">
            {children}
          </div>
        </div>
      )}
    </div>
  );
}
