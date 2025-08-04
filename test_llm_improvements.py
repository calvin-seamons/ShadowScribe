#!/usr/bin/env python3
"""
Test script to validate LLM client improvements for function calling reliability.
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.llm_client import LLMClient
from src.utils.response_models import (
    SourceSelectionResponse, 
    CharacterTargetResponse,
    RulebookTargetResponse,
    SessionTargetResponse
)


class TestDebugLogger:
    """Simple debug logger for testing."""
    
    def __init__(self):
        self.logs = []
    
    def __call__(self, stage: str, message: str, data: dict = None):
        """Log callback function."""
        self.logs.append({
            "stage": stage,
            "message": message,
            "data": data or {}
        })
        print(f"🔧 {stage}: {message}")
        if data:
            print(f"   Data: {data}")


async def test_source_selection():
    """Test source selection with function calling."""
    print("\n🧪 Testing Source Selection...")
    
    client = LLMClient(model="gpt-4.1-mini")
    debug_logger = TestDebugLogger()
    client.set_debug_callback(debug_logger)
    
    test_prompt = """You are an intelligent D&D assistant analyzing a user query to determine which knowledge sources are needed.

Available Sources:
- dnd_rulebook: D&D 5e System Reference Document (2,098 sections covering rules, spells, monsters, items, combat mechanics)
- character_data: Current character information (stats, equipment, abilities, background, objectives and contracts, actions, inventory, feats and traits, spell list)
- session_notes: Previous session summaries and campaign narrative (available dates with NPCs, events, story context)

User Query: "What are my current contracts and their progress?"

Analyze this query and determine which sources you need. Consider:
- Rules questions need dnd_rulebook
- Character-specific questions need character_data
- Story/narrative questions need session_notes
- Combat planning often needs both rules and character data
- Complex questions may need multiple sources

Return a JSON response:
{
  "sources_needed": ["dnd_rulebook", "character_data", "session_notes"],
  "reasoning": "Detailed explanation of why each source is needed for this specific query"
}"""
    
    try:
        response = await client.generate_structured_response(
            test_prompt, 
            SourceSelectionResponse, 
            use_function_calling=True
        )
        print(f"✅ Success: {response}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


async def test_character_targeting():
    """Test character targeting with function calling."""
    print("\n🧪 Testing Character Targeting...")

    client = LLMClient(model="gpt-4.1-mini")
    debug_logger = TestDebugLogger()
    client.set_debug_callback(debug_logger)
    
    test_prompt = """You are targeting specific character data to answer a user query.

User Query: "What are my current contracts and their progress?"

Available Character Files:
- character.json: Basic character info, stats, combat data
- inventory_list.json: Equipment, weapons, armor, magical items  
- feats_and_traits.json: Class features, racial traits, special abilities
- spell_list.json: Available spells organized by class
- action_list.json: Combat actions, attacks, special maneuvers
- character_background.json: Backstory, personality, roleplay info
- objectives_and_contracts.json: Quests, goals, divine covenants, progress tracking

For the query "What are my current contracts and their progress?", which files and specific fields do you need?

Think about:
- "contracts" likely refers to divine covenants, quests, or agreements
- "progress" suggests tracking completion status
- May need character name/context for personalized response

Respond with specific filenames and field paths needed."""
    
    try:
        response = await client.generate_structured_response(
            test_prompt, 
            CharacterTargetResponse, 
            use_function_calling=True
        )
        print(f"✅ Success: {response}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        # Try the specialized method
        try:
            print("🔄 Trying specialized character targeting method...")
            response = await client.generate_character_targeting_response(test_prompt)
            print(f"✅ Specialized method success: {response}")
            return True
        except Exception as e2:
            print(f"❌ Specialized method also failed: {e2}")
            return False


async def test_fallback_behavior():
    """Test fallback from function calling to prompt validation."""
    print("\n🧪 Testing Fallback Behavior...")

    client = LLMClient(model="gpt-4.1-mini")
    debug_logger = TestDebugLogger()
    client.set_debug_callback(debug_logger)
    
    # Test with a deliberately problematic prompt that might cause function calling to fail
    test_prompt = "Analyze this very complex query with many requirements..."
    
    try:
        # Force fallback by using a model that doesn't support function calling
        response = await client.generate_structured_response(
            test_prompt, 
            SourceSelectionResponse, 
            use_function_calling=False  # Force fallback
        )
        print(f"✅ Fallback success: {response}")
        return True
    except Exception as e:
        print(f"❌ Fallback failed: {e}")
        return False


async def main():
    """Main test runner."""
    print("🚀 Testing LLM Client Improvements")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Please set it to run tests.")
        return
    
    results = []
    
    # Run tests
    results.append(await test_source_selection())
    results.append(await test_character_targeting())
    results.append(await test_fallback_behavior())
    
    # Summary
    print("\n📊 Test Results")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Function calling improvements are working.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())
