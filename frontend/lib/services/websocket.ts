import type { RoutingMetadata, EntitiesMetadata, ContextSources, PerformanceMetrics } from '../types/metadata'
import type { CharacterCreationEvent, CharacterSummary } from '../types/character'

// Use dynamic host for Docker/network access
// In browser: Use current hostname (works for localhost, LAN IP, etc.)
// Fallback to env var if available
function getWsUrl(): string {
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.hostname
    const port = '8000' // Backend port
    const url = `${protocol}//${host}:${port}`
    console.log(`WebSocket URL configured: ${url} (from hostname: ${host})`)
    return url
  }
  // Server-side fallback (shouldn't be used for WebSocket)
  return process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
}

export type WebSocketMessageHandler = (chunk: string) => void
export type WebSocketErrorHandler = (error: string) => void
export type WebSocketCompleteHandler = () => void
export type WebSocketMetadataHandler = (type: string, data: any) => void
export type WebSocketFeedbackIdHandler = (feedbackId: string) => void
export type CharacterCreationProgressHandler = (event: CharacterCreationEvent) => void

export class WebSocketService {
  private ws: WebSocket | null = null
  private characterCreationWs: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  
  private onMessageHandler: WebSocketMessageHandler | null = null
  private onErrorHandler: WebSocketErrorHandler | null = null
  private onCompleteHandler: WebSocketCompleteHandler | null = null
  private onMetadataHandler: WebSocketMetadataHandler | null = null
  private onFeedbackIdHandler: WebSocketFeedbackIdHandler | null = null
  private onProgressHandler: CharacterCreationProgressHandler | null = null
  
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = getWsUrl() // Get URL dynamically on each connect
        this.ws = new WebSocket(`${wsUrl}/ws/chat`)
        
        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.reconnectAttempts = 0
          resolve()
        }
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            
            switch (data.type) {
              case 'response_chunk':
                this.onMessageHandler?.(data.content)
                break
              
              case 'response_complete':
                this.onCompleteHandler?.()
                break
              
              case 'error':
                this.onErrorHandler?.(data.error)
                break
              
              case 'message_received':
                // Acknowledgment received
                break
              
              case 'history_cleared':
                // History cleared acknowledgment (handled in clearHistory promise)
                break
              
              case 'pong':
                // Keep-alive response
                break
              
              // Metadata message types
              case 'routing_metadata':
              case 'entities_metadata':
              case 'context_sources':
              case 'performance_metrics':
                this.onMetadataHandler?.(data.type, data.data)
                break
              
              case 'feedback_id':
                this.onFeedbackIdHandler?.(data.data.id)
                break
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }
        
        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.onErrorHandler?.('Connection error')
          reject(error)
        }
        
        this.ws.onclose = () => {
          console.log('WebSocket closed')
          this.attemptReconnect()
        }
      } catch (error) {
        reject(error)
      }
    })
  }
  
  sendMessage(message: string, characterName: string, campaignId: string = 'main_campaign') {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected')
    }
    
    this.ws.send(JSON.stringify({
      type: 'message',
      message,
      character_name: characterName,
      campaign_id: campaignId
    }))
  }
  
  clearHistory(characterName: string, campaignId: string = 'main_campaign'): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error('WebSocket is not connected'))
        return
      }
      
      const handler = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'history_cleared') {
            this.ws?.removeEventListener('message', handler)
            resolve()
          }
        } catch (error) {
          // Ignore parsing errors, wait for correct message
        }
      }
      
      this.ws.addEventListener('message', handler)
      
      this.ws.send(JSON.stringify({
        type: 'clear_history',
        character_name: characterName,
        campaign_id: campaignId
      }))
      
      // Timeout after 5 seconds
      setTimeout(() => {
        this.ws?.removeEventListener('message', handler)
        reject(new Error('Clear history timeout'))
      }, 5000)
    })
  }
  
  onMessage(handler: WebSocketMessageHandler) {
    this.onMessageHandler = handler
  }
  
  onError(handler: WebSocketErrorHandler) {
    this.onErrorHandler = handler
  }
  
  onComplete(handler: WebSocketCompleteHandler) {
    this.onCompleteHandler = handler
  }
  
  onMetadata(handler: WebSocketMetadataHandler) {
    this.onMetadataHandler = handler
  }
  
  onFeedbackId(handler: WebSocketFeedbackIdHandler) {
    this.onFeedbackIdHandler = handler
  }
  
  /**
   * Register progress callback for character creation
   */
  onProgress(handler: CharacterCreationProgressHandler) {
    this.onProgressHandler = handler
  }
  
  /**
   * Create character via WebSocket with real-time progress
   * Returns Promise that resolves to character summary when complete
   * 
   * @param urlOrJsonData - Either a D&D Beyond URL string or the complete JSON data object
   * @returns Promise<CharacterSummary> - Character summary upon successful creation
   */
  createCharacter(urlOrJsonData: string | any): Promise<CharacterSummary> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = getWsUrl() // Get URL dynamically on each connect
        // Create separate WebSocket connection for character creation
        this.characterCreationWs = new WebSocket(`${wsUrl}/ws/character/create`)
        
        this.characterCreationWs.onopen = () => {
          console.log('Character creation WebSocket connected')
          
          // Send create_character message
          const message = typeof urlOrJsonData === 'string'
            ? { type: 'create_character', url: urlOrJsonData }
            : { type: 'create_character', json_data: urlOrJsonData }
          
          this.characterCreationWs?.send(JSON.stringify(message))
        }
        
        this.characterCreationWs.onmessage = (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data) as CharacterCreationEvent
            
            // Forward all progress events to the handler
            if (data.type !== 'creation_complete' && data.type !== 'creation_error') {
              this.onProgressHandler?.(data)
            }
            
            // Handle completion
            if (data.type === 'creation_complete') {
              this.onProgressHandler?.(data)
              this.characterCreationWs?.close()
              this.characterCreationWs = null
              resolve(data.character_summary)
            }
            
            // Handle errors
            if (data.type === 'creation_error') {
              this.onProgressHandler?.(data)
              this.characterCreationWs?.close()
              this.characterCreationWs = null
              reject(new Error(data.error))
            }
          } catch (error) {
            console.error('Error parsing character creation message:', error)
            reject(error)
          }
        }
        
        this.characterCreationWs.onerror = (error) => {
          console.error('Character creation WebSocket error:', error)
          this.characterCreationWs?.close()
          this.characterCreationWs = null
          reject(new Error('Character creation WebSocket error'))
        }
        
        this.characterCreationWs.onclose = () => {
          console.log('Character creation WebSocket closed')
          // Don't attempt reconnect for character creation WebSocket
        }
      } catch (error) {
        reject(error)
      }
    })
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    if (this.characterCreationWs) {
      this.characterCreationWs.close()
      this.characterCreationWs = null
    }
  }
  
  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
      
      setTimeout(() => {
        this.connect().catch((error) => {
          console.error('Reconnection failed:', error)
        })
      }, this.reconnectDelay * this.reconnectAttempts)
    } else {
      console.error('Max reconnection attempts reached')
      this.onErrorHandler?.('Connection lost. Please refresh the page.')
    }
  }
  
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

export const websocketService = new WebSocketService()
