#!/usr/bin/env python3
"""
D&D Beyond Actions Parser

This script parses a D&D Beyond character JSON export and extracts all possible non-spell actions
the character can perform, including attacks, special abilities, and item actions.

Usage:
    python parse_actions.py <path_to_json_file>
"""

import json
import re
import asyncio
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

from src.llm.llm_client import LLMClientFactory
from src.llm.json_repair import JSONRepair
from src.rag.character.character_types import (
    ActionActivation,
    ActionUsage,
    ActionRange,
    ActionDamage,
    ActionSave,
    CharacterAction
)


class DNDBeyondActionsParser:
    """Parser for extracting all character actions from D&D Beyond JSON."""
    
    # Action type mappings
    ACTION_TYPE_MAP = {
        1: "action",
        2: "no_action", 
        3: "bonus_action",
        4: "reaction",
        5: "reaction",
        6: "reaction",
        7: "reaction",
        8: "no_action"
    }
    
    RESET_TYPE_MAP = {
        1: "short_rest",
        2: "long_rest",
        3: "dawn",
        4: "dusk",
        5: "recharge",
        6: "turn"
    }
    
    ABILITY_MAP = {
        1: "Strength",
        2: "Dexterity",
        3: "Constitution", 
        4: "Intelligence",
        5: "Wisdom",
        6: "Charisma"
    }
    
    def __init__(self, json_data: Dict[str, Any]):
        """Initialize parser with D&D Beyond JSON data."""
        self.data = json_data.get("data", {})
        
    def clean_html_description(self, description: str) -> str:
        """Clean HTML tags and format text."""
        if not description:
            return ""
            
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', description)
        
        # Replace HTML entities
        replacements = {
            '&amp;': '&', '&lt;': '<', '&gt;': '>', '&nbsp;': ' ',
            '&rsquo;': "'", '&ldquo;': '"', '&rdquo;': '"'
        }
        for old, new in replacements.items():
            clean_text = clean_text.replace(old, new)
        
        # Clean up whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text
    
    def parse_activation(self, activation_data: Dict[str, Any], action_type: int) -> ActionActivation:
        """Parse activation information."""
        activation = ActionActivation()
        
        if action_type in self.ACTION_TYPE_MAP:
            activation.activationType = self.ACTION_TYPE_MAP[action_type]
        
        if activation_data:
            activation.activationTime = activation_data.get("activationTime")
        
        return activation
    
    def parse_usage(self, limited_use_data: Dict[str, Any]) -> Optional[ActionUsage]:
        """Parse usage limitations."""
        if not limited_use_data:
            return None
            
        max_uses = limited_use_data.get("maxUses")
        if not max_uses:
            return None
            
        usage = ActionUsage()
        usage.maxUses = max_uses
        
        reset_type = limited_use_data.get("resetType")
        if reset_type in self.RESET_TYPE_MAP:
            usage.resetType = self.RESET_TYPE_MAP[reset_type]
        
        usage.usesPerActivation = limited_use_data.get("minNumberConsumed", 1)
        
        return usage
    
    def parse_range(self, range_data: Dict[str, Any]) -> Optional[ActionRange]:
        """
        Create an ActionRange object from raw range data extracted from D&D Beyond JSON.
        
        Parameters:
            range_data (Dict[str, Any]): Raw range-related fields from the export. Expected keys include
                "range" (numeric distance in feet), "longRange" (numeric long range in feet),
                "aoeSize" (numeric area size in feet), and "aoeType" (numeric code for AOE shape).
        
        Returns:
            ActionRange | None: An ActionRange with any of these fields populated:
                - range: nominal range in feet
                - longRange: long range in feet
                - aoeSize: area of effect size in feet
                - aoeType: one of "sphere", "cube", "cone", "line" when applicable
                - rangeDescription: human-readable description (e.g., "60 feet", "30-foot cone", or
                  "60 feet (long: 120 feet)")
            Returns None when the input contains no meaningful range or AOE information.
        """
        if not range_data:
            return None
            
        action_range = ActionRange()
        action_range.range = range_data.get("range")
        action_range.longRange = range_data.get("longRange")
        action_range.aoeSize = range_data.get("aoeSize")
        
        # Convert AOE type
        aoe_type = range_data.get("aoeType")
        if aoe_type == 1:
            action_range.aoeType = "sphere"
        elif aoe_type == 2:
            action_range.aoeType = "cube"
        elif aoe_type == 3:
            action_range.aoeType = "cone"
        elif aoe_type == 4:
            action_range.aoeType = "line"
        
        # Build range description
        if action_range.range:
            action_range.rangeDescription = f"{action_range.range} feet"
            if action_range.longRange:
                action_range.rangeDescription += f" (long: {action_range.longRange} feet)"
        elif action_range.aoeType and action_range.aoeSize:
            action_range.rangeDescription = f"{action_range.aoeSize}-foot {action_range.aoeType}"
        
        return action_range if any(getattr(action_range, f) for f in ActionRange.model_fields) else None
    
    def parse_damage(self, dice_data: Dict[str, Any], damage_type_id: int, fixed_value: int) -> Optional[ActionDamage]:
        """
        Parse damage information from provided dice data or a fixed value and map the numeric damage type ID to a damage type name.
        
        Parameters:
        	dice_data (Dict[str, Any]): Damage descriptor that may contain a "diceString" entry.
        	damage_type_id (int): Numeric ID representing the damage type (mapped to names like "bludgeoning", "fire", etc.).
        	fixed_value (int): Fixed damage value to use when no dice string is present.
        
        Returns:
        	ActionDamage or None: An ActionDamage with `diceNotation`, `fixedDamage`, and/or `damageType` set when any damage information exists; `None` if no damage fields were populated.
        """
        damage = ActionDamage()
        
        if dice_data and dice_data.get("diceString"):
            damage.diceNotation = dice_data["diceString"]
        elif fixed_value:
            damage.fixedDamage = fixed_value
        
        # Map damage type ID to name (simplified mapping)
        damage_types = {
            1: "bludgeoning", 2: "piercing", 3: "slashing", 4: "necrotic",
            5: "radiant", 6: "fire", 7: "cold", 8: "lightning", 9: "thunder",
            10: "poison", 11: "acid", 12: "psychic", 13: "force"
        }
        
        if damage_type_id in damage_types:
            damage.damageType = damage_types[damage_type_id]
        
        return damage if any(getattr(damage, f) for f in ActionDamage.model_fields) else None
    
    def parse_save(self, save_dc: int, save_stat_id: int, success_desc: str, fail_desc: str) -> Optional[ActionSave]:
        """
        Create an ActionSave object from provided save details.
        
        Parameters:
            save_dc (int): The save DC value to assign to the ActionSave.
            save_stat_id (int): Numeric ability identifier; mapped to an ability name when present in ABILITY_MAP.
            success_desc (str): HTML or rich-text description for successful saves; will be cleaned.
            fail_desc (str): HTML or rich-text description for failed saves; will be cleaned.
        
        Returns:
            Optional[ActionSave]: An ActionSave with `saveDC`, `saveAbility` (when mapped), `onSuccess`, and `onFailure` populated with cleaned text, or `None` if all inputs are empty or falsy.
        """
        if not any([save_dc, save_stat_id, success_desc, fail_desc]):
            return None
            
        save = ActionSave()
        save.saveDC = save_dc
        
        if save_stat_id in self.ABILITY_MAP:
            save.saveAbility = self.ABILITY_MAP[save_stat_id]
        
        save.onSuccess = self.clean_html_description(success_desc) if success_desc else None
        save.onFailure = self.clean_html_description(fail_desc) if fail_desc else None
        
        return save
    
    def parse_basic_actions(self) -> List[CharacterAction]:
        """Parse actions from the actions section."""
        actions = []
        
        actions_data = self.data.get("actions", {})
        
        for category in ["race", "class", "background", "item", "feat"]:
            category_actions = actions_data.get(category, [])
            if not category_actions:
                continue
                
            for action_data in category_actions:
                action = CharacterAction(
                    name=action_data.get("name", "Unknown Action"),
                    description=self.clean_html_description(action_data.get("description")),
                    shortDescription=self.clean_html_description(action_data.get("snippet")),
                    source=category,
                    actionCategory="feature"
                )
                
                # Parse activation
                action.activation = self.parse_activation(
                    action_data.get("activation", {}),
                    action_data.get("actionType", 0)
                )
                
                # Fix specific activation types based on ability descriptions
                action_name = action.name.lower()
                if "aura of the guardian" in action_name or "rebuke the violent" in action_name:
                    # These are clearly reaction-based abilities
                    action.activation.activationType = "reaction"
                elif "create pact weapon" in action_name or "divine sense" in action_name or "lay on hands" in action_name:
                    # These are action-based abilities despite what the data shows
                    action.activation.activationType = "action"
                
                # Parse usage
                action.usage = self.parse_usage(action_data.get("limitedUse", {}))
                
                # Parse range
                action.actionRange = self.parse_range(action_data.get("range", {}))
                
                # Parse damage
                action.damage = self.parse_damage(
                    action_data.get("dice"),
                    action_data.get("damageTypeId"),
                    action_data.get("value")
                )
                
                # Parse save
                action.save = self.parse_save(
                    action_data.get("fixedSaveDc"),
                    action_data.get("saveStatId"),
                    action_data.get("saveSuccessDescription"),
                    action_data.get("saveFailDescription")
                )
                
                # Combat flags
                action.isWeaponAttack = action_data.get("attackType") in [1, 2]  # Melee or ranged
                action.attackBonus = action_data.get("fixedToHit")
                
                actions.append(action)
        
        return actions
    

    
    def parse_weapon_actions(self) -> List[CharacterAction]:
        """Parse weapon attacks from inventory (equipped weapons only)."""
        actions = []
        
        inventory = self.data.get("inventory", [])
        
        for item_data in inventory:
            definition = item_data.get("definition", {})
            
            # Skip non-weapons or unequipped weapons
            if not definition.get("attackType") or not item_data.get("equipped"):
                continue
            
            action = CharacterAction(
                name=f"{definition.get('name', 'Unknown Weapon')} Attack",
                description=self.clean_html_description(definition.get("description")),
                source="item",
                sourceFeature=definition.get("name"),
                actionCategory="attack",
                isWeaponAttack=True
            )
            
            # Weapon activation (usually action)
            action.activation = ActionActivation(activationType="action")
            
            # Weapon damage
            damage_data = definition.get("damage")
            if damage_data:
                action.damage = ActionDamage()
                action.damage.diceNotation = damage_data.get("diceString")
                
                damage_type = definition.get("damageType")
                if damage_type:
                    action.damage.damageType = damage_type.lower()
            
            # Weapon range
            weapon_range = definition.get("range")
            long_range = definition.get("longRange") 
            if weapon_range or long_range:
                action.actionRange = ActionRange()
                action.actionRange.range = weapon_range
                action.actionRange.longRange = long_range
                
                if weapon_range:
                    desc = f"{weapon_range} feet"
                    if long_range:
                        desc += f" (long: {long_range} feet)"
                    action.actionRange.rangeDescription = desc
            
            # Check for ammunition requirement
            properties = definition.get("properties", [])
            for prop in properties:
                if prop.get("name", "").lower() in ["ammunition", "thrown"]:
                    action.requiresAmmo = True
                    break
            
            actions.append(action)
        
        return actions
    
    async def _extract_spell_actions_from_text(self, text: str, item_name: str, spell_names: List[str] = None) -> List[CharacterAction]:
        """
        Use LLM to extract spell actions from item description text.
        
        Args:
            text: The item description containing spell information
            item_name: The name of the item granting the spells
            spell_names: Optional list of known spell names to look for
        
        Returns:
            List of CharacterAction objects for each spell found
        """
        llm_client = LLMClientFactory.create_router_client()
        
        # Build prompt for LLM
        spell_hint = ""
        if spell_names:
            spell_hint = f"\nKnown spell names to look for: {', '.join(spell_names)}"
        
        prompt = f"""Extract spell casting information from this D&D item description.

Item: {item_name}
Description: {text}{spell_hint}

Return a JSON array of spell actions. For each spell found, include:
- spell_name: The name of the spell
- save_dc: The DC for saving throws (if mentioned)
- activation_type: "action", "bonus_action", or "reaction"
- uses_per_rest: How many times it can be cast (e.g., "once per dawn", "3 charges", "unlimited")
- reset_type: "dawn", "dusk", "short_rest", "long_rest", or null

Return ONLY a JSON object with a "spells" array. If no spells are found, return {{"spells": []}}.

Example output:
{{
  "spells": [
    {{
      "spell_name": "call lightning",
      "save_dc": 18,
      "activation_type": "action",
      "uses_per_rest": "once",
      "reset_type": "dawn"
    }}
  ]
}}"""
        
        try:
            response = await llm_client.generate_json_response(prompt, max_tokens=800)
            
            # Repair and validate response
            repair_result = JSONRepair.repair_json_string(json.dumps(response))
            data = repair_result.data
            
            if "spells" not in data or not isinstance(data["spells"], list):
                return []
            
            actions = []
            for spell_info in data["spells"]:
                if not isinstance(spell_info, dict) or "spell_name" not in spell_info:
                    continue
                
                action = CharacterAction(
                    name=spell_info["spell_name"],
                    description=f"Cast from {item_name}",
                    source="item",
                    sourceFeature=item_name,
                    actionCategory="spell"
                )
                
                # Parse activation
                activation_type = spell_info.get("activation_type", "action")
                action.activation = ActionActivation(activationType=activation_type)
                
                # Parse usage limitations
                uses_per_rest = spell_info.get("uses_per_rest")
                reset_type = spell_info.get("reset_type")
                
                if uses_per_rest or reset_type:
                    usage = ActionUsage()
                    
                    # Extract max uses from text like "once" or "3 charges"
                    if uses_per_rest:
                        if "once" in str(uses_per_rest).lower():
                            usage.maxUses = 1
                        else:
                            # Try to extract number
                            match = re.search(r'(\d+)', str(uses_per_rest))
                            if match:
                                usage.maxUses = int(match.group(1))
                    
                    if reset_type:
                        usage.resetType = reset_type
                    
                    action.usage = usage
                
                # Parse save DC
                save_dc = spell_info.get("save_dc")
                if save_dc:
                    action.save = ActionSave(saveDC=save_dc)
                
                actions.append(action)
            
            return actions
            
        except Exception as e:
            print(f"Warning: Failed to extract spell actions from {item_name}: {e}")
            return []
    
    def parse_unequipped_weapon_actions(self) -> List[CharacterAction]:
        """Parse unequipped weapon attacks from inventory (requires drawing first)."""
        actions = []
        
        inventory = self.data.get("inventory", [])
        
        for item_data in inventory:
            definition = item_data.get("definition", {})
            
            # Only include unequipped weapons
            if not definition.get("attackType") or item_data.get("equipped"):
                continue
            
            action = CharacterAction(
                name=f"{definition.get('name', 'Unknown Weapon')} Attack (Unequipped)",
                description=self.clean_html_description(definition.get("description")),
                shortDescription=f"Requires drawing {definition.get('name', 'weapon')} first (free object interaction or action).",
                source="item",
                sourceFeature=definition.get("name"),
                actionCategory="unequipped_weapon",
                isWeaponAttack=True
            )
            
            # Weapon activation (usually action, but requires drawing)
            action.activation = ActionActivation(activationType="action")
            
            # Weapon damage
            damage_data = definition.get("damage")
            if damage_data:
                action.damage = ActionDamage()
                action.damage.diceNotation = damage_data.get("diceString")
                
                damage_type = definition.get("damageType")
                if damage_type:
                    action.damage.damageType = damage_type.lower()
            
            # Weapon range
            weapon_range = definition.get("range")
            long_range = definition.get("longRange") 
            if weapon_range or long_range:
                action.actionRange = ActionRange()
                action.actionRange.range = weapon_range
                action.actionRange.longRange = long_range
                
                if weapon_range:
                    desc = f"{weapon_range} feet"
                    if long_range:
                        desc += f" (long: {long_range} feet)"
                    action.actionRange.rangeDescription = desc
            
            # Check for ammunition requirement
            properties = definition.get("properties", [])
            for prop in properties:
                if prop.get("name", "").lower() in ["ammunition", "thrown"]:
                    action.requiresAmmo = True
                    break
            
            actions.append(action)
        
        return actions
    
    def parse_item_spell_actions(self) -> List[CharacterAction]:
        """
        Parse spell actions granted by magic items.
        Uses LLM to extract spell information from item descriptions.
        """
        actions = []
        inventory = self.data.get("inventory", [])
        
        # Run async extraction in event loop
        async def extract_all_item_spells():
            all_actions = []
            for item_data in inventory:
                definition = item_data.get("definition", {})
                description = definition.get("description", "")
                item_name = definition.get("name", "Unknown Item")
                
                # Skip if no description or item not equipped
                if not description or not item_data.get("equipped"):
                    continue
                
                # Look for spell-related keywords in description
                lower_desc = description.lower()
                if any(keyword in lower_desc for keyword in ["spell", "cast", "spells."]):
                    # Extract spell actions using LLM
                    item_actions = await self._extract_spell_actions_from_text(
                        self.clean_html_description(description),
                        item_name
                    )
                    all_actions.extend(item_actions)
            
            return all_actions
        
        try:
            actions = asyncio.run(extract_all_item_spells())
        except Exception as e:
            print(f"Warning: Failed to parse item spell actions: {e}")
        
        return actions
    
    def parse_spell_section_actions(self) -> List[CharacterAction]:
        """
        Parse spell actions from the spells.item section.
        These are spells granted by items and already have structured data.
        """
        actions = []
        spells_data = self.data.get("spells", {})
        item_spells = spells_data.get("item", [])
        
        if not item_spells:
            return actions
        
        # Build a mapping of item definition IDs to item names
        item_id_to_name = {}
        inventory = self.data.get("inventory", [])
        for item in inventory:
            item_def_id = item.get("definition", {}).get("id")
            item_name = item.get("definition", {}).get("name")
            if item_def_id and item_name:
                item_id_to_name[item_def_id] = item_name
        
        for spell_data in item_spells:
            try:
                definition = spell_data.get("definition", {})
                spell_name = definition.get("name", "Unknown Spell")
                
                # Get the source item name from the componentId
                component_id = spell_data.get("componentId")
                source_item_name = item_id_to_name.get(component_id, "Unknown Item")
                
                action = CharacterAction(
                    name=spell_name,
                    description=self.clean_html_description(definition.get("description", "")),
                    source="item",
                    actionCategory="spell",
                    sourceFeature=source_item_name
                )
                
                # Parse activation from spell data
                activation_data = definition.get("activation", {})
                activation_type = activation_data.get("activationType", 1)
                if activation_type in self.ACTION_TYPE_MAP:
                    action.activation = ActionActivation(
                        activationType=self.ACTION_TYPE_MAP[activation_type]
                    )
                
                # Parse spell level and school
                level = definition.get("level", 0)
                school = definition.get("school", "")
                if level or school:
                    level_text = "cantrip" if level == 0 else f"level {level}"
                    action.shortDescription = f"{level_text} {school} spell".strip()
                
                # Parse range
                action.actionRange = self.parse_range(definition.get("range", {}))
                
                # Parse duration
                duration_data = definition.get("duration", {})
                if duration_data:
                    duration_unit = duration_data.get("durationUnit", "")
                    duration_interval = duration_data.get("durationInterval", 1)
                    if duration_unit:
                        action.duration = f"{duration_interval} {duration_unit}"
                    
                    # Check for concentration
                    if definition.get("concentration"):
                        action.duration = f"Concentration, {action.duration}" if action.duration else "Concentration"
                
                # Parse components/materials
                components = definition.get("components", [])
                components_desc = definition.get("componentsDescription", "")
                if 3 in components and components_desc:  # 3 = material components
                    action.materials = self.clean_html_description(components_desc)
                
                # Parse charges (usage limitations)
                charges = spell_data.get("charges")
                if charges:
                    action.usage = ActionUsage(maxUses=charges)
                
                actions.append(action)
                
            except Exception as e:
                spell_name = "Unknown"
                try:
                    spell_name = spell_data.get("definition", {}).get("name", "Unknown")
                except:
                    pass
                print(f"Warning: Failed to parse item spell '{spell_name}': {e}")
                continue
        
        return actions
    
    def parse_all_actions(self) -> List[CharacterAction]:
        """Parse all non-spell character actions."""
        all_actions = []
        
        # Parse different action sources
        all_actions.extend(self.parse_basic_actions())
        all_actions.extend(self.parse_weapon_actions())
        all_actions.extend(self.parse_unequipped_weapon_actions())
        
        # Parse item-granted spells (uses LLM to extract from descriptions)
        all_actions.extend(self.parse_item_spell_actions())
        
        # Parse item spells from structured spell data
        all_actions.extend(self.parse_spell_section_actions())
        
        # Remove duplicates (case-insensitive name matching) and sort by name
        unique_actions = {}
        for action in all_actions:
            # Use lowercase name for deduplication to catch case variations
            key = (action.name.lower(), action.source, action.actionCategory)
            if key not in unique_actions:
                unique_actions[key] = action
            else:
                # Keep the one with more complete information (prefer structured over LLM-extracted)
                existing = unique_actions[key]
                # If the new one has usage info and the existing doesn't, replace it
                if action.usage and not existing.usage:
                    unique_actions[key] = action
                # If the new one has longer description, prefer it
                elif action.description and len(action.description or "") > len(existing.description or ""):
                    unique_actions[key] = action
        
        return sorted(unique_actions.values(), key=lambda x: x.name.lower())
    
    def print_actions_summary(self, actions: List[CharacterAction]):
        """Print a summary of all character actions."""
        print("\\n" + "="*60)
        print("CHARACTER ACTIONS SUMMARY")
        print("="*60)
        
        # Group by category
        by_category = {}
        for action in actions:
            category = action.actionCategory or "other"
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(action)
        
        # Ensure consistent ordering
        category_order = ["attack", "feature", "spell", "unequipped_weapon", "other"]
        ordered_categories = []
        for cat in category_order:
            if cat in by_category:
                ordered_categories.append((cat, by_category[cat]))
        for cat, actions_list in by_category.items():
            if cat not in category_order:
                ordered_categories.append((cat, actions_list))
        
        by_category = dict(ordered_categories)
        
        for category, category_actions in by_category.items():
            category_name = category.upper().replace("_", " ")
            print(f"\\n{category_name} ACTIONS ({len(category_actions)}):")
            print("-" * 40)
            
            for action in category_actions:
                # Build action summary line
                parts = [f"• {action.name}"]
                
                if action.activation and action.activation.activationType:
                    parts.append(f"[{action.activation.activationType}]")
                
                if action.usage and action.usage.maxUses:
                    reset = f" per {action.usage.resetType}" if action.usage.resetType else ""
                    parts.append(f"({action.usage.maxUses} uses{reset})")
                
                if action.damage and (action.damage.diceNotation or action.damage.fixedDamage):
                    damage_str = action.damage.diceNotation or str(action.damage.fixedDamage)
                    if action.damage.damageType:
                        damage_str += f" {action.damage.damageType}"
                    parts.append(f"[{damage_str}]")
                
                if action.actionRange and action.actionRange.rangeDescription:
                    parts.append(f"({action.actionRange.rangeDescription})")
                
                print("  " + " ".join(parts))
