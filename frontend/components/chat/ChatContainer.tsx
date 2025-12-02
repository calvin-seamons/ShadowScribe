'use client'

import { useEffect, useRef, useState } from 'react'
import { useChatStore } from '@/lib/stores/chatStore'
import { useMetadataStore } from '@/lib/stores/metadataStore'
import { websocketService } from '@/lib/services/websocket'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import FeedbackModal from './FeedbackModal'
import { Message } from '@/lib/types/conversation'
import { getConversationByCharacter, getConversationById, saveConversation, createConversation } from '@/lib/services/localStorage'
import { RefreshCw, AlertTriangle, Sparkles } from 'lucide-react'

interface ChatContainerProps {
  characterName: string
  conversationId?: string | null
  onConversationCreated?: (conversationId: string) => void
}

export default function ChatContainer({ characterName, conversationId, onConversationCreated }: ChatContainerProps) {
  const { messages, addMessage, startStreaming, appendToStreamingMessage, completeStreaming, setError, clearMessages, clearHistory, setMessages } = useChatStore()
  const { updateCurrentMetadata, saveMessageMetadata, clearCurrentMetadata, setCurrentFeedbackId, saveFeedbackIdForMessage } = useMetadataStore()
  const [isConnecting, setIsConnecting] = useState(true)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const conversationIdRef = useRef<string | null>(null)
  const currentMessageIdRef = useRef<string | null>(null)

  // Store callback in ref to avoid dependency issues
  const onConversationCreatedRef = useRef(onConversationCreated)
  useEffect(() => {
    onConversationCreatedRef.current = onConversationCreated
  }, [onConversationCreated])

  // Track previous conversationId to detect when it becomes null (new conversation requested)
  const prevConversationIdRef = useRef<string | null | undefined>(undefined)

  // Load or create conversation when component mounts or conversationId changes
  useEffect(() => {
    const characterId = characterName.toLowerCase().replace(/\s+/g, '-')
    const chatStore = useChatStore.getState()

    // Detect if user clicked "New Conversation" (conversationId went from a value to null)
    const isNewConversationRequest = prevConversationIdRef.current !== undefined && 
                                      prevConversationIdRef.current !== null && 
                                      conversationId === null
    prevConversationIdRef.current = conversationId

    if (isNewConversationRequest) {
      // Clear backend and frontend state, create new conversation
      const triggerNewConversation = async () => {
        try {
          // Clear backend conversation history if connected
          if (websocketService.isConnected()) {
            await websocketService.clearHistory(characterName)
          }
          
          // Clear frontend state
          chatStore.clearHistory()
          clearCurrentMetadata()
          
          // Create new conversation
          const conversation = createConversation(characterId, characterName)
          saveConversation(conversation)
          conversationIdRef.current = conversation.id
          
          // Notify parent about new conversation
          onConversationCreatedRef.current?.(conversation.id)
        } catch (error) {
          console.error('Error creating new conversation:', error)
        }
      }
      triggerNewConversation()
      return
    }

    if (conversationId) {
      // Load existing conversation by ID
      const conversation = getConversationById(conversationId)
      if (conversation) {
        // Only update if this is a different conversation
        if (conversationIdRef.current !== conversation.id) {
          conversationIdRef.current = conversation.id
          chatStore.setMessages(conversation.messages)
        }
        return
      }
    }

    // Only create new conversation if we don't already have one (initial mount)
    if (!conversationIdRef.current) {
      const conversation = createConversation(characterId, characterName)
      saveConversation(conversation)
      conversationIdRef.current = conversation.id
      chatStore.clearMessages()
      onConversationCreatedRef.current?.(conversation.id)
    }
  }, [conversationId, characterName, clearCurrentMetadata])

  useEffect(() => {
    // Connect WebSocket
    const connect = async () => {
      try {
        setIsConnecting(true)
        setConnectionError(null)
        console.log('Attempting to connect WebSocket...')

        // Give it more time on first attempt
        const maxWaitTime = retryCount === 0 ? 10000 : 5000
        const connectionPromise = websocketService.connect()
        const timeoutPromise = new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Connection timeout')), maxWaitTime)
        )

        await Promise.race([connectionPromise, timeoutPromise])

        console.log('WebSocket connected successfully!')
        setIsConnecting(false)
        setRetryCount(0) // Reset retry count on success

        // Set up message handlers
        websocketService.onMessage((chunk) => {
          appendToStreamingMessage(chunk)
        })

        websocketService.onComplete(() => {
          completeStreaming()
        })

        websocketService.onError((error) => {
          setError(error)
        })

        // Set up metadata handler
        websocketService.onMetadata((type, data) => {
          console.log(`Received metadata: ${type}`, data)

          switch (type) {
            case 'routing_metadata':
              updateCurrentMetadata({ routing: data })
              break
            case 'entities_metadata':
              updateCurrentMetadata({ entities: data })
              break
            case 'context_sources':
              updateCurrentMetadata({ sources: data })
              break
            case 'performance_metrics':
              updateCurrentMetadata({ performance: data })
              // Save complete metadata when performance arrives (last event)
              if (currentMessageIdRef.current) {
                const currentMetadata = useMetadataStore.getState().currentMetadata
                if (currentMetadata) {
                  saveMessageMetadata(currentMessageIdRef.current, currentMetadata)
                }
              }
              break
          }
        })

        // Set up feedback ID handler
        websocketService.onFeedbackId((feedbackId) => {
          console.log(`Received feedback ID: ${feedbackId}`)
          setCurrentFeedbackId(feedbackId)
          // Associate feedback ID with current message
          if (currentMessageIdRef.current) {
            saveFeedbackIdForMessage(currentMessageIdRef.current, feedbackId)
          }
        })
      } catch (error) {
        console.error('Failed to connect WebSocket:', error)
        const errorMessage = error instanceof Error ? error.message : 'Unknown error'

        // Only show error after a few retries (give WebSocket time to establish)
        setRetryCount(prev => prev + 1)

        if (retryCount < 2) {
          // Retry silently without showing error
          console.log(`Silent retry attempt ${retryCount + 1}...`)
          setTimeout(() => connect(), 1000)
        } else {
          // After retries, show error
          setConnectionError(`Failed to connect to server: ${errorMessage}. Please check if the backend is running.`)
          setIsConnecting(false)
        }
      }
    }

    connect()

    return () => {
      websocketService.disconnect()
    }
  }, [characterName])

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (conversationIdRef.current) {
      const conversation = getConversationById(conversationIdRef.current)
      if (conversation) {
        // Only save if messages actually changed
        const messagesChanged = JSON.stringify(conversation.messages) !== JSON.stringify(messages)
        if (messagesChanged) {
          conversation.messages = messages
          conversation.updatedAt = new Date()
          saveConversation(conversation)
        }
      }
    }
  }, [messages])

  const clearConversation = async () => {
    if (!websocketService.isConnected()) {
      setError('Not connected to server')
      return
    }

    try {
      // Clear backend conversation history
      await websocketService.clearHistory(characterName)

      // Clear frontend state using store directly
      const chatStore = useChatStore.getState()
      chatStore.clearHistory()

      // Create new conversation in localStorage
      const characterId = characterName.toLowerCase().replace(/\s+/g, '-')
      const conversation = createConversation(characterId, characterName)
      saveConversation(conversation)
      conversationIdRef.current = conversation.id

      // Clear metadata
      clearCurrentMetadata()

      // Notify parent about new conversation
      onConversationCreated?.(conversation.id)
    } catch (error) {
      console.error('Error clearing conversation:', error)
      setError('Failed to clear conversation')
    }
  }

  const handleSendMessage = async (content: string) => {
    if (!websocketService.isConnected()) {
      setError('Not connected to server')
      return
    }

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    }
    addMessage(userMessage)

    // Generate message ID for the upcoming assistant response
    const assistantMessageId = (Date.now() + 1).toString()
    
    // Store message ID for metadata association
    currentMessageIdRef.current = assistantMessageId

    // Clear previous metadata and start streaming with expected message ID
    clearCurrentMetadata()
    startStreaming(assistantMessageId)

    try {
      websocketService.sendMessage(content, characterName)
    } catch (error) {
      console.error('Error sending message:', error)
      setError('Failed to send message')
    }
  }

  if (isConnecting) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center animate-fade-in-up">
          <div className="relative inline-flex mb-6">
            <div className="w-16 h-16 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
            <Sparkles className="absolute inset-0 m-auto w-6 h-6 text-primary" />
          </div>
          <p className="text-lg text-muted-foreground">Connecting to the arcane network...</p>
          <p className="text-sm text-muted-foreground/60 mt-2">Establishing mystical connection</p>
        </div>
      </div>
    )
  }

  if (connectionError) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <div className="text-center max-w-md animate-fade-in-up">
          <div className="w-20 h-20 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-6">
            <AlertTriangle className="w-10 h-10 text-destructive" />
          </div>
          <h3 className="text-2xl font-bold text-destructive mb-3">Connection Lost</h3>
          <p className="text-muted-foreground mb-6 leading-relaxed">{connectionError}</p>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary inline-flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col min-h-0 bg-gradient-to-b from-background to-background/95">
      {/* Chat header bar */}
      <div className="flex-shrink-0 border-b border-border/50 bg-card/50 backdrop-blur-sm px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-sm text-muted-foreground">
            Conversing with <span className="text-foreground font-medium">{characterName}</span>
          </span>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <MessageList />
      </div>

      {/* Input area */}
      <div className="flex-shrink-0 sticky bottom-0 bg-gradient-to-t from-card via-card to-card/95 border-t border-border/50">
        <MessageInput onSendMessage={handleSendMessage} />
      </div>

      {/* Feedback Modal */}
      <FeedbackModal />
    </div>
  )
}
