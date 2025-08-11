import React, { useState, useEffect } from 'react';
import { User, ChevronDown, Plus } from 'lucide-react';
import { listCharacters } from '../../services/knowledgeBaseApi';

interface CharacterSelectorProps {
  selectedCharacter: string | null;
  onCharacterSelect: (characterName: string | null) => void;
  onCreateNew: () => void;
}

export const CharacterSelector: React.FC<CharacterSelectorProps> = ({
  selectedCharacter,
  onCharacterSelect,
  onCreateNew
}) => {
  const [characters, setCharacters] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCharacters();
  }, []);

  const loadCharacters = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await listCharacters();
      setCharacters(result.characters);
      
      // Auto-select first character if none selected and characters exist
      if (!selectedCharacter && result.characters.length > 0) {
        onCharacterSelect(result.characters[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load characters');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCharacterSelect = (characterName: string) => {
    onCharacterSelect(characterName);
    setIsOpen(false);
  };

  const handleShowAll = () => {
    onCharacterSelect(null);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500"
        disabled={isLoading}
      >
        <div className="flex items-center space-x-2">
          <User className="w-4 h-4" />
          <span>
            {isLoading ? 'Loading...' : 
             selectedCharacter ? selectedCharacter.replace(/_/g, ' ') : 
             'All Characters'}
          </span>
        </div>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-gray-700 border border-gray-600 rounded-md shadow-lg z-10 max-h-60 overflow-y-auto">
          {/* Show All Option */}
          <button
            onClick={handleShowAll}
            className={`w-full text-left px-4 py-2 hover:bg-gray-600 ${
              !selectedCharacter ? 'bg-purple-600' : ''
            }`}
          >
            <div className="flex items-center space-x-2">
              <User className="w-4 h-4" />
              <span>All Characters</span>
            </div>
          </button>

          {/* Divider */}
          {characters.length > 0 && (
            <div className="border-t border-gray-600 my-1"></div>
          )}

          {/* Character List */}
          {characters.map((character) => (
            <button
              key={character}
              onClick={() => handleCharacterSelect(character)}
              className={`w-full text-left px-4 py-2 hover:bg-gray-600 ${
                selectedCharacter === character ? 'bg-purple-600' : ''
              }`}
            >
              <div className="flex items-center space-x-2">
                <User className="w-4 h-4" />
                <span>{character.replace(/_/g, ' ')}</span>
              </div>
            </button>
          ))}

          {/* Create New Character Option */}
          <div className="border-t border-gray-600 mt-1">
            <button
              onClick={() => {
                onCreateNew();
                setIsOpen(false);
              }}
              className="w-full text-left px-4 py-2 hover:bg-gray-600 text-green-400"
            >
              <div className="flex items-center space-x-2">
                <Plus className="w-4 h-4" />
                <span>Create New Character</span>
              </div>
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="px-4 py-2 text-red-400 text-sm border-t border-gray-600">
              Error: {error}
            </div>
          )}

          {/* Empty State */}
          {!isLoading && characters.length === 0 && !error && (
            <div className="px-4 py-2 text-gray-400 text-sm">
              No characters found. Create your first character!
            </div>
          )}
        </div>
      )}
    </div>
  );
};