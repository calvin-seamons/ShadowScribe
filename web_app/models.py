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


# File Management Models
class ConflictInfo(BaseModel):
    """Information about a file conflict."""
    type: str
    message: str
    severity: str  # 'warning', 'error', 'info'
    recommendation: str
    details: Optional[Dict[str, Any]] = None


class ConflictCheckResponse(BaseModel):
    """Response for conflict checking."""
    has_conflicts: bool
    conflicts: List[ConflictInfo]
    file_info: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    status: str


class ExportResponse(BaseModel):
    """Response for file export."""
    export_data: Dict[str, Any]
    filename: str
    status: str


class ImportRequest(BaseModel):
    """Request for file import."""
    export_data: Dict[str, Any]
    filename: Optional[str] = None
    overwrite: bool = False


class CharacterExportResponse(BaseModel):
    """Response for character export."""
    export_package: Dict[str, Any]
    character_name: str
    status: str


class CharacterImportRequest(BaseModel):
    """Request for character import."""
    export_package: Dict[str, Any]
    character_name: Optional[str] = None
    overwrite: bool = False


class CharacterImportResponse(BaseModel):
    """Response for character import."""
    character_name: str
    imported_files: List[str]
    failed_files: List[str]
    action: str
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


# PDF Import Models
class UncertainField(BaseModel):
    """Field with uncertain parsing results."""
    file_type: str
    field_path: str
    extracted_value: Any
    confidence: float
    suggestions: List[str]


class PDFImageResult(BaseModel):
    """Result of PDF to image conversion."""
    session_id: str
    images: List[str]  # Base64 encoded images or file IDs
    page_count: int
    image_format: str
    total_size_mb: float


class PDFImportSessionData(BaseModel):
    """PDF import session data for API responses."""
    session_id: str
    user_id: str
    created_at: str
    last_activity: str
    status: str
    pdf_filename: Optional[str] = None
    converted_images: Optional[List[str]] = None
    image_count: Optional[int] = None
    image_format: Optional[str] = None
    total_image_size_mb: Optional[float] = None
    parsed_data: Optional[Dict[str, Dict]] = None
    uncertain_fields: Optional[List[UncertainField]] = None
    parsing_confidence: Optional[float] = None
    validation_results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    progress: float = 0.0





class PDFUploadResponse(BaseModel):
    """Response for PDF upload."""
    session_id: str
    upload_url: Optional[str] = None
    status: str
    message: str


class PDFParseRequest(BaseModel):
    """Request for PDF vision parsing."""
    session_id: str
    images: Optional[List[str]] = None  # Optional override images for parsing


class PDFParseResponse(BaseModel):
    """Response for PDF parsing."""
    session_id: str
    character_files: Dict[str, Dict[str, Any]]
    uncertain_fields: List[UncertainField]
    parsing_confidence: float
    status: str


class PDFImportStatusResponse(BaseModel):
    """Response for PDF import status."""
    session_data: PDFImportSessionData
    status: str


class PDFImportCleanupResponse(BaseModel):
    """Response for PDF import cleanup."""
    session_id: str
    cleaned_up: bool
    status: str
    message: str
