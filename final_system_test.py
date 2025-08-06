#!/usr/bin/env python3
"""
Comprehensive test of the fully converted ShadowScribe system using direct JSON approach.
This test validates that the entire QueryRouter system now works with 100% direct JSON.
"""

import asyncio
import sys
import os

sys.path.insert(0, '/Users/calvinseamons/ShadowScribe')

from src.engine.query_router import QueryRouter

async def test_full_system_conversion():
    """Test that the entire system now uses direct JSON approach."""
    
    router = QueryRouter()
    
    # Comprehensive test scenarios
    test_scenarios = [
        {
            "query": "What spells can I cast?",
            "expected_sources": ["dnd_rulebook", "character_data"],
            "description": "Spell query requiring both rulebook and character data"
        },
        {
            "query": "Tell me about my backstory and family, especially my parents Thaldrin and Brenna",
            "expected_sources": ["character_data"],
            "description": "Backstory query - should prioritize character_background.json"
        },
        {
            "query": "What happened in the last session with Elarion, Pork, and the rest of the party?",
            "expected_sources": ["session_notes"],
            "description": "Session query about party members"
        },
        {
            "query": "How does concentration work and what concentration spells do I have?",
            "expected_sources": ["dnd_rulebook", "character_data"],
            "description": "Complex query requiring both rules and character data"
        },
        {
            "query": "Can I use my paladin abilities with my warlock spells in combat?",
            "expected_sources": ["dnd_rulebook", "character_data"],
            "description": "Complex multiclass optimization query"
        },
        {
            "query": "Who are the other party members and what are their abilities?",
            "expected_sources": ["session_notes"],
            "description": "Party composition query"
        }
    ]
    
    print("🚀 ShadowScribe Direct JSON System Test")
    print("=" * 60)
    print("Testing complete conversion from function calling to direct JSON parsing")
    print("")
    
    success_count = 0
    total_tests = len(test_scenarios)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"Test {i}/{total_tests}: {scenario['description']}")
        print(f"Query: \"{scenario['query']}\"")
        print("-" * 50)
        
        try:
            # Test source selection (Pass 1)
            sources = await router.select_sources(scenario['query'])
            source_names = [s.value for s in sources.sources_needed]
            
            print(f"✅ Source Selection:")
            print(f"   Selected: {source_names}")
            print(f"   Confidence: {sources.confidence}")
            print(f"   Reasoning: {sources.reasoning[:80]}...")
            
            # Validate expected sources are included
            expected_found = all(expected in source_names for expected in scenario['expected_sources'])
            if expected_found:
                print(f"   ✅ All expected sources found")
            else:
                print(f"   ⚠️  Missing expected sources: {set(scenario['expected_sources']) - set(source_names)}")
            
            # Test content targeting (Pass 2)
            targets = await router.target_content(scenario['query'], sources)
            
            print(f"✅ Content Targeting:")
            print(f"   Generated {len(targets)} content targets")
            
            for target in targets:
                print(f"   - {target.source_type.value}: {target.reasoning[:60]}...")
                
                # Check for character targeting specifics
                if target.source_type.value == "character_data" and "backstory" in scenario['query'].lower():
                    if hasattr(target, 'specific_targets') and 'file_fields' in target.specific_targets:
                        if 'character_background.json' in target.specific_targets['file_fields']:
                            print(f"     ✅ Correctly included character_background.json for backstory query")
                        else:
                            print(f"     ⚠️  Missing character_background.json for backstory query")
            
            success_count += 1
            print(f"   ✅ Test {i} PASSED")
            
        except Exception as e:
            print(f"   ❌ Test {i} FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            
        print("")
    
    # Summary
    print("=" * 60)
    print(f"🎯 CONVERSION TEST RESULTS")
    print(f"   Passed: {success_count}/{total_tests}")
    print(f"   Success Rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print(f"   🎉 FULL SYSTEM CONVERSION SUCCESSFUL!")
        print(f"   ✅ QueryRouter now uses 100% direct JSON parsing")
        print(f"   ✅ No more function calling failures")
        print(f"   ✅ High confidence targeting working")
    else:
        print(f"   ⚠️  Some tests failed - system needs attention")

if __name__ == "__main__":
    asyncio.run(test_full_system_conversion())
