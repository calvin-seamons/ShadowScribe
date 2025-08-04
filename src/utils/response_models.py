"""
Pydantic models for enforcing LLM response structure.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from enum import Enum


class SourceTypeEnum(str, Enum):
    """Valid source types for LLM responses."""
    DND_RULEBOOK = "dnd_rulebook"
    CHARACTER_DATA = "character_data"
    SESSION_NOTES = "session_notes"


class SourceSelectionResponse(BaseModel):
    """Enforced structure for Pass 1 source selection."""
    sources_needed: List[SourceTypeEnum] = Field(
        ..., 
        description="List of required knowledge sources",
        min_items=1,
        max_items=3
    )
    reasoning: str = Field(
        ..., 
        description="Explanation of why each source is needed",
        min_length=10,
        max_length=500
    )
    
    @validator('sources_needed')
    def validate_sources(cls, v):
        if not v:
            raise ValueError("At least one source must be specified")
        return v


class RulebookTargetResponse(BaseModel):
    """Enforced structure for rulebook content targeting."""
    section_ids: List[str] = Field(
        default_factory=list,
        description="Specific section IDs to retrieve",
        max_items=10
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords to search for",
        max_items=10
    )
    reasoning: str = Field(
        ...,
        description="Why these sections will answer the query",
        min_length=10
    )
    
    @validator('section_ids', 'keywords')
    def validate_at_least_one_target(cls, v, values):
        # Ensure we have either section_ids or keywords
        section_ids = values.get('section_ids', []) if 'section_ids' in values else v
        keywords = values.get('keywords', []) if 'keywords' in values else v
        
        if not section_ids and not keywords:
            raise ValueError("Must specify either section_ids or keywords")
        return v


class CharacterTargetResponse(BaseModel):
    """Enforced structure for character data targeting."""
    file_fields: Dict[str, List[str]] = Field(
        ...,
        description="Mapping of filenames to required fields"
    )
    reasoning: str = Field(
        ...,
        description="Why these specific data points answer the query",
        min_length=10
    )
    
    @validator('file_fields')
    def validate_file_fields(cls, v):
        valid_files = {
            "character.json", "inventory_list.json", "feats_and_traits.json",
            "spell_list.json", "action_list.json", "character_background.json",
            "objectives_and_contracts.json"
        }
        
        for filename in v.keys():
            if filename not in valid_files:
                raise ValueError(f"Invalid filename: {filename}")
        
        if not v:
            raise ValueError("At least one file must be specified")
        return v


class SessionTargetResponse(BaseModel):
    """Enforced structure for session notes targeting."""
    session_dates: List[str] = Field(
        default_factory=list,
        description="Specific session dates to retrieve"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords to search within sessions"
    )
    reasoning: str = Field(
        ...,
        description="Why these sessions provide relevant context",
        min_length=10
    )
    
    @validator('session_dates', 'keywords')
    def validate_targeting(cls, v, values):
        session_dates = values.get('session_dates', []) if 'session_dates' in values else v
        keywords = values.get('keywords', []) if 'keywords' in values else v
        
        if not session_dates and not keywords:
            raise ValueError("Must specify either session_dates or keywords")
        return v