#!/usr/bin/env python3
"""
Direct test of character handler loading
"""

import sys
import os

sys.path.insert(0, '/Users/calvinseamons/ShadowScribe')

from src.knowledge.character_handler import CharacterHandler

def test_character_handler():
    """Test the character handler directly."""
    
    print("🧪 Testing CharacterHandler directly")
    print("=" * 40)
    
    try:
        handler = CharacterHandler("/Users/calvinseamons/ShadowScribe/knowledge_base")
        print("✅ Handler created")
        
        handler.load_data()
        print("✅ Data loaded")
        
        # Check what properties exist
        print(f"📊 Handler properties:")
        for attr in dir(handler):
            if not attr.startswith('_') and hasattr(handler, attr):
                value = getattr(handler, attr)
                if not callable(value):
                    print(f"   - {attr}: {type(value)} (loaded: {bool(value)})")
        
        # Test specific data access
        print(f"\n📚 Testing spell data:")
        spell_data = getattr(handler, 'spell_data', None)
        if spell_data:
            print(f"   Spell data type: {type(spell_data)}")
            if isinstance(spell_data, dict):
                print(f"   Top level keys: {list(spell_data.keys())}")
                if 'spellcasting' in spell_data:
                    print(f"   Spellcasting keys: {list(spell_data['spellcasting'].keys())}")
        else:
            print("   ❌ No spell_data attribute")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_character_handler()
