"""
Dataset Generation Script for 574 Assignment

Generates synthetic training data for the joint classification model.
Outputs train.json, val.json, test.json to 574-assignment/data/generated/

Features:
- K-expansion: Each template generates K samples with different entity fills
- Augmentation: Typos, case variations, contractions applied to queries
- Placeholder preservation: {CHARACTER}, {PARTY_MEMBER}, {NPC} remain as literal tokens
- NO NER: Entity extraction handled by gazetteer at inference time

Run from project root:
    cd 574-assignment
    uv run python -m scripts.generate_dataset

Output structure:
{
    "text": "What level is {CHARACTER}?",
    "tool": "character_data",
    "intent": "character_basics"
}
"""

import json
import random
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Set

# Import templates and gazetteers
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATASET_CONFIG

# Import augmentation module
from data.augmentation import augment_query, AugmentationConfig

from data.templates.entity_gazetteers import (
    SPELL_NAMES, CLASS_NAMES, RACE_NAMES, CREATURE_NAMES, WEAPON_NAMES,
    ARMOR_NAMES, EQUIPMENT_NAMES, MAGIC_ITEM_NAMES, SKILL_NAMES,
    CONDITION_NAMES, DAMAGE_TYPES, LOCATION_NAMES, CLASS_FEATURE_NAMES,
    ABILITY_NAMES_EXTENDED, FEAT_NAMES, BACKGROUND_NAMES, SUBCLASS_NAMES,
    MECHANIC_NAMES, CREATURE_ABILITY_NAMES, WEAPON_PROPERTIES, LANGUAGE_NAMES,
    LEVEL_NAMES, SPELL_LEVEL_NAMES
)
from data.templates.character_templates import (
    CHARACTER_BASICS_TEMPLATES, COMBAT_INFO_TEMPLATES, ABILITIES_INFO_TEMPLATES,
    INVENTORY_INFO_TEMPLATES, MAGIC_INFO_TEMPLATES, STORY_INFO_TEMPLATES,
    SOCIAL_INFO_TEMPLATES, PROGRESS_INFO_TEMPLATES, FULL_CHARACTER_TEMPLATES,
    CHARACTER_SUMMARY_TEMPLATES
)
from data.templates.session_templates import (
    CHARACTER_STATUS_TEMPLATES, EVENT_SEQUENCE_TEMPLATES, NPC_INFO_TEMPLATES,
    LOCATION_DETAILS_TEMPLATES, ITEM_TRACKING_TEMPLATES, COMBAT_RECAP_TEMPLATES,
    SPELL_ABILITY_USAGE_TEMPLATES, CHARACTER_DECISIONS_TEMPLATES, PARTY_DYNAMICS_TEMPLATES,
    QUEST_TRACKING_TEMPLATES, PUZZLE_SOLUTIONS_TEMPLATES, LOOT_REWARDS_TEMPLATES,
    DEATH_REVIVAL_TEMPLATES, DIVINE_RELIGIOUS_TEMPLATES, MEMORY_VISION_TEMPLATES,
    RULES_MECHANICS_TEMPLATES, HUMOR_MOMENTS_TEMPLATES, UNRESOLVED_MYSTERIES_TEMPLATES,
    FUTURE_IMPLICATIONS_TEMPLATES, CROSS_SESSION_TEMPLATES
)
from data.templates.rulebook_templates import (
    DESCRIBE_ENTITY_TEMPLATES, COMPARE_ENTITIES_TEMPLATES, LEVEL_PROGRESSION_TEMPLATES,
    ACTION_OPTIONS_TEMPLATES, RULE_MECHANICS_TEMPLATES, CALCULATE_VALUES_TEMPLATES,
    SPELL_DETAILS_TEMPLATES, CLASS_SPELL_ACCESS_TEMPLATES, MONSTER_STATS_TEMPLATES,
    CONDITION_EFFECTS_TEMPLATES, CHARACTER_CREATION_TEMPLATES, MULTICLASS_RULES_TEMPLATES,
    EQUIPMENT_PROPERTIES_TEMPLATES, DAMAGE_TYPES_TEMPLATES, REST_MECHANICS_TEMPLATES,
    SKILL_USAGE_TEMPLATES, FIND_BY_CRITERIA_TEMPLATES, PREREQUISITE_CHECK_TEMPLATES,
    INTERACTION_RULES_TEMPLATES, TACTICAL_USAGE_TEMPLATES, ENVIRONMENTAL_RULES_TEMPLATES,
    CREATURE_ABILITIES_TEMPLATES, SAVING_THROWS_TEMPLATES, MAGIC_ITEM_USAGE_TEMPLATES,
    PLANAR_PROPERTIES_TEMPLATES, DOWNTIME_ACTIVITIES_TEMPLATES, SUBCLASS_FEATURES_TEMPLATES,
    COST_LOOKUP_TEMPLATES, LEGENDARY_MECHANICS_TEMPLATES, OPTIMIZATION_ADVICE_TEMPLATES
)
from data.templates.multi_tool_templates import (
    CHARACTER_RULEBOOK_TEMPLATES, CHARACTER_SESSION_TEMPLATES, SESSION_RULEBOOK_TEMPLATES,
    THREE_TOOL_TEMPLATES
)

# =============================================================================
# Configuration (loaded from config.py)
# =============================================================================

RANDOM_SEED = DATASET_CONFIG.get('random_seed', 42)
EXPANSIONS_PER_TEMPLATE = DATASET_CONFIG.get('expansions_per_template', 10)
AUGMENTATIONS_PER_SAMPLE = DATASET_CONFIG.get('augmentations_per_sample', 3)
DEDUPLICATE = DATASET_CONFIG.get('deduplicate', True)

TRAIN_RATIO = DATASET_CONFIG.get('train_split', 0.8)
VAL_RATIO = DATASET_CONFIG.get('val_split', 0.1)
TEST_RATIO = DATASET_CONFIG.get('test_split', 0.1)

# =============================================================================
# Placeholder tokens that are preserved as literal text (NOT filled from gazetteer)
# =============================================================================

PRESERVED_PLACEHOLDERS = {"{CHARACTER}", "{PARTY_MEMBER}", "{NPC}"}

# =============================================================================
# Entity Gazetteers Mapping (for D&D entity slots only)
# =============================================================================

ENTITY_GAZETTEERS = {
    # Core entity types
    "spell": SPELL_NAMES,
    "spell1": SPELL_NAMES,
    "spell2": SPELL_NAMES,
    "class": CLASS_NAMES,
    "class1": CLASS_NAMES,
    "class2": CLASS_NAMES,
    "class_name": CLASS_NAMES,
    "race": RACE_NAMES,
    "race1": RACE_NAMES,
    "race2": RACE_NAMES,
    "creature": CREATURE_NAMES,
    "creature1": CREATURE_NAMES,
    "creature2": CREATURE_NAMES,
    "monster": CREATURE_NAMES,
    
    # Items
    "weapon": WEAPON_NAMES if WEAPON_NAMES else EQUIPMENT_NAMES[:50],
    "weapon1": WEAPON_NAMES if WEAPON_NAMES else EQUIPMENT_NAMES[:50],
    "weapon2": WEAPON_NAMES if WEAPON_NAMES else EQUIPMENT_NAMES[:50],
    "armor": ARMOR_NAMES if ARMOR_NAMES else EQUIPMENT_NAMES[:20],
    "armor1": ARMOR_NAMES if ARMOR_NAMES else EQUIPMENT_NAMES[:20],
    "armor2": ARMOR_NAMES if ARMOR_NAMES else EQUIPMENT_NAMES[:20],
    "item": EQUIPMENT_NAMES + MAGIC_ITEM_NAMES,
    "item1": EQUIPMENT_NAMES + MAGIC_ITEM_NAMES,
    "item2": EQUIPMENT_NAMES + MAGIC_ITEM_NAMES,
    "magic_item": MAGIC_ITEM_NAMES,
    "equipment": EQUIPMENT_NAMES,
    
    # Character building
    "ability": ABILITY_NAMES_EXTENDED,
    "ability1": ABILITY_NAMES_EXTENDED,
    "ability2": ABILITY_NAMES_EXTENDED,
    "skill": SKILL_NAMES,
    "skill1": SKILL_NAMES,
    "skill2": SKILL_NAMES,
    "condition": CONDITION_NAMES,
    "condition1": CONDITION_NAMES,
    "condition2": CONDITION_NAMES,
    "damage_type": DAMAGE_TYPES,
    "damage_type1": DAMAGE_TYPES,
    "damage_type2": DAMAGE_TYPES,
    "feat": FEAT_NAMES,
    "feat2": FEAT_NAMES,
    "background": BACKGROUND_NAMES,
    "location": LOCATION_NAMES,
    "feature": CLASS_FEATURE_NAMES,
    "feature1": CLASS_FEATURE_NAMES,
    "feature2": CLASS_FEATURE_NAMES,
    "subclass": SUBCLASS_NAMES,
    "subclass1": SUBCLASS_NAMES,
    "subclass2": SUBCLASS_NAMES,
    
    # Misc
    "level": LEVEL_NAMES,
    "spell_level": SPELL_LEVEL_NAMES,
    "plane": LOCATION_NAMES[:20],
    "plane1": LOCATION_NAMES[:20],
    "plane2": LOCATION_NAMES[:20],
    "mechanic": MECHANIC_NAMES,
    "creature_ability": CREATURE_ABILITY_NAMES,
    "weapon_property": WEAPON_PROPERTIES,
    "property": WEAPON_PROPERTIES,
    "language": LANGUAGE_NAMES,
}

# =============================================================================
# Single-Tool Template Mappings
# =============================================================================

CHARACTER_TEMPLATES = {
    "character_basics": CHARACTER_BASICS_TEMPLATES,
    "combat_info": COMBAT_INFO_TEMPLATES,
    "abilities_info": ABILITIES_INFO_TEMPLATES,
    "inventory_info": INVENTORY_INFO_TEMPLATES,
    "magic_info": MAGIC_INFO_TEMPLATES,
    "story_info": STORY_INFO_TEMPLATES,
    "social_info": SOCIAL_INFO_TEMPLATES,
    "progress_info": PROGRESS_INFO_TEMPLATES,
    "full_character": FULL_CHARACTER_TEMPLATES,
    "character_summary": CHARACTER_SUMMARY_TEMPLATES,
}

SESSION_TEMPLATES = {
    "character_status": CHARACTER_STATUS_TEMPLATES,
    "event_sequence": EVENT_SEQUENCE_TEMPLATES,
    "npc_info": NPC_INFO_TEMPLATES,
    "location_details": LOCATION_DETAILS_TEMPLATES,
    "item_tracking": ITEM_TRACKING_TEMPLATES,
    "combat_recap": COMBAT_RECAP_TEMPLATES,
    "spell_ability_usage": SPELL_ABILITY_USAGE_TEMPLATES,
    "character_decisions": CHARACTER_DECISIONS_TEMPLATES,
    "party_dynamics": PARTY_DYNAMICS_TEMPLATES,
    "quest_tracking": QUEST_TRACKING_TEMPLATES,
    "puzzle_solutions": PUZZLE_SOLUTIONS_TEMPLATES,
    "loot_rewards": LOOT_REWARDS_TEMPLATES,
    "death_revival": DEATH_REVIVAL_TEMPLATES,
    "divine_religious": DIVINE_RELIGIOUS_TEMPLATES,
    "memory_vision": MEMORY_VISION_TEMPLATES,
    "rules_mechanics": RULES_MECHANICS_TEMPLATES,
    "humor_moments": HUMOR_MOMENTS_TEMPLATES,
    "unresolved_mysteries": UNRESOLVED_MYSTERIES_TEMPLATES,
    "future_implications": FUTURE_IMPLICATIONS_TEMPLATES,
    "cross_session": CROSS_SESSION_TEMPLATES,
}

RULEBOOK_TEMPLATES = {
    "describe_entity": DESCRIBE_ENTITY_TEMPLATES,
    "compare_entities": COMPARE_ENTITIES_TEMPLATES,
    "level_progression": LEVEL_PROGRESSION_TEMPLATES,
    "action_options": ACTION_OPTIONS_TEMPLATES,
    "rule_mechanics": RULE_MECHANICS_TEMPLATES,
    "calculate_values": CALCULATE_VALUES_TEMPLATES,
    "spell_details": SPELL_DETAILS_TEMPLATES,
    "class_spell_access": CLASS_SPELL_ACCESS_TEMPLATES,
    "monster_stats": MONSTER_STATS_TEMPLATES,
    "condition_effects": CONDITION_EFFECTS_TEMPLATES,
    "character_creation": CHARACTER_CREATION_TEMPLATES,
    "multiclass_rules": MULTICLASS_RULES_TEMPLATES,
    "equipment_properties": EQUIPMENT_PROPERTIES_TEMPLATES,
    "damage_types": DAMAGE_TYPES_TEMPLATES,
    "rest_mechanics": REST_MECHANICS_TEMPLATES,
    "skill_usage": SKILL_USAGE_TEMPLATES,
    "find_by_criteria": FIND_BY_CRITERIA_TEMPLATES,
    "prerequisite_check": PREREQUISITE_CHECK_TEMPLATES,
    "interaction_rules": INTERACTION_RULES_TEMPLATES,
    "tactical_usage": TACTICAL_USAGE_TEMPLATES,
    "environmental_rules": ENVIRONMENTAL_RULES_TEMPLATES,
    "creature_abilities": CREATURE_ABILITIES_TEMPLATES,
    "saving_throws": SAVING_THROWS_TEMPLATES,
    "magic_item_usage": MAGIC_ITEM_USAGE_TEMPLATES,
    "planar_properties": PLANAR_PROPERTIES_TEMPLATES,
    "downtime_activities": DOWNTIME_ACTIVITIES_TEMPLATES,
    "subclass_features": SUBCLASS_FEATURES_TEMPLATES,
    "cost_lookup": COST_LOOKUP_TEMPLATES,
    "legendary_mechanics": LEGENDARY_MECHANICS_TEMPLATES,
    "optimization_advice": OPTIMIZATION_ADVICE_TEMPLATES,
}

# =============================================================================
# Slot Filling Functions
# =============================================================================

def is_preserved_placeholder(slot_pattern: str) -> bool:
    """Check if a slot pattern is a preserved placeholder (not to be filled)."""
    return slot_pattern in PRESERVED_PLACEHOLDERS


def get_slot_value(slot_type: str) -> str:
    """Get a random value for a slot type."""
    # Handle numbered slots (e.g., spell1, spell2)
    base_type = re.sub(r'\d+$', '', slot_type)

    if base_type in ENTITY_GAZETTEERS:
        gazetteer = ENTITY_GAZETTEERS[base_type]
        if gazetteer:
            return random.choice(gazetteer)
    
    if slot_type == "class_name":
        return random.choice(ENTITY_GAZETTEERS["class"])
    
    # Unknown slot type - return placeholder
    print(f"Warning: Unknown slot type '{slot_type}'")
    return f"[{slot_type}]"


def fill_template(template: str, slots: Dict[str, str]) -> str:
    """
    Fill a template with random entity values.
    Preserved placeholders ({CHARACTER}, {PARTY_MEMBER}, {NPC}) remain as literal text.
    Returns the filled query string.
    """
    filled = template
    
    # First, find all placeholders in the template
    placeholder_pattern = r'\{([^}]+)\}'
    matches = list(re.finditer(placeholder_pattern, filled))
    
    # Process from end to start to maintain positions
    for match in reversed(matches):
        placeholder = match.group(0)  # e.g., "{CHARACTER}" or "{spell}"
        slot_name = match.group(1)    # e.g., "CHARACTER" or "spell"
        
        # Check if this is a preserved placeholder
        if placeholder in PRESERVED_PLACEHOLDERS:
            # Keep as-is - don't replace
            continue
        
        # Check if we have a slot type for this
        slot_type = slots.get(slot_name)
        if slot_type:
            value = get_slot_value(slot_type)
            filled = filled[:match.start()] + value + filled[match.end():]
        elif slot_name.lower() in ENTITY_GAZETTEERS:
            # Try lowercase version
            value = get_slot_value(slot_name.lower())
            filled = filled[:match.start()] + value + filled[match.end():]
        # If no slot type found, leave as-is (will be caught in validation)
    
    return filled


def expand_template_with_augmentation(
    template_data: Dict,
    tool: str = None,
    intent: str = None,
    k_expansions: int = 10,
    n_augmentations: int = 3
) -> List[Dict]:
    """
    Generate samples from a single template with entity fills and augmentations.
    
    For each template:
    1. Generate K variations with different entity fills
    2. For each variation, generate N augmented versions (typos, case changes)
    
    Total samples = K * (1 + N) per template (original + N augmentations)
    
    Args:
        template_data: Template dict with 'template', 'slots', optionally 'tools', 'intents'
        tool: For single-tool templates, the tool name
        intent: For single-tool templates, the intent name
        k_expansions: Number of entity-fill variations
        n_augmentations: Number of augmented versions per variation
        
    Returns:
        List of sample dictionaries with 'text', 'tool', 'intent'
    """
    samples = []
    seen_texts: Set[str] = set()
    
    # Determine tools and intents
    if tool and intent:
        tools = [tool]
        intents = {tool: intent}
    else:
        tools = template_data["tools"]
        intents = template_data["intents"]
    
    slots = template_data.get("slots", {})
    template_str = template_data["template"]
    
    # Check if template has fillable slots (excluding preserved placeholders)
    has_fillable_slots = bool(slots) or bool(
        set(re.findall(r'\{([^}]+)\}', template_str)) - 
        {p.strip('{}') for p in PRESERVED_PLACEHOLDERS}
    )
    
    # Determine expansion count
    actual_k = k_expansions if has_fillable_slots else 1
    
    # Configure augmentation
    aug_config = AugmentationConfig(
        typo_probability=0.15,
        case_variation_probability=0.30,
        contraction_probability=0.20,
        num_variants=1,  # We generate one variant at a time
        include_original=False,  # We handle original separately
    )
    
    attempts = 0
    max_attempts = actual_k * 5
    
    while len([s for s in samples if s.get("_is_original", False)]) < actual_k and attempts < max_attempts:
        attempts += 1
        
        # Generate base query with entity fills
        query = fill_template(template_str, slots)
        
        # Skip if duplicate
        if DEDUPLICATE and query.lower() in seen_texts:
            continue
        seen_texts.add(query.lower())
        
        # Add original (unaugmented) sample
        for t in tools:
            sample = {
                "text": query,
                "tool": t,
                "intent": intents[t],
                "_is_original": True,
            }
            samples.append(sample)
        
        # Generate augmented versions
        for _ in range(n_augmentations):
            augmented_list = augment_query(query, aug_config)
            
            # augment_query returns a list; get the variant if any
            if not augmented_list:
                continue
            augmented = augmented_list[0]
            
            # Skip if same as original or duplicate
            if augmented.lower() == query.lower():
                continue
            if DEDUPLICATE and augmented.lower() in seen_texts:
                continue
            seen_texts.add(augmented.lower())
            
            for t in tools:
                sample = {
                    "text": augmented,
                    "tool": t,
                    "intent": intents[t],
                    "_is_original": False,
                }
                samples.append(sample)
    
    # Remove internal tracking field
    for s in samples:
        s.pop("_is_original", None)
    
    return samples


def generate_dataset_with_expansion(seed: int = 42) -> List[Dict]:
    """
    Generate dataset using K-expansion per template with augmentation.
    
    Each template generates K samples with different entity substitutions,
    and each sample gets N augmented variations.
    """
    random.seed(seed)
    
    all_samples = []
    seen_texts: Set[str] = set()
    
    print(f"Generating dataset with K={EXPANSIONS_PER_TEMPLATE} expansions, "
          f"A={AUGMENTATIONS_PER_SAMPLE} augmentations per sample...")
    
    # Count templates
    template_counts = {"single": 0, "two": 0, "three": 0}
    
    # Generate from single-tool templates
    print("\n  Single-tool templates:")
    for tool_name, templates_dict in [
        ("character_data", CHARACTER_TEMPLATES),
        ("session_notes", SESSION_TEMPLATES),
        ("rulebook", RULEBOOK_TEMPLATES)
    ]:
        tool_samples = []
        for intent_name, template_list in templates_dict.items():
            for template_data in template_list:
                template_counts["single"] += 1
                samples = expand_template_with_augmentation(
                    template_data,
                    tool=tool_name,
                    intent=intent_name,
                    k_expansions=EXPANSIONS_PER_TEMPLATE,
                    n_augmentations=AUGMENTATIONS_PER_SAMPLE,
                )
                # Deduplicate across all samples
                for s in samples:
                    if not DEDUPLICATE or s["text"].lower() not in seen_texts:
                        seen_texts.add(s["text"].lower())
                        tool_samples.append(s)
        
        print(f"    {tool_name}: {len(tool_samples)} samples")
        all_samples.extend(tool_samples)
    
    single_total = len(all_samples)
    print(f"  → Total single-tool: {single_total} samples")
    
    # Generate from two-tool templates
    print("\n  Two-tool templates:")
    two_tool_samples = []
    for template_type_name, template_list in [
        ("character+rulebook", CHARACTER_RULEBOOK_TEMPLATES),
        ("character+session", CHARACTER_SESSION_TEMPLATES),
        ("session+rulebook", SESSION_RULEBOOK_TEMPLATES)
    ]:
        type_samples = []
        for template_data in template_list:
            template_counts["two"] += 1
            samples = expand_template_with_augmentation(
                template_data,
                k_expansions=EXPANSIONS_PER_TEMPLATE,
                n_augmentations=AUGMENTATIONS_PER_SAMPLE,
            )
            for s in samples:
                if not DEDUPLICATE or s["text"].lower() not in seen_texts:
                    seen_texts.add(s["text"].lower())
                    type_samples.append(s)
        print(f"    {template_type_name}: {len(type_samples)} samples")
        two_tool_samples.extend(type_samples)
    
    print(f"  → Total two-tool: {len(two_tool_samples)} samples")
    all_samples.extend(two_tool_samples)
    
    # Generate from three-tool templates
    print("\n  Three-tool templates:")
    three_tool_samples = []
    for template_data in THREE_TOOL_TEMPLATES:
        template_counts["three"] += 1
        samples = expand_template_with_augmentation(
            template_data,
            k_expansions=EXPANSIONS_PER_TEMPLATE,
            n_augmentations=AUGMENTATIONS_PER_SAMPLE,
        )
        for s in samples:
            if not DEDUPLICATE or s["text"].lower() not in seen_texts:
                seen_texts.add(s["text"].lower())
                three_tool_samples.append(s)
    
    print(f"    three-tool: {len(three_tool_samples)} samples")
    print(f"  → Total three-tool: {len(three_tool_samples)} samples")
    all_samples.extend(three_tool_samples)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Template counts:")
    print(f"  Single-tool: {template_counts['single']}")
    print(f"  Two-tool: {template_counts['two']}")
    print(f"  Three-tool: {template_counts['three']}")
    print(f"  TOTAL templates: {sum(template_counts.values())}")
    print(f"\nGenerated samples: {len(all_samples)}")
    print(f"{'='*60}")
    
    # Shuffle
    random.shuffle(all_samples)
    
    return all_samples


def split_dataset(samples: List[Dict], train_ratio: float, val_ratio: float) -> Tuple[List, List, List]:
    """Split dataset into train/val/test."""
    n = len(samples)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    return samples[:train_end], samples[train_end:val_end], samples[val_end:]


def analyze_dataset(samples: List[Dict], name: str) -> Dict[str, Any]:
    """Print dataset statistics and return them for label mapping."""
    print(f"\n{name} Statistics:")
    print(f"  Total samples: {len(samples)}")

    # Tool distribution
    tool_counts = defaultdict(int)
    intent_counts = defaultdict(lambda: defaultdict(int))
    
    # Track placeholder usage
    placeholder_counts = defaultdict(int)
    
    for s in samples:
        tool_counts[s["tool"]] += 1
        intent_counts[s["tool"]][s["intent"]] += 1
        
        # Count placeholders in text
        for placeholder in PRESERVED_PLACEHOLDERS:
            if placeholder in s["text"]:
                placeholder_counts[placeholder] += 1

    print(f"  Tools: {dict(tool_counts)}")
    
    # Print per-tool intent distribution
    print(f"  Intent distribution by tool:")
    for tool in ["character_data", "session_notes", "rulebook"]:
        if intent_counts[tool]:
            top_intents = sorted(intent_counts[tool].items(), key=lambda x: -x[1])[:3]
            print(f"    {tool}: {dict(top_intents)} ...")
    
    print(f"  Placeholder usage: {dict(placeholder_counts)}")
    
    return {
        "tool_counts": dict(tool_counts),
        "intent_counts": {k: dict(v) for k, v in intent_counts.items()},
        "placeholder_counts": dict(placeholder_counts),
    }


def build_label_mappings(train_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Build label mappings for tool and intent classification."""
    
    # Tool mappings
    tool_to_idx = {"character_data": 0, "session_notes": 1, "rulebook": 2}
    idx_to_tool = {v: k for k, v in tool_to_idx.items()}
    
    # Per-tool intent mappings
    character_intents = list(CHARACTER_TEMPLATES.keys())
    session_intents = list(SESSION_TEMPLATES.keys())
    rulebook_intents = list(RULEBOOK_TEMPLATES.keys())
    
    intent_to_idx_per_tool = {
        "character_data": {intent: i for i, intent in enumerate(character_intents)},
        "session_notes": {intent: i for i, intent in enumerate(session_intents)},
        "rulebook": {intent: i for i, intent in enumerate(rulebook_intents)},
    }
    
    idx_to_intent_per_tool = {
        "character_data": {i: intent for i, intent in enumerate(character_intents)},
        "session_notes": {i: intent for i, intent in enumerate(session_intents)},
        "rulebook": {i: intent for i, intent in enumerate(rulebook_intents)},
    }
    
    # Global intent mapping (for backward compatibility)
    all_intents = []
    intent_to_tool = {}
    for intent in character_intents:
        all_intents.append(intent)
        intent_to_tool[intent] = "character_data"
    for intent in session_intents:
        all_intents.append(intent)
        intent_to_tool[intent] = "session_notes"
    for intent in rulebook_intents:
        all_intents.append(intent)
        intent_to_tool[intent] = "rulebook"
    
    global_intent_to_idx = {intent: i for i, intent in enumerate(all_intents)}
    
    # Calculate class weights for imbalanced intents
    intent_weights = calculate_intent_weights(train_stats["intent_counts"])
    
    return {
        # Core mappings
        "tool_to_idx": tool_to_idx,
        "idx_to_tool": idx_to_tool,
        
        # Per-tool intent mappings
        "intent_to_idx_per_tool": intent_to_idx_per_tool,
        "idx_to_intent_per_tool": idx_to_intent_per_tool,
        
        # Intent counts per tool
        "num_intents_per_tool": {
            "character_data": len(character_intents),
            "session_notes": len(session_intents),
            "rulebook": len(rulebook_intents),
        },
        
        # Global mappings (backward compatible)
        "intent_to_idx": global_intent_to_idx,
        "intent_to_tool": intent_to_tool,
        
        # Class weights for handling imbalance
        "intent_weights_per_tool": intent_weights,
        
        # Preserved placeholders for name normalization at inference
        "preserved_placeholders": list(PRESERVED_PLACEHOLDERS),
        
        # Metadata
        "num_tools": len(tool_to_idx),
        "total_intents": len(all_intents),
    }


def calculate_intent_weights(intent_counts: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, float]]:
    """Calculate class weights for imbalanced intents using inverse frequency."""
    weights = {}
    
    for tool, counts in intent_counts.items():
        if not counts:
            continue
            
        total = sum(counts.values())
        num_classes = len(counts)
        
        # Inverse frequency weighting
        tool_weights = {}
        for intent, count in counts.items():
            weight = total / (num_classes * count) if count > 0 else 1.0
            tool_weights[intent] = round(weight, 4)
        
        weights[tool] = tool_weights
    
    return weights


def validate_dataset(samples: List[Dict], label_mappings: Dict) -> bool:
    """Validate that all samples have correct structure and valid labels."""
    errors = []
    
    valid_tools = set(label_mappings["tool_to_idx"].keys())
    
    for i, sample in enumerate(samples):
        # Check required fields
        if "text" not in sample:
            errors.append(f"Sample {i}: Missing 'text' field")
            continue
        if "tool" not in sample:
            errors.append(f"Sample {i}: Missing 'tool' field")
            continue
        if "intent" not in sample:
            errors.append(f"Sample {i}: Missing 'intent' field")
            continue
        
        # Check tool validity
        if sample["tool"] not in valid_tools:
            errors.append(f"Sample {i}: Invalid tool '{sample['tool']}'")
        
        # Check intent validity
        tool = sample["tool"]
        intent = sample["intent"]
        if intent not in label_mappings["intent_to_idx_per_tool"].get(tool, {}):
            errors.append(f"Sample {i}: Invalid intent '{intent}' for tool '{tool}'")
        
        # Check for unfilled placeholders (except preserved ones)
        unfilled = re.findall(r'\{([^}]+)\}', sample["text"])
        for slot in unfilled:
            placeholder = "{" + slot + "}"
            if placeholder not in PRESERVED_PLACEHOLDERS:
                errors.append(f"Sample {i}: Unfilled slot '{placeholder}' in '{sample['text'][:50]}...'")
    
    if errors:
        print(f"  Found {len(errors)} validation errors:")
        for error in errors[:10]:
            print(f"    - {error}")
        if len(errors) > 10:
            print(f"    ... and {len(errors) - 10} more")
        return False
    else:
        print("  ✓ All samples validated successfully")
        return True


def main():
    """Main entry point."""
    # Setup paths
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    output_dir = project_dir / "data" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Dataset Generation for 574 Assignment")
    print(f"K-expansion: {EXPANSIONS_PER_TEMPLATE} samples per template")
    print(f"Augmentations: {AUGMENTATIONS_PER_SAMPLE} per sample")
    print(f"Deduplication: {DEDUPLICATE}")
    print(f"Preserved placeholders: {PRESERVED_PLACEHOLDERS}")
    print("=" * 60)

    # Generate dataset
    samples = generate_dataset_with_expansion(RANDOM_SEED)

    # Split
    train, val, test = split_dataset(samples, TRAIN_RATIO, VAL_RATIO)

    # Analyze
    train_stats = analyze_dataset(train, "Train")
    val_stats = analyze_dataset(val, "Validation")
    test_stats = analyze_dataset(test, "Test")

    # Build label mappings
    label_mappings = build_label_mappings(train_stats)

    # Validate
    print("\nValidating dataset...")
    all_valid = validate_dataset(train + val + test, label_mappings)

    # Save datasets
    print("\nSaving datasets...")

    with open(output_dir / "train.json", "w") as f:
        json.dump(train, f, indent=2)
    print(f"  Saved {len(train)} samples to {output_dir / 'train.json'}")

    with open(output_dir / "val.json", "w") as f:
        json.dump(val, f, indent=2)
    print(f"  Saved {len(val)} samples to {output_dir / 'val.json'}")

    with open(output_dir / "test.json", "w") as f:
        json.dump(test, f, indent=2)
    print(f"  Saved {len(test)} samples to {output_dir / 'test.json'}")

    with open(output_dir / "label_mappings.json", "w") as f:
        json.dump(label_mappings, f, indent=2)
    print(f"  Saved label mappings to {output_dir / 'label_mappings.json'}")

    print("\n" + "=" * 60)
    print("Dataset generation complete!")
    print(f"Total samples: {len(samples)}")
    print(f"  Train: {len(train)} ({100*len(train)/len(samples):.1f}%)")
    print(f"  Val: {len(val)} ({100*len(val)/len(samples):.1f}%)")
    print(f"  Test: {len(test)} ({100*len(test)/len(samples):.1f}%)")
    print(f"Output directory: {output_dir}")
    print("=" * 60)

    if not all_valid:
        print("\n⚠️  WARNING: Some validation errors detected. Review output above.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
