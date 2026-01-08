/**
 * Displays context sources used to answer the query
 */
'use client';

import { ContextSources as ContextSourcesType } from '@/lib/types/metadata';
import { User, Book, ScrollText } from 'lucide-react';
import { useState } from 'react';

interface ContextSourcesProps {
  sources: ContextSourcesType;
}

export function ContextSources({ sources }: ContextSourcesProps) {
  const [expandedSections, setExpandedSections] = useState({
    character: true,
    rulebook: false,
    sessions: false,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  return (
    <div className="space-y-3">
      {/* Character Fields */}
      {sources.character_fields && sources.character_fields.length > 0 && (
        <div>
          <button
            onClick={() => toggleSection('character')}
            className="flex items-center gap-2 w-full text-left mb-2 hover:text-primary transition-colors"
            aria-expanded={expandedSections.character}
            aria-controls="character-fields-content"
          >
            <User className="w-4 h-4" />
            <span className="text-sm font-medium">
              Character Fields ({sources.character_fields.length})
            </span>
          </button>
          {expandedSections.character && (
            <div id="character-fields-content" className="ml-6 space-y-1">
              {sources.character_fields.map((field, idx) => (
                <div key={idx} className="text-xs px-2 py-1 bg-muted rounded">
                  {field}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Rulebook Sections */}
      {sources.rulebook_sections && sources.rulebook_sections.length > 0 && (
        <div>
          <button
            onClick={() => toggleSection('rulebook')}
            className="flex items-center gap-2 w-full text-left mb-2 hover:text-primary transition-colors"
            aria-expanded={expandedSections.rulebook}
            aria-controls="rulebook-sections-content"
          >
            <Book className="w-4 h-4" />
            <span className="text-sm font-medium">
              Rulebook Sections ({sources.rulebook_sections.length})
            </span>
          </button>
          {expandedSections.rulebook && (
            <div id="rulebook-sections-content" className="ml-6 space-y-2">
              {sources.rulebook_sections.map((section, idx) => (
                <div key={idx} className="text-xs">
                  <div className="font-medium">{section.title}</div>
                  <div className="text-muted-foreground">
                    ID: {section.id} • Score: {(section.score * 100).toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Session Notes */}
      {sources.session_notes && sources.session_notes.length > 0 && (
        <div>
          <button
            onClick={() => toggleSection('sessions')}
            className="flex items-center gap-2 w-full text-left mb-2 hover:text-primary transition-colors"
            aria-expanded={expandedSections.sessions}
            aria-controls="session-notes-content"
          >
            <ScrollText className="w-4 h-4" />
            <span className="text-sm font-medium">
              Session Notes ({sources.session_notes.length})
            </span>
          </button>
          {expandedSections.sessions && (
            <div id="session-notes-content" className="ml-6 space-y-2">
              {sources.session_notes.map((note, idx) => (
                <div key={idx} className="text-xs">
                  <div className="font-medium">Session {note.session_number}</div>
                  <div className="text-muted-foreground">
                    Relevance: {(note.relevance_score * 100).toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {!sources.character_fields?.length && 
       !sources.rulebook_sections?.length && 
       !sources.session_notes?.length && (
        <div className="text-sm text-muted-foreground">No context sources available</div>
      )}
    </div>
  );
}
