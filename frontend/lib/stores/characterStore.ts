import { create } from 'zustand'
import { Character } from '@/lib/types/character'

interface CharacterState {
  characters: Character[]
  selectedCharacter: Character | null
  isLoading: boolean
  error: string | null
  
  setCharacters: (characters: Character[]) => void
  setSelectedCharacter: (character: Character | null) => void
  setLoading: (isLoading: boolean) => void
  setError: (error: string | null) => void
}

export const useCharacterStore = create<CharacterState>((set) => ({
  characters: [],
  selectedCharacter: null,
  isLoading: false,
  error: null,
  
  setCharacters: (characters) => set({ characters }),
  setSelectedCharacter: (character) => set({ selectedCharacter: character }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error })
}))
