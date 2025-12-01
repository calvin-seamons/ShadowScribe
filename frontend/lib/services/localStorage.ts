import { Conversation, Message } from '@/lib/types/conversation'

const STORAGE_KEY = 'shadowscribe-conversations'

export function getConversations(): Conversation[] {
  if (typeof window === 'undefined') return []
  
  const data = localStorage.getItem(STORAGE_KEY)
  if (!data) return []
  
  try {
    const conversations = JSON.parse(data)
    // Parse date strings back to Date objects
    return conversations.map((conv: any) => ({
      ...conv,
      createdAt: new Date(conv.createdAt),
      updatedAt: new Date(conv.updatedAt),
      messages: conv.messages.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }))
    }))
  } catch (error) {
    console.error('Error parsing conversations:', error)
    return []
  }
}

export function getConversationByCharacter(characterId: string): Conversation | null {
  const conversations = getConversations()
  return conversations.find(conv => conv.characterId === characterId) || null
}

export function getConversationById(conversationId: string): Conversation | null {
  const conversations = getConversations()
  return conversations.find(conv => conv.id === conversationId) || null
}

export function saveConversation(conversation: Conversation) {
  const conversations = getConversations()
  const index = conversations.findIndex(conv => conv.id === conversation.id)
  
  if (index >= 0) {
    conversations[index] = conversation
  } else {
    conversations.push(conversation)
  }
  
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
}

export function deleteConversation(conversationId: string) {
  const conversations = getConversations().filter(conv => conv.id !== conversationId)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
}

export function createConversation(characterId: string, characterName: string): Conversation {
  return {
    id: Date.now().toString(),
    characterId,
    characterName,
    messages: [],
    createdAt: new Date(),
    updatedAt: new Date()
  }
}

export function addMessageToConversation(conversationId: string, message: Message) {
  const conversations = getConversations()
  const conversation = conversations.find(conv => conv.id === conversationId)
  
  if (conversation) {
    conversation.messages.push(message)
    conversation.updatedAt = new Date()
    saveConversation(conversation)
  }
}

export function clearAllConversations() {
  localStorage.removeItem(STORAGE_KEY)
}
