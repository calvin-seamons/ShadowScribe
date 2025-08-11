import { useEffect, useState, useCallback } from 'react';
import { Shield, Heart } from 'lucide-react';
import { getCharacterSummary } from '../../services/api';
import type { Character } from '../../types/index';

export const CharacterSheet: React.FC = () => {
  const [character, setCharacter] = useState<Character | null>(null);
  const [loading, setLoading] = useState(true);

  const loadCharacter = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getCharacterSummary();
      setCharacter(data);
    } catch (error) {
      console.error('Failed to load character:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCharacter();

    // Listen for character data changes from the knowledge base editor
    const handleCharacterDataChanged = (event: CustomEvent) => {
      console.log('Character data changed, refreshing character sheet:', event.detail);
      loadCharacter();
    };

    window.addEventListener('character-data-changed', handleCharacterDataChanged as EventListener);

    return () => {
      window.removeEventListener('character-data-changed', handleCharacterDataChanged as EventListener);
    };
  }, [loadCharacter]);

  if (loading) {
    return (
      <div className="p-4 border-b border-gray-700">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded mb-2"></div>
          <div className="h-4 bg-gray-700 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  if (!character) {
    return null;
  }

  return (
    <div className="p-4 border-b border-gray-700">
      <h2 className="text-lg font-bold text-white mb-3">{character.name}</h2>
      <p className="text-sm text-gray-400 mb-3">
        {character.race} {character.class_info}
      </p>

      <div className="space-y-2">
        {/* HP */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Heart className="w-4 h-4 text-red-500" />
            <span className="text-sm text-gray-300">HP</span>
          </div>
          <span className="text-sm font-medium text-white">
            {character.hit_points.current}/{character.hit_points.max}
          </span>
        </div>

        {/* AC */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-blue-500" />
            <span className="text-sm text-gray-300">AC</span>
          </div>
          <span className="text-sm font-medium text-white">{character.armor_class}</span>
        </div>

        {/* Key Stats */}
        <div className="mt-3 pt-3 border-t border-gray-700">
          <h3 className="text-xs uppercase text-gray-400 mb-2">Ability Scores</h3>
          <div className="grid grid-cols-3 gap-2 text-xs">
            {Object.entries(character.key_stats).map(([stat, value]) => (
              <div key={stat} className="text-center">
                <div className="text-gray-400 uppercase">{stat.slice(0, 3)}</div>
                <div className="text-white font-medium">{String(value)}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
