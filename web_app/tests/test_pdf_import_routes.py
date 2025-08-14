"""
Integration Tests for PDF Import API Routes

Tests the complete PDF import workflow including file upload, text extraction,
LLM parsing, and character file generation.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
import io

from pdf_import_routes import router, set_pdf_import_dependencies
from llm_character_parser import LLMCharacterParser, CharacterParseResult, UncertainField
from knowledge_base_service import KnowledgeBaseFileManager
from pdf_import_session_manager import PDFImportSessionManager, PDFImportStatus


@pytest.fixture
def app():
    """Create FastAPI app with PDF import routes for testing."""
    app = FastAPI()
    app.include_router(router, prefix="/api/character/import-pdf")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


# PDF extractor removed - vision-based processing will be implemented in future tasks


@pytest.fixture
def mock_llm_parser():
    """Mock LLM character parser."""
    parser = Mock(spec=LLMCharacterParser)
    
    # Mock successful parsing
    character_files = {
        "character": {
            "name": "Test Character",
            "race": "Human",
            "class": "Fighter",
            "level": 5,
            "ability_scores": {"STR": 16, "DEX": 14, "CON": 15, "INT": 10, "WIS": 12, "CHA": 8}
        },
        "spell_list": {"spells": []},
        "inventory_list": {"items": []},
        "feats_and_traits": {"features": []},
        "action_list": {"actions": []},
        "character_background": {"background": ""},
        "objectives_and_contracts": {"objectives": []}
    }
    
    uncertain_fields = [
        UncertainField(
            file_type="character",
            field_path="ability_scores.STR",
            extracted_value=16,
            confidence=0.7,
            suggestions=["15", "17"],
            reasoning="Text was partially unclear"
        )
    ]
    
    parse_result = CharacterParseResult(
        session_id="test-session",
        character_files=character_files,
        uncertain_fields=uncertain_fields,
        parsing_confidence=0.8,
        validation_results={},
        errors=[],
        warnings=[]
    )
    
    parser.parse_character_data = AsyncMock(return_value=parse_result)
    
    return parser


@pytest.fixture
def mock_file_manager():
    """Mock knowledge base file manager."""
    manager = Mock(spec=KnowledgeBaseFileManager)
    
    manager.list_character_files = Mock(return_value=[])  # No existing character
    manager.create_file = AsyncMock(return_value=True)
    
    return manager


@pytest.fixture
def mock_session_manager():
    """Mock PDF import session manager."""
    with patch('pdf_import_routes.get_session_manager') as mock_get:
        manager = Mock(spec=PDFImportSessionManager)
        
        # Mock session data
        mock_session = Mock()
        mock_session.session_id = "test-session-123"
        mock_session.status = PDFImportStatus.EXTRACTED  # Set to extracted for preview tests
        mock_session.progress = 40.0
        mock_session.extracted_text = "Test extracted text"
        mock_session.pdf_filename = "test_character.pdf"
        mock_session.parsed_data = {
            "character": {"name": "Test Character", "level": 5}
        }
        
        manager.create_session = AsyncMock(return_value="test-session-123")
        manager.store_pdf_content = AsyncMock(return_value="/tmp/test_file.pdf")
        manager.store_extracted_text = AsyncMock()
        manager.store_parsed_data = AsyncMock()
        manager.update_session_status = AsyncMock()
        manager.get_session = AsyncMock(return_value=mock_session)
        manager.get_session_data = AsyncMock(return_value={
            "session_id": "test-session-123",
            "user_id": "test-user",
            "created_at": "2024-01-01T00:00:00",
            "last_activity": "2024-01-01T00:00:00",
            "status": "created",
            "progress": 0.0
        })
        manager.cleanup_session = AsyncMock()
        manager.get_active_sessions = AsyncMock(return_value=[])
        
        mock_get.return_value = manager
        yield manager


@pytest.fixture
def setup_dependencies(mock_llm_parser, mock_file_manager):
    """Setup PDF import dependencies."""
    set_pdf_import_dependencies(mock_llm_parser, mock_file_manager)


class TestPDFUpload:
    """Test PDF file upload endpoint."""
    
    def test_upload_pdf_success(self, client, setup_dependencies, mock_session_manager):
        """Test successful PDF upload and text extraction."""
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF"
        
        files = {"file": ("test_character.pdf", io.BytesIO(pdf_content), "application/pdf")}
        data = {"user_id": "test-user"}
        
        response = client.post("/api/character/import-pdf/upload", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        assert "session_id" in result
        assert "message" in result
    
    def test_upload_non_pdf_file(self, client, setup_dependencies, mock_session_manager):
        """Test upload of non-PDF file."""
        files = {"file": ("test.txt", io.BytesIO(b"Not a PDF"), "text/plain")}
        data = {"user_id": "test-user"}
        
        response = client.post("/api/character/import-pdf/upload", files=files, data=data)
        
        assert response.status_code == 400
        assert "Only PDF files are supported" in response.json()["detail"]
    
    def test_upload_without_file(self, client, setup_dependencies, mock_session_manager):
        """Test upload without file."""
        data = {"user_id": "test-user"}
        
        response = client.post("/api/character/import-pdf/upload", data=data)
        
        assert response.status_code == 422  # Validation error
    
    def test_upload_extraction_failure(self, client, setup_dependencies, mock_session_manager):
        """Test upload with PDF extraction failure - legacy test, will be updated for vision processing."""
        # This test will be updated when vision-based processing is implemented
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF"
        files = {"file": ("test_character.pdf", io.BytesIO(pdf_content), "application/pdf")}
        data = {"user_id": "test-user"}
        
        response = client.post("/api/character/import-pdf/upload", files=files, data=data)
        
        # Currently returns success as text extraction has been removed
        assert response.status_code == 200


class TestPDFPreview:
    """Test PDF preview endpoint."""
    
    def test_get_preview_success(self, client, setup_dependencies, mock_session_manager):
        """Test successful preview retrieval."""
        response = client.get("/api/character/import-pdf/preview/test-session-123")
        
        assert response.status_code == 200
        result = response.json()
        assert result["session_id"] == "test-session-123"
        assert "extracted_text" in result
        assert "pdf_filename" in result
    
    def test_get_preview_session_not_found(self, client, setup_dependencies, mock_session_manager):
        """Test preview for non-existent session."""
        mock_session_manager.get_session.return_value = None
        
        response = client.get("/api/character/import-pdf/preview/nonexistent-session")
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    def test_get_preview_wrong_status(self, client, setup_dependencies, mock_session_manager):
        """Test preview when session is in wrong status."""
        mock_session = Mock()
        mock_session.status = PDFImportStatus.CREATED
        mock_session_manager.get_session.return_value = mock_session
        
        response = client.get("/api/character/import-pdf/preview/test-session-123")
        
        assert response.status_code == 400
        assert "Session not ready for preview" in response.json()["detail"]


class TestCharacterParsing:
    """Test character data parsing endpoint."""
    
    def test_parse_character_success(self, client, setup_dependencies, mock_session_manager):
        """Test successful character data parsing."""
        request_data = {
            "session_id": "test-session-123",
            "extracted_text": "Character Name: Test Fighter\nClass: Fighter\nLevel: 5"
        }
        
        response = client.post("/api/character/import-pdf/parse", json=request_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        assert result["session_id"] == "test-session-123"
        assert "character_files" in result
        assert "uncertain_fields" in result
        assert "parsing_confidence" in result
    
    def test_parse_session_not_found(self, client, setup_dependencies, mock_session_manager):
        """Test parsing for non-existent session."""
        mock_session_manager.get_session.return_value = None
        
        request_data = {"session_id": "nonexistent-session"}
        
        response = client.post("/api/character/import-pdf/parse", json=request_data)
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    def test_parse_no_text_available(self, client, setup_dependencies, mock_session_manager):
        """Test parsing when no text is available."""
        mock_session = Mock()
        mock_session.extracted_text = None
        mock_session_manager.get_session.return_value = mock_session
        
        request_data = {"session_id": "test-session-123"}
        
        response = client.post("/api/character/import-pdf/parse", json=request_data)
        
        assert response.status_code == 400
        assert "No text available for parsing" in response.json()["detail"]


class TestCharacterFileGeneration:
    """Test character file generation endpoint."""
    
    def test_generate_files_success(self, client, setup_dependencies, mock_session_manager):
        """Test successful character file generation."""
        mock_session = Mock()
        mock_session.status = PDFImportStatus.PARSED
        mock_session.parsed_data = {
            "character": {"name": "Test Character", "level": 5},
            "spell_list": {"spells": []}
        }
        mock_session_manager.get_session.return_value = mock_session
        
        data = {"character_name": "Test Character"}
        
        response = client.post("/api/character/import-pdf/generate/test-session-123", data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        assert result["character_name"] == "Test Character"
        assert len(result["files_created"]) > 0
    
    def test_generate_files_session_not_found(self, client, setup_dependencies, mock_session_manager):
        """Test file generation for non-existent session."""
        mock_session_manager.get_session.return_value = None
        
        data = {"character_name": "Test Character"}
        
        response = client.post("/api/character/import-pdf/generate/nonexistent-session", data=data)
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    def test_generate_files_wrong_status(self, client, setup_dependencies, mock_session_manager):
        """Test file generation when session is in wrong status."""
        mock_session = Mock()
        mock_session.status = PDFImportStatus.EXTRACTED
        mock_session_manager.get_session.return_value = mock_session
        
        data = {"character_name": "Test Character"}
        
        response = client.post("/api/character/import-pdf/generate/test-session-123", data=data)
        
        assert response.status_code == 400
        assert "Session not ready for file generation" in response.json()["detail"]
    
    def test_generate_files_empty_name(self, client, setup_dependencies, mock_session_manager):
        """Test file generation with empty character name."""
        mock_session = Mock()
        mock_session.status = PDFImportStatus.PARSED
        mock_session.parsed_data = {"character": {}}
        mock_session_manager.get_session.return_value = mock_session
        
        data = {"character_name": ""}
        
        response = client.post("/api/character/import-pdf/generate/test-session-123", data=data)
        
        assert response.status_code == 400
        assert "Character name is required" in response.json()["detail"]
    
    def test_generate_files_character_exists(self, client, setup_dependencies, mock_session_manager, mock_file_manager):
        """Test file generation when character already exists."""
        mock_session = Mock()
        mock_session.status = PDFImportStatus.PARSED
        mock_session.parsed_data = {"character": {}}
        mock_session_manager.get_session.return_value = mock_session
        
        # Mock existing character
        mock_file_manager.list_character_files.return_value = ["existing_character.json"]
        
        data = {"character_name": "Existing Character"}
        
        response = client.post("/api/character/import-pdf/generate/test-session-123", data=data)
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]


class TestSessionStatus:
    """Test session status endpoint."""
    
    def test_get_status_success(self, client, setup_dependencies, mock_session_manager):
        """Test successful status retrieval."""
        response = client.get("/api/character/import-pdf/status/test-session-123")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        assert "session_data" in result
        assert result["session_data"]["session_id"] == "test-session-123"
    
    def test_get_status_session_not_found(self, client, setup_dependencies, mock_session_manager):
        """Test status for non-existent session."""
        mock_session_manager.get_session_data.return_value = None
        
        response = client.get("/api/character/import-pdf/status/nonexistent-session")
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]


class TestSessionCleanup:
    """Test session cleanup endpoint."""
    
    def test_cleanup_success(self, client, setup_dependencies, mock_session_manager):
        """Test successful session cleanup."""
        response = client.delete("/api/character/import-pdf/cleanup/test-session-123")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        assert result["cleaned_up"] is True
        assert result["session_id"] == "test-session-123"
    
    def test_cleanup_nonexistent_session(self, client, setup_dependencies, mock_session_manager):
        """Test cleanup of non-existent session."""
        mock_session_manager.get_session.return_value = None
        
        response = client.delete("/api/character/import-pdf/cleanup/nonexistent-session")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        assert "not found" in result["message"]


class TestSessionListing:
    """Test session listing endpoint."""
    
    def test_list_sessions_success(self, client, setup_dependencies, mock_session_manager):
        """Test successful session listing."""
        response = client.get("/api/character/import-pdf/sessions")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        assert "sessions" in result
        assert "count" in result
    
    def test_list_sessions_with_user_filter(self, client, setup_dependencies, mock_session_manager):
        """Test session listing with user filter."""
        response = client.get("/api/character/import-pdf/sessions?user_id=test-user")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check_healthy(self, client, setup_dependencies, mock_session_manager):
        """Test health check when all services are healthy."""
        response = client.get("/api/character/import-pdf/health")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "healthy"
        assert "services" in result
        assert result["services"]["llm_parser"] is True
        assert result["services"]["file_manager"] is True
    
    def test_health_check_degraded(self, client, mock_session_manager):
        """Test health check when some services are missing."""
        # Reset dependencies to simulate missing services
        set_pdf_import_dependencies(None, None)
        
        response = client.get("/api/character/import-pdf/health")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "degraded"
        assert result["services"]["llm_parser"] is False


class TestEndToEndWorkflow:
    """Test complete end-to-end PDF import workflow."""
    
    def test_complete_workflow(self, client, setup_dependencies, mock_session_manager):
        """Test the complete PDF import workflow from upload to file generation."""
        
        # Create a session state tracker
        session_state = {
            "status": PDFImportStatus.EXTRACTED,
            "parsed_data": {
                "character": {"name": "Test Character", "level": 5},
                "spell_list": {"spells": []}
            }
        }
        
        def get_mock_session(*args, **kwargs):
            """Return mock session with current state."""
            mock_session = Mock()
            mock_session.session_id = "test-session-123"
            mock_session.status = session_state["status"]
            mock_session.progress = 40.0
            mock_session.extracted_text = "Test extracted text"
            mock_session.pdf_filename = "test_character.pdf"
            mock_session.parsed_data = session_state["parsed_data"]
            return mock_session
        
        def update_session_status(session_id, status, *args, **kwargs):
            """Update session state."""
            session_state["status"] = status
        
        mock_session_manager.get_session.side_effect = get_mock_session
        mock_session_manager.update_session_status.side_effect = update_session_status
        
        # Step 1: Upload PDF
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF"
        files = {"file": ("test_character.pdf", io.BytesIO(pdf_content), "application/pdf")}
        data = {"user_id": "test-user"}
        
        upload_response = client.post("/api/character/import-pdf/upload", files=files, data=data)
        assert upload_response.status_code == 200
        session_id = upload_response.json()["session_id"]
        
        # Step 2: Get preview
        preview_response = client.get(f"/api/character/import-pdf/preview/{session_id}")
        assert preview_response.status_code == 200
        
        # Step 3: Parse character data
        parse_data = {"session_id": session_id}
        parse_response = client.post("/api/character/import-pdf/parse", json=parse_data)
        assert parse_response.status_code == 200
        
        # Manually update session state to PARSED for file generation
        session_state["status"] = PDFImportStatus.PARSED
        
        # Step 4: Generate character files
        generate_data = {"character_name": "Test Character"}
        generate_response = client.post(f"/api/character/import-pdf/generate/{session_id}", data=generate_data)
        assert generate_response.status_code == 200
        
        # Step 5: Check status
        status_response = client.get(f"/api/character/import-pdf/status/{session_id}")
        assert status_response.status_code == 200
        
        # Step 6: Cleanup
        cleanup_response = client.delete(f"/api/character/import-pdf/cleanup/{session_id}")
        assert cleanup_response.status_code == 200
    
    def test_workflow_with_errors(self, client, setup_dependencies, mock_session_manager):
        """Test workflow handling when errors occur - legacy test, will be updated for vision processing."""
        
        # This test will be updated when vision-based processing is implemented
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF"
        files = {"file": ("test_character.pdf", io.BytesIO(pdf_content), "application/pdf")}
        data = {"user_id": "test-user"}
        
        upload_response = client.post("/api/character/import-pdf/upload", files=files, data=data)
        # Currently returns success as text extraction has been removed
        assert upload_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])