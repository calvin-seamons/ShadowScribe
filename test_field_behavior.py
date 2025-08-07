#!/usr/bin/env python3
"""
Test script to verify field path behavior - returns complete subtrees
"""

import sys
import os
sys.path.insert(0, 'src')

from src.knowledge.character_handler import CharacterHandler

def test_field_behavior():
    """Test that field paths return complete subtrees."""
    print("Testing field path behavior...")
    
    # Create handler
    handler = CharacterHandler('knowledge_base')
    handler.load_data()
    
    if not handler.is_loaded():
        print("❌ Handler not loaded properly")
        return
    
    print("✅ Handler loaded successfully")
    
    # Test 1: Request all data from spell_list.json
    all_data = handler.get_file_data('spell_list.json', ['*'])
    if all_data:
        print(f"✅ All data keys: {list(all_data.keys())}")
        
        # Show structure of spellcasting if it exists
        if 'spellcasting' in all_data:
            spellcasting = all_data['spellcasting']
            if isinstance(spellcasting, dict):
                print(f"   Spellcasting classes: {list(spellcasting.keys())}")
                
                # Show paladin structure if it exists
                if 'paladin' in spellcasting:
                    paladin = spellcasting['paladin']
                    if isinstance(paladin, dict):
                        print(f"   Paladin spell sections: {list(paladin.keys())}")
    else:
        print("❌ No data retrieved with '*'")
    
    # Test 2: Request specific nested path
    print("\n--- Testing specific field path: 'spellcasting.paladin' ---")
    nested_data = handler.get_file_data('spell_list.json', ['spellcasting.paladin'])
    
    if nested_data:
        print(f"✅ Nested data result keys: {list(nested_data.keys())}")
        
        # Check if we got the expected key
        if 'spellcasting.paladin' in nested_data:
            paladin_data = nested_data['spellcasting.paladin']
            print(f"✅ Found 'spellcasting.paladin' key")
            print(f"   Type of returned data: {type(paladin_data)}")
            
            if isinstance(paladin_data, dict):
                print(f"   Paladin spellcasting contains: {list(paladin_data.keys())}")
                
                # This is the key test - if we request spellcasting.paladin,
                # we should get ALL paladin spellcasting data, not just a reference
                if 'spells' in paladin_data:
                    spells_data = paladin_data['spells']
                    if isinstance(spells_data, dict):
                        print(f"   ✅ VERIFIED: spells subtree contains: {list(spells_data.keys())}")
                        print("   ✅ CONFIRMED: Field path returns complete subtree!")
                    else:
                        print(f"   ⚠️  Spells data type: {type(spells_data)}")
        else:
            print("❌ 'spellcasting.paladin' key not found in result")
            print(f"   Available keys: {list(nested_data.keys())}")
    else:
        print("❌ No data retrieved with specific field path")
    
    # Test 3: Request even deeper path
    print("\n--- Testing deeper field path: 'spellcasting.paladin.spells' ---")
    deep_data = handler.get_file_data('spell_list.json', ['spellcasting.paladin.spells'])
    
    if deep_data:
        print(f"✅ Deep data result keys: {list(deep_data.keys())}")
        if 'spellcasting.paladin.spells' in deep_data:
            spells_data = deep_data['spellcasting.paladin.spells']
            print(f"✅ Found 'spellcasting.paladin.spells' key")
            print(f"   Type: {type(spells_data)}")
            if isinstance(spells_data, dict):
                print(f"   ✅ VERIFIED: Contains spell levels: {list(spells_data.keys())}")
                print("   ✅ CONFIRMED: Deep field path returns complete subtree!")
    else:
        print("❌ No data retrieved with deep field path")

if __name__ == "__main__":
    test_field_behavior()
