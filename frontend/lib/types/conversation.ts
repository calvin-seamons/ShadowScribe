export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

export interface Conversation {
  id: string
  characterId: string
  characterName: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
}
