"""
Tests for Vision Character Parser Service

This module provides comprehensive tests for the VisionCharacterParser class,
including mock image responses and vision API integration testing.
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision_character_parser import VisionCharacterParser, UncertainField, CharacterParseResult


class TestVisionCharacterParser:
    """Test suite for VisionCharacterParser."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def mock_schema_loader(self):
        """Create a mock schema loader."""
        loader = MagicMock()
        loader.get_schema_for_file_type.return_value = {
            "type": "object",
            "properties": {
                "character_base": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "level": {"type": "integer"}
                    }
                }
            }
        }
        loader.get_template_for_file_type.return_value = {
            "character_base": {
                "name": "",
                "level": 1
            }
        }
        return loader
    
    @pytest.fixture
    def mock_validator(self):
        """Create a mock validator."""
        validator = AsyncMock()
        validator.validate.return_value = MagicMock(
            is_valid=True,
            errors=[],
            warnings=[]
        )
        return validator
    
    @pytest.fixture
    def mock_data_mapper(self):
        """Create a mock data mapper."""
        mapper = MagicMock()
        mapper._map_file_data.return_value = {
            'data': {"character_base": {"name": "Test Character", "level": 5}},
            'validation': {},
            'uncertain_fields': []
        }
        mapper.map_character_data.return_value = MagicMock(
            mapped_data={"character": {"character_base": {"name": "Test Character", "level": 5}}},
            uncertain_fields=[],
            overall_confidence=0.85
        )
        return mapper
    
    @pytest.fixture
    def vision_parser(self, mock_openai_client):
        """Create a VisionCharacterParser instance with mocked dependencies."""
        with patch('vision_character_parser.JSONSchemaLoader') as mock_loader_class, \
             patch('vision_character_parser.JSONSchemaValidator') as mock_validator_class, \
             patch('vision_character_parser.IntelligentDataMapper') as mock_mapper_class:
            
            # Configure mocks
            mock_loader = MagicMock()
            mock_loader.get_schema_for_file_type.return_value = {"type": "object"}
            mock_loader.get_template_for_file_type.return_value = {"character_base": {"name": "", "level": 1}}
            mock_loader_class.return_value = mock_loader
            
            mock_validator = AsyncMock()
            mock_validator.validate.return_value = MagicMock(is_valid=True, errors=[], warnings=[])
            mock_validator_class.return_value = mock_validator
            
            mock_mapper = MagicMock()
            mock_mapper._map_file_data.return_value = {
                'data': {"character_base": {"name": "Test", "level": 1}},
                'validation': {},
                'uncertain_fields': []
            }
            mock_mapper.map_character_data.return_value = MagicMock(
                mapped_data={"character": {"character_base": {"name": "Test", "level": 1}}},
                uncertain_fields=[],
                overall_confidence=0.8
            )
            mock_mapper_class.return_value = mock_mapper
            
            parser = VisionCharacterParser(openai_client=mock_openai_client)
            return parser
    
    @pytest.fixture
    def sample_images(self):
        """Sample base64 encoded images for testing."""
        return [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA4849a6wAAAABJRU5ErkJggg=="
        ]
    
    @pytest.fixture
    def mock_vision_response(self):
        """Mock vision API response."""
        return {
            "data": {
                "character_base": {
                    "name": "Thorin Ironforge",
                    "race": "Dwarf",
                    "class": "Fighter",
                    "total_level": 5
                },
                "ability_scores": {
                    "strength": 16,
                    "dexterity": 12,
                    "constitution": 15,
                    "intelligence": 10,
                    "wisdom": 13,
                    "charisma": 8
                }
            },
            "uncertainties": [
                {
                    "field_path": "character_base.background",
                    "extracted_value": "Soldier",
                    "confidence": 0.6,
                    "reasoning": "Background text is partially obscured",
                    "suggestions": ["Soldier", "Folk Hero"]
                }
            ]
        }

    def test_initialization(self, mock_openai_client):
        """Test VisionCharacterParser initialization."""
        with patch('vision_character_parser.JSONSchemaLoader'), \
             patch('vision_character_parser.JSONSchemaValidator'), \
             patch('vision_character_parser.IntelligentDataMapper'):
            
            parser = VisionCharacterParser(openai_client=mock_openai_client)
            
            assert parser.model == "gpt-4.1"
            assert parser.client == mock_openai_client
            assert len(parser.file_types) == 6
            assert "character" in parser.file_types
            assert "spell_list" in parser.file_types
            assert "objectives_and_contracts" not in parser.file_types  # Should be excluded
    
    def test_file_types_exclude_objectives(self, vision_parser):
        """Test that objectives_and_contracts is excluded from vision processing."""
        assert "objectives_and_contracts" not in vision_parser.file_types
        assert len(vision_parser.file_types) == 6
        expected_types = [
            "character", "spell_list", "feats_and_traits", 
            "inventory_list", "action_list", "character_background"
        ]
        for file_type in expected_types:
            assert file_type in vision_parser.file_types
    
    @pytest.mark.asyncio
    async def test_call_vision_api_with_base64_images(self, vision_parser, sample_images):
        """Test vision API call with base64 encoded images."""
        prompt = "Test prompt"
        
        # Mock the API response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test response"
        vision_parser.client.chat.completions.create.return_value = mock_response
        
        result = await vision_parser._call_vision_api(sample_images, prompt)
        
        assert result == "Test response"
        vision_parser.client.chat.completions.create.assert_called_once()
        
        # Verify the call arguments
        call_args = vision_parser.client.chat.completions.create.call_args
        assert call_args[1]['model'] == "gpt-4.1"
        assert call_args[1]['temperature'] == 0.1
        assert call_args[1]['max_tokens'] == 2000
        
        # Check that images were included in content
        user_message = call_args[1]['messages'][1]
        assert user_message['role'] == 'user'
        content = user_message['content']
        
        # Should have text prompt + 2 images
        assert len(content) == 3
        assert content[0]['type'] == 'text'
        assert content[1]['type'] == 'image_url'
        assert content[2]['type'] == 'image_url'
    
    @pytest.mark.asyncio
    async def test_call_vision_api_with_file_ids(self, vision_parser):
        """Test vision API call with file IDs."""
        file_images = ["file-abc123", "file-def456"]
        prompt = "Test prompt"
        
        # Mock the API response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test response"
        vision_parser.client.chat.completions.create.return_value = mock_response
        
        result = await vision_parser._call_vision_api(file_images, prompt)
        
        assert result == "Test response"
        
        # Check that file IDs were converted properly
        call_args = vision_parser.client.chat.completions.create.call_args
        user_message = call_args[1]['messages'][1]
        content = user_message['content']
        
        assert content[1]['image_url']['url'] == "file://file-abc123"
        assert content[2]['image_url']['url'] == "file://file-def456"
    
    def test_build_single_file_prompt_character(self, vision_parser):
        """Test building focused prompt for character file type."""
        prompt = vision_parser._build_single_file_prompt("character")
        
        assert "character information" in prompt.lower()
        assert "ability scores" in prompt.lower()
        assert "STR, DEX, CON, INT, WIS, CHA" in prompt
        assert "IGNORE information not related to character" in prompt
        assert "TARGET JSON STRUCTURE" in prompt
        assert "CONFIDENCE GUIDELINES" in prompt
    
    def test_build_single_file_prompt_spell_list(self, vision_parser):
        """Test building focused prompt for spell_list file type."""
        prompt = vision_parser._build_single_file_prompt("spell_list")
        
        assert "spell" in prompt.lower()
        assert "cantrips" in prompt.lower()
        assert "spell slots" in prompt.lower()
        assert "IGNORE information not related to spell_list" in prompt
        assert "spell level headers" in prompt.lower()
    
    def test_build_single_file_prompt_inventory(self, vision_parser):
        """Test building focused prompt for inventory_list file type."""
        prompt = vision_parser._build_single_file_prompt("inventory_list")
        
        assert "equipment" in prompt.lower()
        assert "currency" in prompt.lower()
        assert "GP, SP, CP" in prompt
        assert "magic items" in prompt.lower()
        assert "IGNORE information not related to inventory_list" in prompt
    
    def test_parse_vision_response_success(self, vision_parser, mock_vision_response):
        """Test parsing successful vision API response."""
        response_content = json.dumps(mock_vision_response)
        
        parsed_data, uncertainties = vision_parser._parse_vision_response(response_content, "character")
        
        assert parsed_data["character_base"]["name"] == "Thorin Ironforge"
        assert parsed_data["character_base"]["total_level"] == 5
        assert parsed_data["ability_scores"]["strength"] == 16
        
        assert len(uncertainties) == 1
        assert uncertainties[0].field_path == "character_base.background"
        assert uncertainties[0].confidence == 0.6
        assert uncertainties[0].file_type == "character"
    
    def test_parse_vision_response_with_markdown(self, vision_parser, mock_vision_response):
        """Test parsing vision response wrapped in markdown code blocks."""
        response_content = f"```json\n{json.dumps(mock_vision_response)}\n```"
        
        parsed_data, uncertainties = vision_parser._parse_vision_response(response_content, "character")
        
        assert parsed_data["character_base"]["name"] == "Thorin Ironforge"
        assert len(uncertainties) == 1
    
    def test_parse_vision_response_invalid_json(self, vision_parser):
        """Test parsing invalid JSON response."""
        response_content = "This is not valid JSON"
        
        parsed_data, uncertainties = vision_parser._parse_vision_response(response_content, "character")
        
        assert parsed_data == {}
        assert uncertainties == []
    
    def test_extract_json_from_response(self, vision_parser):
        """Test JSON extraction from various response formats."""
        # Test with markdown code blocks
        content_with_markdown = "```json\n{\"test\": \"value\"}\n```"
        result = vision_parser._extract_json_from_response(content_with_markdown)
        assert result == "{\"test\": \"value\"}"
        
        # Test with plain JSON
        content_plain = "{\"test\": \"value\"}"
        result = vision_parser._extract_json_from_response(content_plain)
        assert result == "{\"test\": \"value\"}"
        
        # Test with no JSON
        content_no_json = "This has no JSON content"
        result = vision_parser._extract_json_from_response(content_no_json)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_parse_single_file_type_success(self, vision_parser, sample_images, mock_vision_response):
        """Test successful single file type parsing."""
        # Mock the vision API call
        vision_parser._call_vision_api = AsyncMock(return_value=json.dumps(mock_vision_response))
        
        parsed_data, uncertainties = await vision_parser.parse_single_file_type(sample_images, "character")
        
        assert parsed_data["character_base"]["name"] == "Thorin Ironforge"
        assert len(uncertainties) == 1
        assert uncertainties[0].file_type == "character"
        
        # Verify the vision API was called with correct parameters
        vision_parser._call_vision_api.assert_called_once()
        call_args = vision_parser._call_vision_api.call_args
        assert call_args[0][0] == sample_images  # images
        assert "character information" in call_args[0][1].lower()  # prompt
    
    @pytest.mark.asyncio
    async def test_parse_single_file_type_api_failure(self, vision_parser, sample_images):
        """Test handling of vision API failures."""
        # Mock API failure
        vision_parser._call_vision_api = AsyncMock(side_effect=Exception("API Error"))
        
        parsed_data, uncertainties = await vision_parser.parse_single_file_type(sample_images, "character")
        
        assert parsed_data == {}
        assert uncertainties == []
    
    def test_get_vision_instructions_for_file_type(self, vision_parser):
        """Test vision instructions for different file types."""
        # Test character instructions
        char_instructions = vision_parser._get_vision_instructions_for_file_type("character")
        assert "Character name" in char_instructions
        assert "Ability scores" in char_instructions
        assert "STR, DEX, CON, INT, WIS, CHA" in char_instructions
        
        # Test spell_list instructions
        spell_instructions = vision_parser._get_vision_instructions_for_file_type("spell_list")
        assert "Spell lists" in spell_instructions
        assert "Cantrips" in spell_instructions
        assert "Spell slots" in spell_instructions
        
        # Test action_list instructions
        action_instructions = vision_parser._get_vision_instructions_for_file_type("action_list")
        assert "Weapon attacks" in action_instructions
        assert "attack bonuses" in action_instructions
        assert "Damage dice" in action_instructions
    
    @pytest.mark.asyncio
    async def test_parse_character_data_full_workflow(self, vision_parser, sample_images):
        """Test the complete character data parsing workflow."""
        # Mock all the individual file type parsing
        mock_responses = {
            "character": ({"character_base": {"name": "Test", "level": 5}}, []),
            "spell_list": ({"spells": []}, []),
            "feats_and_traits": ({"features": []}, []),
            "inventory_list": ({"equipment": []}, []),
            "action_list": ({"actions": []}, []),
            "character_background": ({"background": "Soldier"}, [])
        }
        
        async def mock_parse_single_file_type(images, file_type):
            return mock_responses.get(file_type, ({}, []))
        
        vision_parser.parse_single_file_type = mock_parse_single_file_type
        
        result = await vision_parser.parse_character_data(sample_images, "test_session")
        
        assert isinstance(result, CharacterParseResult)
        assert result.session_id == "test_session"
        assert len(result.character_files) == 6
        assert "character" in result.character_files
        assert result.parsing_confidence > 0
    
    def test_merge_with_template(self, vision_parser):
        """Test merging parsed data with template."""
        # Set up a template
        vision_parser.templates["character"] = {
            "character_base": {
                "name": "",
                "level": 1,
                "class": ""
            },
            "ability_scores": {
                "strength": 10,
                "dexterity": 10
            }
        }
        
        parsed_data = {
            "character_base": {
                "name": "Test Character",
                "level": 5
            }
        }
        
        result = vision_parser._merge_with_template(parsed_data, "character")
        
        assert result["character_base"]["name"] == "Test Character"
        assert result["character_base"]["level"] == 5
        assert result["character_base"]["class"] == ""  # From template
        assert result["ability_scores"]["strength"] == 10  # From template
    
    def test_calculate_parsing_confidence(self, vision_parser):
        """Test parsing confidence calculation."""
        character_files = {
            "character": {"name": "Test"},
            "spell_list": {"spells": []},
            "inventory_list": {"items": []}
        }
        
        uncertain_fields = [
            UncertainField("character", "name", "Test", 0.8, [], "Clear"),
            UncertainField("spell_list", "spells", [], 0.6, [], "Unclear")
        ]
        
        validation_results = {
            "character": MagicMock(is_valid=True),
            "spell_list": MagicMock(is_valid=True),
            "inventory_list": MagicMock(is_valid=False)
        }
        
        confidence = vision_parser._calculate_parsing_confidence(
            character_files, uncertain_fields, validation_results
        )
        
        assert 0.0 <= confidence <= 1.0
        assert confidence < 1.0  # Should be penalized for validation failure and uncertainties
    
    def test_nested_value_operations(self, vision_parser):
        """Test getting and setting nested values."""
        data = {
            "character_base": {
                "name": "Test",
                "level": 5
            }
        }
        
        # Test getting nested value
        name = vision_parser._get_nested_value(data, "character_base.name")
        assert name == "Test"
        
        level = vision_parser._get_nested_value(data, "character_base.level")
        assert level == 5
        
        # Test getting non-existent value
        missing = vision_parser._get_nested_value(data, "character_base.missing")
        assert missing is None
        
        # Test setting nested value
        vision_parser._set_nested_value(data, "character_base.class", "Fighter")
        assert data["character_base"]["class"] == "Fighter"
        
        # Test setting deeply nested value
        vision_parser._set_nested_value(data, "new.nested.value", "test")
        assert data["new"]["nested"]["value"] == "test"


if __name__ == "__main__":
    pytest.main([__file__])