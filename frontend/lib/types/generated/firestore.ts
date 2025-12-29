/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

/**
 * Campaign document for Firestore.
 */
export interface CampaignDocument {
  id: string;
  name: string;
  description?: string | null;
  created_at?: string | null;
}
/**
 * Character document for Firestore.
 */
export interface CharacterDocument {
  id: string;
  user_id: string;
  name: string;
  data: {
    [k: string]: unknown;
  };
  campaign_id: string;
  race?: string | null;
  character_class?: string | null;
  level?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}
/**
 * Statistics for query logs.
 */
export interface QueryLogStats {
  queries_total?: number;
  queries_pending_review?: number;
  queries_confirmed_correct?: number;
  queries_corrected?: number;
  queries_exported?: number;
}
/**
 * Query log document for Firestore - captures full query/response cycle.
 */
export interface QueryLogDocument {
  id: string;
  user_query: string;
  character_name: string;
  predicted_tools: {
    [k: string]: unknown;
  }[];
  campaign_id?: string;
  predicted_entities?:
    | {
        [k: string]: unknown;
      }[]
    | null;
  classifier_backend?: string;
  classifier_inference_time_ms?: number | null;
  original_query?: string | null;
  assistant_response?: string | null;
  context_sources?: {
    [k: string]: unknown;
  } | null;
  response_time_ms?: number | null;
  model_used?: string | null;
  is_correct?: boolean | null;
  corrected_tools?:
    | {
        [k: string]: unknown;
      }[]
    | null;
  feedback_notes?: string | null;
  created_at?: string | null;
  feedback_at?: string | null;
  exported_for_training?: boolean;
  exported_at?: string | null;
}
/**
 * Session document for Firestore AND RAG queries.
 *
 * Stored at: campaigns/{campaign_id}/sessions/{session_id}
 *
 * This is the single source of truth for session data - used both for
 * Firestore persistence and in-memory RAG queries. No serialization layer.
 */
export interface SessionDocument {
  id: string;
  campaign_id: string;
  user_id: string;
  session_number: number;
  session_name: string;
  raw_content?: string;
  processed_markdown?: string;
  title?: string;
  summary?: string;
  player_characters?: {
    [k: string]: unknown;
  }[];
  npcs?: {
    [k: string]: unknown;
  }[];
  locations?: {
    [k: string]: unknown;
  }[];
  items?: {
    [k: string]: unknown;
  }[];
  key_events?: {
    [k: string]: unknown;
  }[];
  combat_encounters?: {
    [k: string]: unknown;
  }[];
  spells_abilities_used?: {
    [k: string]: unknown;
  }[];
  character_decisions?: {
    [k: string]: unknown;
  }[];
  character_statuses?: {
    [k: string]: unknown;
  };
  memories_visions?: {
    [k: string]: unknown;
  }[];
  quest_updates?: {
    [k: string]: unknown;
  }[];
  loot_obtained?: {
    [k: string]: unknown;
  };
  deaths?: {
    [k: string]: unknown;
  }[];
  revivals?: {
    [k: string]: unknown;
  }[];
  party_conflicts?: string[];
  party_bonds?: string[];
  quotes?: {
    [k: string]: unknown;
  }[];
  funny_moments?: string[];
  puzzles_encountered?: {
    [k: string]: unknown;
  };
  mysteries_revealed?: string[];
  unresolved_questions?: string[];
  divine_interventions?: string[];
  religious_elements?: string[];
  rules_clarifications?: string[];
  dice_rolls?: {
    [k: string]: unknown;
  }[];
  cliffhanger?: string | null;
  next_session_hook?: string | null;
  dm_notes?: string[];
  raw_sections?: {
    [k: string]: unknown;
  };
  date?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}
/**
 * User document for Firestore.
 */
export interface UserDocument {
  id: string;
  email: string;
  display_name?: string | null;
  created_at?: string | null;
}
