"""
Tool Intentions - Single Source of Truth

This module provides the definitive list of valid tools and their intentions.
The source of truth is the trained classifier model's label_mappings.json.

All components that need to validate or display tool/intention combinations
should import from this module.

Usage:
    from src.rag.tool_intentions import (
        TOOL_INTENTIONS,
        get_intentions_for_tool,
        is_valid_intention,
        get_all_tools,
        get_fallback_intention
    )
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

# Path to the trained model's label mappings (source of truth)
_MODEL_MAPPINGS_PATH = Path(__file__).parent.parent.parent / "574-Assignment" / "models" / "joint_classifier" / "label_mappings.json"

# Fallback intentions used when entity-based routing adds tools
# These are used when no specific intention is determined by the classifier
FALLBACK_INTENTIONS: Dict[str, str] = {
    "character_data": "inventory_info",
    "session_notes": "general_history",
    "rulebook": "general_info"
}


def _load_intentions_from_model() -> Dict[str, List[str]]:
    """
    Load tool intentions from the trained classifier model.
    
    Returns:
        Dict mapping tool names to lists of valid intention strings.
    """
    try:
        with open(_MODEL_MAPPINGS_PATH) as f:
            mappings = json.load(f)
        
        # Extract intentions per tool from idx_to_intent_per_tool
        # The model uses 'character_data', 'session_notes', 'rulebook' as tool names
        tool_intentions = {}
        
        idx_to_intent = mappings.get('idx_to_intent_per_tool', {})
        
        for tool, intent_map in idx_to_intent.items():
            # intent_map is {"0": "intent_name", "1": "another_intent", ...}
            intentions = [intent_map[str(i)] for i in range(len(intent_map))]
            tool_intentions[tool] = intentions
        
        # Add fallback intentions if not already present
        for tool, fallback in FALLBACK_INTENTIONS.items():
            if tool in tool_intentions and fallback not in tool_intentions[tool]:
                tool_intentions[tool].append(fallback)
        
        return tool_intentions
    
    except FileNotFoundError:
        # Fallback if model not found - use hardcoded defaults
        print(f"[tool_intentions] Warning: Model mappings not found at {_MODEL_MAPPINGS_PATH}")
        print("[tool_intentions] Using hardcoded fallback intentions")
        return _get_fallback_intentions()
    except Exception as e:
        print(f"[tool_intentions] Error loading model mappings: {e}")
        return _get_fallback_intentions()


def _get_fallback_intentions() -> Dict[str, List[str]]:
    """
    Fallback intentions if model file is not available.
    These should match the model but are only used as a backup.
    """
    return {
        'character_data': [
            'character_basics',
            'combat_info',
            'abilities_info',
            'inventory_info',
            'magic_info',
            'story_info',
            'social_info',
            'progress_info',
            'full_character',
            'character_summary'
        ],
        'session_notes': [
            'character_status',
            'event_sequence',
            'npc_info',
            'location_details',
            'item_tracking',
            'combat_recap',
            'spell_ability_usage',
            'character_decisions',
            'party_dynamics',
            'quest_tracking',
            'puzzle_solutions',
            'loot_rewards',
            'death_revival',
            'divine_religious',
            'memory_vision',
            'rules_mechanics',
            'humor_moments',
            'unresolved_mysteries',
            'future_implications',
            'cross_session',
            'general_history'  # Fallback
        ],
        'rulebook': [
            'describe_entity',
            'compare_entities',
            'level_progression',
            'action_options',
            'rule_mechanics',
            'calculate_values',
            'spell_details',
            'class_spell_access',
            'monster_stats',
            'condition_effects',
            'character_creation',
            'multiclass_rules',
            'equipment_properties',
            'damage_types',
            'rest_mechanics',
            'skill_usage',
            'find_by_criteria',
            'prerequisite_check',
            'interaction_rules',
            'tactical_usage',
            'environmental_rules',
            'creature_abilities',
            'saving_throws',
            'magic_item_usage',
            'planar_properties',
            'downtime_activities',
            'subclass_features',
            'cost_lookup',
            'legendary_mechanics',
            'optimization_advice',
            'general_info'  # Fallback
        ]
    }


# Load intentions on module import
TOOL_INTENTIONS: Dict[str, List[str]] = _load_intentions_from_model()


def get_intentions_for_tool(tool: str) -> List[str]:
    """
    Get all valid intentions for a specific tool.
    
    Args:
        tool: Tool name ('character_data', 'session_notes', 'rulebook')
        
    Returns:
        List of valid intention strings for that tool, or empty list if tool unknown.
    """
    return TOOL_INTENTIONS.get(tool, [])


def is_valid_intention(tool: str, intention: str) -> bool:
    """
    Check if an intention is valid for a given tool.
    
    Args:
        tool: Tool name
        intention: Intention to validate
        
    Returns:
        True if the intention is valid for the tool.
    """
    return intention in TOOL_INTENTIONS.get(tool, [])


def get_all_tools() -> List[str]:
    """
    Get list of all valid tool names.
    
    Returns:
        List of tool names.
    """
    return list(TOOL_INTENTIONS.keys())


def get_fallback_intention(tool: str) -> str:
    """
    Get the fallback intention for a tool (used in entity-based routing).
    
    Args:
        tool: Tool name
        
    Returns:
        Default intention for the tool.
    """
    return FALLBACK_INTENTIONS.get(tool, "general_info")


def get_tool_intentions_dict() -> Dict[str, List[str]]:
    """
    Get the complete tool intentions dictionary.
    Useful for API responses and UI dropdowns.
    
    Returns:
        Dict mapping tool names to lists of valid intentions.
    """
    return TOOL_INTENTIONS.copy()
