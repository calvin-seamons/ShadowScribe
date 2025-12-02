"""Pydantic schemas for routing feedback API."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ToolPrediction(BaseModel):
    """A single tool prediction with intention and confidence."""
    tool: str = Field(..., description="Tool name: character_data, session_notes, or rulebook")
    intention: str = Field(..., description="The intention/intent for this tool")
    confidence: float = Field(default=1.0, description="Confidence score 0-1")


class EntityExtraction(BaseModel):
    """An extracted entity from the query."""
    name: str = Field(..., description="Canonical entity name")
    text: str = Field(default="", description="Original text from query")
    type: str = Field(default="", description="Entity type (SPELL, NPC, etc)")
    confidence: float = Field(default=1.0, description="Extraction confidence")


class RoutingRecord(BaseModel):
    """Schema for creating a new routing feedback record."""
    user_query: str = Field(..., description="The original user query")
    character_name: str = Field(..., description="Character name for context")
    campaign_id: str = Field(default="main_campaign", description="Campaign ID")
    predicted_tools: List[ToolPrediction] = Field(..., description="Model's tool predictions")
    predicted_entities: Optional[List[EntityExtraction]] = Field(default=None, description="Extracted entities")
    classifier_backend: str = Field(default="local", description="Backend: 'local' or 'llm'")
    classifier_inference_time_ms: Optional[float] = Field(default=None, description="Inference time in ms")


class RoutingRecordResponse(BaseModel):
    """Response schema for a routing feedback record."""
    id: str
    user_query: str
    character_name: str
    campaign_id: str
    predicted_tools: List[Dict[str, Any]]
    predicted_entities: Optional[List[Dict[str, Any]]]
    classifier_backend: str
    classifier_inference_time_ms: Optional[float]
    is_correct: Optional[bool]
    corrected_tools: Optional[List[Dict[str, Any]]]
    feedback_notes: Optional[str]
    created_at: Optional[str]
    feedback_at: Optional[str]
    
    class Config:
        from_attributes = True


class ToolCorrection(BaseModel):
    """A tool correction from the user."""
    tool: str = Field(..., description="Tool name: character_data, session_notes, or rulebook")
    intention: str = Field(..., description="The correct intention for this tool")


class FeedbackSubmission(BaseModel):
    """Schema for submitting user feedback on routing."""
    is_correct: bool = Field(..., description="Whether the routing was correct")
    corrected_tools: Optional[List[ToolCorrection]] = Field(
        default=None, 
        description="If incorrect, the correct tools+intentions"
    )
    feedback_notes: Optional[str] = Field(
        default=None, 
        description="Optional notes about the correction"
    )


class ToolIntentionOptions(BaseModel):
    """Available tools and their valid intentions."""
    tools: Dict[str, List[str]] = Field(..., description="Map of tool -> list of intentions")


class TrainingExportRequest(BaseModel):
    """Request for exporting training data."""
    include_corrections_only: bool = Field(
        default=False, 
        description="If true, only export records with user corrections"
    )
    include_confirmed_correct: bool = Field(
        default=True,
        description="If true, include records confirmed as correct"
    )
    mark_as_exported: bool = Field(
        default=True,
        description="If true, mark exported records so they aren't re-exported"
    )


class TrainingExample(BaseModel):
    """A single training example for the classifier."""
    query: str
    tool: str
    intent: str
    is_correction: bool = False


class TrainingExportResponse(BaseModel):
    """Response containing exported training examples."""
    examples: List[TrainingExample]
    total_records: int
    corrections_count: int
    confirmed_correct_count: int


class FeedbackStats(BaseModel):
    """Statistics about collected feedback."""
    total_records: int
    pending_review: int
    confirmed_correct: int
    corrected: int
    exported: int
