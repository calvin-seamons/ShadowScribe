/**
 * Conversation History Sidebar - Shows past conversations and navigation
 */
'use client';

import { MessageSquare, Plus, Wand2, Trash2, Trash, ScrollText, User } from 'lucide-react';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import { getConversations, deleteConversation, createConversation, saveConversation, clearAllConversations } from '@/lib/services/localStorage';
import { Conversation } from '@/lib/types/conversation';
import { cn } from '@/lib/utils';

interface ConversationHistorySidebarProps {
  characterName: string;
  onConversationSelect?: (conversationId: string) => void;
  onNewConversation?: () => void;
}

export function ConversationHistorySidebar({ characterName, onConversationSelect, onNewConversation }: ConversationHistorySidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);

  // Load conversations for the current character
  useEffect(() => {
    const loadConversations = () => {
      const allConversations = getConversations();
      const characterId = characterName.toLowerCase().replace(/\s+/g, '-');
      const characterConversations = allConversations
        .filter(conv => conv.characterId === characterId)
        .sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
      setConversations(characterConversations);

      // Auto-select the most recent conversation if none selected
      if (characterConversations.length > 0 && !selectedConversationId) {
        setSelectedConversationId(characterConversations[0].id);
      }
    };

    loadConversations();

    // Poll for updates (in case conversations are modified elsewhere)
    const interval = setInterval(loadConversations, 1000);
    return () => clearInterval(interval);
  }, [characterName, selectedConversationId]);

  const handleNewConversation = () => {
    onNewConversation?.();
    // Reload conversations after a brief delay to see the new one
    setTimeout(() => {
      const allConversations = getConversations();
      const characterId = characterName.toLowerCase().replace(/\s+/g, '-');
      const characterConversations = allConversations
        .filter(conv => conv.characterId === characterId)
        .sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
      setConversations(characterConversations);
    }, 100);
  };

  const handleSelectConversation = (conversationId: string) => {
    setSelectedConversationId(conversationId);
    onConversationSelect?.(conversationId);
  };

  const handleDeleteConversation = (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Delete this conversation?')) {
      deleteConversation(conversationId);
      setConversations(prev => prev.filter(conv => conv.id !== conversationId));
      if (selectedConversationId === conversationId) {
        setSelectedConversationId(null);
      }
    }
  };

  const handleClearAllConversations = () => {
    if (confirm('Delete ALL conversations? This cannot be undone.')) {
      clearAllConversations();
      setConversations([]);
      setSelectedConversationId(null);
      onNewConversation?.();
    }
  };

  const getConversationPreview = (conv: Conversation): string => {
    const userMessages = conv.messages.filter(m => m.role === 'user');
    if (userMessages.length === 0) return 'New conversation';
    return userMessages[0].content.substring(0, 50);
  };

  return (
    <div className="w-72 border-r border-border/50 bg-card/50 backdrop-blur-sm flex flex-col h-full min-h-0 flex-shrink-0">
      {/* Header */}
      <div className="p-4 border-b border-border/50">
        <button
          onClick={handleNewConversation}
          className="btn-primary w-full flex items-center justify-center gap-2 py-2.5"
        >
          <Plus className="w-4 h-4" />
          New Conversation
        </button>

        <Link
          href="/characters/create"
          className="w-full mt-3 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-border/50 text-muted-foreground hover:text-foreground hover:border-border transition-all"
        >
          <Wand2 className="w-4 h-4" />
          <span>Character Wizard</span>
        </Link>
      </div>

      {/* Conversations list */}
      <div className="flex-1 overflow-y-auto p-3">
        <div className="flex items-center justify-between mb-3 px-1">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Recent Scrolls
          </span>
          {conversations.length > 0 && (
            <button
              onClick={handleClearAllConversations}
              className="text-xs text-muted-foreground hover:text-destructive transition-colors flex items-center gap-1 px-2 py-1 rounded hover:bg-destructive/10"
              title="Clear all conversations"
            >
              <Trash className="w-3 h-3" />
              Clear
            </button>
          )}
        </div>

        {conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
            <div className="w-14 h-14 rounded-full bg-muted/50 flex items-center justify-center mb-4">
              <ScrollText className="w-7 h-7 text-muted-foreground/50" />
            </div>
            <p className="text-sm text-muted-foreground">
              No conversations yet
            </p>
            <p className="text-xs text-muted-foreground/60 mt-1">
              Start chatting to create one
            </p>
          </div>
        ) : (
          <div className="space-y-1.5">
            {conversations.map((conv, index) => (
              <div
                key={conv.id}
                onClick={() => handleSelectConversation(conv.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && handleSelectConversation(conv.id)}
                className={cn(
                  'group relative w-full text-left p-3 rounded-xl transition-all cursor-pointer',
                  'hover:bg-muted/50',
                  selectedConversationId === conv.id
                    ? 'bg-primary/10 border border-primary/20'
                    : 'border border-transparent'
                )}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className="flex items-start gap-3">
                  <div className={cn(
                    'flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center',
                    selectedConversationId === conv.id
                      ? 'bg-primary/20 text-primary'
                      : 'bg-muted text-muted-foreground'
                  )}>
                    <MessageSquare className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0 pr-6">
                    <p className={cn(
                      'text-sm truncate',
                      selectedConversationId === conv.id
                        ? 'text-foreground font-medium'
                        : 'text-foreground/80'
                    )}>
                      {getConversationPreview(conv)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {formatTimestamp(conv.updatedAt)}
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDeleteConversation(conv.id, e)}
                    className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 p-1.5 hover:bg-destructive/10 rounded-lg transition-all"
                    title="Delete conversation"
                    aria-label="Delete conversation"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-destructive" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Character info footer */}
      <div className="p-4 border-t border-border/50 bg-card/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
            <User className="w-5 h-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">Active Character</p>
            <p className="text-sm font-medium text-foreground truncate mt-0.5">{characterName}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function formatTimestamp(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 7) return `${days} days ago`;
  return date.toLocaleDateString();
}
