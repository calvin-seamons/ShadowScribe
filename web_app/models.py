from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime


class SourcesResponse(BaseModel):
    """Response model for available sources endpoint."""
    sources: Dict[str, Any]
    status: str


class ValidationResponse(BaseModel):
    """Response model for system validation."""
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None


class CharacterSummary(BaseModel):
    """Character summary information."""
    name: str
    class_info: str
    race: str
    hit_points: Dict[str, int]
    armor_class: int
    key_stats: Dict[str, int]


class SessionHistoryItem(BaseModel):
    """Single item in session history."""
    query: str
    response: str
    timestamp: str


class SessionHistoryResponse(BaseModel):
    """Response model for session history."""
    session_id: str
    history: List[Dict[str, Any]]


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str  # 'query', 'progress', 'response', 'error'
    sessionId: str
    data: Dict[str, Any]
