#!/usr/bin/env python3
"""
Integration test for D&D Beyond fetcher + Async Character Builder.

This test demonstrates the complete workflow:
1. Fetch character JSON from D&D Beyond URL
2. Parse character asynchronously with progress updates
3. Verify character data is complete and correct

This simulates what the WebSocket endpoint will do.
"""

import asyncio
import re
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import httpx
from src.character_creation.async_character_builder import AsyncCharacterBuilder


def extract_character_id(url: str) -> Optional[str]:
    """Extract character ID from D&D Beyond URL."""
    pattern = r'/characters/(\d+)'
    match = re.search(pattern, url)
    return match.group(1) if match else None


async def fetch_character_json(character_id: str):
    """Fetch character JSON from D&D Beyond."""
    url = f"https://character-service.dndbeyond.com/character/v5/character/{character_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


async def test_full_workflow(url: str):
    """Test the complete workflow from URL to parsed character."""
    print("\n" + "="*80)
    print("INTEGRATION TEST: D&D BEYOND FETCHER + ASYNC BUILDER")
    print("="*80)
    print(f"\n📍 Step 1: Extract character ID from URL")
    print(f"   URL: {url}")
    
    # Extract character ID
    character_id = extract_character_id(url)
    print(f"   Character ID: {character_id}")
    
    if not character_id:
        print("   ❌ Failed to extract character ID")
        return False
    
    print(f"   ✓ Character ID extracted successfully")
    
    # Fetch character JSON
    print(f"\n📥 Step 2: Fetch character JSON from D&D Beyond")
    try:
        json_data = await fetch_character_json(character_id)
        print(f"   ✓ Character JSON fetched successfully")
        print(f"   Size: {len(str(json_data))} bytes")
        
        # Extract basic info
        character_name = json_data.get('data', {}).get('name', 'Unknown')
        print(f"   Name: {character_name}")
    except Exception as e:
        print(f"   ❌ Failed to fetch character: {e}")
        return False
    
    # Parse character asynchronously
    print(f"\n⚙️  Step 3: Parse character with async builder")
    print(f"   Running 6 parsers in parallel with progress tracking...\n")
    
    progress_events = []
    
    async def progress_callback(event):
        """Track progress events."""
        progress_events.append(event)
        
        event_type = event['type']
        if event_type == 'parser_started':
            print(f"   ⏳ [{event['completed']}/{event['total']}] Starting {event['parser']}...")
        elif event_type == 'parser_complete':
            print(f"   ✓  [{event['completed']}/{event['total']}] {event['parser'].capitalize()} "
                  f"complete ({event['execution_time_ms']:.0f}ms)")
        elif event_type == 'assembly_started':
            print(f"   🔧 Assembling character object...")
        elif event_type == 'creation_complete':
            print(f"   ✓  Character creation complete!")
            print(f"      Total time: {event['total_time_ms']:.0f}ms")
    
    try:
        builder = AsyncCharacterBuilder(json_data)
        character = await builder.build_async(progress_callback=progress_callback)
        print(f"   ✓ Character parsed successfully")
    except Exception as e:
        print(f"   ❌ Failed to parse character: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify character data
    print(f"\n🔍 Step 4: Verify character data completeness")
    
    checks = []
    
    # Check required fields
    checks.append(("Name", character.character_base.name == character_name))
    checks.append(("Race", bool(character.character_base.race)))
    checks.append(("Class", bool(character.character_base.character_class)))
    checks.append(("Level", character.character_base.total_level > 0))
    checks.append(("HP", character.combat_stats.max_hp > 0))
    checks.append(("AC", character.combat_stats.armor_class > 0))
    checks.append(("Ability Scores", all([
        character.ability_scores.strength >= 1,
        character.ability_scores.dexterity >= 1,
        character.ability_scores.constitution >= 1,
        character.ability_scores.intelligence >= 1,
        character.ability_scores.wisdom >= 1,
        character.ability_scores.charisma >= 1
    ])))
    checks.append(("Background", bool(character.background_info)))
    checks.append(("Personality", bool(character.personality)))
    checks.append(("Backstory", bool(character.backstory)))
    
    # Check optional fields
    has_inventory = character.inventory is not None
    has_spells = character.spell_list is not None
    has_actions = character.action_economy is not None
    has_features = character.features_and_traits is not None
    
    checks.append(("Inventory", has_inventory))
    checks.append(("Actions", has_actions))
    checks.append(("Features", has_features))
    
    # Display results
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"   {status} {check_name}")
    
    all_passed = all(passed for _, passed in checks)
    
    # Print character summary
    print(f"\n📊 Step 5: Character Summary")
    print(f"   Name: {character.character_base.name}")
    print(f"   Race: {character.character_base.race}")
    print(f"   Class: {character.character_base.character_class} (Level {character.character_base.total_level})")
    print(f"   HP: {character.combat_stats.max_hp} | AC: {character.combat_stats.armor_class}")
    
    if has_inventory:
        total_items = (
            len(character.inventory.equipped_items) +
            len(character.inventory.backpack)
        )
        print(f"   Inventory: {total_items} items")
    
    if has_spells:
        total_spells = sum(
            len(spells)
            for class_spells in character.spell_list.spells.values()
            for spells in class_spells.values()
        )
        print(f"   Spells: {total_spells} spells known")
    
    if has_actions:
        print(f"   Actions: {len(character.action_economy.actions)} actions")
    
    if has_features:
        total_features = sum(
            len(features)
            for levels in character.features_and_traits.class_features.values()
            for features in levels.values()
        )
        print(f"   Features: {total_features} class features, "
              f"{len(character.features_and_traits.racial_traits)} racial traits")
    
    # Progress analysis
    print(f"\n📈 Step 6: Progress Events Analysis")
    parser_started = [e for e in progress_events if e['type'] == 'parser_started']
    parser_complete = [e for e in progress_events if e['type'] == 'parser_complete']
    
    print(f"   Parser started events: {len(parser_started)}")
    print(f"   Parser complete events: {len(parser_complete)}")
    print(f"   All parsers completed: {len(parser_complete) == 6}")
    
    if parser_complete:
        times = [e['execution_time_ms'] for e in parser_complete]
        print(f"   Fastest parser: {min(times):.0f}ms")
        print(f"   Slowest parser: {max(times):.0f}ms")
        print(f"   Average time: {sum(times)/len(times):.0f}ms")
    
    # Final result
    print("\n" + "="*80)
    if all_passed and len(parser_complete) == 6:
        print("✅ INTEGRATION TEST PASSED")
        print("="*80)
        print("✓ URL parsing works")
        print("✓ D&D Beyond fetcher works")
        print("✓ Async builder works")
        print("✓ Progress callbacks work")
        print("✓ All parsers complete successfully")
        print("✓ Character data is complete and valid")
        print("="*80)
        return True
    else:
        print("❌ INTEGRATION TEST FAILED")
        print("="*80)
        if not all_passed:
            failed = [name for name, passed in checks if not passed]
            print(f"Failed checks: {', '.join(failed)}")
        if len(parser_complete) != 6:
            print(f"Not all parsers completed: {len(parser_complete)}/6")
        print("="*80)
        return False


async def main():
    """Main test function."""
    if len(sys.argv) < 2:
        print("Usage: python test_integration.py <dndbeyond_url>")
        print("\nExample:")
        print("  python scripts/test_integration.py https://www.dndbeyond.com/characters/152248393")
        sys.exit(1)
    
    url = sys.argv[1]
    success = await test_full_workflow(url)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
