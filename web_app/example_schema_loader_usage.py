#!/usr/bin/env python3
"""
Example usage of JSONSchemaLoader

This script demonstrates how to use the JSONSchemaLoader class for PDF character import.
"""

import asyncio
from json_schema_loader import JSONSchemaLoader


async def example_usage():
    """Demonstrate JSONSchemaLoader usage."""
    
    # Initialize the loader
    loader = JSONSchemaLoader()
    
    print("Available file types:", loader.get_all_file_types())
    
    # Get a template for creating a new character
    character_template = loader.get_template_for_file_type("character")
    print("\nCharacter template keys:", list(character_template.keys()))
    
    # Get the schema for validation
    character_schema = loader.get_schema_for_file_type("character")
    print("\nCharacter schema type:", character_schema.get("type"))
    
    # Example: Create a character with some data
    character_data = character_template.copy()
    character_data["character_base"]["name"] = "Aragorn"
    character_data["character_base"]["race"] = "Human"
    character_data["character_base"]["class"] = "Ranger"
    character_data["character_base"]["total_level"] = 5
    
    # Validate the character data
    result = await loader.validate_against_schema(character_data, "character")
    print(f"\nValidation result: {'PASS' if result.is_valid else 'FAIL'}")
    
    if not result.is_valid:
        print("Validation errors:")
        for error in result.errors[:5]:  # Show first 5 errors
            print(f"  - {error.field_path}: {error.message}")
    
    # Get schema info
    schema_info = loader.get_schema_info("spell_list")
    print(f"\nSpell list schema source: {schema_info.source_file}")


if __name__ == "__main__":
    asyncio.run(example_usage())