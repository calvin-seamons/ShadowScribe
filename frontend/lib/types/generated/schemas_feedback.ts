/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

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
 * Statistics about collected feedback.
 */
export interface FeedbackStats {
  total_records: number;
  pending_review: number;
  confirmed_correct: number;
  corrected: number;
  exported: number;
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
 * Schema for creating a new routing feedback record.
 */
export interface RoutingRecord {
  /**
   * The original user query
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
 * Response schema for a routing feedback record.
 */
export interface RoutingRecordResponse {
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
