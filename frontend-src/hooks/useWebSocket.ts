import { useState, useEffect, useCallback, useRef } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8001/ws';

interface WebSocketMessage {
  type: string;
  sessionId?: string;
  data: any;
}

export function useWebSocket(sessionId: string) {
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [messageQueue, setMessageQueue] = useState<Array<{id: number, data: string}>>([]);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [messageCount, setMessageCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageIdRef = useRef(0);

  const connect = useCallback(() => {
    if (!sessionId) return;

    console.log('[useWebSocket] Connecting to sessionId:', sessionId);
    const ws = new WebSocket(`${WS_URL}/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionStatus('connected');
      console.log('[useWebSocket] WebSocket connected to session:', sessionId);
    };

    ws.onmessage = (event) => {
      const msgId = ++messageIdRef.current;
      
      console.log('[WebSocket] Message received:', event.data);
      // Parse and check message type for debugging
      try {
        const parsed = JSON.parse(event.data);
        console.log('[WebSocket] Message type:', parsed.type, 'ID:', msgId);
        if (parsed.type === 'response') {
          console.log('[WebSocket] RESPONSE MESSAGE DETECTED! ID:', msgId);
        }
      } catch (e) {
        console.error('[WebSocket] Failed to parse message for debugging');
      }
      
      // Add to message queue
      setMessageQueue(prev => [...prev, {id: msgId, data: event.data}]);
      // Also update lastMessage for backward compatibility
      setLastMessage(event.data);
      setMessageCount(prev => prev + 1);
    };

    ws.onclose = () => {
      setConnectionStatus('disconnected');
      console.log('WebSocket disconnected');
      
      // Attempt to reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return ws;
  }, [sessionId]);

  useEffect(() => {
    const ws = connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (ws) {
        ws.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }, []);

  return {
    connectionStatus,
    messageQueue,
    lastMessage,
    messageCount,
    sendMessage,
  };
}
