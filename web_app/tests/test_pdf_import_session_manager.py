"""
Tests for PDF Import Session Manager

Tests cover:
- Session creation and lifecycle management
- Temporary file storage and cleanup
- Session timeout and expiration handling
- Progress tracking and state management
- Error handling and edge cases
"""

import pytest
import asyncio
import tempfile
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from web_app.pdf_import_session_manager import (
    PDFImportSessionManager,
    PDFImportSession,
    PDFImportStatus,
    get_session_manager,
    initialize_session_manager
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def session_manager(temp_dir):
    """Create a session manager for testing."""
    manager = PDFImportSessionManager(
        temp_storage_path=temp_dir,
        session_timeout_hours=1,
        cleanup_interval_minutes=1,
        max_file_size_mb=5
    )
    # Disable auto-cleanup for testing
    manager._auto_start_cleanup = False
    return manager


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return b"Sample PDF content for testing"


@pytest.fixture
def sample_parsed_data():
    """Sample parsed character data for testing."""
    return {
        "character.json": {
            "name": "Test Character",
            "race": "Human",
            "class": "Fighter",
            "level": 1
        },
        "spell_list.json": {
            "spells": []
        }
    }


class TestPDFImportSession:
    """Test PDFImportSession data class."""
    
    def test_session_creation(self):
        """Test creating a new session."""
        session_id = "test-session-123"
        user_id = "user-456"
        now = datetime.now()
        
        session = PDFImportSession(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now,
            status=PDFImportStatus.CREATED
        )
        
        assert session.session_id == session_id
        assert session.user_id == user_id
        assert session.status == PDFImportStatus.CREATED
        assert session.progress == 0.0
    
    def test_session_to_dict(self):
        """Test converting session to dictionary."""
        now = datetime.now()
        session = PDFImportSession(
            session_id="test-123",
            user_id="user-456",
            created_at=now,
            last_activity=now,
            status=PDFImportStatus.UPLOADED,
            progress=25.0
        )
        
        data = session.to_dict()
        
        assert data['session_id'] == "test-123"
        assert data['user_id'] == "user-456"
        assert data['status'] == "uploaded"
        assert data['progress'] == 25.0
        assert 'created_at' in data
        assert 'last_activity' in data
    
    def test_session_from_dict(self):
        """Test creating session from dictionary."""
        now = datetime.now()
        data = {
            'session_id': "test-123",
            'user_id': "user-456",
            'created_at': now.isoformat(),
            'last_activity': now.isoformat(),
            'status': "parsed",
            'progress': 75.0
        }
        
        session = PDFImportSession.from_dict(data)
        
        assert session.session_id == "test-123"
        assert session.user_id == "user-456"
        assert session.status == PDFImportStatus.PARSED
        assert session.progress == 75.0
    
    def test_update_activity(self):
        """Test updating session activity timestamp."""
        import time
        now = datetime.now()
        session = PDFImportSession(
            session_id="test-123",
            user_id="user-456",
            created_at=now,
            last_activity=now,
            status=PDFImportStatus.CREATED
        )
        
        original_activity = session.last_activity
        time.sleep(0.001)  # Small delay to ensure different timestamp
        session.update_activity()
        
        assert session.last_activity > original_activity


class TestPDFImportSessionManager:
    """Test PDFImportSessionManager functionality."""
    
    @pytest.mark.asyncio
    async def test_session_manager_initialization(self, temp_dir):
        """Test session manager initialization."""
        manager = PDFImportSessionManager(
            temp_storage_path=temp_dir,
            session_timeout_hours=2,
            max_file_size_mb=10
        )
        
        assert manager.temp_storage_path == Path(temp_dir) / "pdf_import_sessions"
        assert manager.session_timeout == timedelta(hours=2)
        assert manager.max_file_size == 10 * 1024 * 1024
        assert len(manager.sessions) == 0
        
        # Check directories were created
        assert (manager.temp_storage_path / "sessions").exists()
        assert (manager.temp_storage_path / "files").exists()
        
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """Test creating a new session."""
        user_id = "test-user-123"
        
        session_id = await session_manager.create_session(user_id)
        
        assert session_id is not None
        assert len(session_id) > 0
        assert session_id in session_manager.sessions
        
        session = session_manager.sessions[session_id]
        assert session.user_id == user_id
        assert session.status == PDFImportStatus.CREATED
        assert session.progress == 0.0
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_store_pdf_content(self, session_manager, sample_pdf_content):
        """Test storing PDF content."""
        user_id = "test-user-123"
        filename = "test_character.pdf"
        
        session_id = await session_manager.create_session(user_id)
        file_path = await session_manager.store_pdf_content(
            session_id, sample_pdf_content, filename
        )
        
        # Check file was stored
        assert os.path.exists(file_path)
        with open(file_path, 'rb') as f:
            stored_content = f.read()
        assert stored_content == sample_pdf_content
        
        # Check session was updated
        session = await session_manager.get_session(session_id)
        assert session.pdf_filename == filename
        assert session.pdf_file_path == file_path
        assert session.status == PDFImportStatus.UPLOADED
        assert session.progress == 10.0
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_store_pdf_content_file_too_large(self, session_manager):
        """Test storing PDF content that exceeds size limit."""
        user_id = "test-user-123"
        filename = "large_file.pdf"
        large_content = b"x" * (6 * 1024 * 1024)  # 6MB (exceeds 5MB limit)
        
        session_id = await session_manager.create_session(user_id)
        
        with pytest.raises(ValueError, match="File too large"):
            await session_manager.store_pdf_content(
                session_id, large_content, filename
            )
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_store_converted_images(self, session_manager):
        """Test storing converted images."""
        user_id = "test-user-123"
        converted_images = [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA4849a6wAAAABJRU5ErkJggg=="
        ]
        image_format = "PNG"
        total_size_mb = 0.5
        
        session_id = await session_manager.create_session(user_id)
        await session_manager.store_converted_images(
            session_id, converted_images, image_format, total_size_mb
        )
        
        session = await session_manager.get_session(session_id)
        assert session.converted_images == converted_images
        assert session.image_count == 2
        assert session.image_format == image_format
        assert session.total_image_size_mb == total_size_mb
        assert session.status == PDFImportStatus.CONVERTED
        assert session.progress == 30.0
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_get_converted_images(self, session_manager):
        """Test retrieving converted images."""
        user_id = "test-user-123"
        converted_images = [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        ]
        
        session_id = await session_manager.create_session(user_id)
        await session_manager.store_converted_images(session_id, converted_images)
        
        # Test retrieving images
        retrieved_images = await session_manager.get_converted_images(session_id)
        assert retrieved_images == converted_images
        
        # Test non-existent session
        non_existent_images = await session_manager.get_converted_images("non-existent")
        assert non_existent_images is None
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_store_and_cleanup_image_files(self, session_manager, temp_dir):
        """Test storing and cleaning up temporary image files."""
        import tempfile
        
        user_id = "test-user-123"
        
        # Create temporary image files
        temp_files = []
        for i in range(2):
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f"_page_{i}.png", 
                dir=temp_dir, 
                delete=False
            )
            temp_file.write(b"fake image data")
            temp_file.close()
            temp_files.append(temp_file.name)
        
        session_id = await session_manager.create_session(user_id)
        
        # Store image file paths
        await session_manager.store_image_files(session_id, temp_files)
        
        # Verify files exist
        for temp_file in temp_files:
            assert os.path.exists(temp_file)
        
        # Verify session has the file paths
        session = await session_manager.get_session(session_id)
        assert session.temp_image_files == temp_files
        
        # Clean up image files
        await session_manager.cleanup_image_files(session_id)
        
        # Verify files are removed
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)
        
        # Verify session list is cleared
        session = await session_manager.get_session(session_id)
        assert session.temp_image_files == []
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_store_parsed_data(self, session_manager, sample_parsed_data):
        """Test storing parsed character data."""
        user_id = "test-user-123"
        uncertain_fields = [
            {
                "file_type": "character.json",
                "field_path": "background",
                "extracted_value": "Unknown",
                "confidence": 0.3,
                "suggestions": ["Folk Hero", "Soldier"]
            }
        ]
        parsing_confidence = 0.85
        validation_results = {"character.json": {"is_valid": True, "errors": []}}
        
        session_id = await session_manager.create_session(user_id)
        await session_manager.store_parsed_data(
            session_id,
            sample_parsed_data,
            uncertain_fields,
            parsing_confidence,
            validation_results
        )
        
        session = await session_manager.get_session(session_id)
        assert session.parsed_data == sample_parsed_data
        assert session.uncertain_fields == uncertain_fields
        assert session.parsing_confidence == parsing_confidence
        assert session.validation_results == validation_results
        assert session.status == PDFImportStatus.PARSED
        assert session.progress == 70.0
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_update_session_status(self, session_manager):
        """Test updating session status and progress."""
        user_id = "test-user-123"
        
        session_id = await session_manager.create_session(user_id)
        await session_manager.update_session_status(
            session_id,
            PDFImportStatus.COMPLETED,
            progress=100.0
        )
        
        session = await session_manager.get_session(session_id)
        assert session.status == PDFImportStatus.COMPLETED
        assert session.progress == 100.0
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_update_session_status_with_error(self, session_manager):
        """Test updating session status with error message."""
        user_id = "test-user-123"
        error_message = "Failed to parse PDF content"
        
        session_id = await session_manager.create_session(user_id)
        await session_manager.update_session_status(
            session_id,
            PDFImportStatus.FAILED,
            error_message=error_message
        )
        
        session = await session_manager.get_session(session_id)
        assert session.status == PDFImportStatus.FAILED
        assert session.error_message == error_message
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_get_session_nonexistent(self, session_manager):
        """Test getting a non-existent session."""
        session = await session_manager.get_session("nonexistent-session")
        assert session is None
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_get_session_data(self, session_manager):
        """Test getting session data as dictionary."""
        user_id = "test-user-123"
        
        session_id = await session_manager.create_session(user_id)
        session_data = await session_manager.get_session_data(session_id)
        
        assert session_data is not None
        assert session_data['session_id'] == session_id
        assert session_data['user_id'] == user_id
        assert session_data['status'] == "created"
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_cleanup_session_with_images(self, session_manager, sample_pdf_content, temp_dir):
        """Test cleaning up a session with both PDF and image files."""
        import tempfile
        
        user_id = "test-user-123"
        filename = "test_character.pdf"
        
        # Create temporary image files
        temp_files = []
        for i in range(2):
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f"_page_{i}.png", 
                dir=temp_dir, 
                delete=False
            )
            temp_file.write(b"fake image data")
            temp_file.close()
            temp_files.append(temp_file.name)
        
        session_id = await session_manager.create_session(user_id)
        
        # Store PDF and image files
        pdf_path = await session_manager.store_pdf_content(
            session_id, sample_pdf_content, filename
        )
        await session_manager.store_image_files(session_id, temp_files)
        
        # Verify all files exist
        assert os.path.exists(pdf_path)
        for temp_file in temp_files:
            assert os.path.exists(temp_file)
        assert session_id in session_manager.sessions
        
        # Clean up session
        await session_manager.cleanup_session(session_id)
        
        # Verify all cleanup
        assert not os.path.exists(pdf_path)
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)
        assert session_id not in session_manager.sessions
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_cleanup_session(self, session_manager, sample_pdf_content):
        """Test cleaning up a session and its files."""
        user_id = "test-user-123"
        filename = "test_character.pdf"
        
        session_id = await session_manager.create_session(user_id)
        file_path = await session_manager.store_pdf_content(
            session_id, sample_pdf_content, filename
        )
        
        # Verify file exists
        assert os.path.exists(file_path)
        assert session_id in session_manager.sessions
        
        # Clean up session
        await session_manager.cleanup_session(session_id)
        
        # Verify cleanup
        assert not os.path.exists(file_path)
        assert session_id not in session_manager.sessions
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_session_expiration(self, temp_dir):
        """Test session expiration and cleanup."""
        # Create manager with very short timeout
        manager = PDFImportSessionManager(
            temp_storage_path=temp_dir,
            session_timeout_hours=0.001,  # ~3.6 seconds
            cleanup_interval_minutes=0.01  # ~0.6 seconds
        )
        
        user_id = "test-user-123"
        session_id = await manager.create_session(user_id)
        
        # Session should exist initially
        session = await manager.get_session(session_id)
        assert session is not None
        
        # Wait for session to expire
        await asyncio.sleep(4)
        
        # Session should be expired and return None
        session = await manager.get_session(session_id)
        assert session is None
        
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, temp_dir):
        """Test automatic cleanup of expired sessions."""
        manager = PDFImportSessionManager(
            temp_storage_path=temp_dir,
            session_timeout_hours=0.001,  # Very short timeout
            cleanup_interval_minutes=60  # Don't auto-cleanup
        )
        
        # Create multiple sessions
        user_id = "test-user-123"
        session_ids = []
        for i in range(3):
            session_id = await manager.create_session(f"{user_id}-{i}")
            session_ids.append(session_id)
        
        assert len(manager.sessions) == 3
        
        # Wait for sessions to expire
        await asyncio.sleep(4)
        
        # Manually trigger cleanup
        await manager.cleanup_expired_sessions()
        
        # All sessions should be cleaned up
        assert len(manager.sessions) == 0
        
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_get_active_sessions(self, session_manager):
        """Test getting active sessions."""
        user1 = "user-1"
        user2 = "user-2"
        
        # Create sessions for different users
        session1 = await session_manager.create_session(user1)
        session2 = await session_manager.create_session(user2)
        session3 = await session_manager.create_session(user1)
        
        # Get all active sessions
        all_sessions = await session_manager.get_active_sessions()
        assert len(all_sessions) == 3
        
        # Get sessions for specific user
        user1_sessions = await session_manager.get_active_sessions(user1)
        assert len(user1_sessions) == 2
        
        user2_sessions = await session_manager.get_active_sessions(user2)
        assert len(user2_sessions) == 1
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_sanitize_filename(self, session_manager):
        """Test filename sanitization."""
        # Test various problematic filenames
        test_cases = [
            ("../../../etc/passwd", "passwd"),  # os.path.basename removes path components
            ("file with spaces.pdf", "file with spaces.pdf"),
            ("file@#$%^&*().pdf", "file.pdf"),
            ("", "uploaded_file.pdf"),
            ("a" * 150 + ".pdf", "a" * 95 + ".pdf"),
            ("normal_file-123.pdf", "normal_file-123.pdf")
        ]
        
        for input_name, expected in test_cases:
            result = session_manager._sanitize_filename(input_name)
            assert result == expected
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_session_persistence(self, temp_dir):
        """Test that sessions persist across manager restarts."""
        user_id = "test-user-123"
        converted_images = ["data:image/png;base64,test_image_data"]
        
        # Create first manager and session
        manager1 = PDFImportSessionManager(temp_storage_path=temp_dir)
        session_id = await manager1.create_session(user_id)
        await manager1.store_converted_images(session_id, converted_images, "PNG", 0.1)
        await manager1.shutdown()
        
        # Create second manager (should load existing sessions)
        manager2 = PDFImportSessionManager(temp_storage_path=temp_dir)
        
        # Session should be loaded
        session = await manager2.get_session(session_id)
        assert session is not None
        assert session.user_id == user_id
        assert session.converted_images == converted_images
        assert session.image_count == 1
        assert session.image_format == "PNG"
        assert session.total_image_size_mb == 0.1
        assert session.status == PDFImportStatus.CONVERTED
        
        await manager2.shutdown()


class TestGlobalSessionManager:
    """Test global session manager functions."""
    
    @pytest.mark.asyncio
    async def test_get_session_manager(self):
        """Test getting global session manager instance."""
        manager1 = get_session_manager()
        manager2 = get_session_manager()
        
        # Should return same instance
        assert manager1 is manager2
        
        await manager1.shutdown()
    
    @pytest.mark.asyncio
    async def test_initialize_session_manager(self, temp_dir):
        """Test initializing global session manager with custom settings."""
        manager = await initialize_session_manager(
            temp_storage_path=temp_dir,
            session_timeout_hours=3,
            max_file_size_mb=15
        )
        
        assert manager.temp_storage_path == Path(temp_dir) / "pdf_import_sessions"
        assert manager.session_timeout == timedelta(hours=3)
        assert manager.max_file_size == 15 * 1024 * 1024
        
        # Should be same as global instance
        global_manager = get_session_manager()
        assert manager is global_manager
        
        await manager.shutdown()


class TestImageBasedFunctionality:
    """Test image-specific functionality."""
    
    @pytest.mark.asyncio
    async def test_complete_image_workflow(self, session_manager, sample_pdf_content, temp_dir):
        """Test complete workflow from PDF upload to image conversion and cleanup."""
        import tempfile
        
        user_id = "test-user-123"
        filename = "test_character.pdf"
        
        # Step 1: Create session and upload PDF
        session_id = await session_manager.create_session(user_id)
        pdf_path = await session_manager.store_pdf_content(
            session_id, sample_pdf_content, filename
        )
        
        # Step 2: Store converted images
        converted_images = [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA4849a6wAAAABJRU5ErkJggg=="
        ]
        await session_manager.store_converted_images(
            session_id, converted_images, "PNG", 0.5
        )
        
        # Step 3: Store temporary image files
        temp_files = []
        for i in range(2):
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f"_page_{i}.png", 
                dir=temp_dir, 
                delete=False
            )
            temp_file.write(b"fake image data")
            temp_file.close()
            temp_files.append(temp_file.name)
        
        await session_manager.store_image_files(session_id, temp_files)
        
        # Step 4: Verify session state
        session = await session_manager.get_session(session_id)
        assert session.status == PDFImportStatus.CONVERTED
        assert session.converted_images == converted_images
        assert session.image_count == 2
        assert session.image_format == "PNG"
        assert session.total_image_size_mb == 0.5
        assert session.temp_image_files == temp_files
        
        # Step 5: Retrieve images
        retrieved_images = await session_manager.get_converted_images(session_id)
        assert retrieved_images == converted_images
        
        # Step 6: Complete cleanup
        await session_manager.cleanup_session(session_id)
        
        # Verify everything is cleaned up
        assert not os.path.exists(pdf_path)
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)
        assert session_id not in session_manager.sessions
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_empty_image_list_handling(self, session_manager):
        """Test handling of empty image lists."""
        user_id = "test-user-123"
        
        session_id = await session_manager.create_session(user_id)
        
        # Store empty image list
        await session_manager.store_converted_images(session_id, [], "PNG", 0.0)
        
        session = await session_manager.get_session(session_id)
        assert session.converted_images == []
        assert session.image_count == 0
        assert session.image_format == "PNG"
        assert session.total_image_size_mb == 0.0
        
        # Retrieve empty images
        retrieved_images = await session_manager.get_converted_images(session_id)
        assert retrieved_images == []
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_large_image_list_handling(self, session_manager):
        """Test handling of large image lists."""
        user_id = "test-user-123"
        
        session_id = await session_manager.create_session(user_id)
        
        # Create a large list of images (simulate multi-page PDF)
        large_image_list = [
            f"data:image/png;base64,page_{i}_data" for i in range(50)
        ]
        
        await session_manager.store_converted_images(
            session_id, large_image_list, "PNG", 25.0
        )
        
        session = await session_manager.get_session(session_id)
        assert session.converted_images == large_image_list
        assert session.image_count == 50
        assert session.total_image_size_mb == 25.0
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_mixed_image_formats(self, session_manager):
        """Test handling of different image formats."""
        user_id = "test-user-123"
        
        # Test PNG format
        session_id_png = await session_manager.create_session(user_id)
        png_images = ["data:image/png;base64,png_data"]
        await session_manager.store_converted_images(
            session_id_png, png_images, "PNG", 1.0
        )
        
        session_png = await session_manager.get_session(session_id_png)
        assert session_png.image_format == "PNG"
        
        # Test JPEG format
        session_id_jpeg = await session_manager.create_session(user_id)
        jpeg_images = ["data:image/jpeg;base64,jpeg_data"]
        await session_manager.store_converted_images(
            session_id_jpeg, jpeg_images, "JPEG", 0.8
        )
        
        session_jpeg = await session_manager.get_session(session_id_jpeg)
        assert session_jpeg.image_format == "JPEG"
        
        await session_manager.shutdown()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_invalid_session_operations(self, session_manager):
        """Test operations on invalid session IDs."""
        invalid_session_id = "invalid-session-123"
        
        # All operations should raise ValueError for invalid session
        with pytest.raises(ValueError, match="Session not found"):
            await session_manager.store_pdf_content(
                invalid_session_id, b"content", "file.pdf"
            )
        
        with pytest.raises(ValueError, match="Session not found"):
            await session_manager.store_converted_images(
                invalid_session_id, ["image_data"]
            )
        
        with pytest.raises(ValueError, match="Session not found"):
            await session_manager.store_parsed_data(
                invalid_session_id, {}
            )
        
        with pytest.raises(ValueError, match="Session not found"):
            await session_manager.update_session_status(
                invalid_session_id, PDFImportStatus.COMPLETED
            )
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_corrupted_session_file_handling(self, temp_dir):
        """Test handling of corrupted session files."""
        # Create manager directory structure
        sessions_dir = Path(temp_dir) / "pdf_import_sessions" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Create corrupted session file
        corrupted_file = sessions_dir / "corrupted-session.json"
        with open(corrupted_file, 'w') as f:
            f.write("invalid json content {")
        
        # Manager should handle corrupted file gracefully
        manager = PDFImportSessionManager(temp_storage_path=temp_dir)
        
        # Corrupted file should be removed
        assert not corrupted_file.exists()
        assert len(manager.sessions) == 0
        
        await manager.shutdown()


if __name__ == "__main__":
    pytest.main([__file__])