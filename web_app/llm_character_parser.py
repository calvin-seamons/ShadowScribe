"""
LLM Character Parser Service

This module provides LLM-powered parsing of PDF character sheet text into structured
JSON character data using the existing schema-driven approach.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from json_schema_loader import JSONSchemaLoader
from json_schema_validator import JSONSchemaValidator, ValidationResult
from intelligent_data_mapper import IntelligentDataMapper

logger = logging.getLogger(__name__)


@dataclass
class UncertainField:
    """Represents a field that the LLM was uncertain about."""
    file_type: str
    field_path: str
    extracted_value: Any
    confidence: float
    suggestions: List[str]
    reasoning: str


@dataclass
class CharacterParseResult:
    """Result of LLM character parsing."""
    session_id: str
    character_files: Dict[str, Dict[str, Any]]
    uncertain_fields: List[UncertainField]
    parsing_confidence: float
    validation_results: Dict[str, ValidationResult]
    errors: List[str]
    warnings: List[str]


class LLMCharacterParser:
    """
    LLM-powered character sheet parser that converts PDF text into structured JSON.
    
    Uses schema-driven prompts to extract character data and validate against
    the existing JSON schemas from character-json-structures.
    """
    
    def __init__(self, openai_client=None, model: str = "gpt-4o-mini"):
        """
        Initialize the LLM character parser.
        
        Args:
            openai_client: OpenAI client instance (optional, will create if None)
            model: OpenAI model to use for parsing
        """
        self.model = model
        
        # Initialize OpenAI client if not provided
        if openai_client is None:
            import os
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            self.client = openai_client
        
        # Initialize schema components with proper base directory
        import os
        base_dir = os.getenv("SHADOWSCRIBE_BASE_DIR", os.path.join(os.path.dirname(__file__), '..'))
        structures_path = os.path.join(base_dir, "knowledge_base", "character-json-structures")
        srd_data_path = os.path.join(base_dir, "knowledge_base", "dnd5e_srd_full.json")
        
        self.schema_loader = JSONSchemaLoader(structures_path)
        self.validator = JSONSchemaValidator()
        
        # Initialize intelligent data mapper
        self.data_mapper = IntelligentDataMapper(srd_data_path, self.schema_loader)
        
        # Load all available schemas and templates
        self.file_types = self.schema_loader.get_all_file_types()
        self.schemas = {}
        self.templates = {}
        
        for file_type in self.file_types:
            try:
                self.schemas[file_type] = self.schema_loader.get_schema_for_file_type(file_type)
                self.templates[file_type] = self.schema_loader.get_template_for_file_type(file_type)
            except Exception as e:
                logger.error(f"Failed to load schema for {file_type}: {e}")
        
        logger.info(f"LLMCharacterParser initialized with {len(self.schemas)} schemas")
    
    async def parse_character_data(self, pdf_text: str, session_id: str) -> CharacterParseResult:
        """
        Parse character data from PDF text using LLM.
        
        Args:
            pdf_text: Extracted text from PDF character sheet
            session_id: Session identifier for tracking
            
        Returns:
            CharacterParseResult with parsed data and metadata
        """
        logger.info(f"Starting character parsing for session {session_id}")
        print(f"[PDF Import] Starting AI parsing for session {session_id}...")
        
        try:
            # Initialize result containers
            character_files = {}
            uncertain_fields = []
            validation_results = {}
            errors = []
            warnings = []
            
            # Parse each file type sequentially
            total_files = len(self.file_types)
            for idx, file_type in enumerate(self.file_types, 1):
                try:
                    logger.info(f"Parsing {file_type} data")
                    print(f"[PDF Import] Parsing {file_type} ({idx}/{total_files})...")
                    
                    # Generate and execute parsing prompt
                    parsed_data, uncertainties = await self._parse_file_type(pdf_text, file_type)
                    
                    if parsed_data:
                        # Apply intelligent data mapping and validation
                        mapping_result = self.data_mapper._map_file_data(file_type, parsed_data)
                        mapped_data = mapping_result['data']
                        mapping_validations = mapping_result['validation']
                        mapping_uncertainties = mapping_result['uncertain_fields']
                        
                        # Convert mapping uncertainties to UncertainField objects
                        for field_path in mapping_uncertainties:
                            if field_path in mapping_validations:
                                validation = mapping_validations[field_path]
                                uncertainties.append(UncertainField(
                                    file_type=file_type,
                                    field_path=field_path,
                                    extracted_value=None,  # Could be enhanced to include actual value
                                    confidence=validation.confidence,
                                    suggestions=validation.suggestions,
                                    reasoning=f"Intelligent mapping flagged this field: {', '.join(validation.errors)}"
                                ))
                        
                        # Validate mapped data
                        print(f"[PDF Import] Validating {file_type} data...")
                        validation_result = await self.validator.validate(mapped_data, file_type)
                        validation_results[file_type] = validation_result
                        
                        if validation_result.is_valid:
                            character_files[file_type] = mapped_data
                        else:
                            # Attempt to correct validation errors
                            corrected_data = await self._apply_schema_corrections(
                                mapped_data, file_type, validation_result
                            )
                            
                            # Re-validate corrected data
                            revalidation = await self.validator.validate(corrected_data, file_type)
                            validation_results[file_type] = revalidation
                            
                            if revalidation.is_valid:
                                character_files[file_type] = corrected_data
                                warnings.append(f"Applied corrections to {file_type} data")
                            else:
                                # Use template with extracted values where possible
                                template_data = self._merge_with_template(parsed_data, file_type)
                                character_files[file_type] = template_data
                                errors.append(f"Used template for {file_type} due to validation errors")
                    else:
                        # Use empty template if no data could be parsed
                        character_files[file_type] = self.templates[file_type].copy()
                        warnings.append(f"No data extracted for {file_type}, using template")
                    
                    # Add uncertainties to the list
                    uncertain_fields.extend(uncertainties)
                    
                except Exception as e:
                    logger.error(f"Error parsing {file_type}: {e}")
                    character_files[file_type] = self.templates[file_type].copy()
                    errors.append(f"Failed to parse {file_type}: {str(e)}")
            
            # Apply comprehensive intelligent data mapping across all files
            try:
                print(f"[PDF Import] Applying intelligent data mapping...")
                comprehensive_mapping = self.data_mapper.map_character_data(character_files)
                
                # Update character files with comprehensive mapping results
                character_files.update(comprehensive_mapping.mapped_data)
                
                # Add comprehensive mapping uncertainties
                for field_path in comprehensive_mapping.uncertain_fields:
                    # Parse field path to get file type and field
                    parts = field_path.split('.', 1)
                    if len(parts) >= 2:
                        file_type_part = parts[0]
                        field_part = parts[1]
                        
                        uncertain_fields.append(UncertainField(
                            file_type=file_type_part,
                            field_path=field_part,
                            extracted_value=None,
                            confidence=comprehensive_mapping.overall_confidence,
                            suggestions=[],
                            reasoning="Comprehensive intelligent mapping flagged this field"
                        ))
                
                # Update validation results with comprehensive mapping results
                for file_type, file_validations in comprehensive_mapping.validation_results.items():
                    if file_type not in validation_results:
                        validation_results[file_type] = {}
                    # Note: This would need to be adapted based on the actual validation result structure
                
                logger.info(f"Applied comprehensive intelligent mapping with confidence: {comprehensive_mapping.overall_confidence:.2f}")
                print(f"[PDF Import] Intelligent mapping complete (confidence: {comprehensive_mapping.overall_confidence:.0%})")
                
            except Exception as e:
                logger.warning(f"Comprehensive intelligent mapping failed: {e}")
                warnings.append("Comprehensive intelligent mapping failed, using individual file mapping only")
            
            # Calculate overall parsing confidence
            parsing_confidence = self._calculate_parsing_confidence(
                character_files, uncertain_fields, validation_results
            )
            
            logger.info(f"Parsing completed with confidence: {parsing_confidence:.2f}")
            print(f"[PDF Import] AI parsing complete! Overall confidence: {parsing_confidence:.0%}")
            print(f"[PDF Import] Found {len(uncertain_fields)} fields that may need review")
            
            return CharacterParseResult(
                session_id=session_id,
                character_files=character_files,
                uncertain_fields=uncertain_fields,
                parsing_confidence=parsing_confidence,
                validation_results=validation_results,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Critical error during character parsing: {e}")
            print(f"[PDF Import] Error during parsing: {str(e)}")
            print(f"[PDF Import] Falling back to template data")
            
            # Return fallback result with templates
            fallback_files = {ft: self.templates[ft].copy() for ft in self.file_types}
            
            return CharacterParseResult(
                session_id=session_id,
                character_files=fallback_files,
                uncertain_fields=[],
                parsing_confidence=0.0,
                validation_results={},
                errors=[f"Critical parsing error: {str(e)}"],
                warnings=["Using empty templates due to parsing failure"]
            )
    
    async def _parse_file_type(self, pdf_text: str, file_type: str) -> Tuple[Dict[str, Any], List[UncertainField]]:
        """
        Parse a specific file type from PDF text.
        
        Args:
            pdf_text: PDF text content
            file_type: Type of file to parse
            
        Returns:
            Tuple of (parsed_data, uncertain_fields)
        """
        # Build parsing prompt for this file type
        prompt = self._build_parsing_prompt(pdf_text, file_type)
        
        try:
            # Call LLM for parsing
            print(f"[PDF Import] Sending {file_type} data to AI model...")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert D&D character sheet parser. Extract data accurately and indicate uncertainty when information is unclear or missing."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            print(f"[PDF Import] Received AI response for {file_type}")
            
            content = response.choices[0].message.content.strip()
            
            # Parse the LLM response
            parsed_data, uncertainties = self._parse_llm_response(content, file_type)
            
            return parsed_data, uncertainties
            
        except Exception as e:
            logger.error(f"LLM call failed for {file_type}: {e}")
            return {}, []
    
    def _build_parsing_prompt(self, pdf_text: str, file_type: str) -> str:
        """
        Build a structured parsing prompt for a specific file type.
        
        Args:
            pdf_text: PDF text content
            file_type: Type of file to parse
            
        Returns:
            Formatted prompt string
        """
        # Get schema and template for this file type
        schema = self.schemas.get(file_type, {})
        template = self.templates.get(file_type, {})
        
        # Create file-specific parsing instructions
        instructions = self._get_file_type_instructions(file_type)
        
        prompt = f"""Extract {file_type} data from this D&D character sheet text.

CHARACTER SHEET TEXT:
{pdf_text[:4000]}  # Limit text to avoid token limits

TARGET STRUCTURE (use this as your template):
{json.dumps(template, indent=2)}

PARSING INSTRUCTIONS:
{instructions}

CONFIDENCE GUIDELINES:
- HIGH (0.8-1.0): Information is clearly stated and unambiguous
- MEDIUM (0.5-0.7): Information is present but requires interpretation
- LOW (0.2-0.4): Information is unclear or partially missing
- VERY_LOW (0.0-0.1): Information is not found or completely unclear

RESPONSE FORMAT:
Return a JSON object with this exact structure:
{{
  "data": {{
    // The parsed {file_type} data matching the template structure
  }},
  "uncertainties": [
    {{
      "field_path": "path.to.field",
      "extracted_value": "value or null",
      "confidence": 0.5,
      "reasoning": "Why this field is uncertain",
      "suggestions": ["alternative1", "alternative2"]
    }}
  ]
}}

IMPORTANT:
- Use null for missing information, don't make up data
- Include ALL fields from the template, even if empty
- Mark uncertain extractions in the uncertainties array
- Ensure valid JSON format
- Be conservative with confidence scores"""
        
        return prompt
    
    def _get_file_type_instructions(self, file_type: str) -> str:
        """Get specific parsing instructions for each file type."""
        
        instructions = {
            "character": """
- Extract basic character information: name, race, class, level, ability scores
- Look for ability scores (STR, DEX, CON, INT, WIS, CHA) - usually 6 numbers between 8-20
- Find combat stats: HP, AC, initiative, speed
- Identify proficiencies, skills, and saving throws
- Extract physical characteristics and alignment
- For multiclass characters, parse class levels into class_levels object
""",
            
            "character_background": """
- Extract personality traits, ideals, bonds, and flaws (usually 4 categories)
- Look for background name (Acolyte, Criminal, Folk Hero, etc.)
- Find backstory sections and narrative text
- Identify allies, enemies, and organizations
- Extract any personal history or character notes
""",
            
            "spell_list": """
- Find spellcasting classes and their spell lists
- Extract spell names, levels (0-9), and schools of magic
- Look for spell slots, spell save DC, and spell attack bonus
- Identify cantrips (0-level spells) separately
- Parse spell components (V, S, M) and descriptions
- Find spellcasting ability (INT, WIS, or CHA)
""",
            
            "feats_and_traits": """
- Extract class features by class and level
- Find racial traits and abilities
- Identify feats and their effects
- Look for special abilities, resistances, and immunities
- Parse passive abilities and triggered effects
- Extract subclass/archetype features
""",
            
            "action_list": """
- Find attack actions and combat abilities
- Extract weapon attacks with attack bonuses and damage
- Identify special combat actions and maneuvers
- Look for bonus actions, reactions, and other actions
- Parse action economy information
- Find attacks per action and combat options
""",
            
            "inventory_list": """
- Extract weapons, armor, and equipment
- Find currency amounts (gold, silver, copper, etc.)
- Identify magic items and their properties
- Parse equipment weight and carrying capacity
- Extract consumables like potions and scrolls
- Look for equipped vs. carried items
""",
            
            "objectives_and_contracts": """
- Find active quests and missions
- Extract current objectives and goals
- Identify completed tasks and achievements
- Look for contracts, jobs, or assignments
- Parse quest rewards and consequences
- Find patron or employer information
"""
        }
        
        return instructions.get(file_type, "Extract relevant character data for this file type.")
    
    def _parse_llm_response(self, content: str, file_type: str) -> Tuple[Dict[str, Any], List[UncertainField]]:
        """
        Parse the LLM response into structured data and uncertainties.
        
        Args:
            content: LLM response content
            file_type: Type of file being parsed
            
        Returns:
            Tuple of (parsed_data, uncertain_fields)
        """
        try:
            # Clean and extract JSON from response
            json_content = self._extract_json_from_response(content)
            
            if not json_content:
                logger.warning(f"No valid JSON found in LLM response for {file_type}")
                return {}, []
            
            response_data = json.loads(json_content)
            
            # Extract data and uncertainties
            parsed_data = response_data.get("data", {})
            uncertainty_list = response_data.get("uncertainties", [])
            
            # Convert uncertainty list to UncertainField objects
            uncertain_fields = []
            for unc in uncertainty_list:
                if isinstance(unc, dict):
                    uncertain_field = UncertainField(
                        file_type=file_type,
                        field_path=unc.get("field_path", ""),
                        extracted_value=unc.get("extracted_value"),
                        confidence=float(unc.get("confidence", 0.0)),
                        suggestions=unc.get("suggestions", []),
                        reasoning=unc.get("reasoning", "")
                    )
                    uncertain_fields.append(uncertain_field)
            
            return parsed_data, uncertain_fields
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {file_type}: {e}")
            return {}, []
        except Exception as e:
            logger.error(f"Error parsing LLM response for {file_type}: {e}")
            return {}, []
    
    def _extract_json_from_response(self, content: str) -> Optional[str]:
        """Extract JSON content from LLM response."""
        
        # Remove markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        # Find JSON object boundaries
        content = content.strip()
        
        # Look for the main JSON object
        start_idx = content.find("{")
        if start_idx == -1:
            return None
        
        # Find matching closing brace
        brace_count = 0
        end_idx = start_idx
        
        for i, char in enumerate(content[start_idx:], start_idx):
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        if brace_count != 0:
            return None
        
        return content[start_idx:end_idx]
    
    async def _apply_schema_corrections(self, data: Dict[str, Any], file_type: str, 
                                      validation_result: ValidationResult) -> Dict[str, Any]:
        """
        Apply automatic corrections to fix common schema validation errors.
        
        Args:
            data: Original parsed data
            file_type: Type of file
            validation_result: Validation result with errors
            
        Returns:
            Corrected data dictionary
        """
        corrected_data = data.copy()
        
        for error in validation_result.errors:
            try:
                # Fix missing required fields
                if error.error_type == "required":
                    field_path = error.field_path
                    self._set_default_value(corrected_data, field_path, file_type)
                
                # Fix type errors
                elif error.error_type == "type":
                    field_path = error.field_path
                    self._fix_type_error(corrected_data, field_path, error.message)
                
                # Fix format errors
                elif error.error_type == "format":
                    field_path = error.field_path
                    self._fix_format_error(corrected_data, field_path, error.message)
                    
            except Exception as e:
                logger.warning(f"Could not apply correction for {error.field_path}: {e}")
        
        return corrected_data
    
    def _set_default_value(self, data: Dict[str, Any], field_path: str, file_type: str):
        """Set a default value for a missing required field."""
        
        # Get the template value for this field
        template = self.templates.get(file_type, {})
        template_value = self._get_nested_value(template, field_path)
        
        if template_value is not None:
            self._set_nested_value(data, field_path, template_value)
        else:
            # Fallback defaults based on field name
            if "name" in field_path.lower():
                self._set_nested_value(data, field_path, "")
            elif "level" in field_path.lower():
                self._set_nested_value(data, field_path, 1)
            elif "hp" in field_path.lower():
                self._set_nested_value(data, field_path, 1)
            else:
                self._set_nested_value(data, field_path, None)
    
    def _fix_type_error(self, data: Dict[str, Any], field_path: str, error_message: str):
        """Fix type conversion errors."""
        
        current_value = self._get_nested_value(data, field_path)
        
        if "Expected integer" in error_message:
            try:
                # Try to convert to integer
                if isinstance(current_value, str):
                    # Extract numbers from string
                    numbers = re.findall(r'-?\d+', current_value)
                    if numbers:
                        self._set_nested_value(data, field_path, int(numbers[0]))
                    else:
                        self._set_nested_value(data, field_path, 0)
                elif isinstance(current_value, float):
                    self._set_nested_value(data, field_path, int(current_value))
            except (ValueError, TypeError):
                self._set_nested_value(data, field_path, 0)
        
        elif "Expected string" in error_message:
            if current_value is not None:
                self._set_nested_value(data, field_path, str(current_value))
            else:
                self._set_nested_value(data, field_path, "")
        
        elif "Expected boolean" in error_message:
            if isinstance(current_value, str):
                self._set_nested_value(data, field_path, current_value.lower() in ["true", "yes", "1"])
            else:
                self._set_nested_value(data, field_path, bool(current_value))
        
        elif "Expected array" in error_message:
            if not isinstance(current_value, list):
                self._set_nested_value(data, field_path, [])
    
    def _fix_format_error(self, data: Dict[str, Any], field_path: str, error_message: str):
        """Fix format validation errors."""
        
        current_value = self._get_nested_value(data, field_path)
        
        if "minimum" in error_message.lower():
            # Extract minimum value from error message
            min_match = re.search(r'minimum (\d+)', error_message)
            if min_match and isinstance(current_value, (int, float)):
                min_val = int(min_match.group(1))
                if current_value < min_val:
                    self._set_nested_value(data, field_path, min_val)
        
        elif "maximum" in error_message.lower():
            # Extract maximum value from error message
            max_match = re.search(r'maximum (\d+)', error_message)
            if max_match and isinstance(current_value, (int, float)):
                max_val = int(max_match.group(1))
                if current_value > max_val:
                    self._set_nested_value(data, field_path, max_val)
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get a nested value from a dictionary using dot notation."""
        
        keys = field_path.split(".")
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], field_path: str, value: Any):
        """Set a nested value in a dictionary using dot notation."""
        
        keys = field_path.split(".")
        current = data
        
        # Navigate to the parent of the target field
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def _merge_with_template(self, parsed_data: Dict[str, Any], file_type: str) -> Dict[str, Any]:
        """Merge parsed data with template to ensure all required fields exist."""
        
        template = self.templates.get(file_type, {}).copy()
        
        def merge_recursive(template_dict: Dict[str, Any], parsed_dict: Dict[str, Any]) -> Dict[str, Any]:
            """Recursively merge parsed data into template."""
            
            result = template_dict.copy()
            
            for key, value in parsed_dict.items():
                if key in result:
                    if isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = merge_recursive(result[key], value)
                    else:
                        result[key] = value
                else:
                    result[key] = value
            
            return result
        
        return merge_recursive(template, parsed_data)
    
    def _calculate_parsing_confidence(self, character_files: Dict[str, Dict[str, Any]], 
                                    uncertain_fields: List[UncertainField],
                                    validation_results: Dict[str, ValidationResult]) -> float:
        """Calculate overall parsing confidence score."""
        
        if not character_files:
            return 0.0
        
        # Base confidence from successful parsing
        base_confidence = len(character_files) / len(self.file_types)
        
        # Penalty for validation errors
        validation_penalty = 0.0
        total_validations = len(validation_results)
        
        if total_validations > 0:
            failed_validations = sum(1 for vr in validation_results.values() if not vr.is_valid)
            validation_penalty = failed_validations / total_validations * 0.3
        
        # Penalty for uncertain fields
        uncertainty_penalty = 0.0
        if uncertain_fields:
            avg_uncertainty = sum(1.0 - uf.confidence for uf in uncertain_fields) / len(uncertain_fields)
            uncertainty_penalty = avg_uncertainty * 0.2
        
        # Additional penalty for parsing errors (check if we have errors in the result)
        # This is a heuristic - if we're using all templates, confidence should be low
        template_usage_penalty = 0.0
        non_empty_files = 0
        for file_data in character_files.values():
            # Check if the file has meaningful data beyond template defaults
            if self._has_meaningful_data(file_data):
                non_empty_files += 1
        
        if non_empty_files == 0:
            # All files are just templates, very low confidence
            template_usage_penalty = 0.8
        
        # Calculate final confidence
        final_confidence = max(0.0, base_confidence - validation_penalty - uncertainty_penalty - template_usage_penalty)
        
        return min(1.0, final_confidence)
    
    def _has_meaningful_data(self, file_data: Dict[str, Any]) -> bool:
        """Check if file data contains meaningful parsed information beyond template defaults."""
        
        def has_non_default_values(obj: Any) -> bool:
            """Recursively check for non-default values."""
            if isinstance(obj, dict):
                for value in obj.values():
                    if has_non_default_values(value):
                        return True
                return False
            elif isinstance(obj, list):
                return len(obj) > 0 and any(has_non_default_values(item) for item in obj)
            elif isinstance(obj, str):
                return obj.strip() != ""
            elif isinstance(obj, (int, float)):
                return obj != 0
            elif isinstance(obj, bool):
                return obj  # True is considered meaningful
            else:
                return obj is not None
        
        return has_non_default_values(file_data)
    
    async def apply_intelligent_mapping(self, character_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply intelligent data mapping to existing character data.
        
        Args:
            character_data: Dictionary of character file data
            
        Returns:
            Dictionary with mapped data, validation results, and uncertainties
        """
        try:
            # Apply comprehensive intelligent data mapping
            mapping_result = self.data_mapper.map_character_data(character_data)
            
            # Convert mapping uncertainties to UncertainField objects
            uncertain_fields = []
            for field_path in mapping_result.uncertain_fields:
                parts = field_path.split('.', 1)
                if len(parts) >= 2:
                    file_type_part = parts[0]
                    field_part = parts[1]
                    
                    # Get validation info if available
                    validation_info = None
                    if file_type_part in mapping_result.validation_results:
                        file_validations = mapping_result.validation_results[file_type_part]
                        if field_path in file_validations:
                            validation_info = file_validations[field_path]
                    
                    uncertain_fields.append(UncertainField(
                        file_type=file_type_part,
                        field_path=field_part,
                        extracted_value=None,
                        confidence=validation_info.confidence if validation_info else mapping_result.overall_confidence,
                        suggestions=validation_info.suggestions if validation_info else [],
                        reasoning=f"Intelligent mapping: {', '.join(validation_info.errors) if validation_info else 'Flagged for review'}"
                    ))
            
            return {
                'mapped_data': mapping_result.mapped_data,
                'uncertain_fields': uncertain_fields,
                'overall_confidence': mapping_result.overall_confidence,
                'validation_results': mapping_result.validation_results
            }
            
        except Exception as e:
            logger.error(f"Failed to apply intelligent mapping: {e}")
            return {
                'mapped_data': character_data,
                'uncertain_fields': [],
                'overall_confidence': 0.5,
                'validation_results': {}
            }
    
    def validate_spell_name(self, spell_name: str):
        """
        Validate a spell name using the intelligent data mapper.
        
        Args:
            spell_name: The spell name to validate
            
        Returns:
            ValidationResult from the intelligent data mapper
        """
        return self.data_mapper.validate_spell_name(spell_name)
    
    def categorize_ability(self, ability_name: str, expected_type: str):
        """
        Categorize an ability using the intelligent data mapper.
        
        Args:
            ability_name: Name of the ability/feature
            expected_type: Expected category
            
        Returns:
            ValidationResult from the intelligent data mapper
        """
        return self.data_mapper.categorize_ability(ability_name, expected_type)
    
    def classify_equipment(self, item_name: str, expected_type: str):
        """
        Classify equipment using the intelligent data mapper.
        
        Args:
            item_name: Name of the equipment item
            expected_type: Expected equipment type
            
        Returns:
            ValidationResult from the intelligent data mapper
        """
        return self.data_mapper.classify_equipment(item_name, expected_type)