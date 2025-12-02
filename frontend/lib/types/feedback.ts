/**
 * Types for routing feedback collection
 */

export interface ToolPrediction {
  tool: string;
  intention: string;
  confidence: number;
}

export interface EntityExtraction {
  name: string;
  text: string;
  type: string;
  confidence: number;
}

export interface RoutingRecord {
  id: string;
  user_query: string;
  character_name: string;
  campaign_id: string;
  predicted_tools: ToolPrediction[];
  predicted_entities: EntityExtraction[] | null;
  classifier_backend: string;
  classifier_inference_time_ms: number | null;
  is_correct: boolean | null;
  corrected_tools: ToolPrediction[] | null;
  feedback_notes: string | null;
  created_at: string | null;
  feedback_at: string | null;
}

export interface ToolCorrection {
  tool: string;
  intention: string;
}

export interface FeedbackSubmission {
  is_correct: boolean;
  corrected_tools?: ToolCorrection[];
  feedback_notes?: string;
}

export interface ToolIntentionOptions {
  tools: Record<string, string[]>;
}

export interface FeedbackStats {
  total_records: number;
  pending_review: number;
  confirmed_correct: number;
  corrected: number;
  exported: number;
}
