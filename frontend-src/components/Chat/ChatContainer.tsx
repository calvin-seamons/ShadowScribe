import { useState, useEffect, useRef } from 'react';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import ProgressIndicator from './ProgressIndicator';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useSessionStore } from '../../stores/sessionStore';
import type { Message, WebSocketData, Progress } from '../../types/index';

export const ChatContainer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentProgress, setCurrentProgress] = useState<Progress | null>(null);

  const { sessionId } = useSessionStore();
  const { sendMessage, lastMessage, connectionStatus } = useWebSocket(sessionId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Handle incoming WebSocket messages
    if (lastMessage) {
      try {
        const data: WebSocketData = JSON.parse(lastMessage);
        
        switch (data.type) {
          case 'acknowledgment':
            setIsProcessing(true);
            break;
            
          case 'progress':
            if (data.data.progress) {
              setCurrentProgress(data.data.progress);
            }
            break;
            
          case 'response':
            setIsProcessing(false);
            setCurrentProgress(null);
            if (data.data.response) {
              setMessages(prev => [...prev, {
                id: Date.now().toString(),
                type: 'assistant',
                content: data.data.response!,
                timestamp: new Date()
              }]);
            }
            break;
            
          case 'error':
            setIsProcessing(false);
            setCurrentProgress(null);
            setMessages(prev => [...prev, {
              id: Date.now().toString(),
              type: 'assistant',
              content: `Error: ${data.data.error || 'Unknown error'}`,
              timestamp: new Date()
            }]);
            break;
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (query: string) => {
    // Add user message to chat
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      type: 'user',
      content: query,
      timestamp: new Date()
    }]);

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
        {isProcessing && currentProgress && (
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
