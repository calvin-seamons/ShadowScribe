#!/usr/bin/env python3
"""
Test script to verify DirectLLMClient works with gpt-5-mini model.
This tests the temperature parameter fix.
"""

import asyncio
import os
from src.utils.direct_llm_client import DirectLLMClient
from src.engine.shadowscribe_engine import ShadowScribeEngine

async def test_direct_llm_response():
    """Test that gpt-5-mini works with DirectLLMClient."""
    
    print("🧪 Testing DirectLLMClient with gpt-5-mini")
    print("=" * 60)
    
    # Test with gpt-5-mini
    client = DirectLLMClient(model="gpt-5-mini")
    
    test_query = "Tell me about my backstory and my spells. Summarize"
    
    print(f"📝 Query: {test_query}")
    print("-" * 40)
    
    try:
        # Test the natural response generation
        print("🔍 Testing natural response generation...")
        response = await client.generate_natural_response(
            prompt=f"You are a D&D assistant. Answer this query: {test_query}",
            temperature=0.7,  # This should be ignored for gpt-5-mini
            max_tokens=3000
        )
        
        print(f"✅ Response received!")
        print(f"📏 Response length: {len(response)} characters")
        print(f"📄 Response preview: {response[:200]}...")
        
        if len(response) == 0:
            print("❌ ERROR: Empty response received!")
            print("This indicates the temperature parameter issue may not be fixed.")
        else:
            print("✅ SUCCESS: Non-empty response received!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_full_engine():
    """Test the full ShadowScribeEngine with gpt-5-mini."""
    
    print("\n\n🧪 Testing Full Engine with gpt-5-mini")
    print("=" * 60)
    
    # Create engine with gpt-5-mini
    engine = ShadowScribeEngine(model="gpt-5-mini")
    
    test_query = "Tell me about my backstory and my spells. Summarize"
    
    print(f"📝 Query: {test_query}")
    print("-" * 40)
    
    try:
        # Process the query
        print("🔍 Processing query through full engine...")
        result = await engine.process_query(test_query)
        
        print(f"✅ Engine processing complete!")
        print(f"📏 Response length: {len(result.response)} characters")
        print(f"📄 Response preview: {result.response[:200]}...")
        
        if len(result.response) == 0:
            print("❌ ERROR: Empty response from engine!")
        else:
            print("✅ SUCCESS: Full engine works with gpt-5-mini!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_temperature_params():
    """Test that temperature parameters are correctly handled for different models."""
    
    print("\n\n🧪 Testing Temperature Parameter Handling")
    print("=" * 60)
    
    test_models = [
        ("gpt-4o-mini", 0.7, {"temperature": 0.7}),
        ("gpt-5-mini", 0.7, {}),  # Should return empty dict
        ("gpt-5-turbo", 0.5, {}),  # Should return empty dict
        ("o1-preview", 0.3, {}),   # Should return empty dict
        ("gpt-4-turbo", 0.8, {"temperature": 0.8}),
    ]
    
    for model, temp, expected in test_models:
        client = DirectLLMClient(model=model)
        result = client._get_temperature_params(temp)
        
        if result == expected:
            print(f"✅ {model}: Correct params {result}")
        else:
            print(f"❌ {model}: Expected {expected}, got {result}")

if __name__ == "__main__":
    print("🚀 Starting DirectLLMClient Tests for gpt-5-mini\n")
    
    async def main():
        await test_temperature_params()
        await test_direct_llm_response()
        await test_full_engine()
        print("\n🏁 All tests complete!")
    
    asyncio.run(main())
