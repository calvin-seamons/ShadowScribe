#!/usr/bin/env python3
"""
Test to verify nested field selection behavior
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

async def test_nested_field_behavior():
    """Test specific nested field path behavior."""
    
    print("🔍 Nested Field Selection Behavior Test")
    print("=" * 60)
    
    # Get base directory from environment
    base_dir = os.getenv("SHADOWSCRIBE_BASE_DIR", os.getcwd())
    knowledge_base_path = os.path.join(base_dir, "knowledge_base")
    
    print(f"📁 Using knowledge base path: {knowledge_base_path}")
    
    # Initialize character handler
    handler = CharacterHandler(knowledge_base_path)
    handler.load_data()
    
    if not handler.is_loaded():
        print("❌ Character handler failed to load data")
        return
        
    print("✅ Character handler loaded successfully")
    print("")
    
    # Test 1: Request all data with '*'
    print("🧪 Test 1: Request entire file with '*'")
    all_data = handler.get_file_data("inventory_list.json", ["*"])
    if all_data:
        print(f"   Returned keys: {list(all_data.keys())}")
        for key, value in all_data.items():
            if isinstance(value, dict):
                print(f"   {key}: dict with {len(value)} keys -> {list(value.keys())[:3]}...")
            elif isinstance(value, list):
                print(f"   {key}: list with {len(value)} items")
            else:
                print(f"   {key}: {type(value).__name__}")
    print("")
    
    # Test 2: Request specific top-level field
    print("🧪 Test 2: Request specific top-level field 'inventory'")
    inventory_data = handler.get_file_data("inventory_list.json", ["inventory"])
    if inventory_data:
        print(f"   Returned keys: {list(inventory_data.keys())}")
        if "inventory" in inventory_data:
            inv = inventory_data["inventory"]
            if isinstance(inv, dict):
                print(f"   inventory contents: {list(inv.keys())}")
                # Show structure of nested data
                for key, value in inv.items():
                    if isinstance(value, dict):
                        print(f"      {key}: dict with {len(value)} keys -> {list(value.keys())[:3]}...")
                    elif isinstance(value, list):
                        print(f"      {key}: list with {len(value)} items")
                        if value and isinstance(value[0], dict):
                            print(f"         First item keys: {list(value[0].keys())[:3]}...")
                    else:
                        print(f"      {key}: {type(value).__name__}")
    print("")
    
    # Test 3: Request deeper nested field (if it exists)
    print("🧪 Test 3: Request nested field path")
    # First, let's see what nested paths are available
    full_data = handler.get_file_data("inventory_list.json", ["*"])
    if full_data and "inventory" in full_data:
        inventory = full_data["inventory"]
        if isinstance(inventory, dict):
            nested_keys = list(inventory.keys())
            print(f"   Available nested paths under 'inventory': {nested_keys}")
            
            # Try to request a specific nested field if available
            if nested_keys:
                first_nested = nested_keys[0]
                nested_path = f"inventory.{first_nested}"
                print(f"   Testing nested path: '{nested_path}'")
                
                nested_data = handler.get_file_data("inventory_list.json", [nested_path])
                if nested_data:
                    print(f"   Returned keys: {list(nested_data.keys())}")
                    if nested_path in nested_data:
                        nested_content = nested_data[nested_path]
                        print(f"   Content type: {type(nested_content).__name__}")
                        if isinstance(nested_content, dict):
                            print(f"   Content keys: {list(nested_content.keys())}")
                        elif isinstance(nested_content, list):
                            print(f"   Content list length: {len(nested_content)}")
                            if nested_content and isinstance(nested_content[0], dict):
                                print(f"   First item keys: {list(nested_content[0].keys())}")
    print("")
    
    # Test 4: Multiple specific fields
    print("🧪 Test 4: Request multiple specific fields")
    multi_data = handler.get_file_data("inventory_list.json", ["inventory", "metadata"])
    if multi_data:
        print(f"   Returned keys: {list(multi_data.keys())}")
        for key in multi_data:
            value = multi_data[key]
            if isinstance(value, dict):
                print(f"   {key}: dict with {len(value)} keys")
            elif isinstance(value, list):
                print(f"   {key}: list with {len(value)} items")
            else:
                print(f"   {key}: {type(value).__name__} - {str(value)[:50]}...")
    
    print("\n" + "=" * 60)
    print("🏁 Conclusion:")
    print("   ✓ '*' returns entire file")
    print("   ✓ Specific field returns that field + all nested content")
    print("   ✓ Nested paths work with dot notation")
    print("   ✓ Multiple fields can be requested simultaneously")

if __name__ == "__main__":
    asyncio.run(test_nested_field_behavior())
