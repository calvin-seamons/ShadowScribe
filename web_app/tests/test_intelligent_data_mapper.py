"""
Tests for Intelligent Character Data Mapper

Tests spell validation, ability categorization, equipment classification,
background parsing, and mechanical accuracy validation.
"""

import pytest
import json
from unittest.mock import Mock, patch
from pathlib import Path

from web_app.intelligent_data_mapper import (
    IntelligentDataMapper,
    ValidationResult,
    MappingResult
)


@pytest.fixture
def mock_srd_data():
    """Mock SRD data for testing."""
    return {
        "sections": [
            {
                "title": "Spells",
                "content": "**Fire Bolt** (cantrip) **Magic Missile** (1st level) **Fireball** (3rd level)",
                "subsections": [
                    {
                        "title": "Cantrips",
                        "content": "_Eldritch Blast_ _Sacred Flame_ _Vicious Mockery_",
                        "subsections": []
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_schema_loader():
    """Mock schema loader for testing."""
    loader = Mock()
    loader.get_schema_for_file_type.return_value = {"type": "object"}
    loader.validate_against_schema.return_value = {"valid": True}
    return loader


@pytest.fixture
def mapper(mock_schema_loader, tmp_path):
    """Create IntelligentDataMapper instance for testing."""
    # Create temporary SRD file
    srd_file = tmp_path / "srd_data.json"
    srd_data = {
        "sections": [
            {
                "title": "Spells",
                "content": "**Fire Bolt** **Magic Missile** **Fireball** **Eldritch Blast**",
                "subsections": []
            }
        ]
    }
    srd_file.write_text(json.dumps(srd_data))
    
    return IntelligentDataMapper(str(srd_file), mock_schema_loader)


class TestSpellValidation:
    """Test spell name validation against D&D 5e SRD."""
    
    def test_validate_exact_spell_match(self, mapper):
        """Test validation of exact spell name matches."""
        result = mapper.validate_spell_name("Fire Bolt")
        
        assert result.is_valid
        assert result.confidence == 1.0
        assert len(result.errors) == 0
    
    def test_validate_spell_case_insensitive(self, mapper):
        """Test spell validation is case insensitive."""
        result = mapper.validate_spell_name("fire bolt")
        
        assert result.is_valid
        assert result.confidence == 1.0
    
    def test_validate_spell_fuzzy_match(self, mapper):
        """Test fuzzy matching for similar spell names."""
        result = mapper.validate_spell_name("Fire Blot")  # Typo
        
        assert result.confidence > 0.8
        assert "Fire Bolt" in result.suggestions
        assert result.corrected_value == "Fire Bolt"
    
    def test_validate_spell_abbreviation(self, mapper):
        """Test spell abbreviation handling."""
        result = mapper.validate_spell_name("MM")
        
        assert result.is_valid
        assert result.confidence == 1.0
        assert result.corrected_value is None or "Magic Missile" in str(result.corrected_value)
    
    def test_validate_invalid_spell(self, mapper):
        """Test validation of invalid spell names."""
        result = mapper.validate_spell_name("Nonexistent Spell")
        
        assert not result.is_valid
        assert result.confidence == 0.0
        assert len(result.errors) > 0
    
    def test_validate_empty_spell_name(self, mapper):
        """Test validation of empty spell names."""
        result = mapper.validate_spell_name("")
        
        assert not result.is_valid
        assert result.confidence == 0.0
        assert "Empty or invalid spell name" in result.errors
    
    def test_validate_none_spell_name(self, mapper):
        """Test validation of None spell names."""
        result = mapper.validate_spell_name(None)
        
        assert not result.is_valid
        assert result.confidence == 0.0


class TestAbilityCategorization:
    """Test ability and feature categorization logic."""
    
    def test_categorize_class_feature(self, mapper):
        """Test categorization of class features."""
        result = mapper.categorize_ability("Rage", "class_feature")
        
        assert result.is_valid
        assert result.confidence > 0.7
    
    def test_categorize_racial_trait(self, mapper):
        """Test categorization of racial traits."""
        result = mapper.categorize_ability("Darkvision", "racial_trait")
        
        assert result.is_valid
        assert result.confidence > 0.7
    
    def test_categorize_feat(self, mapper):
        """Test categorization of feats."""
        result = mapper.categorize_ability("Great Weapon Master", "feat")
        
        assert result.is_valid
        assert result.confidence > 0.7
    
    def test_categorize_misplaced_ability(self, mapper):
        """Test detection of misplaced abilities."""
        # Rage is a class feature, not a racial trait
        result = mapper.categorize_ability("Rage", "racial_trait")
        
        # Should suggest moving to class_feature category
        assert "class_feature" in str(result.suggestions) or not result.is_valid
    
    def test_categorize_unknown_ability(self, mapper):
        """Test categorization of unknown abilities."""
        result = mapper.categorize_ability("Custom Homebrew Ability", "class_feature")
        
        # Should accept with neutral confidence
        assert result.confidence >= 0.4
        assert result.corrected_value == "Custom Homebrew Ability"
    
    def test_categorize_empty_ability(self, mapper):
        """Test categorization of empty ability names."""
        result = mapper.categorize_ability("", "class_feature")
        
        assert not result.is_valid
        assert result.confidence == 0.0


class TestEquipmentClassification:
    """Test equipment classification and inventory structuring."""
    
    def test_classify_melee_weapon(self, mapper):
        """Test classification of melee weapons."""
        result = mapper.classify_equipment("Longsword", "weapon")
        
        assert result.is_valid
        assert result.confidence > 0.5
        assert result.corrected_value is not None
        assert result.corrected_value.get('attack_type') == 'melee'
    
    def test_classify_ranged_weapon(self, mapper):
        """Test classification of ranged weapons."""
        result = mapper.classify_equipment("Longbow", "weapon")
        
        assert result.is_valid
        assert result.corrected_value.get('attack_type') == 'ranged'
    
    def test_classify_simple_weapon(self, mapper):
        """Test classification of simple weapons."""
        result = mapper.classify_equipment("Dagger", "weapon")
        
        assert result.is_valid
        assert result.corrected_value.get('proficiency_category') == 'simple'
    
    def test_classify_martial_weapon(self, mapper):
        """Test classification of martial weapons."""
        result = mapper.classify_equipment("Longsword", "weapon")
        
        assert result.is_valid
        assert result.corrected_value.get('proficiency_category') == 'martial'
    
    def test_classify_light_armor(self, mapper):
        """Test classification of light armor."""
        result = mapper.classify_equipment("Leather Armor", "armor")
        
        assert result.is_valid
        assert result.corrected_value.get('type') == 'light'
    
    def test_classify_heavy_armor(self, mapper):
        """Test classification of heavy armor."""
        result = mapper.classify_equipment("Plate Armor", "armor")
        
        assert result.is_valid
        assert result.corrected_value.get('type') == 'heavy'
    
    def test_classify_unknown_equipment(self, mapper):
        """Test classification of unknown equipment."""
        result = mapper.classify_equipment("Mysterious Artifact", "weapon")
        
        assert result.is_valid
        assert result.confidence >= 0.5  # Should accept with neutral confidence
    
    def test_weapon_properties_assignment(self, mapper):
        """Test that weapon properties are correctly assigned."""
        result = mapper.classify_equipment("Dagger", "weapon")
        
        assert result.corrected_value is not None
        properties = result.corrected_value
        assert 'damage' in properties
        assert 'damage_type' in properties
        assert properties['damage'] == '1d4'
        assert properties['damage_type'] == 'piercing'
    
    def test_armor_properties_assignment(self, mapper):
        """Test that armor properties are correctly assigned."""
        result = mapper.classify_equipment("Chain Mail", "armor")
        
        assert result.corrected_value is not None
        properties = result.corrected_value
        assert 'armor_class' in properties
        assert properties['armor_class'] == 16


class TestBackgroundParsing:
    """Test character background element parsing and organization."""
    
    def test_validate_known_background(self, mapper):
        """Test validation of known D&D backgrounds."""
        result = mapper.validate_background("Acolyte")
        
        assert result.is_valid
        assert result.confidence == 1.0
    
    def test_validate_background_case_insensitive(self, mapper):
        """Test background validation is case insensitive."""
        result = mapper.validate_background("CRIMINAL")
        
        assert result.is_valid
        assert result.confidence == 1.0
    
    def test_validate_background_fuzzy_match(self, mapper):
        """Test fuzzy matching for background names."""
        result = mapper.validate_background("Acolite")  # Typo
        
        assert result.confidence > 0.8
        assert "acolyte" in result.suggestions
    
    def test_validate_custom_background(self, mapper):
        """Test validation of custom backgrounds."""
        result = mapper.validate_background("Custom Background")
        
        assert result.is_valid
        assert result.confidence == 0.5  # Neutral confidence for custom
    
    def test_validate_character_traits_valid(self, mapper):
        """Test validation of valid character traits."""
        traits = ["I am brave", "I help others", "I seek knowledge"]
        result = mapper.validate_character_traits(traits, "personality_traits")
        
        assert result.is_valid
        assert result.confidence == 1.0
    
    def test_validate_character_traits_mixed(self, mapper):
        """Test validation of mixed valid/invalid traits."""
        traits = ["Valid trait", "", "Another valid trait", None]
        result = mapper.validate_character_traits(traits, "ideals")
        
        assert result.is_valid
        assert result.confidence == 0.5  # 2 valid out of 4
    
    def test_validate_character_traits_empty(self, mapper):
        """Test validation of empty trait lists."""
        result = mapper.validate_character_traits([], "bonds")
        
        assert not result.is_valid  # Empty list should be invalid
        assert result.confidence == 0.0
    
    def test_validate_character_traits_invalid_format(self, mapper):
        """Test validation of invalid trait format."""
        result = mapper.validate_character_traits("Not a list", "flaws")
        
        assert not result.is_valid
        assert result.confidence == 0.0


class TestMechanicalAccuracy:
    """Test mechanical accuracy validation for stats and calculations."""
    
    def test_validate_ability_scores_valid(self, mapper):
        """Test validation of valid ability scores."""
        scores = {
            "strength": 15,
            "dexterity": 14,
            "constitution": 13,
            "intelligence": 12,
            "wisdom": 10,
            "charisma": 8
        }
        result = mapper.validate_ability_scores(scores)
        
        assert result.is_valid
        assert result.confidence == 1.0
    
    def test_validate_ability_scores_missing(self, mapper):
        """Test validation with missing ability scores."""
        scores = {"strength": 15, "dexterity": 14}
        result = mapper.validate_ability_scores(scores)
        
        assert not result.is_valid
        assert "Missing ability scores" in result.errors[0]
    
    def test_validate_ability_scores_out_of_range(self, mapper):
        """Test validation of out-of-range ability scores."""
        scores = {
            "strength": 35,  # Actually too high (>30)
            "dexterity": 0,   # Actually too low (<1)
            "constitution": 13,
            "intelligence": 12,
            "wisdom": 10,
            "charisma": 8
        }
        result = mapper.validate_ability_scores(scores)
        
        assert not result.is_valid
        assert any("outside valid range" in error for error in result.errors)
    
    def test_validate_ability_scores_unusual_values(self, mapper):
        """Test validation of unusual but valid ability scores."""
        scores = {
            "strength": 20,  # High but valid
            "dexterity": 6,   # Low but valid
            "constitution": 13,
            "intelligence": 12,
            "wisdom": 10,
            "charisma": 8
        }
        result = mapper.validate_ability_scores(scores)
        
        assert result.is_valid
        assert len(result.suggestions) > 0  # Should suggest unusual values
        assert result.confidence < 1.0
    
    def test_validate_combat_stats_valid(self, mapper):
        """Test validation of valid combat stats."""
        combat_stats = {
            "max_hp": 25,
            "armor_class": 15,
            "initiative_bonus": 2
        }
        ability_scores = {"dexterity": 14}  # +2 modifier
        
        result = mapper.validate_combat_stats(combat_stats, ability_scores)
        
        assert result.is_valid
        assert result.confidence == 1.0
    
    def test_validate_combat_stats_invalid_hp(self, mapper):
        """Test validation of invalid HP values."""
        combat_stats = {"max_hp": -5}
        result = mapper.validate_combat_stats(combat_stats, {})
        
        assert not result.is_valid
        assert "positive integer" in result.errors[0]
    
    def test_validate_combat_stats_inconsistent_initiative(self, mapper):
        """Test detection of inconsistent initiative bonus."""
        combat_stats = {"initiative_bonus": 10}  # Very high
        ability_scores = {"dexterity": 12}  # +1 modifier
        
        result = mapper.validate_combat_stats(combat_stats, ability_scores)
        
        assert result.is_valid  # Still valid, just inconsistent
        assert len(result.suggestions) > 0
        assert result.confidence < 1.0


class TestDataMapping:
    """Test complete data mapping functionality."""
    
    def test_map_spell_data(self, mapper):
        """Test mapping of spell data."""
        spell_data = {
            "spellcasting": {
                "wizard": {
                    "spells": {
                        "cantrips": [
                            {"name": "Fire Bolt"},
                            {"name": "Mage Hand"}
                        ],
                        "1st_level": [
                            {"name": "Magic Missile"}
                        ]
                    }
                }
            }
        }
        
        result = mapper._map_spell_data(spell_data)
        
        assert "data" in result
        assert "validation" in result
        assert "uncertain_fields" in result
    
    def test_map_features_data(self, mapper):
        """Test mapping of features and traits data."""
        features_data = {
            "features_and_traits": {
                "class_features": {
                    "barbarian": {
                        "features": [
                            {"name": "Rage"},
                            {"name": "Unarmored Defense"}
                        ]
                    }
                }
            }
        }
        
        result = mapper._map_features_data(features_data)
        
        assert "data" in result
        assert "validation" in result
        assert "uncertain_fields" in result
    
    def test_map_inventory_data(self, mapper):
        """Test mapping of inventory data."""
        inventory_data = {
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
        
        result = mapper._map_inventory_data(inventory_data)
        
        assert "data" in result
        assert "validation" in result
        assert "uncertain_fields" in result
    
    def test_map_character_data_complete(self, mapper):
        """Test complete character data mapping."""
        parsed_data = {
            "character": {
                "ability_scores": {
                    "strength": 15,
                    "dexterity": 14,
                    "constitution": 13,
                    "intelligence": 12,
                    "wisdom": 10,
                    "charisma": 8
                },
                "combat_stats": {
                    "max_hp": 25,
                    "armor_class": 15
                }
            },
            "spell_list": {
                "spellcasting": {
                    "wizard": {
                        "spells": {
                            "cantrips": [{"name": "Fire Bolt"}]
                        }
                    }
                }
            }
        }
        
        result = mapper.map_character_data(parsed_data)
        
        assert isinstance(result, MappingResult)
        assert "character" in result.mapped_data
        assert "spell_list" in result.mapped_data
        assert result.overall_confidence > 0.0
    
    def test_calculate_overall_confidence(self, mapper):
        """Test overall confidence calculation."""
        validation_results = {
            "file1": {
                "field1": ValidationResult(True, 0.9, [], []),
                "field2": ValidationResult(True, 0.8, [], [])
            },
            "file2": {
                "field3": ValidationResult(True, 0.7, [], [])
            }
        }
        
        confidence = mapper._calculate_overall_confidence(validation_results)
        
        assert confidence == (0.9 + 0.8 + 0.7) / 3
        assert 0.0 <= confidence <= 1.0


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_srd_data(self, mock_schema_loader, tmp_path):
        """Test handling of empty SRD data."""
        srd_file = tmp_path / "empty_srd.json"
        srd_file.write_text("{}")
        
        mapper = IntelligentDataMapper(str(srd_file), mock_schema_loader)
        result = mapper.validate_spell_name("Fire Bolt")
        
        # Should handle gracefully
        assert isinstance(result, ValidationResult)
    
    def test_invalid_srd_file(self, mock_schema_loader, tmp_path):
        """Test handling of invalid SRD file."""
        srd_file = tmp_path / "invalid_srd.json"
        srd_file.write_text("invalid json")
        
        mapper = IntelligentDataMapper(str(srd_file), mock_schema_loader)
        
        # Should initialize without crashing
        assert mapper.srd_data == {}
    
    def test_missing_srd_file(self, mock_schema_loader):
        """Test handling of missing SRD file."""
        mapper = IntelligentDataMapper("nonexistent_file.json", mock_schema_loader)
        
        # Should initialize without crashing
        assert mapper.srd_data == {}
    
    def test_map_empty_data(self, mapper):
        """Test mapping of empty data."""
        result = mapper.map_character_data({})
        
        assert isinstance(result, MappingResult)
        assert result.mapped_data == {}
        assert result.overall_confidence >= 0.0
    
    def test_map_malformed_data(self, mapper):
        """Test mapping of malformed data."""
        malformed_data = {
            "spell_list": "not a dict",
            "character": None
        }
        
        result = mapper.map_character_data(malformed_data)
        
        # Should handle gracefully without crashing
        assert isinstance(result, MappingResult)


if __name__ == "__main__":
    pytest.main([__file__])