from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime


# Knowledge Base Models
class KnowledgeBaseFile(BaseModel):
    """Information about a knowledge base file."""
    filename: str
    file_type: str  # 'character', 'character_background', 'feats_and_traits', etc.
    size: int
    last_modified: datetime
    is_editable: bool


class FileContent(BaseModel):
    """Content of a knowledge base file."""
    filename: str
    content: Dict[str, Any]
    schema_version: Optional[str] = "1.0"


class ValidationError(BaseModel):
    """Validation error details."""
    field_path: str
    message: str
    error_type: str  # 'required', 'type', 'format', 'custom'


class ValidationResult(BaseModel):
    """Result of file validation."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[str]


class BackupInfo(BaseModel):
    """Information about a backup file."""
    backup_id: str
    filename: str
    created_at: datetime
    size: int


class FileListResponse(BaseModel):
    """Response for listing knowledge base files."""
    files: List[KnowledgeBaseFile]
    status: str


class FileContentResponse(BaseModel):
    """Response for getting file content."""
    content: FileContent
    status: str


class FileUpdateRequest(BaseModel):
    """Request for updating file content."""
    content: Dict[str, Any]


class FileCreateRequest(BaseModel):
    """Request for creating a new file."""
    filename: str
    content: Dict[str, Any]


class ValidationResponse(BaseModel):
    """Response for file validation."""
    result: ValidationResult
    status: str


class BackupListResponse(BaseModel):
    """Response for listing backups."""
    backups: List[BackupInfo]
    status: str


class SchemaResponse(BaseModel):
    """Response for getting JSON schema."""
    json_schema: Dict[str, Any]
    file_type: str
    status: str


class TemplateResponse(BaseModel):
    """Response for getting file template."""
    template: Dict[str, Any]
    file_type: str
    status: str


# Character Creation Models
class CharacterCreationRequest(BaseModel):
    """Request for creating a new character with all files."""
    character_name: str
    race: str
    character_class: str
    level: int = 1
    background: str = ""
    alignment: str = ""
    ability_scores: Optional[Dict[str, int]] = None


class CharacterCreationResponse(BaseModel):
    """Response for character creation."""
    character_name: str
    files_created: List[str]
    status: str
    message: str


# Existing Models
class SourcesResponse(BaseModel):
    """Response model for available sources endpoint."""
    sources: Dict[str, Any]
    status: str


class SystemValidationResponse(BaseModel):
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


class ModelUpdateRequest(BaseModel):
    """Request model for updating the OpenAI model."""
    model: str


class ModelResponse(BaseModel):
    """Response model for model information."""
    current_model: str
    available_models: List[str]
    status: str
