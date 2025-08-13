"""
Integration tests for LLM Character Parser with Intelligent Data Mapper

Tests the integration between the LLM parser and intelligent data mapping functionality.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from web_app.llm_character_parser import LLMCharacterParser


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = AsyncMock()
    return client


@pytest.fixture
def sample_character_data():
    """Sample character data for testing."""
    return {
        "character": {
            "character_base": {
                "name": "Test Character",
                "race": "Human",
                "class": "Fighter",
                "level": 5
            },
            "ability_scores": {
                "strength": 16,
                "dexterity": 14,
                "constitution": 15,
                "intelligence": 10,
                "wisdom": 12,
                "charisma": 8
            },
            "combat_stats": {
                "max_hp": 45,
                "armor_class": 18,
                "initiative_bonus": 2
            }
        },
        "spell_list": {
            "spellcasting": {
                "wizard": {
                    "spells": {
                        "cantrips": [
                            {"name": "Fire Bolt"},
                            {"name": "Mage Hand"}
                        ],
                        "1st_level": [
                            {"name": "Magic Missile"},
                            {"name": "Shield"}
                        ]
                    }
                }
            }
        },
        "feats_and_traits": {
            "features_and_traits": {
                "class_features": {
                    "fighter": {
                        "features": [
                            {"name": "Action Surge"},
                            {"name": "Second Wind"}
                        ]
                    }
                }
            }
        },
        "inventory_list": {
            "inventory": {
                "equipped_items": {
                    "weapons": [
                        {"name": "Longsword"}
                    ],
                    "armor": [
                        {"name": "Chain Mail"}
                    ]
                }
            }
        }
    }


class TestLLMParserIntegration:
    """Test integration between LLM parser and intelligent data mapper."""
    
    @patch('web_app.llm_character_parser.JSONSchemaLoader')
    @patch('web_app.llm_character_parser.JSONSchemaValidator')
    def test_parser_initialization_with_mapper(self, mock_validator, mock_loader, mock_openai_client, tmp_path):
        """Test that parser initializes with intelligent data mapper."""
        # Create temporary SRD file
        srd_file = tmp_path / "srd_data.json"
        srd_data = {"sections": [{"title": "Spells", "content": "Fire Bolt Magic Missile", "subsections": []}]}
        srd_file.write_text(json.dumps(srd_data))
        
        # Mock schema loader
        mock_loader_instance = Mock()
        mock_loader_instance.get_all_file_types.return_value = ["character", "spell_list"]
        mock_loader_instance.get_schema_for_file_type.return_value = {"type": "object"}
        mock_loader_instance.get_template_for_file_type.return_value = {}
        mock_loader.return_value = mock_loader_instance
        
        # Mock validator
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        
        with patch('web_app.llm_character_parser.IntelligentDataMapper') as mock_mapper:
            parser = LLMCharacterParser(mock_openai_client)
            
            # Verify intelligent data mapper was initialized
            mock_mapper.assert_called_once()
            assert hasattr(parser, 'data_mapper')
    
    @patch('web_app.llm_character_parser.JSONSchemaLoader')
    @patch('web_app.llm_character_parser.JSONSchemaValidator')
    @pytest.mark.asyncio
    async def test_apply_intelligent_mapping(self, mock_validator, mock_loader, mock_openai_client, sample_character_data, tmp_path):
        """Test applying intelligent mapping to character data."""
        # Setup mocks
        srd_file = tmp_path / "srd_data.json"
        srd_data = {"sections": [{"title": "Spells", "content": "Fire Bolt Magic Missile", "subsections": []}]}
        srd_file.write_text(json.dumps(srd_data))
        
        mock_loader_instance = Mock()
        mock_loader_instance.get_all_file_types.return_value = ["character", "spell_list"]
        mock_loader_instance.get_schema_for_file_type.return_value = {"type": "object"}
        mock_loader_instance.get_template_for_file_type.return_value = {}
        mock_loader.return_value = mock_loader_instance
        
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        
        with patch('web_app.llm_character_parser.IntelligentDataMapper') as mock_mapper_class:
            # Setup mock mapper instance
            mock_mapper = Mock()
            mock_mapping_result = Mock()
            mock_mapping_result.mapped_data = sample_character_data
            mock_mapping_result.uncertain_fields = []
            mock_mapping_result.overall_confidence = 0.9
            mock_mapping_result.validation_results = {}
            
            mock_mapper.map_character_data.return_value = mock_mapping_result
            mock_mapper_class.return_value = mock_mapper
            
            parser = LLMCharacterParser(mock_openai_client)
            
            # Test applying intelligent mapping
            result = await parser.apply_intelligent_mapping(sample_character_data)
            
            # Verify mapping was called
            mock_mapper.map_character_data.assert_called_once_with(sample_character_data)
            
            # Verify result structure
            assert 'mapped_data' in result
            assert 'uncertain_fields' in result
            assert 'overall_confidence' in result
            assert result['overall_confidence'] == 0.9
    
    @patch('web_app.llm_character_parser.JSONSchemaLoader')
    @patch('web_app.llm_character_parser.JSONSchemaValidator')
    def test_spell_validation_integration(self, mock_validator, mock_loader, mock_openai_client, tmp_path):
        """Test spell validation through parser integration."""
        # Setup mocks
        srd_file = tmp_path / "srd_data.json"
        srd_data = {"sections": [{"title": "Spells", "content": "Fire Bolt Magic Missile", "subsections": []}]}
        srd_file.write_text(json.dumps(srd_data))
        
        mock_loader_instance = Mock()
        mock_loader_instance.get_all_file_types.return_value = ["character", "spell_list"]
        mock_loader_instance.get_schema_for_file_type.return_value = {"type": "object"}
        mock_loader_instance.get_template_for_file_type.return_value = {}
        mock_loader.return_value = mock_loader_instance
        
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        
        with patch('web_app.llm_character_parser.IntelligentDataMapper') as mock_mapper_class:
            # Setup mock mapper instance
            mock_mapper = Mock()
            mock_validation_result = Mock()
            mock_validation_result.is_valid = True
            mock_validation_result.confidence = 1.0
            mock_validation_result.suggestions = []
            mock_validation_result.errors = []
            
            mock_mapper.validate_spell_name.return_value = mock_validation_result
            mock_mapper_class.return_value = mock_mapper
            
            parser = LLMCharacterParser(mock_openai_client)
            
            # Test spell validation
            result = parser.validate_spell_name("Fire Bolt")
            
            # Verify validation was called
            mock_mapper.validate_spell_name.assert_called_once_with("Fire Bolt")
            
            # Verify result
            assert result.is_valid
            assert result.confidence == 1.0
    
    @patch('web_app.llm_character_parser.JSONSchemaLoader')
    @patch('web_app.llm_character_parser.JSONSchemaValidator')
    def test_ability_categorization_integration(self, mock_validator, mock_loader, mock_openai_client, tmp_path):
        """Test ability categorization through parser integration."""
        # Setup mocks
        srd_file = tmp_path / "srd_data.json"
        srd_data = {"sections": []}
        srd_file.write_text(json.dumps(srd_data))
        
        mock_loader_instance = Mock()
        mock_loader_instance.get_all_file_types.return_value = ["character", "spell_list"]
        mock_loader_instance.get_schema_for_file_type.return_value = {"type": "object"}
        mock_loader_instance.get_template_for_file_type.return_value = {}
        mock_loader.return_value = mock_loader_instance
        
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        
        with patch('web_app.llm_character_parser.IntelligentDataMapper') as mock_mapper_class:
            # Setup mock mapper instance
            mock_mapper = Mock()
            mock_validation_result = Mock()
            mock_validation_result.is_valid = True
            mock_validation_result.confidence = 0.9
            mock_validation_result.suggestions = []
            mock_validation_result.errors = []
            
            mock_mapper.categorize_ability.return_value = mock_validation_result
            mock_mapper_class.return_value = mock_mapper
            
            parser = LLMCharacterParser(mock_openai_client)
            
            # Test ability categorization
            result = parser.categorize_ability("Rage", "class_feature")
            
            # Verify categorization was called
            mock_mapper.categorize_ability.assert_called_once_with("Rage", "class_feature")
            
            # Verify result
            assert result.is_valid
            assert result.confidence == 0.9
    
    @patch('web_app.llm_character_parser.JSONSchemaLoader')
    @patch('web_app.llm_character_parser.JSONSchemaValidator')
    def test_equipment_classification_integration(self, mock_validator, mock_loader, mock_openai_client, tmp_path):
        """Test equipment classification through parser integration."""
        # Setup mocks
        srd_file = tmp_path / "srd_data.json"
        srd_data = {"sections": []}
        srd_file.write_text(json.dumps(srd_data))
        
        mock_loader_instance = Mock()
        mock_loader_instance.get_all_file_types.return_value = ["character", "spell_list"]
        mock_loader_instance.get_schema_for_file_type.return_value = {"type": "object"}
        mock_loader_instance.get_template_for_file_type.return_value = {}
        mock_loader.return_value = mock_loader_instance
        
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        
        with patch('web_app.llm_character_parser.IntelligentDataMapper') as mock_mapper_class:
            # Setup mock mapper instance
            mock_mapper = Mock()
            mock_validation_result = Mock()
            mock_validation_result.is_valid = True
            mock_validation_result.confidence = 0.8
            mock_validation_result.suggestions = []
            mock_validation_result.errors = []
            mock_validation_result.corrected_value = {"attack_type": "melee", "proficiency_category": "martial"}
            
            mock_mapper.classify_equipment.return_value = mock_validation_result
            mock_mapper_class.return_value = mock_mapper
            
            parser = LLMCharacterParser(mock_openai_client)
            
            # Test equipment classification
            result = parser.classify_equipment("Longsword", "weapon")
            
            # Verify classification was called
            mock_mapper.classify_equipment.assert_called_once_with("Longsword", "weapon")
            
            # Verify result
            assert result.is_valid
            assert result.confidence == 0.8
            assert result.corrected_value["attack_type"] == "melee"


if __name__ == "__main__":
    pytest.main([__file__])