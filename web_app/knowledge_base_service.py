"""
Knowledge Base File Management Service

This module provides comprehensive file management capabilities for D&D character data
including CRUD operations, validation, and backup functionality.
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging
from dataclasses import dataclass

from backup_service import BackupService
from json_schema_loader import JSONSchemaLoader

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a knowledge base file."""
    filename: str
    file_type: str
    size: int
    last_modified: datetime
    is_editable: bool


@dataclass
class ValidationResult:
    """Result of JSON schema validation."""
    is_valid: bool
    errors: List[Dict[str, str]]
    warnings: List[str]


class KnowledgeBaseFileManager:
    """
    Manages CRUD operations for knowledge base files with validation and backup support.
    
    Supports all D&D character data file types organized in character-specific folders:
    - characters/{character_name}/character.json
    - characters/{character_name}/character_background.json  
    - characters/{character_name}/feats_and_traits.json
    - characters/{character_name}/action_list.json
    - characters/{character_name}/inventory_list.json
    - characters/{character_name}/objectives_and_contracts.json
    - characters/{character_name}/spell_list.json
    """
    
    # Supported file types and their schemas
    SUPPORTED_FILE_TYPES = {
        'character.json': 'character',
        'character_background.json': 'character_background',
        'feats_and_traits.json': 'feats_and_traits',
        'action_list.json': 'action_list',
        'inventory_list.json': 'inventory_list',
        'objectives_and_contracts.json': 'objectives_and_contracts',
        'spell_list.json': 'spell_list'
    }
    
    def __init__(self, knowledge_base_path: str):
        """
        Initialize the file manager.
        
        Args:
            knowledge_base_path: Path to the knowledge base directory
        """
        self.base_path = Path(knowledge_base_path)
        self.characters_path = self.base_path / "characters"
        self.backup_service = BackupService(self.base_path / "backups")
        
        # Initialize schema loader with proper path
        structures_path = self.base_path / "character-json-structures"
        self.schema_loader = JSONSchemaLoader(str(structures_path))
        
        # Ensure knowledge base and characters directories exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.characters_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"KnowledgeBaseFileManager initialized with path: {self.base_path}")
        logger.info(f"Characters directory: {self.characters_path}")
    
    def _get_character_path(self, character_name: str) -> Path:
        """
        Get the path for a character's directory.
        
        Args:
            character_name: Name of the character
            
        Returns:
            Path to the character's directory
        """
        # Sanitize character name for filesystem
        safe_name = "".join(c for c in character_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        return self.characters_path / safe_name
    
    def _parse_file_path(self, file_path: str) -> tuple[str, str]:
        """
        Parse a file path to extract character name and filename.
        
        Args:
            file_path: File path in format "character_name/filename.json" or just "filename.json"
            
        Returns:
            Tuple of (character_name, filename)
        """
        if '/' in file_path:
            character_name, filename = file_path.split('/', 1)
            return character_name, filename
        else:
            # Legacy support for root-level files
            return None, file_path
    
    async def list_characters(self) -> List[str]:
        """
        List all available characters.
        
        Returns:
            List of character names
        """
        try:
            characters = []
            for char_dir in self.characters_path.iterdir():
                if char_dir.is_dir():
                    characters.append(char_dir.name)
            
            logger.info(f"Found {len(characters)} characters")
            return sorted(characters)
            
        except Exception as e:
            logger.error(f"Error listing characters: {e}")
            raise
    
    async def list_files(self, character_name: Optional[str] = None) -> List[FileInfo]:
        """
        List knowledge base files with metadata.
        
        Args:
            character_name: Optional character name to filter files
        
        Returns:
            List of FileInfo objects containing file metadata
        """
        files = []
        
        try:
            if character_name:
                # List files for specific character
                char_path = self._get_character_path(character_name)
                if char_path.exists():
                    for file_path in char_path.glob("*.json"):
                        if file_path.name in self.SUPPORTED_FILE_TYPES:
                            stat = file_path.stat()
                            
                            files.append(FileInfo(
                                filename=f"{character_name}/{file_path.name}",
                                file_type=self.SUPPORTED_FILE_TYPES[file_path.name],
                                size=stat.st_size,
                                last_modified=datetime.fromtimestamp(stat.st_mtime),
                                is_editable=True
                            ))
            else:
                # List files for all characters
                for char_dir in self.characters_path.iterdir():
                    if char_dir.is_dir():
                        for file_path in char_dir.glob("*.json"):
                            if file_path.name in self.SUPPORTED_FILE_TYPES:
                                stat = file_path.stat()
                                
                                files.append(FileInfo(
                                    filename=f"{char_dir.name}/{file_path.name}",
                                    file_type=self.SUPPORTED_FILE_TYPES[file_path.name],
                                    size=stat.st_size,
                                    last_modified=datetime.fromtimestamp(stat.st_mtime),
                                    is_editable=True
                                ))
                
                # Also check for legacy files in root directory
                for file_path in self.base_path.glob("*.json"):
                    if file_path.name in self.SUPPORTED_FILE_TYPES:
                        stat = file_path.stat()
                        
                        files.append(FileInfo(
                            filename=file_path.name,
                            file_type=self.SUPPORTED_FILE_TYPES[file_path.name],
                            size=stat.st_size,
                            last_modified=datetime.fromtimestamp(stat.st_mtime),
                            is_editable=True
                        ))
            
            logger.info(f"Listed {len(files)} knowledge base files" + (f" for {character_name}" if character_name else ""))
            return files
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            raise
    
    async def read_file(self, filename: str) -> Dict[str, Any]:
        """
        Read and parse a knowledge base file.
        
        Args:
            filename: Name of the file to read (can be "character_name/file.json" or "file.json")
            
        Returns:
            Parsed JSON content as dictionary
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not supported or invalid JSON
        """
        character_name, file_name = self._parse_file_path(filename)
        
        if file_name not in self.SUPPORTED_FILE_TYPES:
            raise ValueError(f"Unsupported file type: {file_name}")
        
        if character_name:
            # Character-specific file
            char_path = self._get_character_path(character_name)
            file_path = char_path / file_name
        else:
            # Legacy root-level file
            file_path = self.base_path / file_name
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            logger.info(f"Successfully read file: {filename}")
            return content
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {filename}: {e}")
            raise ValueError(f"Invalid JSON in file {filename}: {e}")
        except Exception as e:
            logger.error(f"Error reading file {filename}: {e}")
            raise
    
    async def write_file(self, filename: str, content: Dict[str, Any]) -> bool:
        """
        Write content to a knowledge base file with validation and backup.
        
        Args:
            filename: Name of the file to write (can be "character_name/file.json" or "file.json")
            content: Dictionary content to write as JSON
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If file type not supported or validation fails
        """
        character_name, file_name = self._parse_file_path(filename)
        
        if file_name not in self.SUPPORTED_FILE_TYPES:
            raise ValueError(f"Unsupported file type: {file_name}")
        
        file_type = self.SUPPORTED_FILE_TYPES[file_name]
        
        if character_name:
            # Character-specific file
            char_path = self._get_character_path(character_name)
            char_path.mkdir(parents=True, exist_ok=True)  # Ensure character directory exists
            file_path = char_path / file_name
        else:
            # Legacy root-level file
            file_path = self.base_path / file_name
        
        # Validate content before writing
        validation_result = await self.validate_content(content, file_type)
        if not validation_result.is_valid:
            error_msg = f"Validation failed for {filename}: {validation_result.errors}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Create backup if file exists
            if file_path.exists():
                existing_content = await self.read_file(filename)
                backup_id = await self.backup_service.create_backup(filename, existing_content)
                logger.info(f"Created backup {backup_id} for {filename}")
            
            # Write new content
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully wrote file: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing file {filename}: {e}")
            raise
    
    async def create_file(self, filename: str, content: Dict[str, Any]) -> bool:
        """
        Create a new knowledge base file.
        
        Args:
            filename: Name of the file to create (can be "character_name/file.json" or "file.json")
            content: Dictionary content to write as JSON
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If file type not supported or file already exists
            FileExistsError: If file already exists
        """
        character_name, file_name = self._parse_file_path(filename)
        
        if file_name not in self.SUPPORTED_FILE_TYPES:
            raise ValueError(f"Unsupported file type: {file_name}")
        
        if character_name:
            # Character-specific file
            char_path = self._get_character_path(character_name)
            file_path = char_path / file_name
        else:
            # Legacy root-level file
            file_path = self.base_path / file_name
        
        if file_path.exists():
            raise FileExistsError(f"File already exists: {filename}")
        
        # Use write_file for validation and creation
        return await self.write_file(filename, content)
    
    async def delete_file(self, filename: str) -> bool:
        """
        Delete a knowledge base file with backup.
        
        Args:
            filename: Name of the file to delete (can be "character_name/file.json" or "file.json")
            
        Returns:
            True if successful
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type not supported
        """
        character_name, file_name = self._parse_file_path(filename)
        
        if file_name not in self.SUPPORTED_FILE_TYPES:
            raise ValueError(f"Unsupported file type: {file_name}")
        
        if character_name:
            # Character-specific file
            char_path = self._get_character_path(character_name)
            file_path = char_path / file_name
        else:
            # Legacy root-level file
            file_path = self.base_path / file_name
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        try:
            # Create backup before deletion
            existing_content = await self.read_file(filename)
            backup_id = await self.backup_service.create_backup(filename, existing_content)
            
            # Delete the file
            file_path.unlink()
            
            logger.info(f"Successfully deleted file: {filename} (backup: {backup_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")
            raise
    
    async def validate_content(self, content: Dict[str, Any], file_type: str) -> ValidationResult:
        """
        Validate content against JSON schema for the file type.
        
        Args:
            content: Dictionary content to validate
            file_type: Type of file (character, character_background, etc.)
            
        Returns:
            ValidationResult with validation status and any errors
        """
        try:
            return await self.schema_loader.validate_against_schema(content, file_type)
        except Exception as e:
            logger.error(f"Error validating content for {file_type}: {e}")
            # Create a compatible ValidationResult
            from json_schema_validator import ValidationResult, ValidationError
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError("validation", str(e), "system_error")],
                warnings=[]
            )
    
    async def get_file_template(self, file_type: str) -> Dict[str, Any]:
        """
        Get a template structure for creating new files of the specified type.
        
        Args:
            file_type: Type of file to get template for
            
        Returns:
            Template dictionary structure
            
        Raises:
            ValueError: If file type not supported
        """
        return self.schema_loader.get_template_for_file_type(file_type)
    
    async def get_schema(self, file_type: str) -> Dict[str, Any]:
        """
        Get the JSON schema for a file type.
        
        Args:
            file_type: Type of file to get schema for
            
        Returns:
            JSON schema dictionary
            
        Raises:
            ValueError: If file type not supported
        """
        return self.schema_loader.get_schema_for_file_type(file_type)
    
    async def create_character(self, character_name: str, character_data: Dict[str, Any]) -> List[str]:
        """
        Create a new character with all associated files in their own folder.
        
        Args:
            character_name: Name of the character
            character_data: Dictionary with character creation data
            
        Returns:
            List of created file paths
            
        Raises:
            FileExistsError: If character already exists
            ValueError: If validation fails
        """
        # Check if character already exists
        char_path = self._get_character_path(character_name)
        if char_path.exists() and any(char_path.glob("*.json")):
            raise FileExistsError(f"Character '{character_name}' already exists")
        
        files_created = []
        
        try:
            # Generate character.json
            character_template = await self.get_file_template('character')
            character_template['character_base']['name'] = character_name
            character_template['character_base']['race'] = character_data.get('race', '')
            character_template['character_base']['class'] = character_data.get('character_class', '')
            character_template['character_base']['total_level'] = character_data.get('level', 1)
            character_template['character_base']['background'] = character_data.get('background', '')
            character_template['characteristics']['alignment'] = character_data.get('alignment', '')
            
            # Set ability scores if provided
            if character_data.get('ability_scores'):
                character_template['ability_scores'].update(character_data['ability_scores'])
            
            # Calculate basic HP (simplified - class hit die + con modifier)
            con_modifier = (character_template['ability_scores']['constitution'] - 10) // 2
            base_hp = max(1, 8 + con_modifier)  # Assuming d8 hit die as default
            character_template['combat_stats']['max_hp'] = base_hp
            character_template['combat_stats']['current_hp'] = base_hp
            
            char_file = f"{character_name}/character.json"
            await self.create_file(char_file, character_template)
            files_created.append(char_file)
            
            # Generate character_background.json
            background_template = await self.get_file_template('character_background')
            background_template['background']['name'] = character_data.get('background', '')
            background_template['backstory']['title'] = f"{character_name}'s Story"
            
            bg_file = f"{character_name}/character_background.json"
            await self.create_file(bg_file, background_template)
            files_created.append(bg_file)
            
            # Generate feats_and_traits.json
            feats_template = await self.get_file_template('feats_and_traits')
            feats_template['features_and_traits']['species_traits']['species'] = character_data.get('race', '')
            feats_template['metadata']['last_updated'] = datetime.now().isoformat()
            
            feats_file = f"{character_name}/feats_and_traits.json"
            await self.create_file(feats_file, feats_template)
            files_created.append(feats_file)
            
            # Generate action_list.json
            actions_template = await self.get_file_template('action_list')
            actions_template['metadata']['last_updated'] = datetime.now().isoformat()
            
            actions_file = f"{character_name}/action_list.json"
            await self.create_file(actions_file, actions_template)
            files_created.append(actions_file)
            
            # Generate inventory_list.json
            inventory_template = await self.get_file_template('inventory_list')
            inventory_template['metadata']['last_updated'] = datetime.now().isoformat()
            
            inventory_file = f"{character_name}/inventory_list.json"
            await self.create_file(inventory_file, inventory_template)
            files_created.append(inventory_file)
            
            # Generate objectives_and_contracts.json
            objectives_template = await self.get_file_template('objectives_and_contracts')
            objectives_template['metadata']['last_updated'] = datetime.now().isoformat()
            
            objectives_file = f"{character_name}/objectives_and_contracts.json"
            await self.create_file(objectives_file, objectives_template)
            files_created.append(objectives_file)
            
            # Generate spell_list.json
            spells_template = await self.get_file_template('spell_list')
            spells_template['metadata']['last_updated'] = datetime.now().isoformat()
            
            spells_file = f"{character_name}/spell_list.json"
            await self.create_file(spells_file, spells_template)
            files_created.append(spells_file)
            
            logger.info(f"Successfully created character '{character_name}' with {len(files_created)} files")
            return files_created
            
        except Exception as e:
            # Cleanup partially created files
            logger.error(f"Error creating character '{character_name}': {e}")
            for filename in files_created:
                try:
                    await self.delete_file(filename)
                    logger.info(f"Cleaned up partially created file: {filename}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup file {filename}: {cleanup_error}")
            
            # Remove character directory if it's empty
            try:
                if char_path.exists() and not any(char_path.iterdir()):
                    char_path.rmdir()
                    logger.info(f"Removed empty character directory: {char_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup character directory: {cleanup_error}")
            
            raise
    
    def get_supported_file_types(self) -> Dict[str, str]:
        """
        Get mapping of supported filenames to file types.
        
        Returns:
            Dictionary mapping filenames to file types
        """
        return self.SUPPORTED_FILE_TYPES.copy()