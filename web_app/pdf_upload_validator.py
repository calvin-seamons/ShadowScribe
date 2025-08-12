"""
PDF Upload Validation and Security Service

This module provides comprehensive validation and security measures
for PDF file uploads in the character import feature.
"""

import os
import tempfile
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of file validation"""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    file_info: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class PDFUploadValidator:
    """
    Comprehensive PDF upload validation with security measures
    """
    
    def __init__(self, temp_storage_path: str = None):
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_mime_types = {
            'application/pdf',
            'application/x-pdf',
            'application/acrobat',
            'applications/vnd.pdf',
            'text/pdf',
            'text/x-pdf'
        }
        self.allowed_extensions = {'.pdf'}
        self.temp_storage_path = temp_storage_path or tempfile.gettempdir()
        
        # Security settings
        self.max_filename_length = 255
        self.blocked_filename_patterns = [
            '../', '..\\', './', '.\\',  # Path traversal
            '<', '>', '|', '&', ';',     # Command injection
            'script', 'javascript',       # Script injection
        ]
        
        # Rate limiting (simple in-memory store)
        self.upload_attempts = {}
        self.max_attempts_per_hour = 10
    
    async def validate_upload(self, file: UploadFile, user_id: str = None) -> ValidationResult:
        """
        Comprehensive validation of uploaded PDF file
        
        Args:
            file: FastAPI UploadFile object
            user_id: Optional user identifier for rate limiting
            
        Returns:
            ValidationResult with validation status and details
        """
        try:
            # Rate limiting check
            if user_id and not self._check_rate_limit(user_id):
                return ValidationResult(
                    is_valid=False,
                    error_message="Too many upload attempts. Please try again later."
                )
            
            # Basic file validation
            basic_validation = self._validate_basic_properties(file)
            if not basic_validation.is_valid:
                return basic_validation
            
            # Filename security validation
            filename_validation = self._validate_filename_security(file.filename)
            if not filename_validation.is_valid:
                return filename_validation
            
            # MIME type validation
            mime_validation = await self._validate_mime_type(file)
            if not mime_validation.is_valid:
                return mime_validation
            
            # File content validation
            content_validation = await self._validate_file_content(file)
            if not content_validation.is_valid:
                return content_validation
            
            # Compile file information
            file_info = {
                'filename': file.filename,
                'size': file.size,
                'content_type': file.content_type,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'validation_passed': True
            }
            
            # Collect all warnings
            all_warnings = []
            for validation in [basic_validation, filename_validation, mime_validation, content_validation]:
                all_warnings.extend(validation.warnings)
            
            return ValidationResult(
                is_valid=True,
                warnings=all_warnings,
                file_info=file_info
            )
            
        except Exception as e:
            logger.error(f"Upload validation error: {str(e)}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation failed: {str(e)}"
            )
    
    async def save_validated_file(self, file: UploadFile, session_id: str) -> str:
        """
        Save validated file to secure temporary storage
        
        Args:
            file: Validated UploadFile object
            session_id: Unique session identifier
            
        Returns:
            Path to saved file
        """
        try:
            # Create secure filename
            safe_filename = self._create_safe_filename(file.filename, session_id)
            file_path = os.path.join(self.temp_storage_path, safe_filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save file with security measures
            with open(file_path, 'wb') as f:
                # Read file in chunks to prevent memory issues
                chunk_size = 8192
                while chunk := await file.read(chunk_size):
                    f.write(chunk)
            
            # Reset file position for potential re-reading
            await file.seek(0)
            
            # Set restrictive file permissions
            os.chmod(file_path, 0o600)  # Read/write for owner only
            
            logger.info(f"File saved securely: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"File save error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    def cleanup_temp_file(self, file_path: str) -> bool:
        """
        Securely delete temporary file
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                # Overwrite file content before deletion (basic security measure)
                file_size = os.path.getsize(file_path)
                with open(file_path, 'wb') as f:
                    f.write(b'\x00' * file_size)
                
                # Delete file
                os.remove(file_path)
                logger.info(f"Temporary file cleaned up: {file_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"File cleanup error: {str(e)}")
            return False
    
    def _validate_basic_properties(self, file: UploadFile) -> ValidationResult:
        """Validate basic file properties"""
        warnings = []
        
        # Check if file is provided
        if not file or not file.filename:
            return ValidationResult(
                is_valid=False,
                error_message="No file provided"
            )
        
        # Check file size
        if hasattr(file, 'size') and file.size is not None:
            if file.size > self.max_file_size:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB"
                )
            
            if file.size == 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="File is empty"
                )
            
            # Warning for very small files
            if file.size < 1024:  # Less than 1KB
                warnings.append("File is very small and may not contain sufficient character data")
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid file type. Only PDF files are allowed. Got: {file_ext}"
            )
        
        return ValidationResult(is_valid=True, warnings=warnings)
    
    def _validate_filename_security(self, filename: str) -> ValidationResult:
        """Validate filename for security issues"""
        if not filename:
            return ValidationResult(
                is_valid=False,
                error_message="Filename is required"
            )
        
        # Check filename length
        if len(filename) > self.max_filename_length:
            return ValidationResult(
                is_valid=False,
                error_message=f"Filename too long. Maximum: {self.max_filename_length} characters"
            )
        
        # Check for blocked patterns
        filename_lower = filename.lower()
        for pattern in self.blocked_filename_patterns:
            if pattern in filename_lower:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Filename contains invalid characters or patterns"
                )
        
        # Check for null bytes
        if '\x00' in filename:
            return ValidationResult(
                is_valid=False,
                error_message="Filename contains invalid null bytes"
            )
        
        return ValidationResult(is_valid=True)
    
    async def _validate_mime_type(self, file: UploadFile) -> ValidationResult:
        """Validate MIME type"""
        warnings = []
        
        # Check declared content type
        if file.content_type and file.content_type not in self.allowed_mime_types:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid content type: {file.content_type}. Expected PDF."
            )
        
        # Guess MIME type from filename
        guessed_type, _ = mimetypes.guess_type(file.filename)
        if guessed_type and guessed_type not in self.allowed_mime_types:
            warnings.append(f"Filename suggests non-PDF type: {guessed_type}")
        
        return ValidationResult(is_valid=True, warnings=warnings)
    
    async def _validate_file_content(self, file: UploadFile) -> ValidationResult:
        """Validate actual file content"""
        try:
            # Read first few bytes to check PDF signature
            initial_position = file.file.tell()
            header = await file.read(8)
            await file.seek(initial_position)  # Reset position
            
            # PDF files should start with %PDF-
            if not header.startswith(b'%PDF-'):
                return ValidationResult(
                    is_valid=False,
                    error_message="File does not appear to be a valid PDF (invalid header)"
                )
            
            # Check PDF version
            if len(header) >= 8:
                try:
                    version_part = header[5:8].decode('ascii')
                    if version_part not in ['1.0', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '2.0']:
                        # Don't fail, just warn
                        pass
                except:
                    pass  # Version check is not critical
            
            return ValidationResult(is_valid=True)
            
        except Exception as e:
            logger.error(f"Content validation error: {str(e)}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Failed to validate file content: {str(e)}"
            )
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit"""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        if user_id in self.upload_attempts:
            self.upload_attempts[user_id] = [
                timestamp for timestamp in self.upload_attempts[user_id]
                if timestamp > hour_ago
            ]
        else:
            self.upload_attempts[user_id] = []
        
        # Check current count
        current_attempts = len(self.upload_attempts[user_id])
        if current_attempts >= self.max_attempts_per_hour:
            return False
        
        # Record this attempt
        self.upload_attempts[user_id].append(now)
        return True
    
    def _create_safe_filename(self, original_filename: str, session_id: str) -> str:
        """Create a safe filename for temporary storage"""
        # Extract extension
        ext = Path(original_filename).suffix.lower()
        
        # Create hash of original filename for uniqueness
        filename_hash = hashlib.md5(original_filename.encode()).hexdigest()[:8]
        
        # Create safe filename with session ID
        safe_name = f"pdf_upload_{session_id}_{filename_hash}{ext}"
        
        return safe_name
    
    def get_upload_stats(self, user_id: str = None) -> Dict[str, Any]:
        """Get upload statistics for monitoring"""
        stats = {
            'max_file_size_mb': self.max_file_size / (1024 * 1024),
            'allowed_extensions': list(self.allowed_extensions),
            'max_attempts_per_hour': self.max_attempts_per_hour
        }
        
        if user_id and user_id in self.upload_attempts:
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            recent_attempts = [
                timestamp for timestamp in self.upload_attempts[user_id]
                if timestamp > hour_ago
            ]
            stats['user_attempts_last_hour'] = len(recent_attempts)
            stats['remaining_attempts'] = max(0, self.max_attempts_per_hour - len(recent_attempts))
        
        return stats