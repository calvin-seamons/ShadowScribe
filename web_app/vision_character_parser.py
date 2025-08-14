"""
Vision Character Parser Service

This module provides GPT-4.1 vision-powered parsing of PDF character sheet images into structured
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
    """Represents a field that the vision parser was uncertain about."""
    file_type: str
    field_path: str
    extracted_value: Any
    confidence: float
    suggestions: List[str]
    reasoning: str


@dataclass
class CharacterParseResult:
    """Result of vision character parsing."""
    session_id: str
    character_files: Dict[str, Dict[str, Any]]
    uncertain_fields: List[UncertainField]
    parsing_confidence: float
    validation_results: Dict[str, ValidationResult]
    errors: List[str]
    warnings: List[str]


class VisionCharacterParser:
    """
    GPT-4.1 vision-powered character sheet parser that converts PDF images into structured JSON.
    
    Uses schema-driven prompts to extract character data from images and validate against
    the existing JSON schemas from character-json-structures.
    """
    
    def __init__(self, openai_client=None, model: str = "gpt-4.1"):
        """
        Initialize the vision character parser.
        
        Args:
            openai_client: OpenAI client instance (optional, will create if None)
            model: OpenAI model to use for vision parsing (must support vision)
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
        
        # Define the 6 character file types for vision processing
        # Note: objectives_and_contracts excluded (campaign-specific, not on character sheets)
        self.file_types = [
            "character",           # Basic character info, stats, AC, HP
            "spell_list",          # Spells and spellcasting information
            "feats_and_traits",    # Class features, racial traits, feats
            "inventory_list",      # Equipment, items, currency
            "action_list",         # Combat actions and attacks
            "character_background" # Background, personality, backstory
        ]
        
        # Load schemas and templates for the file types we process
        self.schemas = {}
        self.templates = {}
        
        for file_type in self.file_types:
            try:
                self.schemas[file_type] = self.schema_loader.get_schema_for_file_type(file_type)
                self.templates[file_type] = self.schema_loader.get_template_for_file_type(file_type)
            except Exception as e:
                logger.error(f"Failed to load schema for {file_type}: {e}")
        
        logger.info(f"VisionCharacterParser initialized with {len(self.schemas)} schemas")
    
    async def parse_character_data(self, images: List[str], session_id: str) -> CharacterParseResult:
        """
        Parse character data from PDF images using GPT-4.1 vision.
        
        Args:
            images: List of base64 encoded images or file IDs from character sheet pages
            session_id: Session identifier for tracking
            
        Returns:
            CharacterParseResult with parsed data and metadata
        """
        logger.info(f"Starting vision character parsing for session {session_id}")
        print(f"[PDF Import] Starting AI vision parsing for session {session_id}...")
        
        try:
            # Initialize result containers
            character_files = {}
            uncertain_fields = []
            validation_results = {}
            errors = []
            warnings = []
            
            # Parse each file type sequentially using vision
            total_files = len(self.file_types)
            for idx, file_type in enumerate(self.file_types, 1):
                try:
                    logger.info(f"Vision parsing {file_type} data")
                    print(f"[PDF Import] Vision parsing {file_type} ({idx}/{total_files})...")
                    
                    # Generate and execute vision parsing for this file type
                    parsed_data, uncertainties = await self.parse_single_file_type(images, file_type)
                    
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
                                    extracted_value=None,
                                    confidence=validation.confidence,
                                    suggestions=validation.suggestions,
                                    reasoning=f"Intelligent mapping flagged this field: {', '.join(validation.errors)}"
                                ))
                        
                        # Validate mapped data
                        print(f"[PDF Import] Validating {file_type} data...")
                        try:
                            validation_result = await self.validator.validate(mapped_data, file_type)
                            validation_results[file_type] = validation_result
                            
                            if validation_result.is_valid:
                                character_files[file_type] = mapped_data
                            else:
                                print(f"[PDF Import] Validation failed for {file_type}, errors: {[e.message for e in validation_result.errors[:3]]}")
                                # For inventory_list, skip validation temporarily to preserve detailed data
                                if file_type == "inventory_list" and parsed_data:
                                    print(f"[PDF Import] Using parsed inventory data despite validation errors")
                                    character_files[file_type] = mapped_data
                                    warnings.append(f"Used parsed {file_type} data despite validation errors")
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
                        except Exception as e:
                            print(f"[PDF Import] Validation error for {file_type}: {e}")
                            # Use parsed data if validation fails completely
                            if parsed_data:
                                character_files[file_type] = mapped_data
                                warnings.append(f"Used parsed {file_type} data due to validation error")
                            else:
                                character_files[file_type] = self.templates[file_type].copy()
                                errors.append(f"Used template for {file_type} due to validation error")
                    else:
                        # Use empty template if no data could be parsed
                        character_files[file_type] = self.templates[file_type].copy()
                        warnings.append(f"No data extracted for {file_type}, using template")
                    
                    # Add uncertainties to the list
                    uncertain_fields.extend(uncertainties)
                    
                except Exception as e:
                    logger.error(f"Error vision parsing {file_type}: {e}")
                    character_files[file_type] = self.templates[file_type].copy()
                    errors.append(f"Failed to vision parse {file_type}: {str(e)}")
            
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
                
                logger.info(f"Applied comprehensive intelligent mapping with confidence: {comprehensive_mapping.overall_confidence:.2f}")
                print(f"[PDF Import] Intelligent mapping complete (confidence: {comprehensive_mapping.overall_confidence:.0%})")
                
            except Exception as e:
                logger.warning(f"Comprehensive intelligent mapping failed: {e}")
                warnings.append("Comprehensive intelligent mapping failed, using individual file mapping only")
            
            # Calculate overall parsing confidence
            parsing_confidence = self._calculate_parsing_confidence(
                character_files, uncertain_fields, validation_results
            )
            
            logger.info(f"Vision parsing completed with confidence: {parsing_confidence:.2f}")
            print(f"[PDF Import] AI vision parsing complete! Overall confidence: {parsing_confidence:.0%}")
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
            logger.error(f"Critical error during vision character parsing: {e}")
            print(f"[PDF Import] Error during vision parsing: {str(e)}")
            print(f"[PDF Import] Falling back to template data")
            
            # Return fallback result with templates
            fallback_files = {ft: self.templates[ft].copy() for ft in self.file_types}
            
            return CharacterParseResult(
                session_id=session_id,
                character_files=fallback_files,
                uncertain_fields=[],
                parsing_confidence=0.0,
                validation_results={},
                errors=[f"Critical vision parsing error: {str(e)}"],
                warnings=["Using empty templates due to vision parsing failure"]
            )   
 
    async def parse_single_file_type(self, images: List[str], file_type: str) -> Tuple[Dict[str, Any], List[UncertainField]]:
        """
        Parse a specific file type from character sheet images using focused vision prompts.
        
        Args:
            images: List of base64 encoded images or file IDs from all character sheet pages
            file_type: Type of file to parse (character, spell_list, etc.)
            
        Returns:
            Tuple of (parsed_data, uncertain_fields)
        """
        # Build focused vision prompt for this file type
        prompt = self._build_single_file_prompt(file_type)
        
        try:
            # Call GPT-4.1 vision API for parsing
            print(f"[PDF Import] Sending {file_type} images to GPT-4.1 vision model...")
            response_content = await self._call_vision_api(images, prompt)
            print(f"[PDF Import] Received vision response for {file_type}")
            
            # Parse the vision response
            parsed_data, uncertainties = self._parse_vision_response(response_content, file_type)
            
            return parsed_data, uncertainties
            
        except Exception as e:
            logger.error(f"Vision API call failed for {file_type}: {e}")
            return {}, []
    
    async def _call_vision_api(self, images: List[str], prompt: str) -> str:
        """
        Call OpenAI Responses API with images and prompt using GPT-4.1 vision.
        
        Args:
            images: List of base64 encoded images or file IDs
            prompt: Vision parsing prompt
            
        Returns:
            Response content from the API
        """
        # Prepare content with images and text
        content = [
            {"type": "text", "text": prompt}
        ]
        
        # Add images to content
        for image in images:
            if image.startswith('data:image'):
                # Base64 data URL
                content.append({
                    "type": "image_url", 
                    "image_url": {"url": image}
                })
            elif image.startswith('file-'):
                # File ID from Files API - convert to appropriate format
                # Note: This may need adjustment based on actual OpenAI API requirements
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"file://{image}"}
                })
            else:
                # Assume it's a base64 string without data URL prefix
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image}"}
                })
        
        # Make the API call using chat completions with vision
        # Use higher token limit for inventory_list due to detailed item structures
        max_tokens = 4000 if "inventory" in prompt.lower() else 2000
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert D&D character sheet vision parser. Analyze character sheet images accurately and indicate uncertainty when information is unclear or missing."
                },
                {
                    "role": "user",
                    "content": content
                }
            ],
            temperature=0.1,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content.strip()
    
    def _build_single_file_prompt(self, file_type: str) -> str:
        """
        Build a focused vision parsing prompt for a specific JSON file type.
        
        Args:
            file_type: Type of file to parse
            
        Returns:
            Formatted vision prompt string
        """
        # Get schema and template for this file type
        template = self.templates.get(file_type, {})
        
        # Create file-specific vision parsing instructions
        instructions = self._get_vision_instructions_for_file_type(file_type)
        
        prompt = f"""Analyze these D&D character sheet images and extract ONLY {file_type} information.

FOCUS AREA: {file_type.replace('_', ' ').title()}
{instructions}

TARGET JSON STRUCTURE (use this as your template):
{json.dumps(template, indent=2)}

VISION ANALYSIS GUIDELINES:
- Examine all images carefully for relevant information
- Look for handwritten text, printed text, checkboxes, and form fields
- Pay attention to table structures and layout relationships
- Handle various scan qualities, orientations, and formats
- Process both text and graphical elements when relevant

{"SPELL EXTRACTION SPECIAL INSTRUCTIONS:" if file_type == "spell_list" else ""}
{"""- For each spell, create a complete spell object with ALL required fields
- Use your D&D 5e knowledge to fill in standard spell details when not visible
- Pay special attention to prepared/known indicators (checkmarks, filled circles)
- Components MUST be in object format: {"verbal": true/false, "somatic": true/false, "material": "description"}
- Look for concentration and ritual markers
- Provide meaningful descriptions based on spell knowledge
- Include appropriate tags array (e.g., ["damage", "utility", "healing"])
- Set prepared=true for spells that appear to be known/prepared on the sheet""" if file_type == "spell_list" else ""}
{"INVENTORY EXTRACTION SPECIAL INSTRUCTIONS:" if file_type == "inventory_list" else ""}
{"""ITEM FORMAT RULES:
- WEAPONS & ARMOR: Always use detailed objects with all fields (attack_bonus, damage, AC, etc.)
- WONDROUS ITEMS: Use detailed objects for magical items, simple strings for mundane items
- CONSUMABLES: Use strings for simple items (food, basic supplies), objects for potions/magical consumables
- TOOLS: Use strings for basic tools, objects for specialized/magical tools
- CONTAINERS: Use strings for basic containers, objects for magical containers
- UNEQUIPPED ITEMS: Mix of strings and objects based on complexity

EXAMPLES:
- Simple items as strings: "Rations (1 day)", "Rope (50 ft)", "Torch (5)", "Bedroll"
- Complex items as objects: Weapons, armor, magic items, potions, specialized tools

DETAILED OBJECT REQUIREMENTS:
- WEAPONS: Include attack_bonus, damage, damage_type, range, properties array
- ARMOR: Include armor_class, stealth_disadvantage, strength_requirement
- MAGICAL ITEMS: Include magical_properties, requires_attunement, description
- Use your D&D 5e knowledge to fill in standard item details
- Pay attention to equipped indicators (checkmarks, filled circles)
- Look for attunement symbols (* or A) and set attuned/requires_attunement accordingly""" if file_type == "inventory_list" else ""}
{"CHARACTER BACKGROUND EXTRACTION SPECIAL INSTRUCTIONS:" if file_type == "character_background" else ""}
{"""- Extract ALL text VERBATIM - do not paraphrase or summarize
- Copy personality traits, ideals, bonds, and flaws exactly as written
- Include complete backstory text word-for-word from any narrative sections
- Preserve the player's original language, style, and formatting
- Extract any notes, descriptions, or character details exactly as they appear
- If text is handwritten and partially illegible, transcribe what you can read
- Use the backstory.sections array for any additional narrative text
- Include allies, enemies, organizations with full descriptions as written""" if file_type == "character_background" else ""}

CONFIDENCE GUIDELINES:
- HIGH (0.8-1.0): Information is clearly visible and unambiguous
- MEDIUM (0.5-0.7): Information is visible but requires interpretation
- LOW (0.2-0.4): Information is unclear, partially obscured, or hard to read
- VERY_LOW (0.0-0.1): Information is not found or completely illegible

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
      "reasoning": "Why this field is uncertain from vision analysis",
      "suggestions": ["alternative1", "alternative2"]
    }}
  ]
}}

IMPORTANT:
- IGNORE information not related to {file_type}
- Use null for missing information, don't make up data
- Include ALL fields from the template, even if empty
- Mark uncertain extractions in the uncertainties array
- Ensure valid JSON format
- Be conservative with confidence scores for vision-extracted data
{"- For spells: Create complete spell objects even if some details require D&D knowledge" if file_type == "spell_list" else ""}"""
        
        return prompt
    
    def _get_vision_instructions_for_file_type(self, file_type: str) -> str:
        """Get specific vision parsing instructions for each file type."""
        
        instructions = {
            "character": """
LOOK FOR in the character sheet images:
- Character name (usually at the top of the sheet)
- Race and class information (often in header sections)
- Character level (total level, may be sum of multiclass levels)
- Ability scores (STR, DEX, CON, INT, WIS, CHA) - typically 6 numbers between 8-20
- Combat stats: HP (max/current), AC, initiative, speed
- Alignment (Lawful Good, Chaotic Evil, etc.)
- Background information
- Physical characteristics (age, height, weight, etc.)

VISUAL CUES to watch for:
- Ability score boxes or circles with numbers
- HP tracking areas (often with current/max)
- AC values (usually prominent)
- Character level indicators
- Class/race selection areas
- Alignment selection boxes
""",
            
            "character_background": """
LOOK FOR in the character sheet images:
- Background name (Acolyte, Criminal, Folk Hero, etc.) - often in a dropdown or text field
- Personality traits (usually 1-2 sentences describing character behavior)
- Ideals (what drives the character, moral compass)
- Bonds (connections to people, places, or things)
- Flaws (character weaknesses or negative traits)
- Backstory sections and narrative text
- Character description and appearance details
- Personal history or character notes
- Allies, enemies, organizations mentioned
- Any handwritten or typed narrative sections

VERBATIM TEXT EXTRACTION:
- Extract ALL text exactly as written on the character sheet
- Do NOT paraphrase or summarize - copy the exact wording
- Include complete sentences and paragraphs from backstory sections
- Preserve the player's original language and style
- Extract any notes, descriptions, or narrative text word-for-word
- If text is partially illegible, note what you can read and mark uncertain parts

VISUAL CUES to watch for:
- Background selection areas or text fields
- Personality trait text boxes (often labeled)
- Backstory narrative sections (larger text areas)
- Character description fields
- Roleplay information areas
- Notes sections with personal details
- Handwritten text in margins or notes sections
- Multi-line text blocks with character history
""",
            
            "spell_list": """
LOOK FOR in the character sheet images:
- Spell lists (often in tables or organized sections)
- Spell names, levels (0-9), and schools of magic (Evocation, Enchantment, etc.)
- Cantrips (0-level spells) - often listed separately
- Spell slots and spellcasting statistics
- Spellcasting ability (INT, WIS, or CHA) and save DC
- Spell attack bonus
- Prepared vs. known spell indicators (checkboxes, circles, or marks)
- Spell details: casting time, range, duration, components (V/S/M)
- Concentration indicators (often marked with 'C' or 'Concentration')
- Ritual spell indicators (often marked with 'R' or 'Ritual')

DETAILED SPELL EXTRACTION:
For each spell found, extract as much detail as possible:
- Name: The spell's full name
- Prepared: Whether the spell is prepared/known (look for checkmarks, filled circles)
- School: School of magic (Abjuration, Conjuration, Divination, Enchantment, Evocation, Illusion, Necromancy, Transmutation)
- Casting Time: How long to cast (1 action, 1 bonus action, 1 minute, etc.)
- Range: Spell range (Self, Touch, 30 feet, 120 feet, etc.)
- Components: V (Verbal), S (Somatic), M (Material) - look for V/S/M indicators
  Format as: {"verbal": true/false, "somatic": true/false, "material": "material description or empty string"}
- Duration: How long spell lasts (Instantaneous, 1 minute, 1 hour, Concentration, etc.)
- Concentration: Whether spell requires concentration (look for 'C' or 'Concentration')
- Ritual: Whether spell can be cast as ritual (look for 'R' or 'Ritual')
- Description: Brief description of what the spell does (if visible)
- Source: Source book (PHB, XGE, etc.) if indicated

AI SPELL KNOWLEDGE:
If spell details are not fully visible on the character sheet, use your knowledge of D&D 5e spells to fill in standard details for common spells like:
- Mage Hand, Prestidigitation, Fire Bolt (cantrips)
- Magic Missile, Cure Wounds, Shield (1st level)
- Fireball, Counterspell, Healing Word (higher levels)

VISUAL CUES to watch for:
- Spell slot circles or checkboxes (filled/empty)
- Spell level headers or organization (1st level, 2nd level, etc.)
- Spellcasting class sections
- Spell save DC and attack bonus numbers
- Cantrip sections (often at top of spell lists)
- Spell preparation checkboxes or indicators
- V/S/M component indicators next to spell names
- Concentration markers (C) or duration text
- Ritual markers (R) next to applicable spells
""",
            
            "feats_and_traits": """
LOOK FOR in the character sheet images:
- Class features and abilities by level
- Racial traits and special abilities
- Chosen feats and their effects
- Passive abilities and resistances
- Subclass/archetype features
- Special abilities from background or other sources

VISUAL CUES to watch for:
- Feature descriptions and mechanics text
- Level-based ability unlocks or lists
- Racial trait sections (often grouped)
- Feat selection areas with descriptions
- Class feature lists organized by level
- Special ability text blocks
""",
            
            "action_list": """
LOOK FOR in the character sheet images:
- Weapon attacks with attack bonuses and damage
- Combat actions and maneuvers
- Special attack abilities
- Bonus actions and reactions
- Action economy information
- Attack tables or lists

VISUAL ELEMENTS to identify:
- Attack tables with to-hit bonuses (+X to hit)
- Damage dice and modifiers (1d8+3, 2d6+4, etc.)
- Weapon names and properties
- Attack type indicators (melee, ranged)
- Special combat abilities or maneuvers
- Action type labels (Action, Bonus Action, Reaction)
""",
            
            "inventory_list": """
LOOK FOR in the character sheet images:
- Equipment lists and inventory sections
- Currency amounts (GP, SP, CP, etc.)
- Magic items and their properties
- Weight calculations and carrying capacity
- General items, tools, and gear
- Equipment organization (worn, carried, stored)
- Weapon attack bonuses, damage, and properties
- Armor AC values and special properties
- Item descriptions and magical effects
- Attunement indicators (often marked with asterisks or special symbols)
- Proficiency indicators for weapons and tools

ITEM EXTRACTION STRATEGY:
For WEAPONS & ARMOR (always detailed objects):
- Extract all combat stats, properties, magical effects
- Include attack bonuses, damage, AC values, requirements

For OTHER ITEMS (use judgment):
- SIMPLE ITEMS → Use strings: "Rations (1 day)", "Rope (50 ft)", "Bedroll"
- COMPLEX ITEMS → Use objects: Magic items, potions, specialized equipment

SIMPLE ITEM EXAMPLES (use strings):
- Basic food: "Rations (1 day)", "Bread", "Water"
- Basic supplies: "Rope (50 ft)", "Torch (5)", "Bedroll", "Blanket"
- Common tools: "Hammer", "Crowbar", "Shovel"
- Basic containers: "Backpack", "Pouch", "Sack"

COMPLEX ITEM EXAMPLES (use objects):
- Magic items: Potions, enchanted items, wondrous items
- Weapons and armor (always objects)
- Specialized tools: Alchemist's supplies, thieves' tools
- Items with special properties or detailed mechanics

AI ITEM KNOWLEDGE:
Use your D&D 5e knowledge to provide detailed descriptions for common items:
- Standard weapons (longsword, crossbow, etc.) - include standard properties
- Common armor (chain mail, leather armor, etc.) - include standard AC values
- Magic items (Bag of Holding, Ring of Protection, etc.) - include full descriptions
- Tools and equipment - describe their typical uses

VISUAL CUES to identify:
- Equipment tables and lists
- Checkboxes for equipped items (filled = equipped)
- Currency symbols and amounts (gold pieces, etc.)
- Weight totals and encumbrance indicators
- Magic item descriptions or special formatting
- Inventory organization sections
- Item quantity indicators
- Attack bonus numbers (+X to hit)
- Damage notation (1d8+3, 2d6, etc.)
- AC values for armor
- Attunement symbols (* or A)
- Proficiency indicators
"""
        }
        
        return instructions.get(file_type, f"Extract relevant {file_type.replace('_', ' ')} data from the character sheet images.")
    
    def _parse_vision_response(self, content: str, file_type: str) -> Tuple[Dict[str, Any], List[UncertainField]]:
        """
        Parse the vision API response into structured data and uncertainties.
        
        Args:
            content: Vision API response content
            file_type: Type of file being parsed
            
        Returns:
            Tuple of (parsed_data, uncertain_fields)
        """
        try:
            # Clean and extract JSON from response
            json_content = self._extract_json_from_response(content)
            
            if not json_content:
                logger.warning(f"No valid JSON found in vision response for {file_type}")
                logger.warning(f"Raw content preview: {content[:500]}...")
                return {}, []
            
            logger.info(f"Attempting to parse JSON for {file_type}, length: {len(json_content)}")
            response_data = json.loads(json_content)
            logger.info(f"Successfully parsed JSON for {file_type}")
            
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
            logger.error(f"JSON decode error for vision response {file_type}: {e}")
            logger.error(f"Raw response content: {content[:500]}...")  # Log first 500 chars
            return {}, []
        except Exception as e:
            logger.error(f"Error parsing vision response for {file_type}: {e}")
            return {}, []
    
    def _extract_json_from_response(self, content: str) -> Optional[str]:
        """Extract JSON content from vision API response."""
        
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
            logger.warning(f"No opening brace found in content: {content[:200]}...")
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
            logger.warning(f"Unmatched braces in JSON. Brace count: {brace_count}")
            return None
        
        extracted_json = content[start_idx:end_idx]
        logger.info(f"Extracted JSON length: {len(extracted_json)} characters")
        return extracted_json  
  
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
            invalid_count = sum(1 for result in validation_results.values() if not result.is_valid)
            validation_penalty = invalid_count / total_validations * 0.3
        
        # Penalty for uncertain fields
        uncertainty_penalty = 0.0
        if uncertain_fields:
            # Calculate average confidence of uncertain fields
            avg_uncertainty = sum(field.confidence for field in uncertain_fields) / len(uncertain_fields)
            # Convert to penalty (lower confidence = higher penalty)
            uncertainty_penalty = (1.0 - avg_uncertainty) * 0.2
        
        # Calculate final confidence
        final_confidence = max(0.0, base_confidence - validation_penalty - uncertainty_penalty)
        
        return min(1.0, final_confidence)