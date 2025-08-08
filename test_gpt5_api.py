#!/usr/bin/env python3
"""
Simple test script to verify gpt-5-mini API functionality
"""

import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

async def test_gpt5_api():
    """Test the gpt-5-mini model with various configurations"""
    
    # Load environment variables
    load_dotenv()
    
    # Get API key and model from environment
    api_key = os.getenv("OPENAI_API_KEY")
    model = "gpt-5-mini"
    
    print(f"Testing model: {model}")
    print(f"API key loaded: {'Yes' if api_key else 'No'}")
    print(f"API key preview: {api_key[:20] + '...' if api_key else 'None'}")
    print("-" * 50)
    
    if not api_key:
        print("ERROR: No OpenAI API key found in .env file")
        return
    
    # Initialize client
    client = AsyncOpenAI(api_key=api_key)
    
    # Test 1: Simple query with no special parameters
    print("TEST 1: Basic query (no temperature/max_tokens)")
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "What is 2 + 2?"}]
        )
        
        content = response.choices[0].message.content
        print(f"Response: {content}")
        print(f"Response length: {len(content) if content else 0}")
        print("✅ Basic query successful")
    except Exception as e:
        print(f"❌ Basic query failed: {e}")
    
    print("-" * 50)
    
    # Test 2: Query with max_completion_tokens (gpt-5 style)
    print("TEST 2: Query with max_completion_tokens")
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Write a short story about a dragon."}],
            max_completion_tokens=100
        )
        
        content = response.choices[0].message.content
        print(f"Response: {content[:200]}..." if content and len(content) > 200 else content)
        print(f"Response length: {len(content) if content else 0}")
        print("✅ max_completion_tokens successful")
    except Exception as e:
        print(f"❌ max_completion_tokens failed: {e}")
    
    print("-" * 50)
    
    # Test 3: Query with old-style max_tokens (for comparison)
    print("TEST 3: Query with max_tokens (old style)")
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Write a short story about a dragon."}],
            max_tokens=100
        )
        
        content = response.choices[0].message.content
        print(f"Response: {content[:200]}..." if content and len(content) > 200 else content)
        print(f"Response length: {len(content) if content else 0}")
        print("✅ max_tokens successful")
    except Exception as e:
        print(f"❌ max_tokens failed: {e}")
    
    print("-" * 50)
    
    # Test 4: Try temperature parameter
    print("TEST 4: Query with temperature")
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Tell me a random fact."}],
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        print(f"Response: {content}")
        print(f"Response length: {len(content) if content else 0}")
        print("✅ Temperature parameter successful")
    except Exception as e:
        print(f"❌ Temperature parameter failed: {e}")
    
    print("-" * 50)
    
    # Test 5: Long prompt test (similar to your ShadowScribe prompts)
    print("TEST 5: Long prompt test")
    long_prompt = """You are a D&D assistant for Duskryn Nightwarden. Answer this query: "Show my spells"

=== CHARACTER DATA ===
SPELL LIST:
  spellcasting:
    paladin:
      spells:
        1st_level:
          - name: Cure Wounds
            level: 1
            school: evocation
            casting_time: 1 action
            range: Touch
            components: V, S
            duration: Instantaneous
            description: A creature you touch regains hit points equal to 1d8 + your spellcasting ability modifier.
          - name: Divine Favor
            level: 1
            school: evocation
            casting_time: 1 bonus action
            range: Self
            components: V, S
            duration: Concentration, up to 1 minute
            description: Your prayer empowers you with divine radiance. Until the spell ends, your weapon attacks deal an extra 1d4 radiant damage on a hit.

=== INSTRUCTIONS ===
Format your response using proper Markdown. List the available spells with their details.
"""
    
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": long_prompt}],
            max_completion_tokens=500
        )
        
        content = response.choices[0].message.content
        print(f"Response length: {len(content) if content else 0}")
        print(f"Response preview: {content[:300]}..." if content and len(content) > 300 else content)
        
        if content and len(content) > 0:
            print("✅ Long prompt successful")
        else:
            print("❌ Long prompt returned empty response")
    except Exception as e:
        print(f"❌ Long prompt failed: {e}")
    
    print("-" * 50)
    
    # Test 6: Test different model for comparison
    print("TEST 6: Comparison with gpt-4o-mini")
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "What is the capital of France?"}],
            temperature=0.7,
            max_tokens=50
        )
        
        content = response.choices[0].message.content
        print(f"gpt-4o-mini response: {content}")
        print(f"Response length: {len(content) if content else 0}")
        print("✅ gpt-4o-mini comparison successful")
    except Exception as e:
        print(f"❌ gpt-4o-mini comparison failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting OpenAI API Test")
    print("=" * 50)
    asyncio.run(test_gpt5_api())
    print("=" * 50)
    print("🏁 Test completed")
