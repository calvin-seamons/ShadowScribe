"""
PDF Import API Routes

This module provides FastAPI routes for the PDF character import feature.
Handles file upload, text extraction, LLM parsing, and character file generation.
"""

import os
import logging
import tempfile
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse

from models import (
    PDFUploadResponse,
    PDFExtractionResult,
    PDFParseRequest,
    PDFParseResponse,
    PDFImportStatusResponse,
    PDFImportCleanupResponse,
    PDFImportSessionData,
    CharacterCreationResponse
)

from llm_character_parser import LLMCharacterParser
from pdf_import_session_manager import get_session_manager, PDFImportStatus
from knowledge_base_service import KnowledgeBaseFileManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Global dependencies - will be set by main.py
_llm_parser: Optional[LLMCharacterParser] = None
_file_manager: Optional[KnowledgeBaseFileManager] = None


def set_pdf_import_dependencies(
    llm_parser: LLMCharacterParser,
    file_manager: KnowledgeBaseFileManager
):
    """Set the PDF import service dependencies."""
    global _llm_parser, _file_manager
    _llm_parser = llm_parser
    _file_manager = file_manager



def get_llm_parser() -> LLMCharacterParser:
    """Dependency to get the LLM parser instance."""
    if _llm_parser is None:
        raise HTTPException(status_code=500, detail="LLM parser not initialized")
    return _llm_parser


def get_file_manager() -> KnowledgeBaseFileManager:
    """Dependency to get the file manager instance."""
    if _file_manager is None:
        raise HTTPException(status_code=500, detail="File manager not initialized")
    return _file_manager


@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    user_id: str = Form("default_user")
) -> PDFUploadResponse:
    """
    Upload PDF file and extract text content.
    
    This endpoint handles PDF file upload, validates the file, extracts text content,
    and creates a session for tracking the import process.
    """
    session_manager = get_session_manager()
    
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Create import session
        session_id = await session_manager.create_session(user_id)
        
        # Read file content
        file_content = await file.read()
        
        # Store PDF content
        try:
            pdf_file_path = await session_manager.store_pdf_content(
                session_id, file_content, file.filename
            )
        except ValueError as e:
            await session_manager.cleanup_session(session_id)
            raise HTTPException(status_code=400, detail=str(e))
        
        # Update progress
        await session_manager.update_session_status(
            session_id, PDFImportStatus.UPLOADED, progress=20.0
        )
        
        # TODO: Replace with vision-based PDF processing (Task 2)
        # Legacy text extraction has been removed
        # This will be replaced with PDF to image conversion in the next task
        
        # For now, mark as uploaded and ready for future vision processing
        await session_manager.update_session_status(
            session_id, PDFImportStatus.UPLOADED, progress=100.0
        )
        
        logger.info(f"PDF uploaded successfully for session {session_id} - awaiting vision processing implementation")
        
        return PDFUploadResponse(
            session_id=session_id,
            status="success",
            message="PDF uploaded successfully. Vision-based processing will be implemented in the next phase."
        )
            

    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during PDF upload: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/preview/{session_id}")
async def get_pdf_preview(session_id: str) -> Dict[str, Any]:
    """
    Get extracted PDF text for user review.
    
    Returns the extracted text content and metadata for user preview
    before proceeding with LLM parsing.
    """
    session_manager = get_session_manager()
    
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.status not in [PDFImportStatus.EXTRACTED, PDFImportStatus.PARSED]:
            raise HTTPException(
                status_code=400,
                detail=f"Session not ready for preview. Current status: {session.status.value}"
            )
        
        if not session.extracted_text:
            raise HTTPException(status_code=404, detail="No extracted text available")
        
        return {
            "session_id": session_id,
            "extracted_text": session.extracted_text,
            "pdf_filename": session.pdf_filename,
            "status": session.status.value,
            "progress": session.progress
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PDF preview for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get preview: {str(e)}"
        )


@router.post("/parse", response_model=PDFParseResponse)
async def parse_character_data(
    request: PDFParseRequest,
    parser: LLMCharacterParser = Depends(get_llm_parser)
) -> PDFParseResponse:
    """
    Parse character data from extracted PDF text using LLM.
    
    Takes the extracted text and uses LLM to parse it into structured
    character data according to the JSON schemas.
    """
    session_manager = get_session_manager()
    
    try:
        session = await session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Use provided text or session text
        text_to_parse = request.extracted_text or session.extracted_text
        if not text_to_parse:
            raise HTTPException(status_code=400, detail="No text available for parsing")
        
        # Update progress
        await session_manager.update_session_status(
            request.session_id, PDFImportStatus.EXTRACTED, progress=50.0
        )
        
        # Parse character data with LLM
        try:
            parse_result = await parser.parse_character_data(text_to_parse, request.session_id)
            
            # Store parsed data
            await session_manager.store_parsed_data(
                request.session_id,
                parse_result.character_files,
                [uf.__dict__ for uf in parse_result.uncertain_fields],
                parse_result.parsing_confidence,
                {k: v.__dict__ for k, v in parse_result.validation_results.items()}
            )
            
            # Update progress
            await session_manager.update_session_status(
                request.session_id, PDFImportStatus.PARSED, progress=80.0
            )
            
            logger.info(f"Successfully parsed character data for session {request.session_id}")
            
            return PDFParseResponse(
                session_id=request.session_id,
                character_files=parse_result.character_files,
                uncertain_fields=[uf.__dict__ for uf in parse_result.uncertain_fields],
                parsing_confidence=parse_result.parsing_confidence,
                status="success"
            )
            
        except Exception as e:
            await session_manager.update_session_status(
                request.session_id, PDFImportStatus.FAILED,
                error_message=f"Parsing error: {str(e)}"
            )
            logger.error(f"Character parsing failed for session {request.session_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Character parsing failed: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during character parsing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Parsing failed: {str(e)}"
        )


@router.post("/generate/{session_id}", response_model=CharacterCreationResponse)
async def generate_character_files(
    session_id: str,
    character_name: str = Form(...),
    file_manager: KnowledgeBaseFileManager = Depends(get_file_manager)
) -> CharacterCreationResponse:
    """
    Generate character JSON files from parsed data.
    
    Takes the parsed character data and creates the actual JSON files
    in the knowledge base directory structure.
    """
    session_manager = get_session_manager()
    
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.status != PDFImportStatus.PARSED:
            raise HTTPException(
                status_code=400,
                detail=f"Session not ready for file generation. Current status: {session.status.value}"
            )
        
        if not session.parsed_data:
            raise HTTPException(status_code=400, detail="No parsed data available")
        
        # Validate character name
        if not character_name or not character_name.strip():
            raise HTTPException(status_code=400, detail="Character name is required")
        
        character_name = character_name.strip()
        
        # Check for existing character
        existing_files = file_manager.list_character_files(character_name)
        if existing_files:
            raise HTTPException(
                status_code=409,
                detail=f"Character '{character_name}' already exists. Choose a different name."
            )
        
        # Create character files
        created_files = []
        failed_files = []
        
        for file_type, file_data in session.parsed_data.items():
            try:
                # Update character name in the data if it's the main character file
                if file_type == "character" and "name" in file_data:
                    file_data["name"] = character_name
                
                # Create the file
                filename = f"{character_name}_{file_type}.json"
                success = await file_manager.create_file(filename, file_data)
                
                if success:
                    created_files.append(filename)
                    logger.info(f"Created character file: {filename}")
                else:
                    failed_files.append(filename)
                    logger.error(f"Failed to create character file: {filename}")
                    
            except Exception as e:
                failed_files.append(f"{character_name}_{file_type}.json")
                logger.error(f"Error creating {file_type} file: {e}")
        
        # Update session status
        if created_files and not failed_files:
            await session_manager.update_session_status(
                session_id, PDFImportStatus.COMPLETED, progress=100.0
            )
            status_message = f"Successfully created {len(created_files)} character files"
        elif created_files:
            await session_manager.update_session_status(
                session_id, PDFImportStatus.COMPLETED, progress=100.0
            )
            status_message = f"Created {len(created_files)} files, {len(failed_files)} failed"
        else:
            await session_manager.update_session_status(
                session_id, PDFImportStatus.FAILED,
                error_message="Failed to create any character files"
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to create character files"
            )
        
        logger.info(f"Character creation completed for session {session_id}: {character_name}")
        
        return CharacterCreationResponse(
            character_name=character_name,
            files_created=created_files,
            status="success",
            message=status_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during character file generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"File generation failed: {str(e)}"
        )


@router.get("/status/{session_id}", response_model=PDFImportStatusResponse)
async def get_import_status(session_id: str) -> PDFImportStatusResponse:
    """
    Get the current status of a PDF import session.
    
    Returns detailed information about the session including progress,
    status, and any available data.
    """
    session_manager = get_session_manager()
    
    try:
        session_data = await session_manager.get_session_data(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Convert to response model
        session_response = PDFImportSessionData(**session_data)
        
        return PDFImportStatusResponse(
            session_data=session_response,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import status for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )


@router.delete("/cleanup/{session_id}", response_model=PDFImportCleanupResponse)
async def cleanup_import_session(session_id: str) -> PDFImportCleanupResponse:
    """
    Clean up a PDF import session and its associated files.
    
    Removes temporary files, session data, and frees up resources.
    Should be called when the import is complete or cancelled.
    """
    session_manager = get_session_manager()
    
    try:
        # Check if session exists
        session = await session_manager.get_session(session_id)
        session_existed = session is not None
        
        # Clean up the session
        await session_manager.cleanup_session(session_id)
        
        logger.info(f"Cleaned up PDF import session: {session_id}")
        
        return PDFImportCleanupResponse(
            session_id=session_id,
            cleaned_up=True,
            status="success",
            message="Session cleaned up successfully" if session_existed else "Session not found, cleanup completed"
        )
        
    except Exception as e:
        logger.error(f"Error cleaning up session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/sessions")
async def list_active_sessions(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    List active PDF import sessions.
    
    Optionally filter by user ID. Useful for debugging and monitoring.
    """
    session_manager = get_session_manager()
    
    try:
        sessions = await session_manager.get_active_sessions(user_id)
        
        return {
            "sessions": sessions,
            "count": len(sessions),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error listing active sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sessions: {str(e)}"
        )


# Health check endpoint for PDF import services
@router.get("/health")
async def pdf_import_health_check() -> Dict[str, Any]:
    """
    Health check for PDF import services.
    
    Verifies that all required services are initialized and working.
    """
    try:
        health_status = {
            "llm_parser": _llm_parser is not None,
            "file_manager": _file_manager is not None,
            "session_manager": True  # Always available as it's a singleton
        }
        
        all_healthy = all(health_status.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": health_status,
            "timestamp": os.times().elapsed if hasattr(os, 'times') else 0
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": os.times().elapsed if hasattr(os, 'times') else 0
        }