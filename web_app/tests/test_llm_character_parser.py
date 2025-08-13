"""
Tests for LLM Character Parser Service

This module contains comprehensive tests for the LLMCharacterParser class,
including mock LLM responses and validation scenarios.
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from llm_character_parser import LLMCharacterParser, CharacterParseResult, UncertainField
from json_schema_validator import ValidationResult, ValidationError


class TestLLMCharacterParser:
    """Test suite for LLMCharacterParser."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def parser(self, mock_openai_client):
        """Create a parser instance with mocked client."""
        return LLMCharacterParser(openai_client=mock_openai_client)
    
    @pytest.fixture
    def sample_pdf_text(self):
        """Sample PDF text for testing."""
        return """
        Character Name: Thorin Ironforge
        Race: Mountain Dwarf
        Class: Fighter
        Level: 5
        
        Ability Scores:
        Strength: 16 (+3)
        Dexterity: 12 (+1)
        Constitution: 15 (+2)
        Intelligence: 10 (+0)
        Wisdom: 13 (+1)
        Charisma: 8 (-1)
        
        Hit Points: 47
        Armor Class: 18
        Speed: 25 ft
        
        Proficiencies:
        - All armor, shields
        - Simple weapons, martial weapons
        - Smith's tools
        
        Spells: None
        
        Equipment:
        - Plate armor
        - Longsword
        - Shield
        - Handaxe (2)
        - 150 gp
        
        Background: Soldier
        Personality Traits: I face problems head-on.
        Ideals: Responsibility. I do what I must.
        Bonds: My honor is my life.
        Flaws: I have trouble trusting in my allies' plans.
        """
    
    @pytest.fixture
    def mock_character_response(self):
        """Mock LLM response for character.json parsing."""
        return {
            "data": {
                "character_base": {
                    "name": "Thorin Ironforge",
                    "race": "Mountain Dwarf",
                    "subrace": "",
                    "class": "Fighter",
                    "class_levels": {"Fighter": 5},
                    "total_level": 5,
                    "experience_points": 6500,
                    "alignment": "",
                    "background": "Soldier",
                    "lifestyle": ""
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
                    "strength": 16,
                    "dexterity": 12,
                    "constitution": 15,
                    "intelligence": 10,
                    "wisdom": 13,
                    "charisma": 8
                },
                "combat_stats": {
                    "max_hp": 47,
                    "current_hp": 47,
                    "temp_hp": 0,
                    "armor_class": 18,
                    "initiative_bonus": 1,
                    "speed": 25,
                    "inspiration": False
                },
                "proficiencies": [
                    {"type": "armor", "name": "All armor", "source": "Fighter"},
                    {"type": "weapon", "name": "Simple weapons", "source": "Fighter"},
                    {"type": "weapon", "name": "Martial weapons", "source": "Fighter"},
                    {"type": "tool", "name": "Smith's tools", "source": "Mountain Dwarf"}
                ],
                "damage_modifiers": [],
                "passive_scores": {},
                "senses": {}
            },
            "uncertainties": [
                {
                    "field_path": "character_base.alignment",
                    "extracted_value": None,
                    "confidence": 0.1,
                    "reasoning": "Alignment not specified in character sheet",
                    "suggestions": ["Lawful Good", "Lawful Neutral"]
                },
                {
                    "field_path": "character_base.experience_points",
                    "extracted_value": 6500,
                    "confidence": 0.6,
                    "reasoning": "Estimated XP based on level 5",
                    "suggestions": ["6500", "7000"]
                }
            ]
        }
    
    @pytest.fixture
    def mock_spell_response(self):
        """Mock LLM response for spell_list.json parsing."""
        return {
            "data": {
                "spellcasting": {},
                "innate_spellcasting": {
                    "source": "",
                    "ability": "",
                    "spell_save_dc": 0,
                    "spells": []
                },
                "metadata": {
                    "version": "1.0",
                    "last_updated": "",
                    "notes": []
                }
            },
            "uncertainties": []
        }
    
    @pytest.fixture
    def mock_background_response(self):
        """Mock LLM response for character_background.json parsing."""
        return {
            "data": {
                "character_id": 1,
                "background": {
                    "name": "Soldier",
                    "feature": {
                        "name": "Military Rank",
                        "description": "You have a military rank from your career as a soldier."
                    }
                },
                "characteristics": {
                    "personality_traits": ["I face problems head-on."],
                    "ideals": ["Responsibility. I do what I must."],
                    "bonds": ["My honor is my life."],
                    "flaws": ["I have trouble trusting in my allies' plans."]
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
            "uncertainties": []
        }
    
    def test_parser_initialization(self, parser):
        """Test parser initializes correctly."""
        assert parser is not None
        assert parser.model == "gpt-4o-mini"
        assert len(parser.file_types) > 0
        assert len(parser.schemas) > 0
        assert len(parser.templates) > 0
    
    def test_build_parsing_prompt(self, parser, sample_pdf_text):
        """Test prompt generation for different file types."""
        
        # Test character prompt
        character_prompt = parser._build_parsing_prompt(sample_pdf_text, "character")
        assert "character" in character_prompt.lower()
        assert "ability scores" in character_prompt.lower()
        assert sample_pdf_text[:100] in character_prompt
        assert "confidence" in character_prompt.lower()
        
        # Test spell prompt
        spell_prompt = parser._build_parsing_prompt(sample_pdf_text, "spell_list")
        assert "spell" in spell_prompt.lower()
        assert "spellcasting" in spell_prompt.lower()
        
        # Test background prompt
        background_prompt = parser._build_parsing_prompt(sample_pdf_text, "character_background")
        assert "personality" in background_prompt.lower()
        assert "background" in background_prompt.lower()
    
    def test_get_file_type_instructions(self, parser):
        """Test file type specific instructions."""
        
        # Test all file types have instructions
        for file_type in parser.file_types:
            instructions = parser._get_file_type_instructions(file_type)
            assert isinstance(instructions, str)
            assert len(instructions) > 0
        
        # Test specific content
        char_instructions = parser._get_file_type_instructions("character")
        assert "ability scores" in char_instructions.lower()
        
        spell_instructions = parser._get_file_type_instructions("spell_list")
        assert "spell" in spell_instructions.lower()
    
    def test_extract_json_from_response(self, parser):
        """Test JSON extraction from various response formats."""
        
        # Test clean JSON
        clean_json = '{"data": {"test": "value"}}'
        result = parser._extract_json_from_response(clean_json)
        assert result == clean_json
        
        # Test JSON with markdown
        markdown_json = '```json\n{"data": {"test": "value"}}\n```'
        result = parser._extract_json_from_response(markdown_json)
        assert result == '{"data": {"test": "value"}}'
        
        # Test JSON with extra text
        extra_text = 'Here is the result:\n{"data": {"test": "value"}}\nThat was the result.'
        result = parser._extract_json_from_response(extra_text)
        assert result == '{"data": {"test": "value"}}'
        
        # Test invalid JSON
        invalid = 'No JSON here'
        result = parser._extract_json_from_response(invalid)
        assert result is None
    
    def test_parse_llm_response(self, parser, mock_character_response):
        """Test parsing of LLM response into structured data."""
        
        # Test valid response
        response_json = json.dumps(mock_character_response)
        parsed_data, uncertainties = parser._parse_llm_response(response_json, "character")
        
        assert isinstance(parsed_data, dict)
        assert "character_base" in parsed_data
        assert parsed_data["character_base"]["name"] == "Thorin Ironforge"
        
        assert len(uncertainties) == 2
        assert uncertainties[0].file_type == "character"
        assert uncertainties[0].field_path == "character_base.alignment"
        assert uncertainties[0].confidence == 0.1
        
        # Test invalid JSON response
        invalid_response = "Invalid JSON content"
        parsed_data, uncertainties = parser._parse_llm_response(invalid_response, "character")
        assert parsed_data == {}
        assert uncertainties == []
    
    def test_nested_value_operations(self, parser):
        """Test getting and setting nested dictionary values."""
        
        test_data = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        
        # Test getting nested value
        value = parser._get_nested_value(test_data, "level1.level2.level3")
        assert value == "value"
        
        # Test getting non-existent value
        value = parser._get_nested_value(test_data, "level1.nonexistent")
        assert value is None
        
        # Test setting nested value
        parser._set_nested_value(test_data, "level1.level2.new_field", "new_value")
        assert test_data["level1"]["level2"]["new_field"] == "new_value"
        
        # Test setting new nested path
        parser._set_nested_value(test_data, "new_level1.new_level2", "another_value")
        assert test_data["new_level1"]["new_level2"] == "another_value"
    
    def test_merge_with_template(self, parser):
        """Test merging parsed data with template."""
        
        # Mock template
        template = {
            "character_base": {
                "name": "",
                "race": "",
                "level": 1
            },
            "ability_scores": {
                "strength": 10,
                "dexterity": 10
            }
        }
        
        # Mock parsed data (partial)
        parsed_data = {
            "character_base": {
                "name": "Test Character",
                "race": "Human"
            },
            "ability_scores": {
                "strength": 15
            }
        }
        
        # Mock the template getter
        parser.templates = {"character": template}
        
        result = parser._merge_with_template(parsed_data, "character")
        
        # Check merged values
        assert result["character_base"]["name"] == "Test Character"
        assert result["character_base"]["race"] == "Human"
        assert result["character_base"]["level"] == 1  # From template
        assert result["ability_scores"]["strength"] == 15  # From parsed
        assert result["ability_scores"]["dexterity"] == 10  # From template
    
    def test_calculate_parsing_confidence(self, parser):
        """Test confidence calculation."""
        
        # Mock data for confidence calculation
        character_files = {
            "character": {"name": "Test"},
            "spell_list": {"spells": []},
            "character_background": {"background": "Test"}
        }
        
        uncertain_fields = [
            UncertainField("character", "name", "Test", 0.8, [], "Clear"),
            UncertainField("character", "race", "Human", 0.5, [], "Unclear")
        ]
        
        validation_results = {
            "character": ValidationResult(True, [], []),
            "spell_list": ValidationResult(True, [], []),
            "character_background": ValidationResult(False, [ValidationError("test", "error", "type")], [])
        }
        
        # Mock file types
        parser.file_types = ["character", "spell_list", "character_background", "inventory_list"]
        
        confidence = parser._calculate_parsing_confidence(
            character_files, uncertain_fields, validation_results
        )
        
        assert 0.0 <= confidence <= 1.0
        assert confidence < 1.0  # Should be penalized for validation failure and uncertainties
    
    @pytest.mark.asyncio
    async def test_apply_schema_corrections(self, parser):
        """Test automatic schema corrections."""
        
        # Mock validation result with errors
        validation_result = ValidationResult(
            is_valid=False,
            errors=[
                ValidationError("character_base.name", "Required field missing: name", "required"),
                ValidationError("ability_scores.strength", "Expected integer, got string", "type"),
                ValidationError("combat_stats.max_hp", "Value too small (minimum 1)", "format")
            ],
            warnings=[]
        )
        
        # Mock data with errors
        data = {
            "character_base": {},  # Missing name
            "ability_scores": {"strength": "16"},  # Wrong type
            "combat_stats": {"max_hp": 0}  # Below minimum
        }
        
        # Mock template
        parser.templates = {
            "character": {
                "character_base": {"name": ""},
                "ability_scores": {"strength": 10},
                "combat_stats": {"max_hp": 1}
            }
        }
        
        corrected = await parser._apply_schema_corrections(data, "character", validation_result)
        
        # Check corrections
        assert corrected["character_base"]["name"] == ""  # Default from template
        assert corrected["ability_scores"]["strength"] == 16  # Converted to int
        assert corrected["combat_stats"]["max_hp"] == 1  # Corrected to minimum
    
    @pytest.mark.asyncio
    async def test_parse_file_type_success(self, parser, mock_character_response, sample_pdf_text):
        """Test successful parsing of a file type."""
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(mock_character_response)
        
        parser.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        parsed_data, uncertainties = await parser._parse_file_type(sample_pdf_text, "character")
        
        assert isinstance(parsed_data, dict)
        assert "character_base" in parsed_data
        assert len(uncertainties) == 2
        
        # Verify LLM was called
        parser.client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_parse_file_type_failure(self, parser, sample_pdf_text):
        """Test handling of LLM parsing failure."""
        
        # Mock LLM failure
        parser.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        parsed_data, uncertainties = await parser._parse_file_type(sample_pdf_text, "character")
        
        assert parsed_data == {}
        assert uncertainties == []
    
    @pytest.mark.asyncio
    async def test_parse_character_data_success(self, parser, sample_pdf_text):
        """Test full character data parsing workflow."""
        
        # Mock successful responses for all file types
        mock_responses = {
            "character": {"data": {"character_base": {"name": "Test"}}, "uncertainties": []},
            "spell_list": {"data": {"spellcasting": {}}, "uncertainties": []},
            "character_background": {"data": {"background": {"name": "Test"}}, "uncertainties": []},
            "feats_and_traits": {"data": {"features_and_traits": {}}, "uncertainties": []},
            "action_list": {"data": {"character_actions": {}}, "uncertainties": []},
            "inventory_list": {"data": {"inventory": {}}, "uncertainties": []},
            "objectives_and_contracts": {"data": {"objectives_and_contracts": {}}, "uncertainties": []}
        }
        
        def mock_parse_file_type(pdf_text, file_type):
            response = mock_responses.get(file_type, {"data": {}, "uncertainties": []})
            return response["data"], []
        
        parser._parse_file_type = AsyncMock(side_effect=mock_parse_file_type)
        
        # Mock validator to return success
        parser.validator.validate = AsyncMock(return_value=ValidationResult(True, [], []))
        
        result = await parser.parse_character_data(sample_pdf_text, "test_session")
        
        assert isinstance(result, CharacterParseResult)
        assert result.session_id == "test_session"
        assert len(result.character_files) == len(parser.file_types)
        assert result.parsing_confidence > 0.0
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_parse_character_data_with_validation_errors(self, parser, sample_pdf_text):
        """Test character parsing with validation errors and corrections."""
        
        # Mock parsing that returns invalid data
        def mock_parse_file_type(pdf_text, file_type):
            return {"invalid": "data"}, []
        
        parser._parse_file_type = AsyncMock(side_effect=mock_parse_file_type)
        
        # Mock validator to return failure, then success after correction
        validation_failure = ValidationResult(False, [ValidationError("test", "error", "type")], [])
        validation_success = ValidationResult(True, [], [])
        
        parser.validator.validate = AsyncMock(side_effect=[validation_failure, validation_success])
        
        # Mock correction method
        parser._apply_schema_corrections = AsyncMock(return_value={"corrected": "data"})
        
        result = await parser.parse_character_data(sample_pdf_text, "test_session")
        
        assert isinstance(result, CharacterParseResult)
        assert len(result.warnings) > 0  # Should have correction warnings
        assert result.parsing_confidence >= 0.0
    
    @pytest.mark.asyncio
    async def test_parse_character_data_critical_failure(self, parser, sample_pdf_text):
        """Test handling of critical parsing failure."""
        
        # Mock critical failure
        parser._parse_file_type = AsyncMock(side_effect=Exception("Critical error"))
        
        result = await parser.parse_character_data(sample_pdf_text, "test_session")
        
        assert isinstance(result, CharacterParseResult)
        assert result.parsing_confidence < 0.5  # Should be low confidence due to template usage
        assert len(result.errors) > 0
        assert any("Critical error" in error for error in result.errors)
        
        # Should still return template data
        assert len(result.character_files) == len(parser.file_types)
    
    def test_confidence_scoring_edge_cases(self, parser):
        """Test confidence scoring with edge cases."""
        
        # Test empty data
        confidence = parser._calculate_parsing_confidence({}, [], {})
        assert confidence == 0.0
        
        # Test scenario with meaningful data
        parser.file_types = ["character", "spell_list"]
        character_files = {
            "character": {"character_base": {"name": "Test Character", "level": 5}},
            "spell_list": {"spellcasting": {"wizard": {"spells": {"cantrips": [{"name": "Mage Hand"}]}}}}
        }
        validation_results = {
            "character": ValidationResult(True, [], []),
            "spell_list": ValidationResult(True, [], [])
        }
        
        confidence = parser._calculate_parsing_confidence(character_files, [], validation_results)
        assert confidence == 1.0
        
        # Test with empty template data (should be penalized)
        empty_files = {"character": {}, "spell_list": {}}
        confidence = parser._calculate_parsing_confidence(empty_files, [], validation_results)
        assert confidence < 0.5  # Should be low due to template usage penalty
        
        # Test with high uncertainty
        uncertain_fields = [
            UncertainField("character", "name", "Test", 0.1, [], "Very uncertain")
        ]
        
        confidence = parser._calculate_parsing_confidence(character_files, uncertain_fields, validation_results)
        assert confidence < 1.0


if __name__ == "__main__":
    pytest.main([__file__])