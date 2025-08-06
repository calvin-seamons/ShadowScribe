"""
Response models for LLM interactions - hybrid approach with direct JSON parsing.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from enum import Enum
import json


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


# Direct JSON parsing classes - no Pydantic validation
class DirectCharacterTargeting:
    """Direct JSON approach for character targeting - bypasses function calling."""
    
    @staticmethod
    def parse_character_target(json_content: str) -> Dict[str, List[str]]:
        """Parse character targeting JSON response."""
        try:
            # Clean up response
            content = json_content.strip()
            
            # Remove code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            # Parse JSON
            result = json.loads(content)
            
            # Validate structure
            if not isinstance(result, dict):
                raise ValueError("Response must be a dictionary")
            
            # Validate file names
            valid_files = {
                "character.json", "inventory_list.json", "feats_and_traits.json",
                "spell_list.json", "action_list.json", "character_background.json",
                "objectives_and_contracts.json"
            }
            
            for filename in result.keys():
                if filename not in valid_files:
                    raise ValueError(f"Invalid filename: {filename}")
            
            return result
            
        except Exception as e:
            # Return fallback on any parsing error
            return DirectCharacterTargeting.create_keyword_fallback(json_content)
    
    @staticmethod
    def create_keyword_fallback(query: str) -> Dict[str, List[str]]:
        """Create smart fallback based on query keywords."""
        query_lower = query.lower()
        files = {}
        
        # Always include base character data
        files["character.json"] = ["character_base"]
        
        # Check for specific keywords
        if any(word in query_lower for word in 
               ["backstory", "background", "family", "parent", "mother", 
                "father", "thaldrin", "brenna", "history", "past", "story"]):
            files["character_background.json"] = [
                "backstory", 
                "backstory.family_backstory",
                "backstory.family_backstory.parents",
                "characteristics",
                "allies",
                "enemies"
            ]
        
        if any(word in query_lower for word in 
               ["spell", "cast", "magic", "slot", "cantrip"]):
            files["spell_list.json"] = ["character_spells"]
        
        if any(word in query_lower for word in 
               ["item", "equipment", "weapon", "armor", "eldaryth", "inventory"]):
            files["inventory_list.json"] = ["inventory"]
        
        if any(word in query_lower for word in 
               ["action", "attack", "damage", "combat", "smite", "fight"]):
            files["action_list.json"] = ["character_actions"]
        
        if any(word in query_lower for word in 
               ["feat", "trait", "feature", "ability", "class"]):
            files["feats_and_traits.json"] = ["features_and_traits"]
        
        if any(word in query_lower for word in 
               ["objective", "quest", "contract", "goal", "covenant", "mission"]):
            files["objectives_and_contracts.json"] = ["objectives_and_contracts"]
        
        # If no specific matches, include character_background as it's commonly needed
        if len(files) == 1:
            files["character_background.json"] = ["backstory", "characteristics"]
        
        return files


class CharacterTargetResponse(BaseModel):
    """Legacy Pydantic model - kept for compatibility."""
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