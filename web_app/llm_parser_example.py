"""
Example usage of the LLM Character Parser

This script demonstrates how to use the LLMCharacterParser to parse
character sheet text into structured JSON data.
"""

import asyncio
import json
import os
from llm_character_parser import LLMCharacterParser


async def main():
    """Example usage of the LLM Character Parser."""
    
    # Add path for imports
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    
    # Sample character sheet text (like what would be extracted from a PDF)
    sample_character_text = """
    Character Name: Elara Moonwhisper
    Race: Half-Elf
    Class: Wizard (School of Evocation)
    Level: 8
    Background: Sage
    
    Ability Scores:
    Strength: 10 (+0)
    Dexterity: 14 (+2)
    Constitution: 13 (+1)
    Intelligence: 18 (+4)
    Wisdom: 12 (+1)
    Charisma: 16 (+3)
    
    Hit Points: 52 (8d6 + 8)
    Armor Class: 12 (15 with Mage Armor)
    Speed: 30 feet
    Proficiency Bonus: +3
    
    Saving Throws:
    Intelligence +7, Wisdom +4
    
    Skills:
    Arcana +7, History +7, Investigation +7, Religion +7
    
    Languages:
    Common, Elvish, Draconic, Celestial
    
    Spells Known:
    Cantrips (4): Mage Hand, Prestidigitation, Fire Bolt, Minor Illusion
    1st Level (4 slots): Magic Missile, Shield, Mage Armor, Detect Magic
    2nd Level (3 slots): Misty Step, Scorching Ray, Web
    3rd Level (3 slots): Fireball, Counterspell, Lightning Bolt
    4th Level (2 slots): Greater Invisibility, Wall of Fire
    
    Equipment:
    - Quarterstaff
    - Dagger
    - Component pouch
    - Scholar's pack
    - Spellbook
    - 2 daggers
    - 150 gp
    
    Personality Traits:
    - I am horribly, horribly awkward in social situations.
    - I speak without really thinking through my words, invariably insulting others.
    
    Ideals:
    - Knowledge. The path to power and self-improvement is through knowledge.
    
    Bonds:
    - The workshop where I learned my trade is the most important place in the world to me.
    
    Flaws:
    - I speak without really thinking through my words, invariably insulting others.
    """
    
    print("=== LLM Character Parser Example ===\n")
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("Note: OPENAI_API_KEY not found. This example will use mock data.")
        print("To test with real LLM parsing, set your OpenAI API key as an environment variable.\n")
        
        # Create parser without real API key for demonstration
        parser = LLMCharacterParser()
        
        # Show what the parser would do
        print("1. Parser Initialization:")
        print(f"   - Loaded {len(parser.file_types)} file type schemas")
        print(f"   - Available file types: {', '.join(parser.file_types)}")
        print()
        
        print("2. Parsing Prompts:")
        for file_type in ["character", "spell_list", "character_background"]:
            prompt = parser._build_parsing_prompt(sample_character_text, file_type)
            print(f"   - {file_type} prompt length: {len(prompt)} characters")
        print()
        
        print("3. Schema Validation:")
        for file_type in parser.file_types:
            schema = parser.schemas.get(file_type, {})
            template = parser.templates.get(file_type, {})
            print(f"   - {file_type}: {len(schema)} schema rules, {len(template)} template fields")
        print()
        
        print("4. Sample Template Structure (character.json):")
        character_template = parser.templates.get("character", {})
        if character_template:
            # Show a subset of the template structure
            sample_structure = {
                "character_base": character_template.get("character_base", {}),
                "ability_scores": character_template.get("ability_scores", {}),
                "combat_stats": character_template.get("combat_stats", {})
            }
            print(json.dumps(sample_structure, indent=2))
        
        return
    
    # Real parsing example with API key
    try:
        print("Initializing LLM Character Parser...")
        parser = LLMCharacterParser()
        
        print(f"Loaded {len(parser.file_types)} character file schemas")
        print("Starting character parsing...\n")
        
        # Parse the character data
        result = await parser.parse_character_data(sample_character_text, "example_session")
        
        print("=== PARSING RESULTS ===")
        print(f"Session ID: {result.session_id}")
        print(f"Parsing Confidence: {result.parsing_confidence:.2f}")
        print(f"Files Generated: {len(result.character_files)}")
        print(f"Uncertain Fields: {len(result.uncertain_fields)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Warnings: {len(result.warnings)}")
        print()
        
        # Show validation results
        if result.validation_results:
            print("=== VALIDATION RESULTS ===")
            for file_type, validation in result.validation_results.items():
                status = "✓ VALID" if validation.is_valid else "✗ INVALID"
                print(f"{file_type}: {status}")
                if not validation.is_valid:
                    for error in validation.errors[:3]:  # Show first 3 errors
                        print(f"  - {error.field_path}: {error.message}")
            print()
        
        # Show uncertain fields
        if result.uncertain_fields:
            print("=== UNCERTAIN FIELDS ===")
            for field in result.uncertain_fields[:5]:  # Show first 5
                print(f"- {field.file_type}.{field.field_path}")
                print(f"  Value: {field.extracted_value}")
                print(f"  Confidence: {field.confidence:.2f}")
                print(f"  Reason: {field.reasoning}")
                if field.suggestions:
                    print(f"  Suggestions: {', '.join(field.suggestions[:3])}")
                print()
        
        # Show sample parsed data
        print("=== SAMPLE PARSED DATA ===")
        
        # Character basic info
        if "character" in result.character_files:
            char_data = result.character_files["character"]
            char_base = char_data.get("character_base", {})
            ability_scores = char_data.get("ability_scores", {})
            
            print("Character Basic Info:")
            print(f"  Name: {char_base.get('name', 'N/A')}")
            print(f"  Race: {char_base.get('race', 'N/A')}")
            print(f"  Class: {char_base.get('class', 'N/A')}")
            print(f"  Level: {char_base.get('total_level', 'N/A')}")
            print()
            
            print("Ability Scores:")
            for ability, score in ability_scores.items():
                print(f"  {ability.title()}: {score}")
            print()
        
        # Spells
        if "spell_list" in result.character_files:
            spell_data = result.character_files["spell_list"]
            spellcasting = spell_data.get("spellcasting", {})
            
            print("Spellcasting:")
            for class_name, class_spells in spellcasting.items():
                print(f"  {class_name.title()}:")
                spells = class_spells.get("spells", {})
                for level, spell_list in spells.items():
                    if spell_list:
                        print(f"    {level}: {len(spell_list)} spells")
                        for spell in spell_list[:3]:  # Show first 3 spells
                            print(f"      - {spell.get('name', 'Unknown')}")
            print()
        
        # Background
        if "character_background" in result.character_files:
            bg_data = result.character_files["character_background"]
            background = bg_data.get("background", {})
            characteristics = bg_data.get("characteristics", {})
            
            print("Background:")
            print(f"  Name: {background.get('name', 'N/A')}")
            
            for trait_type in ["personality_traits", "ideals", "bonds", "flaws"]:
                traits = characteristics.get(trait_type, [])
                if traits:
                    print(f"  {trait_type.replace('_', ' ').title()}: {len(traits)} items")
                    for trait in traits[:2]:  # Show first 2
                        print(f"    - {trait}")
            print()
        
        # Show errors and warnings
        if result.errors:
            print("=== ERRORS ===")
            for error in result.errors:
                print(f"- {error}")
            print()
        
        if result.warnings:
            print("=== WARNINGS ===")
            for warning in result.warnings:
                print(f"- {warning}")
            print()
        
        print("=== PARSING COMPLETE ===")
        print("The parsed character data is now ready for use in the application.")
        print("Each file type has been validated against its schema and can be saved")
        print("to the character's directory structure.")
        
    except Exception as e:
        print(f"Error during parsing: {e}")
        print("This might be due to API limits, network issues, or configuration problems.")


if __name__ == "__main__":
    asyncio.run(main())