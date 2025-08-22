# ShadowScribe Schema Optimization Proposals

## Overview

This document outlines simplified schema approaches to reduce the current 4-pass system complexity and improve LLM response efficiency.

## Current System Analysis

### Current 4-Pass Architecture
1. **Pass 1**: Source Selection (`sources_needed`, `reasoning`)
2. **Pass 2**: Content Targeting (separate schemas per source type)
3. **Pass 3**: Content Retrieval (Python handlers)
4. **Pass 4**: Response Generation

### Issues with Current Approach
- **Multiple LLM calls**: 4 sequential API requests increase latency
- **Complex schemas**: Large, verbose schema descriptions sent to LLM
- **Redundant validation**: Both Pydantic and direct JSON parsing
- **Schema duplication**: File lists and targeting logic repeated across files

---

## Simplified Schema Proposals

### Option 1: Single-Pass Unified Schema
**Goal**: Combine all targeting into one LLM call

```json
{
  "query_type": "character_rules_combo",
  "sources": {
    "character": {
      "files": ["character", "spells", "inventory"],
      "focus": ["combat_stats", "spell_list", "equipment"]
    },
    "rules": {
      "keywords": ["fireball", "spell_attack", "damage"],
      "sections": ["spellcasting", "combat"]
    },
    "sessions": {
      "scope": "recent",
      "keywords": ["covenant", "Ghul-Ghoth"]
    }
  },
  "reasoning": "Need character spell stats and fireball rules for combat calculation"
}
```

**Advantages**:
- Single LLM call reduces latency by ~75%
- Unified targeting logic
- Clear intent expression

**Disadvantages**:
- Larger response schema
- More complex validation

### Option 2: Smart Intent-Based Schema
**Goal**: Use query classification with predefined patterns

```json
{
  "intent": "spell_mechanics_query",
  "entity": "fireball",
  "context_needed": ["character_spells", "spell_rules", "recent_usage"],
  "confidence": 0.9
}
```

**Predefined Intent Patterns**:
- `character_info_query` → character files only
- `rules_lookup_query` → rulebook only  
- `combat_calculation_query` → character + rules
- `story_recap_query` → sessions + character context
- `spell_mechanics_query` → spells + rules
- `equipment_query` → inventory + rules (for magic items)

**Advantages**:
- Minimal LLM response size
- Fast classification
- Predictable data needs

**Disadvantages**:
- Requires good intent classification
- Less flexible for complex queries

### Option 3: Hybrid Smart Targeting
**Goal**: Use compact schema with smart defaults

```json
{
  "primary_source": "character",
  "supporting_sources": ["rules"],
  "targets": ["spells.fireball", "combat_stats", "rules.evocation"],
  "scope": "focused"
}
```

**Smart Defaults Logic**:
- `"character"` primary → auto-include basic character data
- `"rules"` support → only targeted sections
- `"sessions"` → latest 2-3 sessions unless specified
- `scope: "focused"` → minimal data, `"comprehensive"` → broader retrieval

**Advantages**:
- Very compact schema
- Intelligent defaults reduce targeting complexity
- Flexible for both simple and complex queries

---

## Recommended Implementation: Option 3 (Hybrid Smart Targeting)

### New Unified Schema Structure

```json
{
  "primary_source": "character" | "rules" | "sessions",
  "supporting_sources": ["rules", "sessions"],
  "targets": [
    "character.basic",
    "character.spells.fireball", 
    "rules.spellcasting.attack_rolls",
    "sessions.recent"
  ],
  "scope": "focused" | "comprehensive",
  "reasoning": "Brief explanation"
}
```

### Target Path Format
Use dot notation for precise targeting:

**Character Targets**:
- `character.basic` → name, level, class, race
- `character.combat` → HP, AC, stats, saves  
- `character.spells` → all spells
- `character.spells.{spell_name}` → specific spell
- `character.equipment` → all inventory
- `character.equipment.weapons` → weapons only
- `character.features` → class/racial features
- `character.background` → backstory, personality
- `character.objectives` → quests, contracts

**Rules Targets**:
- `rules.{keyword}` → keyword search
- `rules.spellcasting` → all spellcasting rules
- `rules.combat` → combat mechanics
- `rules.classes.{class_name}` → specific class rules

**Session Targets**:
- `sessions.recent` → last 2-3 sessions
- `sessions.latest` → most recent session only
- `sessions.{date}` → specific session
- `sessions.{keyword}` → keyword search across all

### Implementation Benefits

1. **Reduced Latency**: 1 LLM call instead of 4 (75% reduction)
2. **Simpler Codebase**: Single targeting logic path
3. **Better UX**: Faster responses
4. **Easier Maintenance**: One schema to maintain
5. **Smart Defaults**: Most queries need minimal targeting

### Migration Path

1. **Phase 1**: Implement new schema alongside existing (parallel)
2. **Phase 2**: Add smart default logic for common query patterns  
3. **Phase 3**: Switch default behavior to new schema
4. **Phase 4**: Remove old 4-pass system

---

# Knowledge Base Python Tools Reference

## Available Knowledge Handler Classes

### 1. KnowledgeBase (`src/knowledge/knowledge_base.py`)
**Main coordinator class for all knowledge sources**

#### Core Methods:
- `__init__(knowledge_base_path)` - Initialize all handlers
- `get_source_overview()` - Overview of all available sources
- `get_character_data(file_fields)` - Get character data by file/field mapping
- `get_rulebook_data(section_ids, keywords)` - Get D&D rules data
- `get_session_data(session_dates, keywords)` - Get session notes data

---

### 2. CharacterHandler (`src/knowledge/character_handler.py`)
**Manages all character data files and provides rich query interface**

#### Data Loading & Management:
- `load_data()` - Load character from detected folder
- `get_available_files()` - List available character files
- `get_character_name()` - Get current character name
- `get_current_character_folder()` - Get character folder path

#### Core Data Access:
- `get_file_data(filename, fields=None)` - Get specific file data with field filtering
- `get_basic_info()` - Name, level, class, race, alignment, HP, AC
- `get_combat_info()` - Combat stats, saves, initiative, proficiency
- `get_spells(spell_class=None)` - Spellcasting data for class or all classes
- `get_equipment(equipment_type=None)` - Equipment by type or all
- `get_abilities_and_features()` - Class features, racial traits, feats
- `get_background_info()` - Backstory, personality, bonds, flaws
- `get_objectives_and_contracts()` - All quests, goals, divine covenants

#### Specialized Queries:
- `get_spell_save_dc(spell_class)` - Calculate spell save DC for class
- `get_spell_attack_bonus(spell_class)` - Calculate spell attack bonus  
- `get_proficiency_bonus()` - Calculate proficiency bonus from level
- `get_active_objectives()` - Only active/current objectives
- `get_completed_objectives()` - Only completed objectives  
- `get_covenant_details()` - Divine covenant information

#### Available Character Files:
- `character.json` - Basic stats, level, class, race, abilities
- `inventory_list.json` - Weapons, armor, items, gold, equipment
- `feats_and_traits.json` - Class features, racial traits, feats
- `spell_list.json` - Known spells, spell slots, spellcasting abilities
- `action_list.json` - Combat actions, attacks, special abilities
- `character_background.json` - Backstory, personality, allies, enemies
- `objectives_and_contracts.json` - Quests, goals, divine covenants

#### Field Alias System:
The handler includes smart aliases for common field requests:
- `"level"` → `"character_base.total_level"`
- `"name"` → `"character_base.name"`
- `"class"` → `"character_base.class"`
- `"hp"` → `"combat_stats.max_hp"`
- `"ac"` → `"combat_stats.armor_class"`
- `"str"` → `"ability_scores.strength"`
- And many more...

---

### 3. RulebookHandler (`src/knowledge/rulebook_handler.py`)
**Manages D&D 5e SRD data with efficient search capabilities**

#### Data Loading:
- `load_data()` - Load full SRD and query helper
- `is_loaded()` - Check if data is available
- `get_query_helper()` - Get navigation structure for LLM
- `get_section_count()` - Total number of rule sections
- `get_main_categories()` - Top-level rule categories

#### Content Retrieval:
- `get_sections_by_ids(section_ids)` - Get specific rule sections by ID
- `search_by_keywords(keywords)` - Search rules by keywords
- `search_by_content(search_text)` - Full-text search through rules
- `get_section_by_path(path)` - Get section by hierarchical path
- `get_spells_by_class(character_class)` - Get all spells for a class

#### Data Sources:
- `dnd5e_srd_full.json` - Complete D&D 5e SRD content
- `dnd5e_srd_query_helper.json` - Optimized structure for navigation

---

### 4. SessionHandler (`src/knowledge/session_handler.py`)
**Manages campaign session notes and history**

#### Data Loading:
- `load_data()` - Load all session markdown files
- `is_loaded()` - Check if sessions are loaded
- `get_available_sessions()` - List all session dates
- `get_latest_session_date()` - Get most recent session date

#### Session Retrieval:
- `get_session_by_date(date)` - Get specific session by date
- `get_latest_session()` - Get most recent session
- `search_by_keywords(keywords)` - Search sessions by keywords
- `get_session_summaries()` - Get summaries of all sessions

#### Content Analysis:
- `get_npcs_mentioned()` - Extract NPCs mentioned per session
- `get_party_members_mentioned()` - Extract party members per session  
- `get_locations_visited()` - Extract locations per session

#### Data Source:
- `knowledge_base/session_notes/*.md` - Markdown session files

---

## Usage Patterns for New Schema

### Example: Spell Mechanics Query
```python
# New unified approach
targets = [
    "character.spells.fireball",
    "character.combat.spell_attack_bonus", 
    "rules.spellcasting.attack_rolls",
    "rules.spells.fireball"
]

# Direct handler calls
character_spells = character_handler.get_spells("warlock")
fireball_rules = rulebook_handler.search_by_keywords(["fireball"])
spell_attack = character_handler.get_spell_attack_bonus("warlock")
```

### Example: Character Combat Query  
```python
# New unified approach
targets = [
    "character.combat",
    "character.equipment.weapons",
    "character.features.combat",
    "rules.combat.attacks"
]

# Direct handler calls
combat_info = character_handler.get_combat_info()
weapons = character_handler.get_equipment("weapons")
features = character_handler.get_abilities_and_features()
combat_rules = rulebook_handler.search_by_keywords(["attack", "damage"])
```

### Example: Story Context Query
```python
# New unified approach  
targets = [
    "character.basic",
    "character.objectives.active",
    "sessions.recent",
    "sessions.covenant"
]

# Direct handler calls
basic_info = character_handler.get_basic_info()
objectives = character_handler.get_active_objectives()
recent_sessions = session_handler.get_latest_session()
covenant_sessions = session_handler.search_by_keywords(["covenant", "Ghul-Ghoth"])
```

## Conclusion

The proposed hybrid schema approach would significantly simplify the ShadowScribe architecture while maintaining targeting precision. The existing knowledge handler classes provide a robust foundation that can support both the current and proposed schemas during migration.
