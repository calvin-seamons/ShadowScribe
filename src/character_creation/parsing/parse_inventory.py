#!/usr/bin/env python3
"""
Script to extract inventory items from D&D Beyond JSON export.

This script creates InventoryItem objects from the character JSON and outputs them to a JSON file.
"""

import html
import json
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path

from src.rag.character.character_types import (
    ItemModifier,
    LimitedUse,
    InventoryItemDefinition,
    InventoryItem,
    Inventory
)


class DNDBeyondInventoryParser:
    """Parser for D&D Beyond inventory data."""
    
    def __init__(self, json_data: Dict[str, Any]):
        """Initialize with D&D Beyond JSON data."""
        self.json_data = json_data
    
    def parse_inventory(self) -> Inventory:
        """Parse inventory from D&D Beyond JSON and return Inventory object."""
        items = extract_inventory_items(self.json_data)
        
        # Calculate total weight
        total_weight = sum(
            (item.definition.weight or 0) * item.quantity 
            for item in items
        )
        
        # Simple split: equipped vs backpack based on equipped status
        equipped_items = []
        backpack = []
        
        for item in items:
            if item.equipped:
                equipped_items.append(item)
            else:
                backpack.append(item)
        
        return Inventory(
            total_weight=total_weight,
            weight_unit="lb",
            equipped_items=equipped_items,
            backpack=backpack,
            valuables=[]
        )


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON file and return the data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_inventory_items(data: Dict[str, Any]) -> List[InventoryItem]:
    """
    Parse a D&D Beyond JSON export and produce a cleaned, deduplicated list of InventoryItem objects.
    
    Description:
    - Extracts item definitions from data['data']['inventory'] (returns an empty list if the key is missing or not a list).
    - Cleans HTML in item descriptions to plain text.
    - Removes granted modifiers and limited-use entries that contain no meaningful fields.
    - Merges items with the same name and description by summing their quantities; other fields are preserved from the first occurrence.
    
    Parameters:
        data (Dict[str, Any]): Parsed JSON dictionary from a D&D Beyond export.
    
    Returns:
        List[InventoryItem]: A list of cleaned InventoryItem objects with duplicate items (same name and description) combined and their quantities summed.
    """
    items = []
    
    # Access inventory under data key
    if 'data' not in data or 'inventory' not in data['data']:
        print("No 'inventory' key found in JSON data")
        return items
    
    inventory = data['data']['inventory']
    if not isinstance(inventory, list):
        print("Inventory is not a list")
        return items
    
    for item_data in inventory:
        # Extract and clean definition fields
        def_data = item_data.get('definition', {})
        
        # Clean granted modifiers
        granted_modifiers = []
        if def_data.get('grantedModifiers'):
            for mod in def_data['grantedModifiers']:
                dice = mod.get('dice', {})
                cleaned_mod = ItemModifier(
                    type=mod.get('type'),
                    subType=mod.get('subType'),
                    restriction=mod.get('restriction'),
                    friendlyTypeName=mod.get('friendlyTypeName'),
                    friendlySubtypeName=mod.get('friendlySubtypeName'),
                    duration=mod.get('duration'),
                    fixedValue=mod.get('fixedValue'),
                    diceString=dice.get('diceString') if dice else None
                )
                # Only add if it has meaningful data
                if any(getattr(cleaned_mod, field) is not None for field in ItemModifier.model_fields):
                    granted_modifiers.append(cleaned_mod)
        
        # Clean description
        description = def_data.get('description')
        if description:
            description = clean_html(description)
        
        definition = InventoryItemDefinition(
            name=def_data.get('name'),
            type=def_data.get('type'),
            description=description,
            canAttune=def_data.get('canAttune'),
            attunementDescription=def_data.get('attunementDescription'),
            rarity=def_data.get('rarity'),
            weight=def_data.get('weight'),
            capacity=def_data.get('capacity'),
            capacityWeight=def_data.get('capacityWeight'),
            canEquip=def_data.get('canEquip'),
            magic=def_data.get('magic'),
            tags=def_data.get('tags'),
            grantedModifiers=granted_modifiers if granted_modifiers else None,
            damage=def_data.get('damage'),
            damageType=def_data.get('damageType'),
            attackType=def_data.get('attackType'),
            range=def_data.get('range'),
            longRange=def_data.get('longRange'),
            isContainer=def_data.get('isContainer'),
            isCustomItem=def_data.get('isCustomItem')
        )
        
        # Clean limited use
        limited_use = None
        if item_data.get('limitedUse'):
            lu = item_data['limitedUse']
            limited_use = LimitedUse(
                maxUses=lu.get('maxUses'),
                resetType=lu.get('resetType'),
                resetTypeDescription=lu.get('resetTypeDescription')
            )
            # Only keep if it has meaningful data
            if not any(getattr(limited_use, field) is not None for field in LimitedUse.model_fields):
                limited_use = None
        
        # Create InventoryItem
        item = InventoryItem(
            definition=definition,
            quantity=item_data.get('quantity', 1),
            isAttuned=item_data.get('isAttuned', False),
            equipped=item_data.get('equipped', False),
            limitedUse=limited_use
        )
        
        items.append(item)
    
    # Merge items with same name and description
    merged_items = {}
    for item in items:
        key = (item.definition.name, item.definition.description)
        if key in merged_items:
            merged_items[key].quantity += item.quantity
            # For other fields, keep the first one (assuming they are the same)
        else:
            merged_items[key] = item
    
    return list(merged_items.values())


def clean_html(text: str) -> str:
    """Clean HTML tags and formatting from text.
    
    Converts HTML to clean, readable plain text:
    - Removes script and style blocks entirely
    - Decodes HTML entities (&nbsp;, &amp;, etc.)
    - Converts block elements (p, br, div) to newlines
    - Removes all HTML tags
    - Cleans up excessive whitespace while preserving paragraph structure
    """
    if not text:
        return ''
    
    # Remove script and style blocks entirely (before any other processing)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Decode HTML entities (e.g., &nbsp; -> space, &amp; -> &)
    text = html.unescape(text)
    
    # Convert block-level elements to double newlines (paragraph breaks)
    text = re.sub(r'</p>\s*<p[^>]*>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?p[^>]*>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?div[^>]*>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<h[1-6][^>]*>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</h[1-6]>', '\n\n', text, flags=re.IGNORECASE)
    
    # Convert br tags to single newlines
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up whitespace:
    # - Replace \r\n and \r with \n
    text = re.sub(r'\r\n?', '\n', text)
    
    # - Collapse multiple spaces (but not newlines) into single space
    text = re.sub(r'[^\S\n]+', ' ', text)
    
    # - Collapse 3+ newlines into 2 (preserve paragraph breaks)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # - Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # - Remove empty lines at start and end
    text = text.strip()
    
    return text


def should_include_field(key: str, value: Any) -> bool:
    """Determine if a field should be included in the output."""
    # Always exclude null values
    if value is None:
        return False
    
    # Exclude zero values for certain fields
    if key in ['weight', 'capacityWeight'] and value == 0:
        return False
    
    # Exclude empty strings
    if isinstance(value, str) and value.strip() == "":
        return False
    
    # Exclude empty lists
    if isinstance(value, list) and len(value) == 0:
        return False
    
    return True
