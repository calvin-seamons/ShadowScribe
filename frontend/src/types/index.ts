export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface Progress {
  pass: number;
  status: string;
  details: string;
  metadata?: Record<string, any>;
}

export interface WebSocketData {
  type: 'acknowledgment' | 'progress' | 'response' | 'error';
  sessionId: string;
  data: {
    status?: string;
    progress?: Progress;
    response?: string;
    error?: string;
  };
}

export interface WebSocketMessage {
  type: 'query';
  sessionId: string;
  data: {
    query: string;
  };
}
