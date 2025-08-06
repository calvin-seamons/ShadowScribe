#!/usr/bin/env python3
"""
Diagnostic Test for LLM Client Targeting Failures
This script helps identify why generate_structured_response() is failing.
"""

import asyncio
import json
import logging
import traceback
from src.engine.query_router import QueryRouter
from src.utils.llm_client import LLMClient
from src.utils.response_models import CharacterTargetResponse

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_llm_targeting():
    """Test the LLM targeting with detailed debugging."""
    
    print("🔍 DIAGNOSTIC TEST: LLM Character Targeting")
    print("=" * 60)
    
    # Create clients
    router = QueryRouter()
    llm_client = LLMClient(model="gpt-4o-mini")
    
    # Test queries that should target character_background.json
    test_queries = [
        "Tell me about my backstory",
        "Tell me about Duskryn's parents", 
        "What is my family history?",
        "Who are Thaldrin and Brenna?",
        "Tell me about my character's background"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 TEST {i}: {query}")
        print("-" * 40)
        
        try:
            # Test the full targeting process
            print("🎯 Testing full router targeting...")
            target = await router._target_character_content(query, 0.9)
            
            files_selected = list(target.specific_targets.get("file_fields", {}).keys())
            print(f"✅ Router SUCCESS - Files: {files_selected}")
            print(f"📄 Reasoning: {target.reasoning}")
            
            # Check if this looks like a fallback response
            if "Fallback" in target.reasoning:
                print("⚠️  This is a FALLBACK response - function calling failed!")
            
            # Check if character_background.json was included
            if "character_background.json" in files_selected:
                print("✅ character_background.json correctly included!")
            else:
                print("❌ character_background.json MISSING!")
                
        except Exception as e:
            print(f"❌ Router FAILED: {str(e)}")
            print(f"📚 Error details: {traceback.format_exc()}")
            
            # Test the raw LLM call directly
            print("🔧 Testing raw LLM call...")
            await test_raw_llm_call(llm_client, query)
    
    print(f"\n🏁 Diagnostic test complete!")

async def test_raw_llm_call(llm_client: LLMClient, query: str):
    """Test the raw LLM call to see what's actually happening."""
    
    # Use the exact prompt from the router
    prompt = f"""Target specific character data files for Duskryn Nightwarden.

Query: "{query}"

Available character files and their contents:
1. character.json - Core stats
   - character_base (name, race, classes, level)
   - ability_scores (STR, DEX, CON, INT, WIS, CHA)
   - combat_stats (AC, HP, initiative, speed, proficiency)
   - proficiencies (saves, skills, tools, languages)

2. inventory_list.json - All equipment
   - inventory.equipped_items (currently worn/wielded)
   - inventory.weapons (including Eldaryth of Regret)
   - inventory.armor (plate mail, etc.)
   - inventory.consumables (potions, scrolls)
   - inventory.other_items (general equipment)

3. spell_list.json - All known spells
   - character_spells.paladin_spells (by level)
   - character_spells.warlock_spells (by level)
   - character_spells.cantrips
   - character_spells.spell_slots

4. action_list.json - Combat actions
   - character_actions.action_economy (what can be done when)
   - character_actions.attacks_per_action
   - character_actions.special_abilities (Divine Smite, Hex, etc.)

5. feats_and_traits.json - Abilities
   - features_and_traits.class_features (Paladin/Warlock abilities)
   - features_and_traits.species_traits (Hill Dwarf traits)
   - features_and_traits.feats (Lucky, Fey Touched)

6. character_background.json - Roleplay info
   - background (Acolyte background and features)
   - characteristics (alignment, physical appearance, personality traits, ideals, bonds, flaws)
   - backstory (main story sections)
   - backstory.family_backstory (family history and parents)
   - backstory.family_backstory.parents (Thaldrin and Brenna Nightwarden)
   - organizations (Holy Knights of Kluntul, etc.)
   - allies (High Acolyte Aldric, fellow knights)
   - enemies (Xurmurrin, The Voiceless One)
   - notes (additional character context)

7. objectives_and_contracts.json - Quests
   - objectives_and_contracts.active_contracts
   - objectives_and_contracts.current_objectives
   - objectives_and_contracts.completed_objectives
   - objectives_and_contracts.divine_covenants (Ghul'Vor pact)

TARGETING GUIDANCE - Match queries to appropriate files:
- Combat/stats queries → character.json, action_list.json, inventory_list.json
- Spell queries → spell_list.json
- Equipment queries → inventory_list.json  
- Abilities/features queries → feats_and_traits.json
- BACKSTORY/FAMILY/PERSONALITY queries → character_background.json
- Quest/objective queries → objectives_and_contracts.json

For BACKSTORY queries specifically, you MUST include character_background.json with these fields:
- backstory, backstory.family_backstory, characteristics, allies, enemies, organizations

Select the files and specific fields needed. Use dot notation for nested fields.
Be selective - when in doubt, include more data.

Return file_fields as a dict mapping filenames to field lists."""

    try:
        print(f"📤 Sending prompt to LLM...")
        print(f"📊 Prompt length: {len(prompt)} characters")
        
        response = await llm_client.generate_structured_response(
            prompt, 
            CharacterTargetResponse,
            max_retries=0  # No retries to see raw failure
        )
        
        print(f"✅ Raw LLM SUCCESS!")
        print(f"📄 Response: {response.model_dump_json(indent=2)}")
        
    except Exception as e:
        print(f"❌ Raw LLM FAILED: {str(e)}")
        print(f"📚 Full error: {traceback.format_exc()}")
        
        # Try to get more details about what went wrong
        try:
            # Test if it's a basic API connectivity issue
            simple_response = await llm_client.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Say 'API working'"}],
                max_tokens=10
            )
            print(f"✅ Basic API connectivity works: {simple_response.choices[0].message.content}")
            
        except Exception as api_error:
            print(f"❌ Basic API also failed: {str(api_error)}")

async def test_schema_complexity():
    """Test if the Pydantic schema is too complex."""
    print(f"\n🧪 SCHEMA COMPLEXITY TEST")
    print("-" * 40)
    
    # Print the actual schema being sent to the LLM
    schema = CharacterTargetResponse.model_json_schema()
    print(f"📋 CharacterTargetResponse schema:")
    print(json.dumps(schema, indent=2))
    
    # Check schema size
    schema_size = len(json.dumps(schema))
    print(f"📏 Schema size: {schema_size} characters")
    
    if schema_size > 2000:
        print("⚠️  Schema might be too large for function calling")
    else:
        print("✅ Schema size looks reasonable")

if __name__ == "__main__":
    print("🚀 Starting LLM Diagnostic Test...")
    
    async def main():
        await test_schema_complexity()
        await test_llm_targeting()
    
    asyncio.run(main())
