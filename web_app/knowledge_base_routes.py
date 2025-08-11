"""
Knowledge Base API Routes

This module provides REST API endpoints for managing D&D character data files
including CRUD operations, validation, templates, and character creation.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List, Optional
import logging
import os
from datetime import datetime

from models import (
    KnowledgeBaseFile,
    FileContent,
    FileListResponse,
    FileContentResponse,
    FileUpdateRequest,
    FileCreateRequest,
    ValidationResponse,
    BackupListResponse,
    SchemaResponse,
    TemplateResponse,
    CharacterCreationRequest,
    CharacterCreationResponse,
    ConflictInfo,
    ConflictCheckResponse,
    ExportResponse,
    ImportRequest,
    CharacterExportResponse,
    CharacterImportRequest,
    CharacterImportResponse
)
from knowledge_base_service import KnowledgeBaseFileManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])

# Global variable to store the file manager - will be set by main.py
_file_manager = None

def set_file_manager(file_manager: KnowledgeBaseFileManager):
    """Set the file manager dependency."""
    global _file_manager
    _file_manager = file_manager

def get_file_manager():
    """Dependency to get the file manager instance."""
    if _file_manager is None:
        raise HTTPException(status_code=500, detail="File manager not initialized")
    return _file_manager


@router.get("/characters")
async def list_characters(file_manager=Depends(get_file_manager)):
    """
    List all available characters.
    
    Returns:
        List of character names
    """
    try:
        characters = await file_manager.list_characters()
        
        logger.info(f"Listed {len(characters)} characters")
        return {
            "status": "success",
            "characters": characters,
            "count": len(characters)
        }
        
    except Exception as e:
        logger.error(f"Error listing characters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files", response_model=FileListResponse)
async def list_knowledge_base_files(character_name: Optional[str] = None, file_manager=Depends(get_file_manager)):
    """
    List knowledge base files with metadata.
    
    Args:
        character_name: Optional character name to filter files
    
    Returns:
        FileListResponse: List of files with metadata
    """
    try:
        files = await file_manager.list_files(character_name)
        
        # Convert FileInfo dataclass to KnowledgeBaseFile model
        file_models = [
            KnowledgeBaseFile(
                filename=file.filename,
                file_type=file.file_type,
                size=file.size,
                last_modified=file.last_modified,
                is_editable=file.is_editable
            )
            for file in files
        ]
        
        logger.info(f"Listed {len(file_models)} knowledge base files" + (f" for {character_name}" if character_name else ""))
        return FileListResponse(
            files=file_models,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error listing knowledge base files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{filename:path}", response_model=FileContentResponse)
async def get_file_content(filename: str, file_manager=Depends(get_file_manager)):
    """
    Get the content of a specific knowledge base file.
    
    Args:
        filename: Name of the file to retrieve
        
    Returns:
        FileContentResponse: File content and metadata
    """
    try:
        # URL decode the filename to handle encoded slashes
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        
        content = await file_manager.read_file(decoded_filename)
        
        file_content = FileContent(
            filename=decoded_filename,
            content=content,
            schema_version="1.0"
        )
        
        logger.info(f"Retrieved content for file: {decoded_filename}")
        return FileContentResponse(
            content=file_content,
            status="success"
        )
        
    except FileNotFoundError:
        logger.warning(f"File not found: {filename}")
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    except ValueError as e:
        logger.error(f"Invalid file or content: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/files/{filename}")
async def update_file_content(
    filename: str, 
    request: FileUpdateRequest, 
    file_manager=Depends(get_file_manager)
):
    """
    Update the content of a knowledge base file.
    
    Args:
        filename: Name of the file to update
        request: File update request with new content
        
    Returns:
        Success message
    """
    try:
        # URL decode the filename to handle encoded slashes
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        
        success = await file_manager.write_file(decoded_filename, request.content)
        
        if success:
            logger.info(f"Successfully updated file: {decoded_filename}")
            return {
                "status": "success",
                "message": f"File {decoded_filename} updated successfully",
                "filename": filename
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update file")
            
    except FileNotFoundError:
        logger.warning(f"File not found for update: {filename}")
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    except ValueError as e:
        logger.error(f"Validation error updating {filename}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files", status_code=status.HTTP_201_CREATED)
async def create_file(request: FileCreateRequest, file_manager=Depends(get_file_manager)):
    """
    Create a new knowledge base file.
    
    Args:
        request: File creation request with filename and content
        
    Returns:
        Success message with created file info
    """
    try:
        success = await file_manager.create_file(request.filename, request.content)
        
        if success:
            logger.info(f"Successfully created file: {request.filename}")
            return {
                "status": "success",
                "message": f"File {request.filename} created successfully",
                "filename": request.filename
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create file")
            
    except FileExistsError:
        logger.warning(f"File already exists: {request.filename}")
        raise HTTPException(status_code=409, detail=f"File already exists: {request.filename}")
    except ValueError as e:
        logger.error(f"Validation error creating {request.filename}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating file {request.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{filename}")
async def delete_file(filename: str, file_manager=Depends(get_file_manager)):
    """
    Delete a knowledge base file (with backup).
    
    Args:
        filename: Name of the file to delete
        
    Returns:
        Success message
    """
    try:
        success = await file_manager.delete_file(filename)
        
        if success:
            logger.info(f"Successfully deleted file: {filename}")
            return {
                "status": "success",
                "message": f"File {filename} deleted successfully (backup created)",
                "filename": filename
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
            
    except FileNotFoundError:
        logger.warning(f"File not found for deletion: {filename}")
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    except ValueError as e:
        logger.error(f"Error deleting {filename}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/{filename}", response_model=ValidationResponse)
async def validate_file(filename: str, request: FileUpdateRequest, file_manager=Depends(get_file_manager)):
    """
    Validate file content against its schema without saving.
    
    Args:
        filename: Name of the file type to validate against
        request: Content to validate
        
    Returns:
        ValidationResponse: Validation results with errors and warnings
    """
    try:
        # Get file type from filename
        supported_types = file_manager.get_supported_file_types()
        if filename not in supported_types:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {filename}")
        
        file_type = supported_types[filename]
        validation_result = await file_manager.validate_content(request.content, file_type)
        
        # Convert ValidationResult dataclass to ValidationResponse model
        from models import ValidationError as ValidationErrorModel
        
        error_models = [
            ValidationErrorModel(
                field_path=error.field_path,
                message=error.message,
                error_type=error.error_type
            )
            for error in validation_result.errors
        ]
        
        from models import ValidationResult as ValidationResultModel
        result_model = ValidationResultModel(
            is_valid=validation_result.is_valid,
            errors=error_models,
            warnings=validation_result.warnings
        )
        
        logger.info(f"Validated content for {filename}: {'valid' if validation_result.is_valid else 'invalid'}")
        return ValidationResponse(
            result=result_model,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating content for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/{file_type}", response_model=SchemaResponse)
async def get_file_schema(file_type: str, file_manager=Depends(get_file_manager)):
    """
    Get the JSON schema for a specific file type.
    
    Args:
        file_type: Type of file to get schema for (character, character_background, etc.)
        
    Returns:
        SchemaResponse: JSON schema for the file type
    """
    try:
        schema = await file_manager.get_schema(file_type)
        
        logger.info(f"Retrieved schema for file type: {file_type}")
        return SchemaResponse(
            json_schema=schema,
            file_type=file_type,
            status="success"
        )
        
    except ValueError as e:
        logger.warning(f"Invalid file type requested: {file_type}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting schema for {file_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/template/{file_type}", response_model=TemplateResponse)
async def get_file_template(file_type: str, file_manager=Depends(get_file_manager)):
    """
    Get a template structure for creating new files of the specified type.
    
    Args:
        file_type: Type of file to get template for (character, character_background, etc.)
        
    Returns:
        TemplateResponse: Template structure for the file type
    """
    try:
        template = await file_manager.get_file_template(file_type)
        
        logger.info(f"Retrieved template for file type: {file_type}")
        return TemplateResponse(
            template=template,
            file_type=file_type,
            status="success"
        )
        
    except ValueError as e:
        logger.warning(f"Invalid file type requested: {file_type}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting template for {file_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/character/new", response_model=CharacterCreationResponse)
async def create_new_character(request: CharacterCreationRequest, file_manager=Depends(get_file_manager)):
    """
    Create a new character with all associated files in their own folder.
    
    This endpoint generates all seven core files for a D&D character in a character-specific folder:
    - characters/{character_name}/character.json
    - characters/{character_name}/character_background.json
    - characters/{character_name}/feats_and_traits.json
    - characters/{character_name}/action_list.json
    - characters/{character_name}/inventory_list.json
    - characters/{character_name}/objectives_and_contracts.json
    - characters/{character_name}/spell_list.json
    
    Args:
        request: Character creation request with basic character info
        
    Returns:
        CharacterCreationResponse: List of created files and status
    """
    try:
        character_data = {
            'race': request.race,
            'character_class': request.character_class,
            'level': request.level,
            'background': request.background,
            'alignment': request.alignment,
            'ability_scores': request.ability_scores
        }
        
        files_created = await file_manager.create_character(request.character_name, character_data)
        
        logger.info(f"Successfully created new character '{request.character_name}' with {len(files_created)} files")
        return CharacterCreationResponse(
            character_name=request.character_name,
            files_created=files_created,
            status="success",
            message=f"Character '{request.character_name}' created successfully with all associated files in their own folder"
        )
        
    except FileExistsError as e:
        logger.warning(f"Character creation failed - character already exists: {e}")
        raise HTTPException(
            status_code=409, 
            detail=f"Character '{request.character_name}' already exists. Please choose a different character name."
        )
    except ValueError as e:
        logger.error(f"Validation error during character creation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating character '{request.character_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Character creation failed: {str(e)}")


@router.get("/backups", response_model=BackupListResponse)
async def list_backups(filename: Optional[str] = None, file_manager=Depends(get_file_manager)):
    """
    List available backups, optionally filtered by filename.
    
    Args:
        filename: Optional filename to filter backups
        
    Returns:
        BackupListResponse: List of available backups
    """
    try:
        backups = await file_manager.backup_service.list_backups(filename)
        
        # Convert BackupInfo dataclass to BackupInfo model
        from models import BackupInfo as BackupInfoModel
        
        backup_models = [
            BackupInfoModel(
                backup_id=backup.backup_id,
                filename=backup.filename,
                created_at=backup.created_at,
                size=backup.size
            )
            for backup in backups
        ]
        
        logger.info(f"Listed {len(backup_models)} backups" + (f" for {filename}" if filename else ""))
        return BackupListResponse(
            backups=backup_models,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backups/{backup_id}/restore")
async def restore_backup(backup_id: str, file_manager=Depends(get_file_manager)):
    """
    Restore a file from backup.
    
    Args:
        backup_id: ID of the backup to restore
        
    Returns:
        Success message with restored file info
    """
    try:
        # Get backup info first
        backup_info = await file_manager.backup_service.get_backup_info(backup_id)
        
        # Restore content from backup
        restored_content = await file_manager.backup_service.restore_backup(backup_id)
        
        # Write restored content to the original file
        success = await file_manager.write_file(backup_info.filename, restored_content)
        
        if success:
            logger.info(f"Successfully restored backup {backup_id} to {backup_info.filename}")
            return {
                "status": "success",
                "message": f"Backup {backup_id} restored to {backup_info.filename}",
                "backup_id": backup_id,
                "filename": backup_info.filename
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to restore backup")
            
    except FileNotFoundError:
        logger.warning(f"Backup not found: {backup_id}")
        raise HTTPException(status_code=404, detail=f"Backup not found: {backup_id}")
    except ValueError as e:
        logger.error(f"Error restoring backup {backup_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error restoring backup {backup_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported-types")
async def get_supported_file_types(file_manager=Depends(get_file_manager)):
    """
    Get mapping of supported filenames to file types.
    
    Returns:
        Dictionary mapping filenames to file types
    """
    try:
        supported_types = file_manager.get_supported_file_types()
        
        logger.info(f"Retrieved {len(supported_types)} supported file types")
        return {
            "status": "success",
            "supported_types": supported_types,
            "count": len(supported_types)
        }
        
    except Exception as e:
        logger.error(f"Error getting supported file types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/{filename}/duplicate")
async def duplicate_file(filename: str, new_filename: str, file_manager=Depends(get_file_manager)):
    """
    Duplicate a knowledge base file with a new name.
    
    Args:
        filename: Name of the file to duplicate
        new_filename: Name for the duplicated file
        
    Returns:
        Success message with duplicated file info
    """
    try:
        # Read the original file content
        content = await file_manager.read_file(filename)
        
        # Create the duplicate with new filename
        success = await file_manager.create_file(new_filename, content)
        
        if success:
            logger.info(f"Successfully duplicated file {filename} to {new_filename}")
            return {
                "status": "success",
                "message": f"File {filename} duplicated to {new_filename}",
                "original_filename": filename,
                "new_filename": new_filename
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to duplicate file")
            
    except FileNotFoundError:
        logger.warning(f"Original file not found for duplication: {filename}")
        raise HTTPException(status_code=404, detail=f"Original file not found: {filename}")
    except FileExistsError:
        logger.warning(f"Duplicate file already exists: {new_filename}")
        raise HTTPException(status_code=409, detail=f"File already exists: {new_filename}")
    except ValueError as e:
        logger.error(f"Validation error duplicating {filename}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error duplicating file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{filename}/export", response_model=ExportResponse)
async def export_file(filename: str, file_manager=Depends(get_file_manager)):
    """
    Export a knowledge base file for download.
    
    Args:
        filename: Name of the file to export
        
    Returns:
        File content with export metadata
    """
    try:
        content = await file_manager.read_file(filename)
        
        # Add export metadata
        export_data = {
            "export_metadata": {
                "filename": filename,
                "exported_at": datetime.now().isoformat(),
                "export_version": "1.0",
                "source": "ShadowScribe Knowledge Base"
            },
            "file_content": content
        }
        
        logger.info(f"Exported file: {filename}")
        return ExportResponse(
            status="success",
            export_data=export_data,
            filename=filename
        )
        
    except FileNotFoundError:
        logger.warning(f"File not found for export: {filename}")
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    except Exception as e:
        logger.error(f"Error exporting file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/import")
async def import_file(request: ImportRequest, file_manager=Depends(get_file_manager)):
    """
    Import a knowledge base file from export data.
    
    Args:
        request: Import request with export data and optional new filename
        
    Returns:
        Success message with imported file info
    """
    try:
        export_data = request.export_data
        new_filename = request.filename  # Optional override
        overwrite = request.overwrite
        
        if not export_data or "file_content" not in export_data:
            raise HTTPException(status_code=400, detail="Invalid export data")
        
        # Get filename from export metadata or use provided override
        original_filename = export_data.get("export_metadata", {}).get("filename")
        filename = new_filename or original_filename
        
        if not filename:
            raise HTTPException(status_code=400, detail="No filename specified for import")
        
        content = export_data["file_content"]
        
        # Check if file exists and handle accordingly
        try:
            if overwrite:
                success = await file_manager.write_file(filename, content)
                action = "updated"
            else:
                success = await file_manager.create_file(filename, content)
                action = "created"
        except FileExistsError:
            raise HTTPException(
                status_code=409, 
                detail=f"File already exists: {filename}. Set overwrite=true to replace it."
            )
        
        if success:
            logger.info(f"Successfully imported file: {filename}")
            return {
                "status": "success",
                "message": f"File {filename} {action} successfully",
                "filename": filename,
                "action": action
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to import file")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/characters/{character_name}/export", response_model=CharacterExportResponse)
async def export_character(character_name: str, file_manager=Depends(get_file_manager)):
    """
    Export all files for a character as a single package.
    
    Args:
        character_name: Name of the character to export
        
    Returns:
        Character export package with all files
    """
    try:
        # Get all files for the character
        files = await file_manager.list_files(character_name)
        
        if not files:
            raise HTTPException(status_code=404, detail=f"No files found for character: {character_name}")
        
        # Read all file contents
        character_data = {}
        for file_info in files:
            try:
                content = await file_manager.read_file(file_info.filename)
                # Extract just the filename part (remove character_name/ prefix)
                file_key = file_info.filename.split('/')[-1] if '/' in file_info.filename else file_info.filename
                character_data[file_key] = content
            except Exception as e:
                logger.warning(f"Failed to read file {file_info.filename} for character export: {e}")
                continue
        
        # Create export package
        export_package = {
            "export_metadata": {
                "character_name": character_name,
                "exported_at": datetime.now().isoformat(),
                "export_version": "1.0",
                "source": "ShadowScribe Knowledge Base",
                "file_count": len(character_data)
            },
            "character_data": character_data
        }
        
        logger.info(f"Exported character '{character_name}' with {len(character_data)} files")
        return CharacterExportResponse(
            status="success",
            export_package=export_package,
            character_name=character_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting character {character_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/characters/import", response_model=CharacterImportResponse)
async def import_character(request: CharacterImportRequest, file_manager=Depends(get_file_manager)):
    """
    Import a character from an export package.
    
    Args:
        request: Import request with export package and optional new character name
        
    Returns:
        Success message with imported character info
    """
    try:
        export_package = request.export_package
        new_character_name = request.character_name  # Optional override
        overwrite = request.overwrite
        
        if not export_package or "character_data" not in export_package:
            raise HTTPException(status_code=400, detail="Invalid export package")
        
        # Get character name from export metadata or use provided override
        original_character_name = export_package.get("export_metadata", {}).get("character_name")
        character_name = new_character_name or original_character_name
        
        if not character_name:
            raise HTTPException(status_code=400, detail="No character name specified for import")
        
        character_data = export_package["character_data"]
        
        # Check if character already exists
        existing_files = await file_manager.list_files(character_name)
        if existing_files and not overwrite:
            raise HTTPException(
                status_code=409,
                detail=f"Character '{character_name}' already exists. Set overwrite=true to replace it."
            )
        
        # Import all character files
        imported_files = []
        failed_files = []
        
        for filename, content in character_data.items():
            try:
                full_filename = f"{character_name}/{filename}"
                
                if overwrite:
                    success = await file_manager.write_file(full_filename, content)
                else:
                    success = await file_manager.create_file(full_filename, content)
                
                if success:
                    imported_files.append(full_filename)
                else:
                    failed_files.append(filename)
                    
            except Exception as e:
                logger.warning(f"Failed to import file {filename} for character {character_name}: {e}")
                failed_files.append(filename)
        
        if not imported_files:
            raise HTTPException(status_code=500, detail="Failed to import any character files")
        
        action = "updated" if overwrite else "created"
        message = f"Character '{character_name}' {action} successfully with {len(imported_files)} files"
        
        if failed_files:
            message += f" ({len(failed_files)} files failed to import)"
        
        logger.info(f"Imported character '{character_name}': {len(imported_files)} files succeeded, {len(failed_files)} failed")
        return CharacterImportResponse(
            status="success",
            message=message,
            character_name=character_name,
            imported_files=imported_files,
            failed_files=failed_files,
            action=action
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing character: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{filename}/conflicts", response_model=ConflictCheckResponse)
async def check_file_conflicts(filename: str, file_manager=Depends(get_file_manager)):
    """
    Check for potential conflicts before modifying a file.
    
    Args:
        filename: Name of the file to check for conflicts
        
    Returns:
        Conflict information and recommendations
    """
    try:
        # Check if file exists and get current metadata
        try:
            current_content = await file_manager.read_file(filename)
            files = await file_manager.list_files()
            current_file = next((f for f in files if f.filename == filename), None)
            
            if not current_file:
                return ConflictCheckResponse(
                    status="success",
                    has_conflicts=False,
                    conflicts=[],
                    message="No conflicts - file does not exist"
                )
            
            # Check for recent backups (potential concurrent editing)
            backups = await file_manager.backup_service.list_backups(filename)
            recent_backups = [b for b in backups if (datetime.now() - datetime.fromisoformat(b.created_at.replace('Z', '+00:00') if b.created_at.endswith('Z') else b.created_at)).total_seconds() < 300]  # 5 minutes
            
            conflicts = []
            
            # Check for recent modifications (potential concurrent editing)
            if recent_backups:
                conflicts.append({
                    "type": "recent_modification",
                    "message": f"File was recently modified ({len(recent_backups)} recent backups found)",
                    "severity": "warning",
                    "recommendation": "Review recent changes before modifying"
                })
            
            # Check file size (potential corruption or unexpected changes)
            if current_file.size > 1024 * 1024:  # 1MB
                conflicts.append({
                    "type": "large_file",
                    "message": f"File is unusually large ({current_file.size} bytes)",
                    "severity": "warning",
                    "recommendation": "Verify file integrity before modifying"
                })
            
            # Check for validation issues
            character_name, file_name = file_manager._parse_file_path(filename)
            if file_name in file_manager.SUPPORTED_FILE_TYPES:
                file_type = file_manager.SUPPORTED_FILE_TYPES[file_name]
                validation_result = await file_manager.validate_content(current_content, file_type)
                
                if not validation_result.is_valid:
                    conflicts.append({
                        "type": "validation_error",
                        "message": f"File has validation errors: {len(validation_result.errors)} errors found",
                        "severity": "error",
                        "recommendation": "Fix validation errors before modifying",
                        "details": validation_result.errors
                    })
            
            # Convert conflicts to ConflictInfo models
            conflict_models = [
                ConflictInfo(
                    type=conflict["type"],
                    message=conflict["message"],
                    severity=conflict["severity"],
                    recommendation=conflict["recommendation"],
                    details=conflict.get("details")
                )
                for conflict in conflicts
            ]
            
            logger.info(f"Checked conflicts for {filename}: {len(conflicts)} potential issues found")
            return ConflictCheckResponse(
                status="success",
                has_conflicts=len(conflicts) > 0,
                conflicts=conflict_models,
                file_info={
                    "filename": filename,
                    "size": current_file.size,
                    "last_modified": current_file.last_modified.isoformat(),
                    "recent_backups": len(recent_backups)
                }
            )
            
        except FileNotFoundError:
            return ConflictCheckResponse(
                status="success",
                has_conflicts=False,
                conflicts=[],
                message="No conflicts - file does not exist"
            )
            
    except Exception as e:
        logger.error(f"Error checking conflicts for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))