"""
PDF Import API Routes

This module provides FastAPI routes for the PDF character import feature.
Handles file upload, PDF to image conversion, vision-based parsing, and character file generation.
"""

import os
import logging
import tempfile
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse

from models import (
    PDFUploadResponse,
    PDFImageResult,
    PDFParseRequest,
    PDFParseResponse,
    PDFImportStatusResponse,
    PDFImportCleanupResponse,
    PDFImportSessionData,
    CharacterCreationResponse
)

from vision_character_parser import VisionCharacterParser
from pdf_image_converter import PDFImageConverter
from pdf_import_session_manager import get_session_manager, PDFImportStatus
from knowledge_base_service import KnowledgeBaseFileManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Global dependencies - will be set by main.py
_vision_parser: Optional[VisionCharacterParser] = None
_pdf_converter: Optional[PDFImageConverter] = None
_file_manager: Optional[KnowledgeBaseFileManager] = None


def set_pdf_import_dependencies(
    vision_parser: VisionCharacterParser,
    pdf_converter: PDFImageConverter,
    file_manager: KnowledgeBaseFileManager
):
    """Set the PDF import service dependencies."""
    global _vision_parser, _pdf_converter, _file_manager
    _vision_parser = vision_parser
    _pdf_converter = pdf_converter
    _file_manager = file_manager


def get_vision_parser() -> VisionCharacterParser:
    """Dependency to get the vision parser instance."""
    if _vision_parser is None:
        raise HTTPException(status_code=500, detail="Vision parser not initialized")
    return _vision_parser


def get_pdf_converter() -> PDFImageConverter:
    """Dependency to get the PDF converter instance."""
    if _pdf_converter is None:
        raise HTTPException(status_code=500, detail="PDF converter not initialized")
    return _pdf_converter


def get_file_manager() -> KnowledgeBaseFileManager:
    """Dependency to get the file manager instance."""
    if _file_manager is None:
        raise HTTPException(status_code=500, detail="File manager not initialized")
    return _file_manager


@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    user_id: str = Form("default_user"),
    converter: PDFImageConverter = Depends(get_pdf_converter)
) -> PDFUploadResponse:
    """
    Upload PDF file and convert to images for vision processing.
    
    This endpoint handles PDF file upload, validates the file, converts PDF pages to images,
    and creates a session for tracking the vision-based import process.
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
        
        # Update progress - PDF uploaded
        await session_manager.update_session_status(
            session_id, PDFImportStatus.UPLOADED, progress=20.0
        )
        
        logger.info(f"PDF uploaded successfully for session {session_id}, starting image conversion")
        
        # Convert PDF to images
        try:
            logger.info(f"Starting PDF to image conversion for session {session_id}")
            conversion_result = await converter.convert_pdf_to_images(pdf_file_path, session_id)
            logger.info(f"Conversion result: page_count={conversion_result.page_count}, images_count={len(conversion_result.images)}, format={conversion_result.image_format}, size={conversion_result.total_size_mb}MB")
            
            # Store converted images in session
            await session_manager.store_converted_images(
                session_id,
                conversion_result.images,
                conversion_result.image_format,
                conversion_result.total_size_mb
            )
            
            # Update progress - Images converted
            await session_manager.update_session_status(
                session_id, PDFImportStatus.CONVERTED, progress=40.0
            )
            
            logger.info(f"Successfully converted {conversion_result.page_count} pages to images for session {session_id}")
            
            return PDFUploadResponse(
                session_id=session_id,
                status="success",
                message=f"PDF uploaded and converted to {conversion_result.page_count} images successfully. Ready for vision processing."
            )
            
        except Exception as e:
            await session_manager.update_session_status(
                session_id, PDFImportStatus.FAILED,
                error_message=f"Image conversion failed: {str(e)}"
            )
            logger.error(f"Image conversion failed for session {session_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Image conversion failed: {str(e)}"
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
    Get converted PDF images for user review.
    
    Returns the converted image previews and metadata for user review
    before proceeding with vision-based parsing.
    """
    session_manager = get_session_manager()
    
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.status not in [PDFImportStatus.CONVERTED, PDFImportStatus.PARSED]:
            raise HTTPException(
                status_code=400,
                detail=f"Session not ready for preview. Current status: {session.status.value}"
            )
        
        if not session.converted_images:
            raise HTTPException(status_code=404, detail="No converted images available")
        
        # Transform base64 strings into ImageData objects for frontend
        image_objects = []
        for i, base64_image in enumerate(session.converted_images):
            try:
                # Decode base64 to get image dimensions
                import base64
                from PIL import Image
                import io
                
                # Remove data URL prefix if present
                if base64_image.startswith('data:image'):
                    base64_data = base64_image.split(',')[1]
                else:
                    base64_data = base64_image
                
                # Decode and get dimensions
                image_bytes = base64.b64decode(base64_data)
                pil_image = Image.open(io.BytesIO(image_bytes))
                width, height = pil_image.size
                
                image_objects.append({
                    "id": f"{session_id}_page_{i+1}",
                    "base64": f"data:image/{session.image_format.lower()};base64,{base64_data}",
                    "pageNumber": i + 1,
                    "dimensions": {
                        "width": width,
                        "height": height
                    }
                })
            except Exception as e:
                logger.warning(f"Failed to process image {i+1}: {e}")
                # Fallback with default dimensions
                image_objects.append({
                    "id": f"{session_id}_page_{i+1}",
                    "base64": base64_image if base64_image.startswith('data:') else f"data:image/{session.image_format.lower()};base64,{base64_image}",
                    "pageNumber": i + 1,
                    "dimensions": {
                        "width": 0,
                        "height": 0
                    }
                })
        
        return {
            "session_id": session_id,
            "images": image_objects,
            "image_count": session.image_count,
            "image_format": session.image_format,
            "total_size_mb": session.total_image_size_mb,
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
    parser: VisionCharacterParser = Depends(get_vision_parser)
) -> PDFParseResponse:
    """
    Parse character data from PDF images using GPT-4.1 vision.
    
    Takes the converted images and uses GPT-4.1 vision to parse them into structured
    character data according to the JSON schemas.
    """
    session_manager = get_session_manager()
    
    try:
        session = await session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if images are available
        if not session.converted_images:
            raise HTTPException(status_code=400, detail="No converted images available for parsing")
        
        # Verify session is in correct state
        if session.status not in [PDFImportStatus.CONVERTED, PDFImportStatus.PARSED]:
            raise HTTPException(
                status_code=400,
                detail=f"Session not ready for parsing. Current status: {session.status.value}"
            )
        
        # Update progress - Starting vision parsing
        await session_manager.update_session_status(
            request.session_id, PDFImportStatus.CONVERTED, progress=50.0
        )
        
        logger.info(f"Starting vision-based character parsing for session {request.session_id}")
        
        # Parse character data with vision
        try:
            parse_result = await parser.parse_character_data(session.converted_images, request.session_id)
            
            # Store parsed data
            await session_manager.store_parsed_data(
                request.session_id,
                parse_result.character_files,
                [uf.__dict__ for uf in parse_result.uncertain_fields],
                parse_result.parsing_confidence,
                {k: v.__dict__ for k, v in parse_result.validation_results.items()}
            )
            
            # Update progress - Vision parsing complete
            await session_manager.update_session_status(
                request.session_id, PDFImportStatus.PARSED, progress=80.0
            )
            
            logger.info(f"Successfully parsed character data using vision for session {request.session_id}")
            
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
                error_message=f"Vision parsing error: {str(e)}"
            )
            logger.error(f"Vision character parsing failed for session {request.session_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Vision character parsing failed: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during vision character parsing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Vision parsing failed: {str(e)}"
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
    
    Removes temporary files (including images), session data, and frees up resources.
    Should be called when the import is complete or cancelled.
    """
    session_manager = get_session_manager()
    
    try:
        # Check if session exists
        session = await session_manager.get_session(session_id)
        session_existed = session is not None
        
        # Clean up the session (includes image cleanup)
        await session_manager.cleanup_session(session_id)
        
        logger.info(f"Cleaned up PDF import session and images: {session_id}")
        
        return PDFImportCleanupResponse(
            session_id=session_id,
            cleaned_up=True,
            status="success",
            message="Session and images cleaned up successfully" if session_existed else "Session not found, cleanup completed"
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
            "vision_parser": _vision_parser is not None,
            "pdf_converter": _pdf_converter is not None,
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