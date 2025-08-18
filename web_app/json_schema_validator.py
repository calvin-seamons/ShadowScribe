"""
JSON Schema Validator for Knowledge Base Files

This module provides validation capabilities for all D&D character data file types
using JSON schemas derived from the existing file structures.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Represents a validation error."""
    field_path: str
    message: str
    error_type: str  # 'required', 'type', 'format', 'custom'


@dataclass
class ValidationResult:
    """Result of JSON schema validation."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[str]


class JSONSchemaValidator:
    """
    Validates JSON content against schemas for D&D character data files.
    
    Provides validation for:
    - character.json
    - character_background.json
    - feats_and_traits.json
    - action_list.json
    - inventory_list.json
    - objectives_and_contracts.json
    - spell_list.json
    """
    
    def __init__(self):
        """Initialize the validator with schemas."""
        self.schemas = self._load_schemas()
        self.templates = self._load_templates()
        logger.info("JSONSchemaValidator initialized")
    
    def _load_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Load JSON schemas for all supported file types.
        
        Returns:
            Dictionary mapping file types to their schemas
        """
        # Define schemas based on the existing file structures
        schemas = {
            'character': {
                "type": "object",
                "required": ["character_base", "characteristics", "ability_scores", "combat_stats"],
                "properties": {
                    "character_base": {
                        "type": "object",
                        "required": ["name", "race", "class", "total_level"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "race": {"type": "string", "minLength": 1},
                            "subrace": {"type": "string"},
                            "class": {"type": "string", "minLength": 1},
                            "total_level": {"type": "integer", "minimum": 1, "maximum": 20},
                            "alignment": {"type": "string"},
                            "background": {"type": "string"},
                            "lifestyle": {"type": "string"},
                            "hit_dice": {"type": "object"}
                        }
                    },
                    "characteristics": {
                        "type": "object",
                        "properties": {
                            "alignment": {"type": "string"},
                            "gender": {"type": "string"},
                            "eyes": {"type": "string"},
                            "size": {"type": "string"},
                            "height": {"type": "string"},
                            "hair": {"type": "string"},
                            "skin": {"type": "string"},
                            "age": {"type": "integer", "minimum": 0},
                            "weight": {"type": "string"}
                        }
                    },
                    "ability_scores": {
                        "type": "object",
                        "required": ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"],
                        "properties": {
                            "strength": {"type": "integer", "minimum": 1, "maximum": 30},
                            "dexterity": {"type": "integer", "minimum": 1, "maximum": 30},
                            "constitution": {"type": "integer", "minimum": 1, "maximum": 30},
                            "intelligence": {"type": "integer", "minimum": 1, "maximum": 30},
                            "wisdom": {"type": "integer", "minimum": 1, "maximum": 30},
                            "charisma": {"type": "integer", "minimum": 1, "maximum": 30}
                        }
                    },
                    "combat_stats": {
                        "type": "object",
                        "required": ["max_hp", "armor_class"],
                        "properties": {
                            "max_hp": {"type": "integer", "minimum": 1},
                            "armor_class": {"type": "integer", "minimum": 1},
                            "initiative_bonus": {"type": "integer"},
                            "speed": {"type": "integer", "minimum": 0}
                        }
                    },
                    "proficiencies": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["type", "name"],
                            "properties": {
                                "type": {"type": "string", "enum": ["armor", "weapon", "tool", "language", "skill"]},
                                "name": {"type": "string", "minLength": 1}
                            }
                        }
                    },
                    "damage_modifiers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["damage_type", "modifier_type"],
                            "properties": {
                                "damage_type": {"type": "string"},
                                "modifier_type": {"type": "string", "enum": ["resistance", "immunity", "vulnerability"]}
                            }
                        }
                    },
                    "passive_scores": {"type": "object"},
                    "senses": {"type": "object"}
                }
            },
            
            'character_background': {
                "type": "object",
                "required": ["character_id", "background", "characteristics", "backstory"],
                "properties": {
                    "character_id": {"type": "integer"},
                    "background": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "feature": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"}
                                }
                            }
                        }
                    },
                    "characteristics": {
                        "type": "object",
                        "properties": {
                            "personality_traits": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "ideals": {
                                "type": "array", 
                                "items": {"type": "string"}
                            },
                            "bonds": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "flaws": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    },
                    "backstory": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "sections": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["heading", "content"],
                                    "properties": {
                                        "heading": {"type": "string"},
                                        "content": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "organizations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "role"],
                            "properties": {
                                "name": {"type": "string"},
                                "role": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "allies": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"type": "string"},
                                "title": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "enemies": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "notes": {"type": "object"}
                }
            },
            
            'feats_and_traits': {
                "type": "object",
                "required": ["features_and_traits"],
                "properties": {
                    "features_and_traits": {
                        "type": "object",
                        "properties": {
                            "class_features": {"type": "object"},
                            "species_traits": {
                                "type": "object",
                                "properties": {
                                    "species": {"type": "string"},
                                    "subrace": {"type": "string"},
                                    "traits": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["name"],
                                            "properties": {
                                                "name": {"type": "string"},
                                                "source": {"type": "string"},
                                                "effects": {"type": "array"},
                                                "effect": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            },
                            "feats": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["name"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "source": {"type": "string"}
                                    }
                                }
                            },
                            "calculated_features": {"type": "object"}
                        }
                    },
                    "metadata": {"type": "object"}
                }
            },
            
            'action_list': {
                "type": "object",
                "required": ["character_actions"],
                "properties": {
                    "character_actions": {
                        "type": "object",
                        "properties": {
                            "attacks_per_action": {"type": "integer", "minimum": 1},
                            "action_economy": {
                                "type": "object",
                                "properties": {
                                    "actions": {"type": "array"},
                                    "bonus_actions": {"type": "array"},
                                    "reactions": {"type": "array"},
                                    "other_actions": {"type": "array"},
                                    "special_abilities": {"type": "array"}
                                }
                            },
                            "combat_actions_reference": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    },
                    "metadata": {"type": "object"}
                }
            },
            
            'inventory_list': {
                "type": "object",
                "required": ["inventory"],
                "properties": {
                    "inventory": {
                        "type": "object",
                        "properties": {
                            "total_weight": {"type": "number", "minimum": 0},
                            "weight_unit": {"type": "string"},
                            "equipped_items": {
                                "type": "object",
                                "properties": {
                                    "weapons": {"type": "array"},
                                    "armor": {"type": "array"},
                                    "wondrous_items": {"type": "array"},
                                    "rods": {"type": "array"}
                                }
                            },
                            "consumables": {"type": "array"},
                            "utility_items": {"type": "array"},
                            "clothing": {"type": "array"}
                        }
                    },
                    "metadata": {"type": "object"}
                }
            },
            
            'objectives_and_contracts': {
                "type": "object",
                "required": ["objectives_and_contracts"],
                "properties": {
                    "objectives_and_contracts": {
                        "type": "object",
                        "properties": {
                            "active_contracts": {"type": "array"},
                            "current_objectives": {"type": "array"},
                            "completed_objectives": {"type": "array"},
                            "contract_templates": {"type": "object"}
                        }
                    },
                    "metadata": {"type": "object"}
                }
            },
            
            'spell_list': {
                "type": "object",
                "required": ["spellcasting"],
                "properties": {
                    "spellcasting": {
                        "type": "object",
                        "patternProperties": {
                            "^[a-zA-Z_]+$": {
                                "type": "object",
                                "properties": {
                                    "spells": {
                                        "type": "object",
                                        "patternProperties": {
                                            "^(cantrips|[0-9]+[a-z]*_level)$": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "required": ["name", "level", "school"],
                                                    "properties": {
                                                        "name": {"type": "string"},
                                                        "level": {"type": "integer", "minimum": 0, "maximum": 9},
                                                        "school": {"type": "string"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "metadata": {"type": "object"}
                }
            }
        }
        
        return schemas
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load template structures for creating new files.
        
        Returns:
            Dictionary mapping file types to their templates
        """
        templates = {
            'character': {
                "character_base": {
                    "name": "",
                    "race": "",
                    "subrace": "",
                    "class": "",
                    "total_level": 1,
                    "alignment": "",
                    "background": "",
                    "lifestyle": "",
                    "hit_dice": {}
                },
                "characteristics": {
                    "alignment": "",
                    "gender": "",
                    "eyes": "",
                    "size": "Medium",
                    "height": "",
                    "hair": "",
                    "skin": "",
                    "age": 0,
                    "weight": ""
                },
                "ability_scores": {
                    "strength": 10,
                    "dexterity": 10,
                    "constitution": 10,
                    "intelligence": 10,
                    "wisdom": 10,
                    "charisma": 10
                },
                "combat_stats": {
                    "max_hp": 1,
                    "armor_class": 10,
                    "initiative_bonus": 0,
                    "speed": 30
                },
                "proficiencies": [],
                "damage_modifiers": [],
                "passive_scores": {},
                "senses": {}
            },
            
            'character_background': {
                "character_id": 1,
                "background": {
                    "name": "",
                    "feature": {
                        "name": "",
                        "description": ""
                    }
                },
                "characteristics": {
                    "personality_traits": [],
                    "ideals": [],
                    "bonds": [],
                    "flaws": []
                },
                "backstory": {
                    "title": "",
                    "sections": []
                },
                "organizations": [],
                "allies": [],
                "enemies": [],
                "notes": {}
            },
            
            'feats_and_traits': {
                "features_and_traits": {
                    "class_features": {},
                    "species_traits": {
                        "species": "",
                        "subrace": "",
                        "traits": []
                    },
                    "feats": [],
                    "calculated_features": {}
                },
                "metadata": {
                    "version": "1.0",
                    "last_updated": "",
                    "notes": []
                }
            },
            
            'action_list': {
                "character_actions": {
                    "attacks_per_action": 1,
                    "action_economy": {
                        "actions": [],
                        "bonus_actions": [],
                        "reactions": [],
                        "other_actions": [],
                        "special_abilities": []
                    },
                    "combat_actions_reference": []
                },
                "metadata": {
                    "version": "1.0",
                    "last_updated": "",
                    "notes": []
                }
            },
            
            'inventory_list': {
                "inventory": {
                    "total_weight": 0,
                    "weight_unit": "lb",
                    "equipped_items": {
                        "weapons": [],
                        "armor": [],
                        "wondrous_items": [],
                        "rods": []
                    },
                    "consumables": [],
                    "utility_items": [],
                    "clothing": []
                },
                "metadata": {
                    "version": "1.0",
                    "last_updated": "",
                    "notes": []
                }
            },
            
            'objectives_and_contracts': {
                "objectives_and_contracts": {
                    "active_contracts": [],
                    "current_objectives": [],
                    "completed_objectives": [],
                    "contract_templates": {}
                },
                "metadata": {
                    "version": "1.0",
                    "last_updated": "",
                    "notes": []
                }
            },
            
            'spell_list': {
                "spellcasting": {},
                "metadata": {
                    "version": "1.0",
                    "last_updated": "",
                    "notes": []
                }
            }
        }
        
        return templates
    
    async def validate(self, content: Dict[str, Any], file_type: str) -> ValidationResult:
        """
        Validate content against the schema for the specified file type.
        
        Args:
            content: Dictionary content to validate
            file_type: Type of file to validate against
            
        Returns:
            ValidationResult with validation status and errors
        """
        if file_type not in self.schemas:
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError("file_type", f"Unsupported file type: {file_type}", "custom")],
                warnings=[]
            )
        
        schema = self.schemas[file_type]
        errors = []
        warnings = []
        
        try:
            # Basic validation using the schema
            errors.extend(self._validate_object(content, schema, ""))
            
            # File-specific validation
            if file_type == 'character':
                errors.extend(self._validate_character_specific(content))
            elif file_type == 'character_background':
                errors.extend(self._validate_background_specific(content))
            
            is_valid = len(errors) == 0
            
            logger.info(f"Validation for {file_type}: {'passed' if is_valid else 'failed'} with {len(errors)} errors")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError("validation", f"Validation error: {str(e)}", "custom")],
                warnings=[]
            )
    
    def _validate_object(self, obj: Any, schema: Dict[str, Any], path: str) -> List[ValidationError]:
        """Validate an object against a schema."""
        errors = []
        
        if schema.get("type") == "object":
            if not isinstance(obj, dict):
                errors.append(ValidationError(path, f"Expected object, got {type(obj).__name__}", "type"))
                return errors
            
            # Check required fields
            required = schema.get("required", [])
            for field in required:
                if field not in obj:
                    errors.append(ValidationError(f"{path}.{field}" if path else field, f"Required field missing: {field}", "required"))
            
            # Validate properties
            properties = schema.get("properties", {})
            for field, field_schema in properties.items():
                if field in obj:
                    field_path = f"{path}.{field}" if path else field
                    errors.extend(self._validate_object(obj[field], field_schema, field_path))
        
        elif schema.get("type") == "array":
            if not isinstance(obj, list):
                errors.append(ValidationError(path, f"Expected array, got {type(obj).__name__}", "type"))
                return errors
            
            items_schema = schema.get("items", {})
            for i, item in enumerate(obj):
                item_path = f"{path}[{i}]"
                errors.extend(self._validate_object(item, items_schema, item_path))
        
        elif schema.get("type") == "string":
            if not isinstance(obj, str):
                errors.append(ValidationError(path, f"Expected string, got {type(obj).__name__}", "type"))
            elif "minLength" in schema and len(obj) < schema["minLength"]:
                errors.append(ValidationError(path, f"String too short (minimum {schema['minLength']})", "format"))
        
        elif schema.get("type") == "integer":
            if not isinstance(obj, int):
                errors.append(ValidationError(path, f"Expected integer, got {type(obj).__name__}", "type"))
            elif "minimum" in schema and obj < schema["minimum"]:
                errors.append(ValidationError(path, f"Value too small (minimum {schema['minimum']})", "format"))
            elif "maximum" in schema and obj > schema["maximum"]:
                errors.append(ValidationError(path, f"Value too large (maximum {schema['maximum']})", "format"))
        
        elif schema.get("type") == "number":
            if not isinstance(obj, (int, float)):
                errors.append(ValidationError(path, f"Expected number, got {type(obj).__name__}", "type"))
            elif "minimum" in schema and obj < schema["minimum"]:
                errors.append(ValidationError(path, f"Value too small (minimum {schema['minimum']})", "format"))
        
        elif schema.get("type") == "boolean":
            if not isinstance(obj, bool):
                errors.append(ValidationError(path, f"Expected boolean, got {type(obj).__name__}", "type"))
        
        return errors
    
    def _validate_character_specific(self, content: Dict[str, Any]) -> List[ValidationError]:
        """Character-specific validation rules."""
        errors = []
        
        # Validate ability scores are reasonable
        if "ability_scores" in content:
            for ability, score in content["ability_scores"].items():
                if isinstance(score, int) and (score < 1 or score > 30):
                    errors.append(ValidationError(
                        f"ability_scores.{ability}",
                        f"Ability score {score} is outside valid range (1-30)",
                        "format"
                    ))
        
        return errors
    
    def _validate_background_specific(self, content: Dict[str, Any]) -> List[ValidationError]:
        """Background-specific validation rules."""
        errors = []
        
        # Validate backstory sections have content
        if "backstory" in content and "sections" in content["backstory"]:
            for i, section in enumerate(content["backstory"]["sections"]):
                if not section.get("content", "").strip():
                    errors.append(ValidationError(
                        f"backstory.sections[{i}].content",
                        "Backstory section content cannot be empty",
                        "custom"
                    ))
        
        return errors
    
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
        if file_type not in self.schemas:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return self.schemas[file_type].copy()
    
    async def get_template(self, file_type: str) -> Dict[str, Any]:
        """
        Get a template structure for creating new files.
        
        Args:
            file_type: Type of file to get template for
            
        Returns:
            Template dictionary structure
            
        Raises:
            ValueError: If file type not supported
        """
        if file_type not in self.templates:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        template = self.templates[file_type].copy()
        
        # Add current timestamp to metadata if present
        if "metadata" in template and "last_updated" in template["metadata"]:
            template["metadata"]["last_updated"] = datetime.now().isoformat()
        
        return template