"""
PDF Import Session Manager

Manages temporary sessions for PDF character import workflow including:
- Session creation and lifecycle management
- Temporary file storage and cleanup
- Progress tracking and state management
- Automatic session timeout and cleanup
"""

import os
import json
import uuid
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PDFImportStatus(Enum):
    """PDF import session status states."""
    CREATED = "created"
    UPLOADED = "uploaded"
    CONVERTED = "converted"  # Changed from EXTRACTED to CONVERTED for images
    PARSED = "parsed"
    REVIEWED = "reviewed"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class PDFImportSession:
    """PDF import session data structure."""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    status: PDFImportStatus
    pdf_filename: Optional[str] = None
    pdf_file_path: Optional[str] = None
    converted_images: Optional[List[str]] = None  # Changed from extracted_text to converted_images
    image_count: Optional[int] = None  # Number of images converted
    image_format: Optional[str] = None  # Format of converted images (PNG/JPEG)
    total_image_size_mb: Optional[float] = None  # Total size of all images
    temp_image_files: Optional[List[str]] = None  # Temporary image file paths for cleanup
    parsed_data: Optional[Dict[str, Dict]] = None
    uncertain_fields: Optional[List[Dict]] = None
    parsing_confidence: Optional[float] = None
    validation_results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    progress: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for JSON serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PDFImportSession':
        """Create session from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        data['status'] = PDFImportStatus(data['status'])
        return cls(**data)
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()


class PDFImportSessionManager:
    """
    Manages PDF import sessions with secure temporary storage and automatic cleanup.
    
    Features:
    - Session lifecycle management
    - Secure temporary file storage
    - Automatic cleanup and timeout handling
    - Progress tracking and state management
    """
    
    def __init__(
        self,
        temp_storage_path: str = None,
        session_timeout_hours: int = 2,
        cleanup_interval_minutes: int = 30,
        max_file_size_mb: int = 10
    ):
        """
        Initialize the PDF import session manager.
        
        Args:
            temp_storage_path: Path for temporary file storage
            session_timeout_hours: Hours before session expires
            cleanup_interval_minutes: Minutes between cleanup runs
            max_file_size_mb: Maximum PDF file size in MB
        """
        self.temp_storage_path = Path(temp_storage_path or tempfile.gettempdir()) / "pdf_import_sessions"
        self.session_timeout = timedelta(hours=session_timeout_hours)
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes
        
        # In-memory session cache
        self.sessions: Dict[str, PDFImportSession] = {}
        
        # Create storage directories
        self._ensure_storage_directories()
        
        # Load existing sessions
        self._load_existing_sessions()
        
        # Start cleanup task
        self._cleanup_task = None
        self._auto_start_cleanup = True
    
    def _ensure_storage_directories(self):
        """Create necessary storage directories."""
        self.temp_storage_path.mkdir(parents=True, exist_ok=True)
        (self.temp_storage_path / "sessions").mkdir(exist_ok=True)
        (self.temp_storage_path / "files").mkdir(exist_ok=True)
    
    def _load_existing_sessions(self):
        """Load existing sessions from disk."""
        sessions_dir = self.temp_storage_path / "sessions"
        if not sessions_dir.exists():
            return
        
        for session_file in sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    session = PDFImportSession.from_dict(session_data)
                    self.sessions[session.session_id] = session
                    logger.info(f"Loaded existing session: {session.session_id}")
            except Exception as e:
                logger.error(f"Error loading session from {session_file}: {e}")
                # Remove corrupted session file
                try:
                    session_file.unlink()
                except:
                    pass
    
    def _start_cleanup_task(self):
        """Start the automatic cleanup background task."""
        if self._auto_start_cleanup and (self._cleanup_task is None or self._cleanup_task.done()):
            try:
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            except RuntimeError:
                # No event loop running, will start later when needed
                pass
    
    async def _cleanup_loop(self):
        """Background task for automatic session cleanup."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def create_session(self, user_id: str) -> str:
        """
        Create a new PDF import session.
        
        Args:
            user_id: Identifier for the user creating the session
            
        Returns:
            session_id: Unique identifier for the created session
        """
        # Start cleanup task if not already running
        self._start_cleanup_task()
        
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session = PDFImportSession(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now,
            status=PDFImportStatus.CREATED
        )
        
        self.sessions[session_id] = session
        await self._save_session(session_id)
        
        logger.info(f"Created PDF import session: {session_id} for user: {user_id}")
        return session_id
    
    async def store_pdf_content(self, session_id: str, content: bytes, filename: str) -> str:
        """
        Store uploaded PDF content securely.
        
        Args:
            session_id: Session identifier
            content: PDF file content as bytes
            filename: Original filename
            
        Returns:
            file_path: Path to stored file
            
        Raises:
            ValueError: If session not found or file too large
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Validate file size
        if len(content) > self.max_file_size:
            raise ValueError(f"File too large: {len(content)} bytes (max: {self.max_file_size})")
        
        # Create secure file path
        safe_filename = self._sanitize_filename(filename)
        file_path = self.temp_storage_path / "files" / f"{session_id}_{safe_filename}"
        
        # Store file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Update session
        session.pdf_filename = filename
        session.pdf_file_path = str(file_path)
        session.status = PDFImportStatus.UPLOADED
        session.progress = 10.0
        session.update_activity()
        
        await self._save_session(session_id)
        
        logger.info(f"Stored PDF content for session {session_id}: {filename}")
        return str(file_path)
    
    async def store_converted_images(
        self,
        session_id: str,
        images: List[str],
        image_format: str = "PNG",
        total_size_mb: float = 0.0
    ):
        """
        Store converted PDF images.
        
        Args:
            session_id: Session identifier
            images: List of base64 encoded images or file IDs
            image_format: Format of the images (PNG/JPEG)
            total_size_mb: Total size of all images in MB
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        session.converted_images = images
        session.image_count = len(images)
        session.image_format = image_format
        session.total_image_size_mb = total_size_mb
        session.status = PDFImportStatus.CONVERTED
        session.progress = 30.0
        session.update_activity()
        
        await self._save_session(session_id)
        
        logger.info(f"Stored {len(images)} converted images for session {session_id}")
    
    async def get_converted_images(self, session_id: str) -> Optional[List[str]]:
        """
        Get converted images for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of base64 encoded images or file IDs, None if not found
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        return session.converted_images
    
    async def store_image_files(self, session_id: str, image_files: List[str]):
        """
        Store temporary image file paths for cleanup.
        
        Args:
            session_id: Session identifier
            image_files: List of temporary image file paths
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Store image file paths in session for cleanup
        if session.temp_image_files is None:
            session.temp_image_files = []
        
        session.temp_image_files.extend(image_files)
        session.update_activity()
        
        await self._save_session(session_id)
        
        logger.info(f"Stored {len(image_files)} temporary image file paths for session {session_id}")
    
    async def cleanup_image_files(self, session_id: str):
        """
        Clean up temporary image files for a session.
        
        Args:
            session_id: Session identifier
        """
        # Get session directly from memory to avoid recursion
        session = self.sessions.get(session_id)
        if not session:
            return
        
        # Clean up temporary image files if they exist
        if session.temp_image_files:
            for image_file in session.temp_image_files:
                if os.path.exists(image_file):
                    try:
                        os.remove(image_file)
                        logger.debug(f"Removed temporary image file: {image_file}")
                    except Exception as e:
                        logger.error(f"Error removing image file {image_file}: {e}")
            
            # Clear the list after cleanup
            session.temp_image_files = []
            await self._save_session(session_id)
    
    async def store_parsed_data(
        self,
        session_id: str,
        parsed_data: Dict[str, Dict],
        uncertain_fields: List[Dict] = None,
        parsing_confidence: float = None,
        validation_results: Dict[str, Any] = None
    ):
        """
        Store LLM parsed character data.
        
        Args:
            session_id: Session identifier
            parsed_data: Parsed character data by file type
            uncertain_fields: List of fields with low confidence
            parsing_confidence: Overall parsing confidence score
            validation_results: Schema validation results
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        session.parsed_data = parsed_data
        session.uncertain_fields = uncertain_fields or []
        session.parsing_confidence = parsing_confidence
        session.validation_results = validation_results
        session.status = PDFImportStatus.PARSED
        session.progress = 70.0
        session.update_activity()
        
        await self._save_session(session_id)
        
        logger.info(f"Stored parsed data for session {session_id}")
    
    async def update_session_status(
        self,
        session_id: str,
        status: PDFImportStatus,
        progress: float = None,
        error_message: str = None
    ):
        """
        Update session status and progress.
        
        Args:
            session_id: Session identifier
            status: New session status
            progress: Progress percentage (0-100)
            error_message: Error message if status is FAILED
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        session.status = status
        if progress is not None:
            session.progress = progress
        if error_message is not None:
            session.error_message = error_message
        session.update_activity()
        
        await self._save_session(session_id)
        
        logger.info(f"Updated session {session_id} status to {status.value}")
    
    async def get_session(self, session_id: str) -> Optional[PDFImportSession]:
        """
        Get session data by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            PDFImportSession or None if not found
        """
        session = self.sessions.get(session_id)
        if session:
            # Check if session has expired
            if self._is_session_expired(session):
                await self.cleanup_session(session_id)
                return None
        return session
    
    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data as dictionary.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dictionary or None if not found
        """
        session = await self.get_session(session_id)
        return session.to_dict() if session else None
    
    async def cleanup_session(self, session_id: str):
        """
        Clean up a specific session and its associated files.
        
        Args:
            session_id: Session identifier
        """
        session = self.sessions.get(session_id)
        if not session:
            return
        
        # Clean up temporary image files first
        await self.cleanup_image_files(session_id)
        
        # Remove PDF file if exists
        if session.pdf_file_path and os.path.exists(session.pdf_file_path):
            try:
                os.remove(session.pdf_file_path)
                logger.info(f"Removed PDF file: {session.pdf_file_path}")
            except Exception as e:
                logger.error(f"Error removing PDF file {session.pdf_file_path}: {e}")
        
        # Remove session file
        session_file = self.temp_storage_path / "sessions" / f"{session_id}.json"
        if session_file.exists():
            try:
                session_file.unlink()
                logger.info(f"Removed session file: {session_file}")
            except Exception as e:
                logger.error(f"Error removing session file {session_file}: {e}")
        
        # Remove from memory
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        logger.info(f"Cleaned up session: {session_id}")
    
    async def cleanup_expired_sessions(self):
        """Clean up all expired sessions."""
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.cleanup_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def _is_session_expired(self, session: PDFImportSession) -> bool:
        """Check if a session has expired."""
        return datetime.now() - session.last_activity > self.session_timeout
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for secure storage."""
        # Remove path components and dangerous characters
        safe_name = os.path.basename(filename)
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._ -")
        
        # Ensure it has a reasonable length
        if len(safe_name) > 100:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:95] + ext
        
        # Ensure it's not empty
        if not safe_name:
            safe_name = "uploaded_file.pdf"
        
        return safe_name
    
    async def _save_session(self, session_id: str):
        """Save session data to disk."""
        session = self.sessions.get(session_id)
        if not session:
            return
        
        session_file = self.temp_storage_path / "sessions" / f"{session_id}.json"
        try:
            with open(session_file, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")
    
    async def get_active_sessions(self, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get list of active sessions, optionally filtered by user.
        
        Args:
            user_id: Optional user ID filter
            
        Returns:
            List of session data dictionaries
        """
        sessions = []
        for session in self.sessions.values():
            if not self._is_session_expired(session):
                if user_id is None or session.user_id == user_id:
                    sessions.append(session.to_dict())
        
        # Sort by last activity (most recent first)
        sessions.sort(key=lambda x: x['last_activity'], reverse=True)
        return sessions
    
    async def shutdown(self):
        """Shutdown the session manager and cleanup resources."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("PDF import session manager shutdown complete")


# Global session manager instance
_session_manager: Optional[PDFImportSessionManager] = None


def get_session_manager() -> PDFImportSessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = PDFImportSessionManager()
    return _session_manager


async def initialize_session_manager(
    temp_storage_path: str = None,
    session_timeout_hours: int = 2,
    cleanup_interval_minutes: int = 30,
    max_file_size_mb: int = 10
):
    """Initialize the global session manager with custom settings."""
    global _session_manager
    if _session_manager is not None:
        await _session_manager.shutdown()
    
    _session_manager = PDFImportSessionManager(
        temp_storage_path=temp_storage_path,
        session_timeout_hours=session_timeout_hours,
        cleanup_interval_minutes=cleanup_interval_minutes,
        max_file_size_mb=max_file_size_mb
    )
    
    return _session_manager