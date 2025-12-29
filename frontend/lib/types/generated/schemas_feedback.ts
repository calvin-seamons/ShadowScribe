/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

/**
 * Sources of context used for a query response.
 */
export interface ContextSources {
  /**
   * Character fields retrieved
   */
  character_fields?: string[] | null;
  /**
   * Rulebook sections retrieved
   */
  rulebook_sections?: string[] | null;
  /**
   * Session note IDs/titles retrieved
   */
  session_notes?: string[] | null;
}
/**
 * An extracted entity from the query.
 */
export interface EntityExtraction {
  /**
   * Canonical entity name
   */
  name: string;
  /**
   * Original text from query
   */
  text?: string;
  /**
   * Entity type (SPELL, NPC, etc)
   */
  type?: string;
  /**
   * Extraction confidence
   */
  confidence?: number;
}
/**
 * Statistics about collected query logs.
 */
export interface QueryLogStats {
  queries_total: number;
  queries_pending_review: number;
  queries_confirmed_correct: number;
  queries_corrected: number;
  queries_exported: number;
}
/**
 * Schema for submitting user feedback on routing.
 */
export interface FeedbackSubmission {
  /**
   * Whether the routing was correct
   */
  is_correct: boolean;
  /**
   * If incorrect, the correct tools+intentions
   */
  corrected_tools?: ToolCorrection[] | null;
  /**
   * Optional notes about the correction
   */
  feedback_notes?: string | null;
}
/**
 * A tool correction from the user.
 */
export interface ToolCorrection {
  /**
   * Tool name: character_data, session_notes, or rulebook
   */
  tool: string;
  /**
   * The correct intention for this tool
   */
  intention: string;
}
/**
 * Schema for creating a new query log record.
 */
export interface QueryLogRecord {
  /**
   * The normalized user query (with placeholders replaced)
   */
  user_query: string;
  /**
   * Character name for context
   */
  character_name: string;
  /**
   * Campaign ID
   */
  campaign_id?: string;
  /**
   * Model's tool predictions
   */
  predicted_tools: ToolPrediction[];
  /**
   * Extracted entities
   */
  predicted_entities?: EntityExtraction[] | null;
  /**
   * Backend: 'local' or 'llm'
   */
  classifier_backend?: string;
  /**
   * Inference time in ms
   */
  classifier_inference_time_ms?: number | null;
  /**
   * Original query before placeholder normalization
   */
  original_query?: string | null;
  /**
   * Full LLM response
   */
  assistant_response?: string | null;
  /**
   * Context sources used
   */
  context_sources?: ContextSources | null;
  /**
   * Total query-to-response time in ms
   */
  response_time_ms?: number | null;
  /**
   * LLM model used (e.g., 'claude-sonnet-4-20250514')
   */
  model_used?: string | null;
}
/**
 * A single tool prediction with intention and confidence.
 */
export interface ToolPrediction {
  /**
   * Tool name: character_data, session_notes, or rulebook
   */
  tool: string;
  /**
   * The intention/intent for this tool
   */
  intention: string;
  /**
   * Confidence score 0-1
   */
  confidence?: number;
}
/**
 * Response schema for a query log record.
 */
export interface QueryLogResponse {
  id: string;
  user_query: string;
  character_name: string;
  campaign_id: string;
  predicted_tools: ToolPrediction[];
  predicted_entities: EntityExtraction[] | null;
  classifier_backend: string;
  classifier_inference_time_ms: number | null;
  is_correct: boolean | null;
  corrected_tools: ToolCorrection[] | null;
  feedback_notes: string | null;
  created_at: string | null;
  feedback_at: string | null;
  original_query?: string | null;
  assistant_response?: string | null;
  context_sources?: ContextSources | null;
  response_time_ms?: number | null;
  model_used?: string | null;
}
/**
 * Available tools and their valid intentions.
 */
export interface ToolIntentionOptions {
  /**
   * Map of tool -> list of intentions
   */
  tools: {
    [k: string]: string[];
  };
}
/**
 * A single training example for the classifier.
 */
export interface TrainingExample {
  query: string;
  tool: string;
  intent: string;
  is_correction?: boolean;
}
/**
 * Request for exporting training data.
 */
export interface TrainingExportRequest {
  /**
   * If true, only export records with user corrections
   */
  include_corrections_only?: boolean;
  /**
   * If true, include records confirmed as correct
   */
  include_confirmed_correct?: boolean;
  /**
   * If true, mark exported records so they aren't re-exported
   */
  mark_as_exported?: boolean;
}
/**
 * Response containing exported training examples.
 */
export interface TrainingExportResponse {
  examples: TrainingExample[];
  total_records: number;
  corrections_count: number;
  confirmed_correct_count: number;
}
