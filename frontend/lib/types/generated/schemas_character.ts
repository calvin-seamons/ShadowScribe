/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

/**
 * Request schema for creating a new character.
 */
export interface CharacterCreateRequest {
  /**
   * Complete Character dataclass as JSON dictionary
   */
  character: {
    [k: string]: unknown;
  };
  /**
   * ID of the campaign to assign this character to (required)
   */
  campaign_id: string;
}
/**
 * Character list response schema.
 */
export interface CharacterListResponse {
  characters: CharacterResponse[];
}
/**
 * Character response schema.
 */
export interface CharacterResponse {
  id: string;
  user_id?: string | null;
  campaign_id?: string | null;
  name: string;
  race?: string | null;
  character_class?: string | null;
  level?: number | null;
  data: {
    [k: string]: unknown;
  };
  created_at?: string | null;
  updated_at?: string | null;
}
/**
 * Request schema for full character update.
 */
export interface CharacterUpdateRequest {
  /**
   * Complete Character dataclass as JSON dictionary
   */
  character: {
    [k: string]: unknown;
  };
}
/**
 * Request schema for fetching character from D&D Beyond.
 */
export interface FetchCharacterRequest {
  url: string;
}
/**
 * Response schema for fetched D&D Beyond character data.
 */
export interface FetchCharacterResponse {
  json_data: {
    [k: string]: unknown;
  };
  character_id: string;
}
/**
 * Request schema for partial section update.
 */
export interface SectionUpdateRequest {
  /**
   * Section-specific data to update
   */
  data: {
    [k: string]: unknown;
  };
}
/**
 * Response schema for section update.
 */
export interface SectionUpdateResponse {
  updated: boolean;
  section: string;
  message?: string | null;
}
