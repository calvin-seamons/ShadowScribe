"""Pydantic schemas for character API."""
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any


class CharacterResponse(BaseModel):
    """Character response schema."""
    id: str
    user_id: Optional[str] = None
    campaign_id: Optional[str] = None
    name: str
    race: Optional[str] = None
    character_class: Optional[str] = None
    level: Optional[int] = None
    data: Dict[str, Any]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CharacterListResponse(BaseModel):
    """Character list response schema."""
    characters: List[CharacterResponse]


class FetchCharacterRequest(BaseModel):
    """Request schema for fetching character from D&D Beyond."""
    url: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://www.dndbeyond.com/characters/152248393"
            }
        }
    )


class FetchCharacterResponse(BaseModel):
    """Response schema for fetched D&D Beyond character data."""
    json_data: Dict[str, Any]
    character_id: str


class CharacterCreateRequest(BaseModel):
    """Request schema for creating a new character."""
    character: Dict[str, Any] = Field(
        ...,
        description="Complete Character dataclass as JSON dictionary"
    )
    campaign_id: str = Field(
        ...,
        description="ID of the campaign to assign this character to (required)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "campaign_id": "abc123-uuid",
                "character": {
                    "character_base": {
                        "name": "Duskryn Nightwarden",
                        "race": "Drow",
                        "character_class": "Ranger",
                        "total_level": 10
                    },
                    "ability_scores": {
                        "strength": 12,
                        "dexterity": 18,
                        "constitution": 14,
                        "intelligence": 10,
                        "wisdom": 16,
                        "charisma": 8
                    }
                }
            }
        }
    )


class CharacterUpdateRequest(BaseModel):
    """Request schema for full character update."""
    character: Dict[str, Any] = Field(
        ...,
        description="Complete Character dataclass as JSON dictionary"
    )


class SectionUpdateRequest(BaseModel):
    """Request schema for partial section update."""
    data: Dict[str, Any] = Field(
        ...,
        description="Section-specific data to update"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "strength": 14,
                    "dexterity": 18,
                    "constitution": 16,
                    "intelligence": 10,
                    "wisdom": 15,
                    "charisma": 8
                }
            }
        }
    )


class SectionUpdateResponse(BaseModel):
    """Response schema for section update."""
    updated: bool
    section: str
    message: Optional[str] = None
