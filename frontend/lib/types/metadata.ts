/**
 * Metadata types for RAG pipeline visualization
 */

export interface ToolInfo {
  tool: string;
  intention: string;
  confidence: number;
}

export interface EntityInfo {
  name: string;
  confidence: number;
}

export interface RoutingMetadata {
  tools_needed: ToolInfo[];
  entities: EntityInfo[];
  classifier_backend: 'llm' | 'local';
  normalized_query?: string;
  // Local classifier results (for comparison mode only)
  local_tools_needed?: ToolInfo[];
  local_inference_time_ms?: number;
}

export interface ResolvedEntity {
  name: string;
  found_in_sections: string[][];
  match_confidence: number[];
  match_strategy: string[];
}

export interface EntitiesMetadata {
  entities: ResolvedEntity[];
}

export interface RulebookSection {
  title: string;
  id: string;
  score: number;
}

export interface SessionNote {
  session_number: number;
  relevance_score: number;
}

export interface ContextSources {
  character_fields: string[];
  rulebook_sections: RulebookSection[];
  session_notes: SessionNote[];
}

export interface PerformanceMetrics {
  timing: {
    routing_and_entities?: number;
    entity_resolution?: number;
    rag_queries?: number;
    response_generation?: number;
    total?: number;
  };
}

export interface QueryMetadata {
  routing?: RoutingMetadata;
  entities?: EntitiesMetadata;
  sources?: ContextSources;
  performance?: PerformanceMetrics;
}
