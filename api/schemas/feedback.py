"""Pydantic schemas for query log API."""
from pydantic import BaseModel, ConfigDict, Field
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


class ToolCorrection(BaseModel):
    """A tool correction from the user."""
    tool: str = Field(..., description="Tool name: character_data, session_notes, or rulebook")
    intention: str = Field(..., description="The correct intention for this tool")


class ContextSources(BaseModel):
    """Sources of context used for a query response."""
    character_fields: Optional[List[str]] = Field(default=None, description="Character fields retrieved")
    rulebook_sections: Optional[List[str]] = Field(default=None, description="Rulebook sections retrieved")
    session_notes: Optional[List[str]] = Field(default=None, description="Session note IDs/titles retrieved")


class QueryLogRecord(BaseModel):
    """Schema for creating a new query log record."""
    user_query: str = Field(..., description="The normalized user query (with placeholders replaced)")
    character_name: str = Field(..., description="Character name for context")
    campaign_id: str = Field(default="main_campaign", description="Campaign ID")
    predicted_tools: List[ToolPrediction] = Field(..., description="Model's tool predictions")
    predicted_entities: Optional[List[EntityExtraction]] = Field(default=None, description="Extracted entities")
    classifier_backend: str = Field(default="local", description="Backend: 'local' or 'llm'")
    classifier_inference_time_ms: Optional[float] = Field(default=None, description="Inference time in ms")
    # New fields
    original_query: Optional[str] = Field(default=None, description="Original query before placeholder normalization")
    assistant_response: Optional[str] = Field(default=None, description="Full LLM response")
    context_sources: Optional[ContextSources] = Field(default=None, description="Context sources used")
    response_time_ms: Optional[float] = Field(default=None, description="Total query-to-response time in ms")
    model_used: Optional[str] = Field(default=None, description="LLM model used (e.g., 'claude-sonnet-4-20250514')")


# Backward compatibility alias
RoutingRecord = QueryLogRecord


class QueryLogResponse(BaseModel):
    """Response schema for a query log record."""
    id: str
    user_query: str
    character_name: str
    campaign_id: str
    predicted_tools: List[ToolPrediction]
    predicted_entities: Optional[List[EntityExtraction]]
    classifier_backend: str
    classifier_inference_time_ms: Optional[float]
    is_correct: Optional[bool]
    corrected_tools: Optional[List[ToolCorrection]]
    feedback_notes: Optional[str]
    created_at: Optional[str]
    feedback_at: Optional[str]
    # New fields
    original_query: Optional[str] = None
    assistant_response: Optional[str] = None
    context_sources: Optional[ContextSources] = None
    response_time_ms: Optional[float] = None
    model_used: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Backward compatibility alias
RoutingRecordResponse = QueryLogResponse


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


class QueryLogStats(BaseModel):
    """Statistics about collected query logs."""
    queries_total: int
    queries_pending_review: int
    queries_confirmed_correct: int
    queries_corrected: int
    queries_exported: int


# Backward compatibility alias
FeedbackStats = QueryLogStats
