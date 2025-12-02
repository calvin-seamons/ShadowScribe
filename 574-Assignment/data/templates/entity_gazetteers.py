"""
Entity Gazetteers for D&D 5e Query Classification

This module loads D&D 5e SRD entities from cached API data.
Run `scripts/fetch_srd_data.py` first to populate the cache.

Provides:
- Entity name lists (SPELL_NAMES, CREATURE_NAMES, etc.)
- SLOT_FILLERS: Maps template slot types to entity lists
- NER_ENTITY_MAPPING: Maps NER tag types to entity lists
- Helper functions for entity type lookup
"""

import json
from pathlib import Path


# =============================================================================
# LOAD CACHED SRD DATA
# =============================================================================

CACHE_DIR = Path(__file__).parent.parent / "srd_cache"


def _load_names(filename: str) -> list[str]:
    """Load entity names from a cached JSON file."""
    cache_file = CACHE_DIR / filename
    if not cache_file.exists():
        print(f"Warning: Cache file {filename} not found. Run fetch_srd_data.py first.")
        return []
    
    with open(cache_file) as f:
        data = json.load(f)
    
    if "results" in data:
        return [item["name"] for item in data["results"]]
    return []


# =============================================================================
# SPELLS - From D&D 5e SRD API (319 spells)
# =============================================================================

SPELL_NAMES = _load_names("spells.json")

# =============================================================================
# CREATURES/MONSTERS - From D&D 5e SRD API (334 monsters)
# =============================================================================

CREATURE_NAMES = _load_names("monsters.json")

# =============================================================================
# EQUIPMENT - From D&D 5e SRD API (237 items)
# =============================================================================

EQUIPMENT_NAMES = _load_names("equipment.json")

# =============================================================================
# MAGIC ITEMS - From D&D 5e SRD API (362 items)
# =============================================================================

MAGIC_ITEM_NAMES = _load_names("magic-items.json")

# =============================================================================
# CLASS FEATURES - From D&D 5e SRD API (407 features)
# =============================================================================

CLASS_FEATURE_NAMES = _load_names("features.json")

# =============================================================================
# CONDITIONS - From D&D 5e SRD API (15 conditions)
# =============================================================================

CONDITION_NAMES = _load_names("conditions.json")

# =============================================================================
# CLASSES - From D&D 5e SRD API (12 classes)
# =============================================================================

CLASS_NAMES = _load_names("classes.json")

# =============================================================================
# RACES - From D&D 5e SRD API (9 races)
# =============================================================================

RACE_NAMES = _load_names("races.json")

# =============================================================================
# SUBCLASSES - From D&D 5e SRD API (12 subclasses)
# =============================================================================

SUBCLASS_NAMES = _load_names("subclasses.json")

# =============================================================================
# TRAITS - From D&D 5e SRD API (38 traits)
# =============================================================================

TRAIT_NAMES = _load_names("traits.json")

# =============================================================================
# SKILLS - From D&D 5e SRD API (18 skills)
# =============================================================================

SKILL_NAMES = _load_names("skills.json")

# =============================================================================
# ABILITY SCORES - From D&D 5e SRD API (6 abilities)
# =============================================================================

ABILITY_NAMES = _load_names("ability-scores.json")

# Add common abbreviations
ABILITY_NAMES_EXTENDED = ABILITY_NAMES + ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

# =============================================================================
# DAMAGE TYPES - From D&D 5e SRD API (13 damage types)
# =============================================================================

DAMAGE_TYPES = _load_names("damage-types.json")

# =============================================================================
# WEAPON PROPERTIES - From D&D 5e SRD API (11 properties)
# =============================================================================

WEAPON_PROPERTIES = _load_names("weapon-properties.json")

# =============================================================================
# LANGUAGES - From D&D 5e SRD API (16 languages)
# =============================================================================

LANGUAGE_NAMES = _load_names("languages.json")

# =============================================================================
# BACKGROUNDS - From D&D 5e SRD API (limited in SRD)
# Supplemented with common backgrounds from core rules
# =============================================================================

_API_BACKGROUNDS = _load_names("backgrounds.json")
BACKGROUND_NAMES = _API_BACKGROUNDS if len(_API_BACKGROUNDS) > 5 else [
    "Acolyte", "Charlatan", "Criminal", "Entertainer", "Folk Hero",
    "Guild Artisan", "Hermit", "Noble", "Outlander", "Sage",
    "Sailor", "Soldier", "Urchin",
]

# =============================================================================
# DERIVED/COMBINED LISTS
# =============================================================================

# All items combined (weapons, armor, equipment, magic items)
ITEM_NAMES = EQUIPMENT_NAMES + MAGIC_ITEM_NAMES

# Weapon names (filtered from equipment)
WEAPON_NAMES = [
    name for name in EQUIPMENT_NAMES 
    if any(w in name.lower() for w in [
        "sword", "axe", "mace", "dagger", "bow", "crossbow", "spear", 
        "hammer", "club", "staff", "pike", "halberd", "glaive", "trident",
        "whip", "flail", "morningstar", "rapier", "scimitar", "sling",
        "javelin", "dart", "net", "lance", "maul", "sickle", "quarterstaff"
    ])
]

# Armor names (filtered from equipment)
ARMOR_NAMES = [
    name for name in EQUIPMENT_NAMES
    if any(a in name.lower() for a in [
        "armor", "mail", "plate", "shield", "leather", "hide", "padded",
        "breastplate", "half plate", "scale", "chain", "ring", "splint"
    ])
]

# =============================================================================
# SUPPLEMENTARY LISTS (Not in API or limited)
# =============================================================================

# Locations/Planes (not in SRD API - keep manual)
LOCATION_NAMES = [
    # Planes of Existence
    "Material Plane", "Feywild", "Shadowfell", "Ethereal Plane", "Astral Plane",
    "Elemental Plane of Air", "Elemental Plane of Earth", "Elemental Plane of Fire",
    "Elemental Plane of Water", "Elemental Chaos",
    # Outer Planes
    "Mount Celestia", "Bytopia", "Elysium", "The Beastlands", "Arborea",
    "Ysgard", "Limbo", "Pandemonium", "The Abyss", "Carceri", "Hades",
    "Gehenna", "Nine Hells", "Acheron", "Mechanus", "Arcadia", "Outlands", "Sigil",
    # Generic Fantasy Locations
    "Underdark", "Dungeon", "Cave", "Castle", "Tower", "Temple", "Shrine",
    "Tomb", "Crypt", "Forest", "Swamp", "Mountain", "Desert", "Tundra",
    "Ocean", "Island", "City", "Village", "Town", "Fortress", "Ruins",
    "Tavern", "Inn", "Guild Hall", "Arena", "Marketplace", "Harbor",
]

# Feats (limited in SRD - keep common ones)
FEAT_NAMES = [
    "Alert", "Athlete", "Actor", "Charger", "Crossbow Expert",
    "Defensive Duelist", "Dual Wielder", "Dungeon Delver", "Durable",
    "Elemental Adept", "Grappler", "Great Weapon Master", "Healer",
    "Heavily Armored", "Heavy Armor Master", "Inspiring Leader",
    "Keen Mind", "Lightly Armored", "Linguist", "Lucky", "Mage Slayer",
    "Magic Initiate", "Martial Adept", "Medium Armor Master", "Mobile",
    "Moderately Armored", "Mounted Combatant", "Observant", "Polearm Master",
    "Resilient", "Ritual Caster", "Savage Attacker", "Sentinel",
    "Sharpshooter", "Shield Master", "Skilled", "Skulker", "Spell Sniper",
    "Tavern Brawler", "Tough", "War Caster", "Weapon Master",
]

# Combat stats (conceptual, not API entities)
COMBAT_STAT_NAMES = [
    "AC", "Armor Class", "HP", "Hit Points", "Hit Dice",
    "Initiative", "Speed", "Walking Speed", "Flying Speed", "Swimming Speed",
    "Climbing Speed", "Proficiency Bonus", "Spell Save DC", "Spell Attack Bonus",
    "Attack Bonus", "Damage Bonus",
]

# Levels (for template slots)
LEVEL_NAMES = [str(i) for i in range(1, 21)]
SPELL_LEVEL_NAMES = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th"]

# Mechanics (for rulebook queries)
MECHANIC_NAMES = [
    "advantage", "disadvantage", "proficiency", "expertise",
    "concentration", "ritual", "reaction", "bonus action",
    "opportunity attack", "grappling", "shoving", "hiding",
    "cover", "flanking", "inspiration", "death saves",
    "short rest", "long rest",
]

# Creature abilities (for monster queries)
CREATURE_ABILITY_NAMES = [
    "Multiattack", "Legendary Actions", "Legendary Resistance",
    "Lair Actions", "Frightful Presence", "Breath Weapon",
    "Spellcasting", "Innate Spellcasting", "Magic Resistance",
    "Pack Tactics", "Sneak Attack", "Regeneration",
]

# =============================================================================
# SLOT MAPPINGS FOR TEMPLATE FILLING
# =============================================================================

SLOT_FILLERS = {
    # Core entity types
    "spell": SPELL_NAMES,
    "spell_name": SPELL_NAMES,
    "spell1": SPELL_NAMES,
    "spell2": SPELL_NAMES,
    "creature": CREATURE_NAMES,
    "monster": CREATURE_NAMES,
    "npc_type": CREATURE_NAMES,
    
    # Items
    "item": ITEM_NAMES,
    "item_name": ITEM_NAMES,
    "item1": ITEM_NAMES,
    "item2": ITEM_NAMES,
    "weapon": WEAPON_NAMES if WEAPON_NAMES else EQUIPMENT_NAMES[:50],
    "armor": ARMOR_NAMES if ARMOR_NAMES else EQUIPMENT_NAMES[:20],
    "magic_item": MAGIC_ITEM_NAMES,
    "equipment": EQUIPMENT_NAMES,
    
    # Character building
    "feature": CLASS_FEATURE_NAMES,
    "class_feature": CLASS_FEATURE_NAMES,
    "feature1": CLASS_FEATURE_NAMES,
    "feature2": CLASS_FEATURE_NAMES,
    "race": RACE_NAMES,
    "class": CLASS_NAMES,
    "class_name": CLASS_NAMES,
    "class1": CLASS_NAMES,
    "class2": CLASS_NAMES,
    "subclass": SUBCLASS_NAMES,
    "trait": TRAIT_NAMES,
    "background": BACKGROUND_NAMES,
    "feat": FEAT_NAMES,
    
    # Stats and mechanics
    "condition": CONDITION_NAMES,
    "skill": SKILL_NAMES,
    "skill1": SKILL_NAMES,
    "skill2": SKILL_NAMES,
    "ability": ABILITY_NAMES_EXTENDED,
    "ability1": ABILITY_NAMES_EXTENDED,
    "ability2": ABILITY_NAMES_EXTENDED,
    "stat": COMBAT_STAT_NAMES + ABILITY_NAMES_EXTENDED,
    "combat_stat": COMBAT_STAT_NAMES,
    "damage_type": DAMAGE_TYPES,
    "damage_type1": DAMAGE_TYPES,
    "damage_type2": DAMAGE_TYPES,
    
    # World building
    "location": LOCATION_NAMES,
    "plane": LOCATION_NAMES[:20],
    "language": LANGUAGE_NAMES,
    
    # Misc
    "level": LEVEL_NAMES,
    "spell_level": SPELL_LEVEL_NAMES,
    "mechanic": MECHANIC_NAMES,
    "creature_ability": CREATURE_ABILITY_NAMES,
    "weapon_property": WEAPON_PROPERTIES,
}

# =============================================================================
# NER ENTITY TYPE MAPPING
# =============================================================================

NER_ENTITY_MAPPING = {
    "SPELL": SPELL_NAMES,
    "ITEM": ITEM_NAMES,
    "CREATURE": CREATURE_NAMES,
    "LOCATION": LOCATION_NAMES,
    "FEATURE": CLASS_FEATURE_NAMES,
    "CLASS": CLASS_NAMES + SUBCLASS_NAMES,
    "RACE": RACE_NAMES,
    "CONDITION": CONDITION_NAMES,
    "SKILL": SKILL_NAMES,
    "ABILITY": ABILITY_NAMES_EXTENDED,
    "DAMAGE_TYPE": DAMAGE_TYPES,
    "FEAT": FEAT_NAMES,
    "BACKGROUND": BACKGROUND_NAMES,
}

# All entities combined for gazetteer lookup
ALL_ENTITIES = (
    SPELL_NAMES + CREATURE_NAMES + ITEM_NAMES + CLASS_FEATURE_NAMES +
    RACE_NAMES + CLASS_NAMES + SUBCLASS_NAMES + CONDITION_NAMES + 
    LOCATION_NAMES + SKILL_NAMES + FEAT_NAMES
)


def get_entity_type(entity_name: str) -> str | None:
    """
    Determine the entity type for a given entity name.
    Returns the NER tag (SPELL, ITEM, etc.) or None if not found.
    """
    entity_lower = entity_name.lower()

    for entity_type, entity_list in NER_ENTITY_MAPPING.items():
        if any(e.lower() == entity_lower for e in entity_list):
            return entity_type

    return None


def get_slot_values(slot_name: str) -> list[str]:
    """
    Get the list of possible values for a template slot.
    """
    return SLOT_FILLERS.get(slot_name, [])


# =============================================================================
# VALIDATION ON IMPORT
# =============================================================================

def _validate_cache():
    """Check if cache is populated."""
    if not CACHE_DIR.exists():
        print(f"⚠️  SRD cache not found at {CACHE_DIR}")
        print("   Run: uv run python -m scripts.fetch_srd_data")
        return False
    
    required = ["spells.json", "monsters.json", "equipment.json"]
    missing = [f for f in required if not (CACHE_DIR / f).exists()]
    
    if missing:
        print(f"⚠️  Missing cache files: {missing}")
        print("   Run: uv run python -m scripts.fetch_srd_data")
        return False
    
    return True


# Validate on import (warning only, don't fail)
if not _validate_cache():
    print("   Gazetteers may be empty or incomplete!")
else:
    # Print summary on first import
    _summary = {
        "Spells": len(SPELL_NAMES),
        "Monsters": len(CREATURE_NAMES),
        "Equipment": len(EQUIPMENT_NAMES),
        "Magic Items": len(MAGIC_ITEM_NAMES),
        "Features": len(CLASS_FEATURE_NAMES),
        "Classes": len(CLASS_NAMES),
        "Subclasses": len(SUBCLASS_NAMES),
        "Conditions": len(CONDITION_NAMES),
        "Skills": len(SKILL_NAMES),
    }
    _total = sum(_summary.values())
    # Uncomment for debug: print(f"✓ Loaded {_total} entities from SRD cache")
