#!/usr/bin/env python3
"""
Test to debug the exact data flow to response generator
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

from src.knowledge.character_handler import CharacterHandler
from src.engine.content_retriever import ContentRetriever, RetrievedContent
from src.engine.response_generator import ResponseGenerator
from src.knowledge.knowledge_base import KnowledgeBase
from src.engine.query_router import ContentTarget, SourceType

async def test_data_flow():
    """Test the exact data flow to response generator."""
    
    print("🔍 Response Generator Data Flow Test")
    print("=" * 60)
    
    # Get base directory from environment
    base_dir = os.getenv("SHADOWSCRIBE_BASE_DIR", os.getcwd())
    knowledge_base_path = os.path.join(base_dir, "knowledge_base")
    
    print(f"📁 Using knowledge base path: {knowledge_base_path}")
    
    # Initialize components
    kb = KnowledgeBase(knowledge_base_path)
    content_retriever = ContentRetriever(kb)
    response_generator = ResponseGenerator(model="gpt-4o-mini")
    
    # Create a mock target for inventory data
    target = ContentTarget(
        source_type=SourceType.CHARACTER_DATA,
        specific_targets={
            "file_fields": {
                "inventory_list.json": ["*"]
            }
        },
        reasoning="Testing inventory data flow"
    )
    
    print("🎯 Step 1: Content Retrieval")
    content = await content_retriever.fetch_content([target])
    
    print(f"   Retrieved {len(content)} content items")
    for i, item in enumerate(content):
        print(f"   Item {i+1}: {item.source_type.value}")
        if hasattr(item, 'content'):
            print(f"      Content type: {type(item.content)}")
            if isinstance(item.content, dict):
                print(f"      Content keys: {list(item.content.keys())}")
                for filename, data in item.content.items():
                    if isinstance(data, dict):
                        print(f"         {filename}: {list(data.keys())}")
                        if "inventory" in data:
                            inv = data["inventory"]
                            if isinstance(inv, dict):
                                print(f"            inventory keys: {list(inv.keys())}")
                                if "equipped_items" in inv:
                                    equipped = inv["equipped_items"]
                                    if isinstance(equipped, dict):
                                        print(f"               equipped_items keys: {list(equipped.keys())}")
                                        for eq_type, items in equipped.items():
                                            if isinstance(items, list):
                                                print(f"                  {eq_type}: {len(items)} items")
                                                for item_data in items[:2]:  # Show first 2
                                                    if isinstance(item_data, dict) and "name" in item_data:
                                                        print(f"                     - {item_data['name']}")
    
    print("\n🎯 Step 2: Content Organization")
    organized = response_generator._organize_content(content)
    print(f"   Organized keys: {list(organized.keys())}")
    
    if "character" in organized:
        char_data = organized["character"]
        print(f"   Character data keys: {list(char_data.keys())}")
        
        if "equipment" in char_data:
            equipment = char_data["equipment"]
            print(f"   Equipment type: {type(equipment)}")
            if isinstance(equipment, dict):
                print(f"   Equipment keys: {list(equipment.keys())}")
                
                if "equipped_items" in equipment:
                    equipped = equipment["equipped_items"]
                    print(f"   Equipped items type: {type(equipped)}")
                    if isinstance(equipped, dict):
                        print(f"   Equipped categories: {list(equipped.keys())}")
                        
                        # Look for Mantle of Shadow specifically
                        for category, items in equipped.items():
                            if isinstance(items, list):
                                print(f"      {category}: {len(items)} items")
                                for item in items:
                                    if isinstance(item, dict) and "name" in item:
                                        if "mantle" in item["name"].lower() or "shadow" in item["name"].lower():
                                            print(f"         🎯 FOUND: {item['name']}")
                                            print(f"            Keys: {list(item.keys())}")
                                            if "description" in item:
                                                desc = item["description"]
                                                print(f"            Description: {desc[:100]}...")
                                            if "features" in item:
                                                features = item["features"]
                                                print(f"            Features: {list(features.keys()) if isinstance(features, dict) else type(features)}")
    
    print("\n🎯 Step 3: Prompt Creation")
    query = "Tell me about the Mantle of Shadow"
    prompt = response_generator._create_response_prompt(query, organized)
    
    print(f"   Prompt length: {len(prompt)} characters")
    print("   Prompt preview (first 1000 chars):")
    print("   " + "-" * 50)
    print("   " + prompt[:1000].replace('\n', '\n   '))
    print("   " + "-" * 50)
    
    # Look specifically for Mantle of Shadow in the prompt
    if "mantle" in prompt.lower() and "shadow" in prompt.lower():
        print("   ✅ Mantle of Shadow found in prompt!")
        
        # Extract the relevant section
        lines = prompt.split('\n')
        mantle_section = []
        in_mantle_section = False
        
        for line in lines:
            if "mantle" in line.lower() and "shadow" in line.lower():
                in_mantle_section = True
                mantle_section.append(line)
            elif in_mantle_section:
                if line.strip() and not line.startswith(' '):
                    # New section started
                    break
                mantle_section.append(line)
        
        if mantle_section:
            print("   Mantle of Shadow section:")
            for line in mantle_section[:10]:  # Show first 10 lines
                print(f"     {line}")
    else:
        print("   ❌ Mantle of Shadow NOT found in prompt!")
        
        # Let's see what IS in the equipment section
        if "equipment" in prompt.lower():
            print("   Equipment section found, checking content...")
            lines = prompt.split('\n')
            in_equipment = False
            equipment_lines = []
            
            for line in lines:
                if "equipment" in line.lower() and line.strip().endswith(':'):
                    in_equipment = True
                    equipment_lines.append(line)
                elif in_equipment:
                    if line.strip() and not line.startswith(' '):
                        break
                    equipment_lines.append(line)
            
            print("   Equipment section content:")
            for line in equipment_lines[:15]:
                print(f"     {line}")

if __name__ == "__main__":
    asyncio.run(test_data_flow())
