#!/usr/bin/env python3
"""
Test the file structure extraction
"""

import asyncio
import sys
import os

sys.path.insert(0, '/Users/calvinseamons/ShadowScribe')

from src.utils.direct_llm_client import DirectLLMClient

async def test_file_structure():
    """Test getting file structures."""
    
    client = DirectLLMClient()
    
    files_to_test = ["spell_list.json", "character.json", "character_background.json"]
    
    for filename in files_to_test:
        print(f"\n📁 Testing structure for {filename}")
        print("-" * 40)
        
        try:
            structure = await client._get_file_structure(filename)
            print(f"Structure retrieved: {bool(structure)}")
            if structure:
                import json
                print(json.dumps(structure, indent=2))
            else:
                print("❌ No structure returned")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_file_structure())
