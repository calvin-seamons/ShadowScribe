"""
Integration tests for Vision Character Parser

This module provides integration tests to verify the VisionCharacterParser
works correctly with the existing system components.
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision_character_parser import VisionCharacterParser


class TestVisionParserIntegration:
    """Integration test suite for VisionCharacterParser."""
    
    @pytest.fixture
    def sample_character_sheet_images(self):
        """Sample character sheet images (base64 encoded 1x1 pixel images for testing)."""
        return [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA4849a6wAAAABJRU5ErkJggg=="
        ]
    
    @pytest.fixture
    def mock_complete_vision_responses(self):
        """Mock complete vision responses for all 6 file types."""
        return {
            "character": {
                "data": {
                    "character_base": {
                        "name": "Thorin Ironforge",
                        "race": "Mountain Dwarf",
                        "class": "Fighter",
                        "total_level": 5,
                        "experience_points": 6500,
                        "alignment": "Lawful Good",
                        "background": "Soldier"
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
                    }
                },
                "uncertainties": []
            },
            "spell_list": {
                "data": {
                    "spellcasting_classes": [],
                    "spells": []
                },
                "uncertainties": []
            },
            "feats_and_traits": {
                "data": {
                    "racial_traits": [
                        {
                            "name": "Darkvision",
                            "description": "You can see in dim light within 60 feet as if it were bright light."
                        }
                    ],
                    "class_features": [
                        {
                            "name": "Fighting Style",
                            "description": "Defense - +1 AC while wearing armor"
                        },
                        {
                            "name": "Second Wind",
                            "description": "Regain 1d10+5 hit points as a bonus action"
                        }
                    ],
                    "feats": []
                },
                "uncertainties": []
            },
            "inventory_list": {
                "data": {
                    "currency": {
                        "gold": 150,
                        "silver": 23,
                        "copper": 45
                    },
                    "equipment": [
                        {
                            "name": "Chain Mail",
                            "type": "armor",
                            "equipped": True,
                            "weight": 55
                        },
                        {
                            "name": "Battleaxe",
                            "type": "weapon",
                            "equipped": True,
                            "weight": 4
                        }
                    ]
                },
                "uncertainties": []
            },
            "action_list": {
                "data": {
                    "attacks": [
                        {
                            "name": "Battleaxe",
                            "attack_bonus": 6,
                            "damage": "1d8+3",
                            "damage_type": "slashing",
                            "type": "melee"
                        }
                    ],
                    "actions": [
                        {
                            "name": "Second Wind",
                            "type": "bonus_action",
                            "description": "Regain 1d10+5 hit points"
                        }
                    ]
                },
                "uncertainties": []
            },
            "character_background": {
                "data": {
                    "background": "Soldier",
                    "personality_traits": [
                        "I face problems head-on. A simple, direct solution is the best path to success."
                    ],
                    "ideals": [
                        "Greater Good. Our lot in life is to lay down our lives in defense of others."
                    ],
                    "bonds": [
                        "I would still lay down my life for the people I served with."
                    ],
                    "flaws": [
                        "I have little respect for anyone who is not a proven warrior."
                    ]
                },
                "uncertainties": []
            }
        }
    
    @pytest.mark.asyncio
    async def test_complete_character_parsing_workflow(self, sample_character_sheet_images, mock_complete_vision_responses):
        """Test the complete character parsing workflow with all 6 file types."""
        
        with patch('vision_character_parser.JSONSchemaLoader') as mock_loader_class, \
             patch('vision_character_parser.JSONSchemaValidator') as mock_validator_class, \
             patch('vision_character_parser.IntelligentDataMapper') as mock_mapper_class:
            
            # Set up mocks
            mock_loader = MagicMock()
            mock_loader.get_schema_for_file_type.return_value = {"type": "object"}
            mock_loader.get_template_for_file_type.return_value = {}
            mock_loader_class.return_value = mock_loader
            
            mock_validator = AsyncMock()
            mock_validator.validate.return_value = MagicMock(is_valid=True, errors=[], warnings=[])
            mock_validator_class.return_value = mock_validator
            
            mock_mapper = MagicMock()
            mock_mapper._map_file_data.side_effect = lambda file_type, data: {
                'data': data,
                'validation': {},
                'uncertain_fields': []
            }
            mock_mapper.map_character_data.return_value = MagicMock(
                mapped_data={},
                uncertain_fields=[],
                overall_confidence=0.9
            )
            mock_mapper_class.return_value = mock_mapper
            
            # Create parser with mock client
            mock_client = AsyncMock()
            parser = VisionCharacterParser(openai_client=mock_client)
            
            # Mock the vision API responses for each file type
            def mock_vision_api_call(images, prompt):
                # Determine file type from prompt content
                if "character information" in prompt.lower():
                    return json.dumps(mock_complete_vision_responses["character"])
                elif "spell" in prompt.lower() and "spell_list" in prompt.lower():
                    return json.dumps(mock_complete_vision_responses["spell_list"])
                elif "feats and traits" in prompt.lower():
                    return json.dumps(mock_complete_vision_responses["feats_and_traits"])
                elif "inventory" in prompt.lower():
                    return json.dumps(mock_complete_vision_responses["inventory_list"])
                elif "action" in prompt.lower() and "combat" in prompt.lower():
                    return json.dumps(mock_complete_vision_responses["action_list"])
                elif "background" in prompt.lower() and "personality" in prompt.lower():
                    return json.dumps(mock_complete_vision_responses["character_background"])
                return json.dumps({"data": {}, "uncertainties": []})
            
            parser._call_vision_api = AsyncMock(side_effect=mock_vision_api_call)
            
            # Execute the parsing
            result = await parser.parse_character_data(sample_character_sheet_images, "integration_test_session")
            
            # Verify the result structure
            assert result.session_id == "integration_test_session"
            assert len(result.character_files) == 6
            
            # Verify all expected file types are present
            expected_file_types = ["character", "spell_list", "feats_and_traits", "inventory_list", "action_list", "character_background"]
            for file_type in expected_file_types:
                assert file_type in result.character_files
            
            # Verify character data was parsed correctly
            character_data = result.character_files["character"]
            assert "character_base" in character_data
            
            # Verify spell list (should be empty for non-caster)
            spell_data = result.character_files["spell_list"]
            assert "spells" in spell_data
            
            # Verify features and traits
            features_data = result.character_files["feats_and_traits"]
            assert "racial_traits" in features_data or "class_features" in features_data
            
            # Verify inventory
            inventory_data = result.character_files["inventory_list"]
            assert "equipment" in inventory_data or "currency" in inventory_data
            
            # Verify actions
            actions_data = result.character_files["action_list"]
            assert "attacks" in actions_data or "actions" in actions_data
            
            # Verify background
            background_data = result.character_files["character_background"]
            assert "background" in background_data or "personality_traits" in background_data
            
            # Verify parsing confidence
            assert 0.0 <= result.parsing_confidence <= 1.0
            
            # Verify vision API was called for each file type
            assert parser._call_vision_api.call_count == 6
    
    @pytest.mark.asyncio
    async def test_vision_api_error_handling(self, sample_character_sheet_images):
        """Test error handling when vision API calls fail."""
        
        with patch('vision_character_parser.JSONSchemaLoader') as mock_loader_class, \
             patch('vision_character_parser.JSONSchemaValidator') as mock_validator_class, \
             patch('vision_character_parser.IntelligentDataMapper') as mock_mapper_class:
            
            # Set up mocks
            mock_loader = MagicMock()
            mock_loader.get_schema_for_file_type.return_value = {"type": "object"}
            mock_loader.get_template_for_file_type.return_value = {"default": "template"}
            mock_loader_class.return_value = mock_loader
            
            mock_validator = AsyncMock()
            mock_validator.validate.return_value = MagicMock(is_valid=True, errors=[], warnings=[])
            mock_validator_class.return_value = mock_validator
            
            mock_mapper = MagicMock()
            mock_mapper._map_file_data.return_value = {
                'data': {"default": "template"},
                'validation': {},
                'uncertain_fields': []
            }
            mock_mapper.map_character_data.return_value = MagicMock(
                mapped_data={},
                uncertain_fields=[],
                overall_confidence=0.1
            )
            mock_mapper_class.return_value = mock_mapper
            
            # Create parser with mock client
            mock_client = AsyncMock()
            parser = VisionCharacterParser(openai_client=mock_client)
            
            # Mock vision API to fail
            parser._call_vision_api = AsyncMock(side_effect=Exception("Vision API Error"))
            
            # Execute the parsing
            result = await parser.parse_character_data(sample_character_sheet_images, "error_test_session")
            
            # Verify graceful error handling
            assert result.session_id == "error_test_session"
            assert len(result.character_files) == 6  # Should still have all file types with templates
            assert len(result.warnings) == 6  # Should have warnings for all file types (not errors)
            assert result.parsing_confidence >= 0.0  # Should not crash
            
            # Verify all file types use templates
            for file_type in parser.file_types:
                assert file_type in result.character_files
                assert result.character_files[file_type] == {"default": "template"}
    
    def test_focused_prompts_exclude_irrelevant_content(self):
        """Test that focused prompts properly exclude irrelevant content."""
        
        with patch('vision_character_parser.JSONSchemaLoader') as mock_loader_class, \
             patch('vision_character_parser.JSONSchemaValidator') as mock_validator_class, \
             patch('vision_character_parser.IntelligentDataMapper') as mock_mapper_class:
            
            # Set up minimal mocks
            mock_loader = MagicMock()
            mock_loader.get_schema_for_file_type.return_value = {"type": "object"}
            mock_loader.get_template_for_file_type.return_value = {}
            mock_loader_class.return_value = mock_loader
            
            mock_validator_class.return_value = AsyncMock()
            mock_mapper_class.return_value = MagicMock()
            
            parser = VisionCharacterParser(openai_client=AsyncMock())
            
            # Test character prompt excludes spell information
            character_prompt = parser._build_single_file_prompt("character")
            assert "IGNORE information not related to character" in character_prompt
            assert "character information" in character_prompt.lower()
            
            # Test spell_list prompt excludes equipment information
            spell_prompt = parser._build_single_file_prompt("spell_list")
            assert "IGNORE information not related to spell_list" in spell_prompt
            assert "spell" in spell_prompt.lower()
            
            # Test inventory_list prompt excludes combat actions
            inventory_prompt = parser._build_single_file_prompt("inventory_list")
            assert "IGNORE information not related to inventory_list" in inventory_prompt
            assert "equipment" in inventory_prompt.lower()
            
            # Test action_list prompt excludes general equipment
            action_prompt = parser._build_single_file_prompt("action_list")
            assert "IGNORE information not related to action_list" in action_prompt
            assert "combat" in action_prompt.lower() or "attack" in action_prompt.lower()
    
    def test_vision_parser_replaces_llm_parser_interface(self):
        """Test that VisionCharacterParser has the same interface as LLMCharacterParser."""
        
        with patch('vision_character_parser.JSONSchemaLoader'), \
             patch('vision_character_parser.JSONSchemaValidator'), \
             patch('vision_character_parser.IntelligentDataMapper'):
            
            parser = VisionCharacterParser(openai_client=AsyncMock())
            
            # Verify it has the main parsing method with correct signature
            assert hasattr(parser, 'parse_character_data')
            assert callable(parser.parse_character_data)
            
            # Verify it has the same result structure
            # (This would be tested more thoroughly in the full workflow test)
            assert hasattr(parser, 'file_types')
            assert hasattr(parser, 'schemas')
            assert hasattr(parser, 'templates')
            
            # Verify it excludes objectives_and_contracts as specified in requirements
            assert "objectives_and_contracts" not in parser.file_types
            assert len(parser.file_types) == 6


if __name__ == "__main__":
    pytest.main([__file__])