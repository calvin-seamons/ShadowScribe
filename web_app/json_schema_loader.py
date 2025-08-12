"""
JSON Schema Loader for PDF Character Import

This module provides a schema loader that reads the character JSON structure files
from the knowledge_base/character-json-structures directory and converts them into
usable schemas and templates for the PDF import feature.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from json_schema_validator import JSONSchemaValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class SchemaInfo:
    """Information about a loaded schema."""
    file_type: str
    schema: Dict[str, Any]
    template: Dict[str, Any]
    source_file: str


class JSONSchemaLoader:
    """
    Loads JSON schemas and templates from character-json-structures files.
    
    This class reads the markdown files in knowledge_base/character-json-structures/
    and extracts the JSON structure definitions to create schemas and templates
    for character data validation and generation.
    """
    
    def __init__(self, structures_path: str = "knowledge_base/character-json-structures"):
        """
        Initialize the schema loader.
        
        Args:
            structures_path: Path to the character JSON structures directory
        """
        self.structures_path = Path(structures_path)
        self.validator = JSONSchemaValidator()
        self.schemas: Dict[str, SchemaInfo] = {}
        self._load_all_schemas()
        logger.info(f"JSONSchemaLoader initialized with {len(self.schemas)} schemas")
    
    def _load_all_schemas(self) -> None:
        """Load all schema files from the structures directory."""
        if not self.structures_path.exists():
            logger.error(f"Structures path does not exist: {self.structures_path}")
            return
        
        # Map of file names to their types
        file_type_mapping = {
            "character.json.md": "character",
            "character_background.json.md": "character_background", 
            "feats_and_traits.json.md": "feats_and_traits",
            "action_list.json.md": "action_list",
            "inventory_list.json.md": "inventory_list",
            "objectives_and_contracts.json.md": "objectives_and_contracts",
            "spell_list.json.md": "spell_list"
        }
        
        for filename, file_type in file_type_mapping.items():
            file_path = self.structures_path / filename
            if file_path.exists():
                try:
                    schema_info = self._load_schema_from_file(file_path, file_type)
                    if schema_info:
                        self.schemas[file_type] = schema_info
                        logger.info(f"Loaded schema for {file_type}")
                except Exception as e:
                    logger.error(f"Failed to load schema from {filename}: {e}")
            else:
                logger.warning(f"Schema file not found: {filename}")
    
    def _load_schema_from_file(self, file_path: Path, file_type: str) -> Optional[SchemaInfo]:
        """
        Load schema from a markdown file containing JSON structure.
        
        Args:
            file_path: Path to the markdown file
            file_type: Type of the schema file
            
        Returns:
            SchemaInfo object or None if loading failed
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract JSON from markdown content
            json_content = self._extract_json_from_markdown(content)
            if not json_content:
                logger.error(f"No JSON content found in {file_path}")
                return None
            
            # Parse the JSON to create template
            template = json.loads(json_content)
            
            # Generate schema from template
            schema = self._generate_schema_from_template(template)
            
            return SchemaInfo(
                file_type=file_type,
                schema=schema,
                template=template,
                source_file=str(file_path)
            )
            
        except Exception as e:
            logger.error(f"Error loading schema from {file_path}: {e}")
            return None
    
    def _extract_json_from_markdown(self, content: str) -> Optional[str]:
        """
        Extract JSON content from markdown file.
        
        Args:
            content: Markdown file content
            
        Returns:
            JSON string or None if not found
        """
        # Remove comments and clean up the JSON
        lines = content.split('\n')
        json_lines = []
        in_json = False
        
        for line in lines:
            # Skip markdown headers and empty lines at start
            if not in_json and (line.startswith('#') or line.strip() == ''):
                continue
            
            # Start collecting JSON when we see opening brace
            if line.strip().startswith('{') and not in_json:
                in_json = True
            
            if in_json:
                # Remove single-line comments
                if '//' in line:
                    line = line[:line.index('//')]
                
                # Remove trailing commas before closing braces/brackets
                line = re.sub(r',(\s*[}\]])', r'\1', line)
                
                json_lines.append(line)
        
        if not json_lines:
            return None
        
        json_content = '\n'.join(json_lines)
        
        # Additional cleanup for common JSON issues
        json_content = self._clean_json_content(json_content)
        
        return json_content
    
    def _clean_json_content(self, json_content: str) -> str:
        """
        Clean up JSON content to make it parseable.
        
        Args:
            json_content: Raw JSON content
            
        Returns:
            Cleaned JSON content
        """
        # Remove any remaining comments first
        json_content = re.sub(r'//.*', '', json_content)
        
        # Handle dynamic object comments
        json_content = re.sub(r'//.*Dynamic.*', '', json_content)
        json_content = re.sub(r'//.*For.*', '', json_content)
        
        # Remove trailing commas before closing braces/brackets
        # This regex handles commas followed by optional whitespace and closing brace/bracket
        json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
        
        # Clean up extra whitespace and empty lines
        json_content = re.sub(r'\n\s*\n', '\n', json_content)
        
        return json_content.strip()
    
    def _generate_schema_from_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a JSON schema from a template structure.
        
        Args:
            template: Template dictionary
            
        Returns:
            JSON schema dictionary
        """
        def infer_type(value: Any) -> Dict[str, Any]:
            """Infer JSON schema type from a value."""
            # Check boolean first since isinstance(True, int) is True in Python
            if isinstance(value, bool):
                return {"type": "boolean"}
            elif isinstance(value, str):
                return {"type": "string"}
            elif isinstance(value, int):
                return {"type": "integer"}
            elif isinstance(value, float):
                return {"type": "number"}
            elif isinstance(value, list):
                if len(value) > 0:
                    return {
                        "type": "array",
                        "items": infer_type(value[0])
                    }
                else:
                    return {"type": "array"}
            elif isinstance(value, dict):
                properties = {}
                required = []
                
                for key, val in value.items():
                    properties[key] = infer_type(val)
                    # Consider non-empty strings and non-zero numbers as required
                    if (isinstance(val, str) and val) or \
                       (isinstance(val, (int, float)) and val != 0) or \
                       isinstance(val, bool) or \
                       (isinstance(val, (list, dict)) and val):
                        required.append(key)
                
                schema = {
                    "type": "object",
                    "properties": properties
                }
                
                if required:
                    schema["required"] = required
                
                return schema
            else:
                return {"type": "string"}  # Default fallback
        
        return infer_type(template)
    
    def get_schema_for_file_type(self, file_type: str) -> Dict[str, Any]:
        """
        Get the JSON schema for a specific file type.
        
        Args:
            file_type: Type of character file
            
        Returns:
            JSON schema dictionary
            
        Raises:
            ValueError: If file type not supported
        """
        if file_type not in self.schemas:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return self.schemas[file_type].schema.copy()
    
    def get_template_for_file_type(self, file_type: str) -> Dict[str, Any]:
        """
        Get the template structure for a specific file type.
        
        Args:
            file_type: Type of character file
            
        Returns:
            Template dictionary
            
        Raises:
            ValueError: If file type not supported
        """
        if file_type not in self.schemas:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return self._create_empty_template(self.schemas[file_type].template)
    
    def _create_empty_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an empty template with default values.
        
        Args:
            template: Source template
            
        Returns:
            Empty template with appropriate default values
        """
        def create_empty_value(value: Any) -> Any:
            """Create an empty/default value based on type."""
            # Check boolean first since isinstance(True, int) is True in Python
            if isinstance(value, bool):
                return False
            elif isinstance(value, str):
                return ""
            elif isinstance(value, int):
                return 0
            elif isinstance(value, float):
                return 0.0
            elif isinstance(value, list):
                return []
            elif isinstance(value, dict):
                return {k: create_empty_value(v) for k, v in value.items()}
            else:
                return None
        
        return create_empty_value(template)
    
    async def validate_against_schema(self, data: Dict[str, Any], file_type: str) -> ValidationResult:
        """
        Validate data against the schema for a file type.
        
        Args:
            data: Data to validate
            file_type: Type of character file
            
        Returns:
            ValidationResult with validation status and errors
        """
        # Use the existing validator for comprehensive validation
        return await self.validator.validate(data, file_type)
    
    def get_all_file_types(self) -> List[str]:
        """
        Get list of all supported file types.
        
        Returns:
            List of file type names
        """
        return list(self.schemas.keys())
    
    def get_schema_info(self, file_type: str) -> SchemaInfo:
        """
        Get complete schema information for a file type.
        
        Args:
            file_type: Type of character file
            
        Returns:
            SchemaInfo object
            
        Raises:
            ValueError: If file type not supported
        """
        if file_type not in self.schemas:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return self.schemas[file_type]
    
    def reload_schemas(self) -> None:
        """Reload all schemas from the structures directory."""
        self.schemas.clear()
        self._load_all_schemas()
        logger.info("Schemas reloaded")