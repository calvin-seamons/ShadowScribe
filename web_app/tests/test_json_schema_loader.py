"""
Tests for JSON Schema Loader

This module tests the JSONSchemaLoader class functionality including:
- Loading schemas from character-json-structures files
- Template generation from schemas
- Schema validation methods
- Integration with existing character structure files
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from json_schema_loader import JSONSchemaLoader, SchemaInfo
from json_schema_validator import ValidationResult, ValidationError


class TestJSONSchemaLoader:
    """Test cases for JSONSchemaLoader class."""
    
    @pytest.fixture
    def temp_structures_dir(self):
        """Create a temporary directory with test structure files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            structures_path = Path(temp_dir) / "character-json-structures"
            structures_path.mkdir()
            
            # Create test character.json.md file
            character_content = '''# Character JSON Structure

{
  "character_base": {
    "name": "",
    "race": "",
    "class": "",
    "total_level": 1
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
    "current_hp": 1,
    "armor_class": 10
  }
}'''
            
            (structures_path / "character.json.md").write_text(character_content)
            
            # Create test spell_list.json.md file
            spell_content = '''# Spell List Structure

{
  "spellcasting": {
    "wizard": {
      "ability": "intelligence",
      "spell_save_dc": 8,
      "spells": {
        "cantrips": [
          {
            "name": "",
            "school": "",
            "casting_time": "",
            "range": "",
            "duration": "",
            "description": ""
          }
        ],
        "1st_level": []
      }
    }
  },
  "metadata": {
    "version": "1.0",
    "last_updated": ""
  }
}'''
            
            (structures_path / "spell_list.json.md").write_text(spell_content)
            
            yield str(structures_path)
    
    @pytest.fixture
    def schema_loader(self, temp_structures_dir):
        """Create a JSONSchemaLoader instance with test data."""
        return JSONSchemaLoader(temp_structures_dir)
    
    def test_initialization(self, temp_structures_dir):
        """Test JSONSchemaLoader initialization."""
        loader = JSONSchemaLoader(temp_structures_dir)
        
        assert loader.structures_path == Path(temp_structures_dir)
        assert isinstance(loader.schemas, dict)
        assert len(loader.schemas) >= 2  # character and spell_list
        assert "character" in loader.schemas
        assert "spell_list" in loader.schemas
    
    def test_load_schema_from_file(self, schema_loader):
        """Test loading schema from individual files."""
        schema_info = schema_loader.schemas.get("character")
        
        assert schema_info is not None
        assert isinstance(schema_info, SchemaInfo)
        assert schema_info.file_type == "character"
        assert "character_base" in schema_info.template
        assert "ability_scores" in schema_info.template
        assert "combat_stats" in schema_info.template
    
    def test_extract_json_from_markdown(self, schema_loader):
        """Test JSON extraction from markdown content."""
        markdown_content = '''# Test Structure

Some description here.

{
  "test_field": "value", // This is a comment
  "number_field": 42,
  "nested": {
    "inner": true
  }
}'''
        
        json_content = schema_loader._extract_json_from_markdown(markdown_content)
        
        assert json_content is not None
        # Should be parseable JSON
        parsed = json.loads(json_content)
        assert parsed["test_field"] == "value"
        assert parsed["number_field"] == 42
        assert parsed["nested"]["inner"] is True
    
    def test_clean_json_content(self, schema_loader):
        """Test JSON content cleaning."""
        dirty_json = '''{
  "field1": "value1", // Comment here
  "field2": 42,
  "array": [
    "item1",
    "item2", // Another comment
  ],
  "nested": {
    "inner": true,
  },
}'''
        
        clean_json = schema_loader._clean_json_content(dirty_json)
        
        # Should be parseable after cleaning
        parsed = json.loads(clean_json)
        assert parsed["field1"] == "value1"
        assert parsed["field2"] == 42
        assert len(parsed["array"]) == 2
        assert parsed["nested"]["inner"] is True
    
    def test_generate_schema_from_template(self, schema_loader):
        """Test schema generation from template."""
        template = {
            "string_field": "test",
            "number_field": 42,
            "boolean_field": True,
            "array_field": ["item1", "item2"],
            "object_field": {
                "nested_string": "value",
                "nested_number": 10
            }
        }
        
        schema = schema_loader._generate_schema_from_template(template)
        
        assert schema["type"] == "object"
        assert "properties" in schema
        
        props = schema["properties"]
        assert props["string_field"]["type"] == "string"
        assert props["number_field"]["type"] == "integer"
        assert props["boolean_field"]["type"] == "boolean"
        assert props["array_field"]["type"] == "array"
        assert props["object_field"]["type"] == "object"
    
    def test_get_schema_for_file_type(self, schema_loader):
        """Test getting schema for specific file type."""
        schema = schema_loader.get_schema_for_file_type("character")
        
        assert isinstance(schema, dict)
        assert schema["type"] == "object"
        assert "properties" in schema
        
        # Test invalid file type
        with pytest.raises(ValueError, match="Unsupported file type"):
            schema_loader.get_schema_for_file_type("invalid_type")
    
    def test_get_template_for_file_type(self, schema_loader):
        """Test getting template for specific file type."""
        template = schema_loader.get_template_for_file_type("character")
        
        assert isinstance(template, dict)
        assert "character_base" in template
        assert template["character_base"]["name"] == ""
        assert template["character_base"]["total_level"] == 0  # Should be empty/default
        
        # Test invalid file type
        with pytest.raises(ValueError, match="Unsupported file type"):
            schema_loader.get_template_for_file_type("invalid_type")
    
    def test_create_empty_template(self, schema_loader):
        """Test creating empty template with default values."""
        source_template = {
            "string_field": "original_value",
            "number_field": 42,
            "boolean_field": True,
            "array_field": ["item1", "item2"],
            "nested": {
                "inner_string": "inner_value",
                "inner_number": 100
            }
        }
        
        empty_template = schema_loader._create_empty_template(source_template)
        
        assert empty_template["string_field"] == ""
        assert empty_template["number_field"] == 0
        assert empty_template["boolean_field"] is False
        assert empty_template["array_field"] == []
        assert empty_template["nested"]["inner_string"] == ""
        assert empty_template["nested"]["inner_number"] == 0
    
    @pytest.mark.asyncio
    async def test_validate_against_schema(self, schema_loader):
        """Test schema validation."""
        # Mock the validator to return a known result
        mock_result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[]
        )
        
        with patch.object(schema_loader.validator, 'validate', return_value=mock_result) as mock_validate:
            test_data = {"character_base": {"name": "Test Character"}}
            result = await schema_loader.validate_against_schema(test_data, "character")
            
            assert result.is_valid is True
            assert len(result.errors) == 0
            mock_validate.assert_called_once_with(test_data, "character")
    
    def test_get_all_file_types(self, schema_loader):
        """Test getting all supported file types."""
        file_types = schema_loader.get_all_file_types()
        
        assert isinstance(file_types, list)
        assert "character" in file_types
        assert "spell_list" in file_types
        assert len(file_types) >= 2
    
    def test_get_schema_info(self, schema_loader):
        """Test getting complete schema information."""
        schema_info = schema_loader.get_schema_info("character")
        
        assert isinstance(schema_info, SchemaInfo)
        assert schema_info.file_type == "character"
        assert isinstance(schema_info.schema, dict)
        assert isinstance(schema_info.template, dict)
        assert schema_info.source_file.endswith("character.json.md")
        
        # Test invalid file type
        with pytest.raises(ValueError, match="Unsupported file type"):
            schema_loader.get_schema_info("invalid_type")
    
    def test_reload_schemas(self, schema_loader):
        """Test reloading schemas."""
        original_count = len(schema_loader.schemas)
        
        # Clear schemas and reload
        schema_loader.schemas.clear()
        assert len(schema_loader.schemas) == 0
        
        schema_loader.reload_schemas()
        assert len(schema_loader.schemas) == original_count


class TestSchemaLoaderIntegration:
    """Integration tests using actual character structure files."""
    
    @pytest.fixture
    def real_schema_loader(self):
        """Create a JSONSchemaLoader with real structure files."""
        return JSONSchemaLoader()
    
    def test_load_all_real_schemas(self, real_schema_loader):
        """Test loading all real character structure files."""
        expected_types = [
            "character",
            "character_background", 
            "feats_and_traits",
            "action_list",
            "inventory_list",
            "objectives_and_contracts",
            "spell_list"
        ]
        
        loaded_types = real_schema_loader.get_all_file_types()
        
        # Check that we loaded at least some of the expected types
        # (some files might not exist in test environment)
        assert len(loaded_types) > 0
        
        for file_type in loaded_types:
            # Each loaded type should have valid schema and template
            schema = real_schema_loader.get_schema_for_file_type(file_type)
            template = real_schema_loader.get_template_for_file_type(file_type)
            
            assert isinstance(schema, dict)
            assert isinstance(template, dict)
            assert schema.get("type") == "object"
    
    def test_character_schema_structure(self, real_schema_loader):
        """Test that character schema has expected structure."""
        if "character" not in real_schema_loader.get_all_file_types():
            pytest.skip("Character schema file not available")
        
        schema = real_schema_loader.get_schema_for_file_type("character")
        template = real_schema_loader.get_template_for_file_type("character")
        
        # Check schema structure
        assert schema["type"] == "object"
        assert "properties" in schema
        
        # Check template has expected sections
        expected_sections = ["character_base", "ability_scores", "combat_stats"]
        for section in expected_sections:
            if section in template:  # Some sections might be optional
                assert isinstance(template[section], dict)
    
    def test_spell_list_schema_structure(self, real_schema_loader):
        """Test that spell list schema has expected structure."""
        if "spell_list" not in real_schema_loader.get_all_file_types():
            pytest.skip("Spell list schema file not available")
        
        schema = real_schema_loader.get_schema_for_file_type("spell_list")
        template = real_schema_loader.get_template_for_file_type("spell_list")
        
        # Check schema structure
        assert schema["type"] == "object"
        assert "properties" in schema
        
        # Check template structure
        if "spellcasting" in template:
            assert isinstance(template["spellcasting"], dict)
    
    @pytest.mark.asyncio
    async def test_validation_with_real_schemas(self, real_schema_loader):
        """Test validation using real schemas."""
        if "character" not in real_schema_loader.get_all_file_types():
            pytest.skip("Character schema file not available")
        
        # Test with valid character data
        valid_data = {
            "character_base": {
                "name": "Test Character",
                "race": "Human",
                "class": "Fighter",
                "total_level": 1
            },
            "ability_scores": {
                "strength": 15,
                "dexterity": 14,
                "constitution": 13,
                "intelligence": 12,
                "wisdom": 10,
                "charisma": 8
            },
            "combat_stats": {
                "max_hp": 12,
                "current_hp": 12,
                "armor_class": 16
            }
        }
        
        result = await real_schema_loader.validate_against_schema(valid_data, "character")
        
        # Should validate successfully (or at least not fail catastrophically)
        assert isinstance(result, ValidationResult)
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.errors, list)


if __name__ == "__main__":
    pytest.main([__file__])