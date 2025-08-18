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
  const responseReceivedRef = useRef(false);

  const { sessionId } = useSessionStore();
  const { sendMessage, messageQueue, connectionStatus } = useWebSocket(sessionId);
  const { currentProgress, setCurrentProgress, setActiveSources, setLastUsedSources } = useProgress();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastProcessedIdRef = useRef(0);

  // Function to process a WebSocket message
  const processWebSocketMessage = (messageData: string) => {
    try {
      const data: WebSocketData = JSON.parse(messageData);
      console.log('[ChatContainer] Processing message type:', data.type);
      
      if (data.type === 'response') {
        console.log('[ChatContainer] >>> RESPONSE MESSAGE FOUND <<<');
      }
      
      switch (data.type) {
        case 'acknowledgment':
          setIsProcessing(true);
          responseReceivedRef.current = false;
          sourceUsageRef.current = {};
          setActiveSources([]);
          setLastUsedSources([]);
          break;
          
        case 'progress':
          if (responseReceivedRef.current) {
            console.log('[ChatContainer] Skipping progress - response already received');
            break;
          }
          
          if (data.data.progress) {
            setCurrentProgress(data.data.progress);
            const progress = data.data.progress;
            if (progress.metadata) {
              const metadata = progress.metadata;
              const currentUsage = sourceUsageRef.current;
              
              if (metadata.sources && Array.isArray(metadata.sources)) {
                currentUsage.sources = metadata.sources;
                setActiveSources(metadata.sources);
              }
              if (metadata.targets) {
                currentUsage.targets = metadata.targets;
              }
              if (metadata.content) {
                currentUsage.content = metadata.content;
              }
            }
          }
          break;
          
        case 'response':
          console.log('[ChatContainer] Processing response!');
          responseReceivedRef.current = true;
          setIsProcessing(false);
          
          const currentUsage = sourceUsageRef.current;
          if (currentUsage.sources && currentUsage.sources.length > 0) {
            setLastUsedSources(currentUsage.sources);
          }
          
          setCurrentProgress(null);
          setActiveSources([]);
          
          if (data.data.response) {
            let sourceUsage: QuerySourceUsage | undefined;
            
            if (data.data.sourceUsage) {
              sourceUsage = {
                sources: data.data.sourceUsage.sources || [],
                targets: data.data.sourceUsage.targets || {},
                content: data.data.sourceUsage.content || 'No content summary available',
                retrievedAt: typeof data.data.sourceUsage.retrievedAt === 'number' 
                  ? new Date(data.data.sourceUsage.retrievedAt * 1000) 
                  : new Date()
              };
            } else {
              const usage = sourceUsageRef.current;
              sourceUsage = usage.sources && usage.sources.length > 0
                ? {
                    sources: usage.sources,
                    targets: usage.targets || {},
                    content: usage.content || 'No content summary available',
                    retrievedAt: new Date()
                  }
                : undefined;
            }
            
            setMessages(prev => {
              const newMessage = {
                id: Date.now().toString(),
                type: 'assistant' as const,
                content: data.data.response!,
                timestamp: new Date(),
                sourceUsage
              };
              console.log('[ChatContainer] Adding message to state');
              return [...prev, newMessage];
            });
            
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
          sourceUsageRef.current = {};
          break;
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  };

  // Debug: Log when messages change
  useEffect(() => {
    console.log('[ChatContainer] Messages state changed:', messages, 'SessionId:', sessionId);
  }, [messages, sessionId]);

  // Process message queue
  useEffect(() => {
    if (messageQueue.length === 0) return;
    
    // Find unprocessed messages
    const unprocessed = messageQueue.filter(msg => msg.id > lastProcessedIdRef.current);
    if (unprocessed.length === 0) return;
    
    console.log(`[ChatContainer] Processing ${unprocessed.length} messages from queue`);
    
    // Process each message in order
    unprocessed.forEach(msg => {
      console.log(`[ChatContainer] Processing queued message ID: ${msg.id}`);
      processWebSocketMessage(msg.data);
      lastProcessedIdRef.current = msg.id;
    });
  }, [messageQueue, processWebSocketMessage]);

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
