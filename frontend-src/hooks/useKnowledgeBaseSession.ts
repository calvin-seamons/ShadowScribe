import { useEffect, useCallback } from 'react';
import { useSessionStore } from '../stores/sessionStore';
import { useKnowledgeBaseStore } from '../stores/knowledgeBaseStore';
import { useNavigationStore } from '../stores/navigationStore';

/**
 * Hook to manage knowledge base editor session and access controls
 * This ensures proper session management and cleanup when switching between views
 */
export const useKnowledgeBaseSession = () => {
  const { sessionId } = useSessionStore();
  const { 
    hasUnsavedChanges, 
    resetState: resetKnowledgeBaseState 
  } = useKnowledgeBaseStore();
  const { 
    isKnowledgeBaseEditorOpen,
    closeKnowledgeBaseEditor 
  } = useNavigationStore();

  // Check if user has access to knowledge base editor
  const hasAccess = useCallback(() => {
    // For now, all users with a valid session have access
    // This could be extended to check user permissions, roles, etc.
    return !!sessionId;
  }, [sessionId]);

  // Handle session cleanup when leaving knowledge base editor
  const handleSessionCleanup = useCallback(() => {
    if (hasUnsavedChanges) {
      const shouldCleanup = window.confirm(
        'You have unsaved changes in the Knowledge Base Editor. Do you want to discard them?'
      );
      if (!shouldCleanup) {
        return false;
      }
    }
    
    resetKnowledgeBaseState();
    return true;
  }, [hasUnsavedChanges, resetKnowledgeBaseState]);

  // Handle browser navigation/refresh with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (isKnowledgeBaseEditorOpen && hasUnsavedChanges) {
        event.preventDefault();
        event.returnValue = 'You have unsaved changes in the Knowledge Base Editor. Are you sure you want to leave?';
        return event.returnValue;
      }
    };

    const handlePopState = () => {
      if (isKnowledgeBaseEditorOpen && hasUnsavedChanges) {
        const shouldLeave = window.confirm(
          'You have unsaved changes in the Knowledge Base Editor. Are you sure you want to leave?'
        );
        if (!shouldLeave) {
          // Push the current state back to prevent navigation
          window.history.pushState(null, '', window.location.href);
          return;
        }
        closeKnowledgeBaseEditor();
      }
    };

    if (isKnowledgeBaseEditorOpen) {
      window.addEventListener('beforeunload', handleBeforeUnload);
      window.addEventListener('popstate', handlePopState);
    }

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('popstate', handlePopState);
    };
  }, [isKnowledgeBaseEditorOpen, hasUnsavedChanges, closeKnowledgeBaseEditor]);

  // Auto-save functionality (optional)
  const enableAutoSave = useCallback((intervalMs: number = 30000) => {
    if (!isKnowledgeBaseEditorOpen) return;

    const autoSaveInterval = setInterval(() => {
      if (hasUnsavedChanges) {
        // Trigger auto-save event
        const event = new CustomEvent('knowledge-base-auto-save');
        window.dispatchEvent(event);
      }
    }, intervalMs);

    return () => clearInterval(autoSaveInterval);
  }, [isKnowledgeBaseEditorOpen, hasUnsavedChanges]);

  return {
    hasAccess,
    handleSessionCleanup,
    enableAutoSave,
    sessionId,
    isKnowledgeBaseEditorOpen,
    hasUnsavedChanges
  };
};