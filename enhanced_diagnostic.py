#!/usr/bin/env python3
"""
Enhanced Diagnostic Test to show LLM vs Keyword Logic usage
"""

import asyncio
import json
import logging
import traceback
from src.engine.query_router import QueryRouter
from src.utils.direct_llm_client import DirectLLMClient
from src.utils.response_models import DirectCharacterTargeting

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_llm_vs_keyword_usage():
    """Test to see if we use LLM response or fall back to keyword logic."""
    
    print("🔍 LLM vs KEYWORD USAGE DIAGNOSTIC")
    print("=" * 60)
    
    # Create direct client with debug callback
    direct_client = DirectLLMClient(model="gpt-4o-mini")
    
    # Track what happens
    debug_events = []
    
    async def debug_callback(stage: str, message: str, data: dict = None):
        debug_events.append({
            "stage": stage,
            "message": message,
            "data": data or {}
        })
        print(f"🔧 DEBUG [{stage}]: {message}")
        if data:
            print(f"   📊 Data: {data}")
    
    direct_client.set_debug_callback(debug_callback)
    
    # Test queries
    test_queries = [
        "Tell me about my backstory",
        "Who are Thaldrin and Brenna?",
        "What spells do I know?",
        "Invalid query that might cause LLM to fail xyz123"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 TEST {i}: {query}")
        print("=" * 50)
        
        debug_events.clear()  # Reset for each test
        
        try:
            # Call the direct client
            result = await direct_client.target_character_files(query)
            
            print(f"✅ RESULT: {result}")
            
            # Analyze the debug events to see what happened
            print(f"\n🔍 ANALYSIS FOR TEST {i}:")
            
            llm_succeeded = any(event["stage"] == "PARSING_SUCCESS" for event in debug_events)
            fallback_used = any(event["stage"] == "FALLBACK_APPLIED" for event in debug_events)
            
            if llm_succeeded:
                print("✅ LLM RESPONSE USED - Direct JSON parsing succeeded")
                
                # Show the raw LLM response
                llm_response_event = next((e for e in debug_events if e["stage"] == "LLM_RESPONSE"), None)
                if llm_response_event:
                    raw_content = llm_response_event["data"].get("raw_content", "")
                    print(f"📤 LLM Raw Response: {raw_content}")
                
            elif fallback_used:
                print("⚠️  KEYWORD FALLBACK USED - LLM response failed, using keyword logic")
                
                # Test what the keyword fallback would produce
                keyword_result = DirectCharacterTargeting.create_keyword_fallback(query)
                print(f"🔧 Keyword fallback result: {keyword_result}")
                
                # Compare with actual result
                if result == keyword_result:
                    print("✅ Result matches keyword fallback exactly")
                else:
                    print("⚠️  Result differs from keyword fallback - unexpected!")
                    
            else:
                print("❓ UNCLEAR - Neither clear success nor fallback detected")
            
            # Show file targeting accuracy
            is_backstory_query = any(word in query.lower() for word in 
                                   ["backstory", "background", "family", "parent", "thaldrin", "brenna"])
            
            if is_backstory_query:
                if "character_background.json" in result:
                    print("✅ Backstory query correctly targeted character_background.json")
                else:
                    print("❌ Backstory query MISSED character_background.json")
            
            print(f"📊 Total files selected: {len(result)}")
            print(f"📄 Files: {list(result.keys())}")
            
        except Exception as e:
            print(f"❌ TEST FAILED: {str(e)}")
            print(f"📚 Error: {traceback.format_exc()}")

async def test_keyword_fallback_directly():
    """Test keyword fallback logic directly to understand its behavior."""
    
    print(f"\n🔧 TESTING KEYWORD FALLBACK DIRECTLY")
    print("=" * 60)
    
    test_queries = [
        "Tell me about my backstory",
        "Who are Thaldrin and Brenna?", 
        "What spells do I know?",
        "What's my combat damage?",
        "Random query about nothing specific"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 KEYWORD TEST {i}: {query}")
        print("-" * 40)
        
        result = DirectCharacterTargeting.create_keyword_fallback(query)
        
        print(f"📊 Keyword fallback selected {len(result)} files:")
        for filename, fields in result.items():
            print(f"   📄 {filename}: {fields}")
        
        # Analyze keyword matching
        query_lower = query.lower()
        
        matched_categories = []
        if any(word in query_lower for word in ["backstory", "background", "family", "parent", "thaldrin", "brenna"]):
            matched_categories.append("backstory")
        if any(word in query_lower for word in ["spell", "cast", "magic"]):
            matched_categories.append("spell")
        if any(word in query_lower for word in ["combat", "damage", "attack"]):
            matched_categories.append("combat")
        
        print(f"🎯 Keyword categories matched: {matched_categories}")

async def test_router_full_flow():
    """Test the router to see its complete flow."""
    
    print(f"\n🌊 TESTING ROUTER FULL FLOW")
    print("=" * 60)
    
    router = QueryRouter()
    
    # Set up debug tracking for the router
    router_events = []
    
    async def router_debug_callback(stage: str, message: str, data: dict = None):
        router_events.append({
            "stage": stage,
            "message": message,
            "data": data or {}
        })
        print(f"🔧 ROUTER [{stage}]: {message}")
    
    router.set_debug_callback(router_debug_callback)
    
    query = "Tell me about my backstory"
    print(f"📝 TESTING QUERY: {query}")
    
    try:
        target = await router._target_character_content(query, 0.9)
        
        print(f"✅ ROUTER SUCCESS")
        print(f"📄 Reasoning: {target.reasoning}")
        print(f"📊 Files: {list(target.specific_targets.get('file_fields', {}).keys())}")
        
        # Analyze router events
        print(f"\n🔍 ROUTER EVENT ANALYSIS:")
        for event in router_events:
            print(f"   📋 {event['stage']}: {event['message']}")
        
    except Exception as e:
        print(f"❌ ROUTER FAILED: {str(e)}")

async def main():
    """Run all diagnostic tests."""
    print("🚀 Starting Enhanced LLM vs Keyword Diagnostic...")
    
    await test_llm_vs_keyword_usage()
    await test_keyword_fallback_directly()
    await test_router_full_flow()
    
    print(f"\n🏁 All diagnostics complete!")

if __name__ == "__main__":
    asyncio.run(main())
