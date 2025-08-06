#!/usr/bin/env python3
"""
Test the new direct JSON approach for character targeting.
"""

import asyncio
import traceback
from src.engine.query_router import QueryRouter
from src.utils.direct_llm_client import DirectLLMClient

async def test_direct_character_targeting():
    """Test the direct character targeting approach."""
    
    print("🔥 TESTING NEW DIRECT CHARACTER TARGETING")
    print("=" * 60)
    
    # Create direct client
    direct_client = DirectLLMClient(model="gpt-4o-mini")
    
    # Test queries that should target character_background.json
    test_queries = [
        "Tell me about my backstory",
        "Tell me about Duskryn's parents", 
        "What is my family history?",
        "Who are Thaldrin and Brenna?",
        "Tell me about my character's background",
        "What spells do I know?",  # Should target spell_list.json
        "What's my combat damage?",  # Should target action_list.json + character.json
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 TEST {i}: {query}")
        print("-" * 40)
        
        try:
            # Test direct client
            result = await direct_client.target_character_files(query)
            
            files_selected = list(result.keys())
            print(f"✅ Direct client SUCCESS - Files: {files_selected}")
            
            # Check if character_background.json was included for backstory queries
            is_backstory_query = any(word in query.lower() for word in 
                                   ["backstory", "background", "family", "parent", "thaldrin", "brenna"])
            
            if is_backstory_query:
                if "character_background.json" in files_selected:
                    print("✅ character_background.json correctly included!")
                    
                    # Check specific fields
                    bg_fields = result.get("character_background.json", [])
                    if "backstory.family_backstory" in bg_fields or "backstory" in bg_fields:
                        print("✅ Family backstory fields included!")
                    else:
                        print("⚠️  Family fields might be missing")
                        
                else:
                    print("❌ character_background.json MISSING for backstory query!")
            
            # Show field breakdown
            total_fields = sum(len(fields) for fields in result.values())
            print(f"📊 Total fields selected: {total_fields}")
            
            # Show specific files and fields
            for filename, fields in result.items():
                print(f"   📄 {filename}: {fields[:3]}{'...' if len(fields) > 3 else ''}")
                
        except Exception as e:
            print(f"❌ Direct client FAILED: {str(e)}")
            print(f"📚 Error details: {traceback.format_exc()}")

async def test_updated_router():
    """Test the updated router with direct character targeting."""
    
    print(f"\n🔄 TESTING UPDATED ROUTER")
    print("=" * 60)
    
    # Create router
    router = QueryRouter()
    
    test_queries = [
        "Tell me about my backstory",
        "Who are Thaldrin and Brenna?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 ROUTER TEST {i}: {query}")
        print("-" * 40)
        
        try:
            # Test the full router targeting process
            print("🎯 Testing router targeting...")
            target = await router._target_character_content(query, 0.9)
            
            files_selected = list(target.specific_targets.get("file_fields", {}).keys())
            print(f"✅ Router SUCCESS - Files: {files_selected}")
            print(f"📄 Reasoning: {target.reasoning}")
            
            # Check if this is using direct targeting (should not contain "Fallback")
            if "Fallback" in target.reasoning:
                print("❌ Router still using fallback - direct targeting failed!")
            else:
                print("✅ Router using direct targeting successfully!")
            
            # Check if character_background.json was included
            if "character_background.json" in files_selected:
                print("✅ character_background.json correctly included!")
            else:
                print("❌ character_background.json MISSING!")
                
        except Exception as e:
            print(f"❌ Router FAILED: {str(e)}")
            print(f"📚 Error details: {traceback.format_exc()}")

async def main():
    """Run all tests."""
    print("🚀 Starting Direct JSON Targeting Tests...")
    
    await test_direct_character_targeting()
    await test_updated_router()
    
    print(f"\n🏁 All tests complete!")

if __name__ == "__main__":
    asyncio.run(main())
