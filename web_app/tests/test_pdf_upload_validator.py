"""
Unit tests for PDF upload validation functionality
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import UploadFile
from io import BytesIO

from web_app.pdf_upload_validator import (
    PDFUploadValidator,
    ValidationResult
)


class TestPDFUploadValidator:
    """Test cases for PDFUploadValidator class"""
    
    @pytest.fixture
    def validator(self):
        """Create PDFUploadValidator instance for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield PDFUploadValidator(temp_storage_path=temp_dir)
    
    @pytest.fixture
    def valid_pdf_file(self):
        """Create a mock valid PDF UploadFile"""
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Character Sheet) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000189 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
284
%%EOF"""
        
        file_obj = BytesIO(pdf_content)
        
        # Create a mock UploadFile with proper content_type
        upload_file = Mock(spec=UploadFile)
        upload_file.filename = "test_character.pdf"
        upload_file.file = file_obj
        upload_file.size = len(pdf_content)
        upload_file.content_type = "application/pdf"
        upload_file.read = AsyncMock(side_effect=lambda size=None: file_obj.read(size))
        upload_file.seek = AsyncMock(side_effect=lambda pos: file_obj.seek(pos))
        
        return upload_file
    
    @pytest.fixture
    def invalid_pdf_file(self):
        """Create a mock invalid PDF UploadFile"""
        content = b"This is not a PDF file"
        file_obj = BytesIO(content)
        
        # Create a mock UploadFile with proper content_type
        upload_file = Mock(spec=UploadFile)
        upload_file.filename = "fake.pdf"
        upload_file.file = file_obj
        upload_file.size = len(content)
        upload_file.content_type = "application/pdf"
        upload_file.read = AsyncMock(side_effect=lambda size=None: file_obj.read(size))
        upload_file.seek = AsyncMock(side_effect=lambda pos: file_obj.seek(pos))
        
        return upload_file
    
    @pytest.mark.asyncio
    async def test_validate_upload_success(self, validator, valid_pdf_file):
        """Test successful upload validation"""
        result = await validator.validate_upload(valid_pdf_file, "test_user")
        
        assert result.is_valid is True
        assert result.error_message is None
        assert result.file_info is not None
        assert result.file_info['filename'] == "test_character.pdf"
        assert result.file_info['validation_passed'] is True
    
    @pytest.mark.asyncio
    async def test_validate_upload_no_file(self, validator):
        """Test validation with no file provided"""
        result = await validator.validate_upload(None, "test_user")
        
        assert result.is_valid is False
        assert "No file provided" in result.error_message
    
    @pytest.mark.asyncio
    async def test_validate_upload_empty_filename(self, validator):
        """Test validation with empty filename"""
        file_obj = BytesIO(b"content")
        upload_file = UploadFile(filename="", file=file_obj)
        
        result = await validator.validate_upload(upload_file, "test_user")
        
        assert result.is_valid is False
        assert "No file provided" in result.error_message
    
    @pytest.mark.asyncio
    async def test_validate_upload_wrong_extension(self, validator):
        """Test validation with wrong file extension"""
        file_obj = BytesIO(b"content")
        upload_file = UploadFile(
            filename="document.txt",
            file=file_obj,
            size=7
        )
        
        result = await validator.validate_upload(upload_file, "test_user")
        
        assert result.is_valid is False
        assert "Invalid file type" in result.error_message
        assert ".txt" in result.error_message
    
    @pytest.mark.asyncio
    async def test_validate_upload_file_too_large(self, validator):
        """Test validation with file too large"""
        # Create a large content
        large_content = b"x" * (validator.max_file_size + 1)
        file_obj = BytesIO(large_content)
        upload_file = UploadFile(
            filename="large.pdf",
            file=file_obj,
            size=len(large_content)
        )
        
        result = await validator.validate_upload(upload_file, "test_user")
        
        assert result.is_valid is False
        assert "File too large" in result.error_message
    
    @pytest.mark.asyncio
    async def test_validate_upload_empty_file(self, validator):
        """Test validation with empty file"""
        file_obj = BytesIO(b"")
        upload_file = UploadFile(
            filename="empty.pdf",
            file=file_obj,
            size=0
        )
        
        result = await validator.validate_upload(upload_file, "test_user")
        
        assert result.is_valid is False
        assert "File is empty" in result.error_message
    
    @pytest.mark.asyncio
    async def test_validate_upload_very_small_file_warning(self, validator):
        """Test validation with very small file generates warning"""
        small_content = b"x" * 500  # Less than 1KB
        file_obj = BytesIO(small_content)
        upload_file = Mock(spec=UploadFile)
        upload_file.filename = "small.pdf"
        upload_file.file = file_obj
        upload_file.size = len(small_content)
        upload_file.content_type = "application/pdf"
        upload_file.read = AsyncMock(side_effect=lambda size=None: file_obj.read(size))
        upload_file.seek = AsyncMock(side_effect=lambda pos: file_obj.seek(pos))
        
        # Mock the content validation to pass
        with patch.object(validator, '_validate_file_content') as mock_content:
            mock_content.return_value = ValidationResult(is_valid=True)
            
            result = await validator.validate_upload(upload_file, "test_user")
            
            assert result.is_valid is True
            assert any("very small" in warning for warning in result.warnings)
    
    @pytest.mark.asyncio
    async def test_validate_upload_invalid_content_type(self, validator):
        """Test validation with invalid content type"""
        file_obj = BytesIO(b"content")
        upload_file = Mock(spec=UploadFile)
        upload_file.filename = "document.pdf"
        upload_file.file = file_obj
        upload_file.size = 7
        upload_file.content_type = "text/plain"
        upload_file.read = AsyncMock(side_effect=lambda size=None: file_obj.read(size))
        upload_file.seek = AsyncMock(side_effect=lambda pos: file_obj.seek(pos))
        
        result = await validator.validate_upload(upload_file, "test_user")
        
        assert result.is_valid is False
        assert "Invalid content type" in result.error_message
    
    @pytest.mark.asyncio
    async def test_validate_upload_invalid_pdf_header(self, validator, invalid_pdf_file):
        """Test validation with invalid PDF header"""
        result = await validator.validate_upload(invalid_pdf_file, "test_user")
        
        assert result.is_valid is False
        assert "invalid header" in result.error_message
    
    def test_validate_filename_security_path_traversal(self, validator):
        """Test filename security validation for path traversal"""
        result = validator._validate_filename_security("../../../etc/passwd.pdf")
        
        assert result.is_valid is False
        assert "invalid characters" in result.error_message
    
    def test_validate_filename_security_command_injection(self, validator):
        """Test filename security validation for command injection"""
        result = validator._validate_filename_security("file|rm -rf /.pdf")
        
        assert result.is_valid is False
        assert "invalid characters" in result.error_message
    
    def test_validate_filename_security_script_injection(self, validator):
        """Test filename security validation for script injection"""
        result = validator._validate_filename_security("javascript:alert(1).pdf")
        
        assert result.is_valid is False
        assert "invalid characters" in result.error_message
    
    def test_validate_filename_security_null_bytes(self, validator):
        """Test filename security validation for null bytes"""
        result = validator._validate_filename_security("file\x00.pdf")
        
        assert result.is_valid is False
        assert "null bytes" in result.error_message
    
    def test_validate_filename_security_too_long(self, validator):
        """Test filename security validation for too long filename"""
        long_name = "a" * (validator.max_filename_length + 1) + ".pdf"
        result = validator._validate_filename_security(long_name)
        
        assert result.is_valid is False
        assert "too long" in result.error_message
    
    def test_validate_filename_security_valid(self, validator):
        """Test filename security validation with valid filename"""
        result = validator._validate_filename_security("character_sheet_v1.pdf")
        
        assert result.is_valid is True
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, validator, valid_pdf_file):
        """Test rate limiting functionality"""
        user_id = "test_user_rate_limit"
        
        # Exceed rate limit
        for i in range(validator.max_attempts_per_hour + 1):
            result = await validator.validate_upload(valid_pdf_file, user_id)
            
            if i < validator.max_attempts_per_hour:
                # Should succeed within limit
                assert result.is_valid is True or "Too many upload attempts" not in (result.error_message or "")
            else:
                # Should fail when exceeding limit
                assert result.is_valid is False
                assert "Too many upload attempts" in result.error_message
    
    def test_check_rate_limit_cleanup(self, validator):
        """Test rate limit cleanup of old entries"""
        user_id = "test_cleanup"
        
        # Add old entries
        old_time = datetime.utcnow() - timedelta(hours=2)
        validator.upload_attempts[user_id] = [old_time] * 5
        
        # Check rate limit (should clean old entries)
        result = validator._check_rate_limit(user_id)
        
        assert result is True
        assert len(validator.upload_attempts[user_id]) == 1  # Only the new entry
    
    @pytest.mark.asyncio
    async def test_save_validated_file(self, validator, valid_pdf_file):
        """Test saving validated file to temporary storage"""
        session_id = "test_session_123"
        
        file_path = await validator.save_validated_file(valid_pdf_file, session_id)
        
        assert os.path.exists(file_path)
        assert session_id in file_path
        assert file_path.endswith('.pdf')
        
        # Check file permissions (Unix-like systems)
        if hasattr(os, 'stat'):
            file_stat = os.stat(file_path)
            # Check that file is readable by owner
            assert file_stat.st_mode & 0o400  # Owner read permission
    
    @pytest.mark.asyncio
    async def test_save_validated_file_creates_directory(self, validator, valid_pdf_file):
        """Test that save_validated_file creates directory if needed"""
        # Use a non-existent subdirectory
        validator.temp_storage_path = os.path.join(validator.temp_storage_path, "subdir")
        session_id = "test_session_dir"
        
        file_path = await validator.save_validated_file(valid_pdf_file, session_id)
        
        assert os.path.exists(file_path)
        assert os.path.exists(os.path.dirname(file_path))
    
    def test_cleanup_temp_file(self, validator):
        """Test cleanup of temporary files"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            f.write(b"test content")
            temp_path = f.name
        
        # Verify file exists
        assert os.path.exists(temp_path)
        
        # Cleanup file
        result = validator.cleanup_temp_file(temp_path)
        
        assert result is True
        assert not os.path.exists(temp_path)
    
    def test_cleanup_temp_file_nonexistent(self, validator):
        """Test cleanup of non-existent file"""
        result = validator.cleanup_temp_file("/nonexistent/file.pdf")
        
        assert result is False
    
    def test_create_safe_filename(self, validator):
        """Test creation of safe filename"""
        original = "My Character Sheet (v2).pdf"
        session_id = "session_123"
        
        safe_name = validator._create_safe_filename(original, session_id)
        
        assert session_id in safe_name
        assert safe_name.endswith('.pdf')
        assert safe_name.startswith('pdf_upload_')
        assert len(safe_name) < 100  # Reasonable length
    
    def test_get_upload_stats_basic(self, validator):
        """Test getting basic upload statistics"""
        stats = validator.get_upload_stats()
        
        assert 'max_file_size_mb' in stats
        assert 'allowed_extensions' in stats
        assert 'max_attempts_per_hour' in stats
        assert stats['max_file_size_mb'] == 10.0
        assert '.pdf' in stats['allowed_extensions']
    
    def test_get_upload_stats_with_user(self, validator):
        """Test getting upload statistics for specific user"""
        user_id = "test_stats_user"
        
        # Add some recent attempts
        now = datetime.utcnow()
        validator.upload_attempts[user_id] = [now, now - timedelta(minutes=30)]
        
        stats = validator.get_upload_stats(user_id)
        
        assert 'user_attempts_last_hour' in stats
        assert 'remaining_attempts' in stats
        assert stats['user_attempts_last_hour'] == 2
        assert stats['remaining_attempts'] == validator.max_attempts_per_hour - 2


class TestValidationResult:
    """Test cases for ValidationResult dataclass"""
    
    def test_validation_result_creation(self):
        """Test creation of ValidationResult"""
        result = ValidationResult(
            is_valid=True,
            warnings=["Test warning"],
            file_info={"filename": "test.pdf"}
        )
        
        assert result.is_valid is True
        assert len(result.warnings) == 1
        assert result.file_info["filename"] == "test.pdf"
        assert result.error_message is None
    
    def test_validation_result_default_warnings(self):
        """Test ValidationResult with default warnings"""
        result = ValidationResult(is_valid=False, error_message="Test error")
        
        assert result.warnings == []
        assert result.error_message == "Test error"
    
    def test_validation_result_failure(self):
        """Test ValidationResult for failure case"""
        result = ValidationResult(
            is_valid=False,
            error_message="File validation failed",
            warnings=["Size warning", "Type warning"]
        )
        
        assert result.is_valid is False
        assert result.error_message == "File validation failed"
        assert len(result.warnings) == 2


class TestIntegrationScenarios:
    """Integration test scenarios for PDF upload validation"""
    
    @pytest.mark.asyncio
    async def test_complete_validation_workflow(self):
        """Test complete validation workflow from upload to cleanup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = PDFUploadValidator(temp_storage_path=temp_dir)
            
            # Create valid PDF content
            pdf_content = b"%PDF-1.4\n1 0 obj\n<</Type/Catalog>>\nendobj\nxref\n0 1\ntrailer<</Root 1 0 R>>\n%%EOF"
            file_obj = BytesIO(pdf_content)
            upload_file = Mock(spec=UploadFile)
            upload_file.filename = "character_sheet.pdf"
            upload_file.file = file_obj
            upload_file.size = len(pdf_content)
            upload_file.content_type = "application/pdf"
            upload_file.read = AsyncMock(side_effect=lambda size=None: file_obj.read(size))
            upload_file.seek = AsyncMock(side_effect=lambda pos: file_obj.seek(pos))
            
            # Validate upload
            validation_result = await validator.validate_upload(upload_file, "integration_user")
            assert validation_result.is_valid is True
            
            # Save file
            session_id = "integration_session"
            file_path = await validator.save_validated_file(upload_file, session_id)
            assert os.path.exists(file_path)
            
            # Cleanup file
            cleanup_result = validator.cleanup_temp_file(file_path)
            assert cleanup_result is True
            assert not os.path.exists(file_path)
    
    @pytest.mark.asyncio
    async def test_security_validation_comprehensive(self):
        """Test comprehensive security validation"""
        validator = PDFUploadValidator()
        
        # Test various malicious filenames
        malicious_filenames = [
            "../../../etc/passwd.pdf",
            "file|rm -rf /.pdf",
            "script.pdf<script>alert(1)</script>",
            "file\x00.pdf",
            "javascript:alert(1).pdf",
            "file&whoami.pdf"
        ]
        
        for filename in malicious_filenames:
            file_obj = BytesIO(b"content")
            upload_file = UploadFile(filename=filename, file=file_obj, size=7)
            
            result = await validator.validate_upload(upload_file, "security_test")
            assert result.is_valid is False, f"Should reject malicious filename: {filename}"
    
    @pytest.mark.asyncio
    async def test_mime_type_validation_comprehensive(self):
        """Test comprehensive MIME type validation"""
        validator = PDFUploadValidator()
        
        # Test various invalid MIME types
        invalid_types = [
            "text/plain",
            "image/jpeg",
            "application/msword",
            "text/html",
            "application/javascript"
        ]
        
        for content_type in invalid_types:
            file_obj = BytesIO(b"content")
            upload_file = Mock(spec=UploadFile)
            upload_file.filename = "test.pdf"
            upload_file.file = file_obj
            upload_file.size = 7
            upload_file.content_type = content_type
            upload_file.read = AsyncMock(side_effect=lambda size=None: file_obj.read(size))
            upload_file.seek = AsyncMock(side_effect=lambda pos: file_obj.seek(pos))
            
            result = await validator.validate_upload(upload_file, "mime_test")
            assert result.is_valid is False, f"Should reject invalid MIME type: {content_type}"
    
    @pytest.mark.asyncio
    async def test_file_size_edge_cases(self):
        """Test file size validation edge cases"""
        validator = PDFUploadValidator()
        
        # Test exactly at the limit
        max_size_content = b"x" * validator.max_file_size
        file_obj = BytesIO(max_size_content)
        upload_file = Mock(spec=UploadFile)
        upload_file.filename = "max_size.pdf"
        upload_file.file = file_obj
        upload_file.size = len(max_size_content)
        upload_file.content_type = "application/pdf"
        upload_file.read = AsyncMock(side_effect=lambda size=None: file_obj.read(size))
        upload_file.seek = AsyncMock(side_effect=lambda pos: file_obj.seek(pos))
        
        # Mock content validation to focus on size validation
        with patch.object(validator, '_validate_file_content') as mock_content:
            mock_content.return_value = ValidationResult(is_valid=True)
            
            result = await validator.validate_upload(upload_file, "size_test")
            assert result.is_valid is True, "Should accept file at exactly max size"