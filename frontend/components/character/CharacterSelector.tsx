'use client'

import { useEffect, useState } from 'react'
import { useCharacterStore } from '@/lib/stores/characterStore'
import { fetchCharacters } from '@/lib/services/api'
import { Character } from '@/lib/types/character'
import { ChevronDown, User, Loader2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CharacterSelectorProps {
  selectedCharacter: string | null
  onSelectCharacter: (characterName: string) => void
}

export default function CharacterSelector({ selectedCharacter, onSelectCharacter }: CharacterSelectorProps) {
  const { characters, setCharacters, setLoading, setError, isLoading: loading, error } = useCharacterStore()
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    loadCharacters()
  }, [])

  const loadCharacters = async () => {
    setLoading(true)
    setError(null)

    const maxRetries = 3
    let lastError: Error | null = null

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await fetchCharacters()
        setCharacters(response.characters)
        setError(null)
        setLoading(false)
        return
      } catch (error) {
        console.error(`Error loading characters (attempt ${attempt}/${maxRetries}):`, error)
        lastError = error as Error

        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt))
        }
      }
    }

    setError('Failed to load characters. Please check if the API server is running.')
    setLoading(false)
  }

  const handleSelect = (character: Character) => {
    onSelectCharacter(character.name)
    setIsOpen(false)
  }

  const selectedCharacterData = characters.find(c => c.name === selectedCharacter)

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-3 px-4 py-2.5 rounded-xl border transition-all',
          'bg-card/80 border-border/50 hover:border-primary/50 hover:bg-card',
          isOpen && 'border-primary/50 ring-2 ring-primary/20'
        )}
      >
        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
          <User className="w-4 h-4 text-primary" />
        </div>
        <div className="text-left">
          {loading ? (
            <span className="text-sm text-muted-foreground">Loading...</span>
          ) : selectedCharacter ? (
            <>
              <span className="text-sm font-medium text-foreground block">{selectedCharacter}</span>
              {selectedCharacterData && (
                <span className="text-xs text-muted-foreground">
                  Level {selectedCharacterData.level} {selectedCharacterData.character_class}
                </span>
              )}
            </>
          ) : (
            <span className="text-sm text-muted-foreground">Select Character</span>
          )}
        </div>
        <ChevronDown className={cn(
          'w-4 h-4 text-muted-foreground transition-transform ml-2',
          isOpen && 'rotate-180'
        )} />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 w-72 rounded-xl border border-border/50 bg-popover shadow-2xl z-50 overflow-hidden animate-scale-in">
            {/* Header */}
            <div className="px-4 py-3 border-b border-border/50 bg-muted/30">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Your Characters
              </p>
            </div>

            {/* Content */}
            <div className="max-h-80 overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-5 h-5 animate-spin text-primary" />
                </div>
              ) : error ? (
                <div className="p-4 flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
                  <div>
                    <p className="text-sm text-destructive font-medium">Connection Error</p>
                    <p className="text-xs text-muted-foreground mt-1">{error}</p>
                    <button
                      onClick={loadCharacters}
                      className="text-xs text-primary hover:underline mt-2"
                    >
                      Retry
                    </button>
                  </div>
                </div>
              ) : characters.length === 0 ? (
                <div className="p-6 text-center">
                  <div className="w-12 h-12 rounded-full bg-muted/50 flex items-center justify-center mx-auto mb-3">
                    <User className="w-6 h-6 text-muted-foreground/50" />
                  </div>
                  <p className="text-sm text-muted-foreground">No characters found</p>
                  <p className="text-xs text-muted-foreground/60 mt-1">Create one to get started</p>
                </div>
              ) : (
                <div className="p-2">
                  {characters.map((character, index) => (
                    <button
                      key={character.id}
                      onClick={() => handleSelect(character)}
                      className={cn(
                        'w-full flex items-center gap-3 p-3 rounded-lg transition-all',
                        'hover:bg-muted/50',
                        selectedCharacter === character.name && 'bg-primary/10 border border-primary/20'
                      )}
                      style={{ animationDelay: `${index * 30}ms` }}
                    >
                      <div className={cn(
                        'w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold',
                        selectedCharacter === character.name
                          ? 'bg-primary/20 text-primary'
                          : 'bg-muted text-muted-foreground'
                      )}>
                        {character.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 text-left">
                        <p className={cn(
                          'font-medium',
                          selectedCharacter === character.name ? 'text-foreground' : 'text-foreground/80'
                        )}>
                          {character.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {character.race} {character.character_class} • Lvl {character.level}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
