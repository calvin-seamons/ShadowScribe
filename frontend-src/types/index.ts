export interface SourceDetails {
  count: number | string;
  description?: string;
}

export interface Character {
  name: string;
  class_info: string;
  race: string;
  hit_points: {
    current: number;
    max: number;
  };
  armor_class: number;
  key_stats: Record<string, number>;
}

export interface HistoryItem {
  query: string;
  response: string;
  timestamp: string;
}

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface Progress {
  pass: number;
  status: 'starting' | 'complete' | 'error' | 'unknown';
  stage?: string;
  message: string;
  details?: string;
  metadata?: any;
  timestamp?: number;
}

export interface WebSocketData {
  type: 'query' | 'progress' | 'response' | 'error' | 'acknowledgment';
  sessionId: string;
  data: {
    query?: string;
    response?: string;
    error?: string;
    status?: string;
    progress?: Progress;
  };
}

export interface ModelInfo {
  current_model: string;
  available_models: string[];
  status: string;
}
