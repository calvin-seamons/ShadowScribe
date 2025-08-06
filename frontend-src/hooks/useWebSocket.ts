import { useState, useEffect, useCallback, useRef } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

interface WebSocketMessage {
  type: string;
  sessionId?: string;
  data: any;
}

export function useWebSocket(sessionId: string) {
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (!sessionId) return;

    const ws = new WebSocket(`${WS_URL}/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionStatus('connected');
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      setLastMessage(event.data);
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
    lastMessage,
    sendMessage,
  };
}
