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
  sourceUsage?: QuerySourceUsage;
}

export interface SourceUsage {
  source: string;
  targets?: string[] | Record<string, string[]>;
  content?: string;
  summary?: string;
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

export interface QuerySourceUsage {
  sources: string[];
  targets: Record<string, any>;
  content: string | Record<string, any>;
  retrievedAt: Date;
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
    sourceUsage?: QuerySourceUsage;
  };
}

export interface ModelInfo {
  current_model: string;
  available_models: string[];
  status: string;
}

// Knowledge Base Types
export interface KnowledgeBaseFile {
  filename: string;
  file_type: 'character' | 'character_background' | 'feats_and_traits' | 'action_list' | 'inventory_list' | 'objectives_and_contracts' | 'spell_list' | 'other';
  size: number;
  last_modified: string;
  is_editable: boolean;
}

export interface FileContent {
  filename: string;
  content: Record<string, any>;
  schema_version?: string;
}

export interface ValidationError {
  field_path: string;
  message: string;
  error_type: 'required' | 'type' | 'format' | 'custom';
}

export interface ValidationResult {
  is_valid: boolean;
  errors: ValidationError[];
  warnings: string[];
}

export interface BackupInfo {
  backup_id: string;
  filename: string;
  created_at: string;
  size: number;
}

export interface CharacterCreationRequest {
  character_name: string;
  race: string;
  character_class: string;
  level?: number;
  background?: string;
  alignment?: string;
  ability_scores?: Record<string, number>;
}

export interface CharacterCreationResponse {
  character_name: string;
  files_created: string[];
  status: string;
  message: string;
}

// PDF Import Types
export interface PDFExtractionResult {
  session_id: string;
  extracted_text: string;
  page_count: number;
  structure_info: PDFStructureInfo;
  confidence_score: number;
}

export interface PDFStructureInfo {
  has_form_fields: boolean;
  has_tables: boolean;
  detected_format: string; // 'dnd_beyond', 'roll20', 'handwritten', 'unknown'
  text_quality: string; // 'high', 'medium', 'low'
}

export interface CharacterParseResult {
  session_id: string;
  character_files: Record<string, Record<string, any>>;
  uncertain_fields: UncertainField[];
  parsing_confidence: number;
  validation_results: Record<string, ValidationResult>;
}

export interface UncertainField {
  file_type: string;
  field_path: string;
  extracted_value: any;
  confidence: number;
  suggestions: string[];
}

export interface PDFImportSession {
  session_id: string;
  status: 'upload' | 'extract' | 'parse' | 'review' | 'finalize';
  progress: number;
  extracted_text?: string;
  parsed_data?: ParsedCharacterData;
}

export interface ParsedCharacterData {
  character_files: Record<string, Record<string, any>>;
  uncertain_fields: UncertainField[];
  parsing_confidence: number;
  validation_results: Record<string, ValidationResult>;
}
