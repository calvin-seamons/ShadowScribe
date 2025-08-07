#!/usr/bin/env python3
"""
Detailed Spell Data Test - Examine exactly what spell information is being retrieved
"""

import asyncio
import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.getcwd())

from src.engine.shadowscribe_engine import ShadowScribeEngine

async def test_spell_data_retrieval():
    """Test specifically what spell data is being retrieved and processed."""
    
    print("🧙 Detailed Spell Data Retrieval Test")
    print("=" * 60)
    
    # Get base directory from environment or use current directory
    base_dir = os.getenv("SHADOWSCRIBE_BASE_DIR", os.getcwd())
    knowledge_base_path = os.path.join(base_dir, "knowledge_base")
    
    print(f"📁 Using knowledge base path: {knowledge_base_path}")
    print("")
    
    # Initialize engine
    engine = ShadowScribeEngine(
        knowledge_base_path=knowledge_base_path,
        model="gpt-4o-mini"
    )
    
    # Test the complete pipeline step by step
    query = "What do you know about the Mantle of Shadow in Dusk's inventory, and also the Eldaryth"
    print(f"📝 Query: {query}")
    print("")
    
    try:
        # Step 1: Source Selection
        print("🎯 Step 1: Source Selection")
        sources = await engine.query_router.select_sources(query)
        print(f"   Selected sources: {[s.value for s in sources.sources_needed]}")
        print(f"   Reasoning: {sources.reasoning}")
        print("")
        
        # Step 2: Content Targeting
        print("🎯 Step 2: Content Targeting")
        targets = await engine.query_router.target_content(query, sources)
        print(f"   Number of targets: {len(targets)}")
        
        for i, target in enumerate(targets):
            print(f"   Target {i+1}: {target.source_type.value}")
            print(f"      Specific targets: {target.specific_targets}")
            if hasattr(target, 'reasoning'):
                print(f"      Reasoning: {target.reasoning}")
        print("")
        
        # Step 3: Content Retrieval - This is where we'll examine the actual data
        print("🎯 Step 3: Content Retrieval (DETAILED)")
        content = await engine.content_retriever.fetch_content(targets)
        print(f"   Retrieved {len(content)} content items")
        
        for i, item in enumerate(content):
            print(f"\n   📄 Content Item {i+1}: {item.source_type.value}")
            print(f"      Content type: {type(item.content)}")
            
            if hasattr(item, 'content') and item.content:
                if isinstance(item.content, dict):
                    print(f"      Content keys: {list(item.content.keys())}")
                    
                    # If this is character data, examine the spell information specifically
                    if item.source_type.value == "character_data":
                        print("\n      🧙 SPELL DATA EXAMINATION:")
                        for filename, data in item.content.items():
                            if "spell" in filename.lower():
                                print(f"         📚 {filename}:")
                                if isinstance(data, dict):
                                    print(f"            Top-level keys: {list(data.keys())}")
                                    
                                    # Look for actual spell data
                                    for key, value in data.items():
                                        if "spell" in key.lower():
                                            print(f"            🔮 {key}:")
                                            if isinstance(value, dict):
                                                print(f"               Spell categories: {list(value.keys())}")
                                                # Show a sample of actual spells
                                                for spell_cat, spell_data in value.items():
                                                    if isinstance(spell_data, (list, dict)):
                                                        spell_count = len(spell_data) if isinstance(spell_data, list) else len(spell_data.keys()) if isinstance(spell_data, dict) else 0
                                                        print(f"                  {spell_cat}: {spell_count} spells")
                                                        
                                                        # Show first few spells as examples
                                                        if isinstance(spell_data, list) and spell_data:
                                                            print(f"                     Examples: {spell_data[:3]}")
                                                        elif isinstance(spell_data, dict) and spell_data:
                                                            sample_keys = list(spell_data.keys())[:3]
                                                            print(f"                     Examples: {sample_keys}")
                                            elif isinstance(value, list):
                                                print(f"               List with {len(value)} items: {value[:3] if value else []}")
                                            else:
                                                print(f"               Value: {str(value)[:100]}...")
                                else:
                                    print(f"            Data type: {type(data)} - {str(data)[:100]}...")
                else:
                    print(f"      Content preview: {str(item.content)[:200]}...")
        
        print("\n" + "="*60)
        print("🎯 Step 4: Response Generation Test")
        
        # Test the response generator's content organization
        organized = engine.response_generator._organize_content(content)
        print(f"   Organized content keys: {list(organized.keys())}")
        
        if "character" in organized:
            print(f"\n   📊 Character data organization:")
            char_data = organized["character"]
            print(f"      Character sections: {list(char_data.keys())}")
            
            # Look specifically for spells
            for section, data in char_data.items():
                if "spell" in section.lower():
                    print(f"\n      🔮 SPELL SECTION: {section}")
                    if isinstance(data, dict):
                        print(f"         Keys: {list(data.keys())}")
                        for key, value in data.items():
                            if isinstance(value, dict):
                                print(f"            {key}: {len(value)} spell categories")
                            elif isinstance(value, list):
                                print(f"            {key}: {len(value)} spells")
                            else:
                                print(f"            {key}: {type(value)} - {str(value)[:50]}...")
                    else:
                        print(f"         Data type: {type(data)}")
        
        # Now generate the actual response
        print("\n🎯 Step 5: Final Response Generation")
        response = await engine.response_generator.generate_response(query, content)
        print(f"   Response length: {len(response)} characters")
        print(f"   Response preview:")
        print("   " + "-" * 50)
        print("   " + response[:500].replace('\n', '\n   ') + "...")
        print("   " + "-" * 50)
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_spell_data_retrieval())
