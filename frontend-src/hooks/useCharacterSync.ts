import { useEffect, useCallback } from 'react';
import { useKnowledgeBaseStore } from '../stores/knowledgeBaseStore';
// import { getCharacterSummary } from '../services/api';

/**
 * Hook to synchronize character data between the knowledge base editor and main application
 * This ensures that when character files are modified in the editor, the character sheet
 * in the sidebar is updated to reflect the changes
 */
export const useCharacterSync = () => {
  const { 
    lastModifiedCharacter, 
    characterDataVersion,
    incrementCharacterDataVersion 
  } = useKnowledgeBaseStore();

  // Function to refresh character data
  const refreshCharacterData = useCallback(async () => {
    try {
      // Trigger a refresh of character data in the main application
      // This could be done by dispatching an event or calling a refresh function
      const event = new CustomEvent('character-data-changed', {
        detail: {
          characterName: lastModifiedCharacter,
          version: characterDataVersion
        }
      });
      window.dispatchEvent(event);
      
      // You could also directly call the character summary API here
      // and update a global state if needed
      
    } catch (error) {
      console.error('Failed to refresh character data:', error);
    }
  }, [lastModifiedCharacter, characterDataVersion]);

  // Listen for character modifications
  useEffect(() => {
    if (lastModifiedCharacter) {
      refreshCharacterData();
    }
  }, [lastModifiedCharacter, characterDataVersion, refreshCharacterData]);

  // Function to manually trigger character data refresh
  const triggerCharacterRefresh = useCallback(() => {
    incrementCharacterDataVersion();
  }, [incrementCharacterDataVersion]);

  return {
    refreshCharacterData,
    triggerCharacterRefresh,
    lastModifiedCharacter,
    characterDataVersion
  };
};