import { useState, useEffect, useRef } from 'react';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import ProgressIndicator from './ProgressIndicator';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useSessionStore } from '../../stores/sessionStore';
import { useProgress } from '../../contexts/ProgressContext';
import type { Message, WebSocketData, QuerySourceUsage } from '../../types/index';

export const ChatContainer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const sourceUsageRef = useRef<Partial<QuerySourceUsage>>({});

  const { sessionId } = useSessionStore();
  const { sendMessage, lastMessage, connectionStatus } = useWebSocket(sessionId);
  const { currentProgress, setCurrentProgress, setActiveSources } = useProgress();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Handle incoming WebSocket messages
    if (lastMessage) {
      try {
        const data: WebSocketData = JSON.parse(lastMessage);
        
        switch (data.type) {
          case 'acknowledgment':
            setIsProcessing(true);
            // Reset source usage for new query
            sourceUsageRef.current = {};
            setActiveSources([]);
            break;
            
          case 'progress':
            if (data.data.progress) {
              setCurrentProgress(data.data.progress);
              
              // Capture source usage information from progress metadata
              const progress = data.data.progress;
              if (progress.metadata) {
                const metadata = progress.metadata;
                
                // Update source usage based on progress pass
                const currentUsage = sourceUsageRef.current;
                
                // Pass 1: Capture selected sources
                if (metadata.sources && Array.isArray(metadata.sources)) {
                  currentUsage.sources = metadata.sources;
                  setActiveSources(metadata.sources);
                }
                
                // Pass 2: Capture targets
                if (metadata.targets) {
                  currentUsage.targets = metadata.targets;
                }
                
                // Pass 3: Capture content summary
                if (metadata.content) {
                  currentUsage.content = metadata.content;
                }
              }
            }
            break;
            
          case 'response':
            setIsProcessing(false);
            setCurrentProgress(null);
            setActiveSources([]);
            if (data.data.response) {
              // Check if sourceUsage is provided in the response data
              let sourceUsage: QuerySourceUsage | undefined;
              
              if (data.data.sourceUsage) {
                // Use sourceUsage from response if available
                sourceUsage = {
                  sources: data.data.sourceUsage.sources || [],
                  targets: data.data.sourceUsage.targets || {},
                  content: data.data.sourceUsage.content || 'No content summary available',
                  retrievedAt: typeof data.data.sourceUsage.retrievedAt === 'number' 
                    ? new Date(data.data.sourceUsage.retrievedAt * 1000) 
                    : new Date()
                };
              } else {
                // Fallback to accumulated data from progress updates
                const currentUsage = sourceUsageRef.current;
                sourceUsage = 
                  currentUsage.sources && currentUsage.sources.length > 0
                    ? {
                        sources: currentUsage.sources,
                        targets: currentUsage.targets || {},
                        content: currentUsage.content || 'No content summary available',
                        retrievedAt: new Date()
                      }
                    : undefined;
              }
              
              setMessages(prev => [...prev, {
                id: Date.now().toString(),
                type: 'assistant',
                content: data.data.response!,
                timestamp: new Date(),
                sourceUsage
              }]);
              
              // Reset source usage after message is created
              sourceUsageRef.current = {};
            }
            break;
            
          case 'error':
            setIsProcessing(false);
            setCurrentProgress(null);
            setActiveSources([]);
            setMessages(prev => [...prev, {
              id: Date.now().toString(),
              type: 'assistant',
              content: `Error: ${data.data.error || 'Unknown error'}`,
              timestamp: new Date()
            }]);
            // Reset source usage on error
            sourceUsageRef.current = {};
            break;
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    }
  }, [lastMessage, setCurrentProgress, setActiveSources]);

  useEffect(() => {
    // Scroll to bottom when new messages arrive, with a small delay to ensure DOM is updated
    // Don't scroll if user is interacting with expanded elements
    const timeoutId = setTimeout(() => {
      const container = messagesEndRef.current?.parentElement;
      if (container) {
        const isAtBottom = container.scrollHeight - container.clientHeight <= container.scrollTop + 100;
        if (isAtBottom) {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
      }
    }, 100);
    
    return () => clearTimeout(timeoutId);
  }, [messages]);

  const handleSendMessage = (query: string) => {
    // Add user message to chat
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      type: 'user',
      content: query,
      timestamp: new Date()
    }]);

    // Reset progress state for new query
    setCurrentProgress(null);
    setIsProcessing(true);

    // Send via WebSocket
    sendMessage({
      type: 'query',
      sessionId,
      data: { query }
    });
  };

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Connection Status */}
      {connectionStatus !== 'connected' && (
        <div className="bg-yellow-600 text-white px-4 py-2 text-sm">
          {connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected - Attempting to reconnect...'}
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} />
        {isProcessing && (
          <div className="px-4 py-2">
            <ProgressIndicator progress={currentProgress} />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <MessageInput 
        onSendMessage={handleSendMessage} 
        disabled={isProcessing || connectionStatus !== 'connected'}
      />
    </div>
  );
};
