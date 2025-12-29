/**
 * Service for routing feedback API interactions
 */

import type {
  QueryLogResponse,
  FeedbackSubmission,
  ToolIntentionOptions,
  QueryLogStats,
  ToolPrediction,
  EntityExtraction
} from '../types/feedback';

// API URL configuration (same logic as api.ts)
function getApiUrl(): string {
  // Check for explicit API URL first (production)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // Development: use localhost with backend port
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1') {
      return `http://${host}:8000`;
    }
    return `${window.location.protocol}//${host}:8000`;
  }

  return 'http://localhost:8000';
}

export class FeedbackService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${getApiUrl()}/api/feedback`;
  }

  /**
   * Get available tools and their valid intentions
   */
  async getToolIntentions(): Promise<ToolIntentionOptions> {
    const response = await fetch(`${this.baseUrl}/tools`);
    if (!response.ok) {
      throw new Error('Failed to fetch tool intentions');
    }
    return response.json();
  }

  /**
   * Record a routing decision for later review
   */
  async recordRouting(
    userQuery: string,
    characterName: string,
    predictedTools: ToolPrediction[],
    predictedEntities: EntityExtraction[] | null,
    classifierBackend: string = 'local',
    inferenceTimeMs: number | null = null,
    campaignId: string = 'main_campaign'
  ): Promise<QueryLogResponse> {
    const response = await fetch(`${this.baseUrl}/record`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_query: userQuery,
        character_name: characterName,
        campaign_id: campaignId,
        predicted_tools: predictedTools,
        predicted_entities: predictedEntities,
        classifier_backend: classifierBackend,
        classifier_inference_time_ms: inferenceTimeMs
      })
    });

    if (!response.ok) {
      throw new Error('Failed to record routing');
    }
    return response.json();
  }

  /**
   * Get pending feedback records
   */
  async getPendingFeedback(limit: number = 50): Promise<QueryLogResponse[]> {
    const response = await fetch(`${this.baseUrl}/pending?limit=${limit}`);
    if (!response.ok) {
      throw new Error('Failed to fetch pending feedback');
    }
    return response.json();
  }

  /**
   * Get recent routing records
   */
  async getRecentRecords(limit: number = 100): Promise<QueryLogResponse[]> {
    const response = await fetch(`${this.baseUrl}/recent?limit=${limit}`);
    if (!response.ok) {
      throw new Error('Failed to fetch recent records');
    }
    return response.json();
  }

  /**
   * Get a specific routing record
   */
  async getRecord(feedbackId: string): Promise<QueryLogResponse> {
    const response = await fetch(`${this.baseUrl}/record/${feedbackId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch routing record');
    }
    return response.json();
  }

  /**
   * Submit feedback on a routing decision
   */
  async submitFeedback(
    feedbackId: string,
    submission: FeedbackSubmission
  ): Promise<QueryLogResponse> {
    const response = await fetch(`${this.baseUrl}/record/${feedbackId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(submission)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit feedback');
    }
    return response.json();
  }

  /**
   * Get feedback collection statistics
   */
  async getStats(): Promise<QueryLogStats> {
    const response = await fetch(`${this.baseUrl}/stats`);
    if (!response.ok) {
      throw new Error('Failed to fetch feedback stats');
    }
    return response.json();
  }
}

export const feedbackService = new FeedbackService();
