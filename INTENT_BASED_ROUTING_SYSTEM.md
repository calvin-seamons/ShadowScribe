# Intent-Based Query Routing System

## Overview

This document outlines a sophisticated intent-based query routing system that replaces the current 4-pass architecture with intelligent intent classification and predefined retrieval routes.

## Core Schema Design

### Simplified Intent Schema
```json
{
  "intent": "spell_details",
  "entity": "fireball", 
  "entity_type": "spell",
  "scope": "comprehensive",
  "search_keywords": ["damage", "area", "save"],
  "context_needed": true,
  "reasoning": "User wants complete fireball mechanics including damage calculation"
}
```

### Schema Fields Explained

#### `intent` (required)
The classified query intention that determines the data retrieval route.

#### `entity` (optional)
Specific entity the query focuses on:
- **Character entities**: Character name, ability names, class features
- **Spell entities**: Specific spell names ("fireball", "eldritch blast")
- **Rule entities**: Specific rule sections ("grappling", "two-weapon fighting")
- **Story entities**: NPC names, location names, quest names
- **Item entities**: Specific equipment or magic items

#### `entity_type` (optional)
Helps route to the correct knowledge base functions:
- `"spell"` → Search character spells + rulebook spells
- `"item"` → Search character equipment + rulebook items
- `"npc"` → Search session notes + character background
- `"location"` → Search session notes primarily
- `"rule"` → Search rulebook primarily
- `"feature"` → Search character features + rulebook classes
- `"objective"` → Search character objectives + session notes

#### `scope` (optional, default: "focused")
Determines breadth of data retrieval:
- `"focused"` → Minimal targeted data (faster)
- `"comprehensive"` → Related information included (more complete)
- `"context_heavy"` → Include surrounding/related content (for complex queries)

#### `search_keywords` (optional array)
Additional keywords to enhance search in rulebook/sessions:
- For **rulebook searches**: Related mechanics, synonyms, rule interactions
- For **session searches**: Related events, alternate names, associated concepts
- For **character searches**: Related abilities, dependencies, interactions

#### `context_needed` (boolean, default: false)
Whether the query depends on previous conversation:
- `true` → Query references previous messages ("why is that?", "explain more", "what about the other option?")
- `false` → Query is self-contained and can be answered independently

---

## Intent Categories & Routing Map

### 1. Character Information Intents

#### `character_overview`
**Description**: General character information request
**Triggers**: "tell me about my character", "character summary", "who am I"
**Entity**: Character name (optional)
**Entity Type**: `"character"`
**Functions Called**:
- `character_handler.get_basic_info()`
- `character_handler.get_background_info()`
- `character_handler.get_combat_info()`

**Scope**: Usually `"comprehensive"` for overview
**Search Keywords**: None typically needed
**Context Needed**: `false` (self-contained character info request)

#### `character_stats`
**Description**: Ability scores, modifiers, and derived stats
**Triggers**: "what are my stats", "ability scores", "strength modifier"
**Entity**: Specific ability name (optional)
**Entity Type**: `"ability"` or `"stat"`
**Functions Called**:
- `character_handler.get_basic_info()` (for ability_scores)
- `character_handler.get_combat_info()` (for derived stats)
- `character_handler.get_proficiency_bonus()`

**Scope**: `"focused"` for specific stats, `"comprehensive"` for all stats
**Search Keywords**: None needed (direct character data)
**Context Needed**: `false` (direct stat lookup)

#### `character_combat_stats`
**Description**: Combat-related statistics and capabilities
**Triggers**: "combat stats", "AC", "hit points", "initiative"
**Entity**: Specific stat name (optional)
**Entity Type**: `"stat"`
**Functions Called**:
- `character_handler.get_combat_info()`
- `character_handler.get_proficiency_bonus()`

**Scope**: `"focused"` for specific stats
**Search Keywords**: None needed
**Context Needed**: `false` (direct stat lookup)

#### `character_background`
**Description**: Backstory, personality, and roleplay information
**Triggers**: "backstory", "personality", "background", "family"
**Entity**: Specific background element (optional)
**Entity Type**: `"background"`
**Functions Called**:
- `character_handler.get_background_info()`

**Scope**: `"comprehensive"` for full backstory context
**Search Keywords**: Entity-related terms for specific backstory elements
**Context Needed**: `true` if follow-up to previous backstory discussion, `false` for initial backstory request

#### `character_progression`
**Description**: Level progression, experience, advancement
**Triggers**: "what level", "experience points", "next level"
**Entity**: None typically
**Entity Type**: None
**Functions Called**:
- `character_handler.get_basic_info()` (for level/experience)
- `character_handler.get_abilities_and_features()` (for level-based features)

**Scope**: `"focused"` for current level, `"comprehensive"` for progression planning
**Search Keywords**: ["advancement", "level", class_name] for progression rules
**Context Needed**: `false` (self-contained level info)

### 2. Combat & Action Intents

#### `combat_actions`
**Description**: Available combat actions and attacks
**Triggers**: "what can I do in combat", "attack options", "actions"
**Entity**: Specific action name (optional)
**Entity Type**: `"action"`
**Functions Called**:
- `character_handler.get_file_data("action_list.json")`
- `character_handler.get_combat_info()`
- `character_handler.get_equipment("weapons")`

**Scope**: `"comprehensive"` for all combat options
**Search Keywords**: ["combat", "action", "attack"] for related rules
**Context Needed**: `false` (self-contained combat capabilities lookup)

#### `attack_calculation`
**Description**: Calculate attack rolls and damage
**Triggers**: "attack with", "damage for", "hit with my sword"
**Entity**: Weapon or spell name (required)
**Entity Type**: `"weapon"` or `"spell"`
**Functions Called**:
- `character_handler.get_equipment("weapons")`
- `character_handler.get_combat_info()`
- `character_handler.get_proficiency_bonus()`
- `rulebook_handler.search_by_keywords([entity])`

**Scope**: `"focused"` for specific attack calculation
**Search Keywords**: [entity, "attack", "damage", "properties"] for weapon/spell rules
**Context Needed**: `false` (self-contained attack calculation)

#### `combat_mechanics`
**Description**: How combat rules work
**Triggers**: "how does grappling work", "what is flanking", "opportunity attacks"
**Entity**: Specific mechanic name (required)
**Entity Type**: `"rule"`
**Functions Called**:
- `rulebook_handler.search_by_keywords([entity])`
- `rulebook_handler.search_by_content(entity)`

**Scope**: `"comprehensive"` for related mechanics
**Search Keywords**: [entity, "combat", "mechanics"] for thorough rule search
**Context Needed**: `false` (self-contained rule explanation)

### 3. Spellcasting Intents

#### `spell_list`
**Description**: Available spells for character
**Triggers**: "what spells do I know", "spell list", "cantrips"
**Entity**: Spell level or class (optional)
**Entity Type**: `"class"` or `"spell_level"`
**Functions Called**:
- `character_handler.get_spells()`
- `character_handler.get_spells(spell_class)` if entity specified

**Scope**: `"comprehensive"` for complete spell list
**Search Keywords**: None needed (direct character data)
**Context Needed**: `false` (self-contained spell list lookup)

#### `spell_details`
**Description**: Specific spell information and mechanics
**Triggers**: "how does fireball work", "spell description", "eldritch blast damage"
**Entity**: Spell name (required)
**Entity Type**: `"spell"`
**Functions Called**:
- `character_handler.get_spells()`
- `rulebook_handler.search_by_keywords([entity])`
- `character_handler.get_spell_save_dc()` if applicable
- `character_handler.get_spell_attack_bonus()` if applicable

**Scope**: `"comprehensive"` for full spell mechanics
**Search Keywords**: ["damage", "range", "duration", "components", entity] for rulebook search
**Context Needed**: `false` (self-contained spell explanation)

#### `spell_mechanics`
**Description**: General spellcasting rules and mechanics
**Triggers**: "how does concentration work", "spell slots", "ritual casting"
**Entity**: Mechanic name (required)
**Entity Type**: `"rule"`
**Functions Called**:
- `rulebook_handler.search_by_keywords([entity, "spellcasting"])`
- `character_handler.get_spells()` for character context

**Scope**: `"comprehensive"` for related mechanics
**Search Keywords**: [entity, "spellcasting", "magic", "caster"] for thorough rule search
**Context Needed**: `false` (self-contained rule explanation)

#### `spell_slot_management`
**Description**: Spell slot usage and recovery
**Triggers**: "spell slots remaining", "when do I recover slots", "short rest spells"
**Entity**: Spell level (optional)
**Entity Type**: `"spell_level"`
**Functions Called**:
- `character_handler.get_spells()`
- `character_handler.get_basic_info()` (for class levels)

**Scope**: `"focused"` for slot information
**Search Keywords**: ["spell slots", "recovery", "rest"] for slot mechanics
**Context Needed**: `false` (self-contained slot lookup)

### 4. Equipment & Inventory Intents

#### `equipment_list`
**Description**: Character's equipment and inventory
**Triggers**: "what do I have", "inventory", "equipment list"
**Entity**: Equipment type (optional)
**Entity Type**: `"equipment_type"`
**Functions Called**:
- `character_handler.get_equipment()`
- `character_handler.get_equipment(entity)` if type specified

**Scope**: `"comprehensive"` for complete inventory
**Search Keywords**: None needed (direct character data)
**Context Needed**: `false` (self-contained inventory lookup)

#### `item_details`
**Description**: Specific item information and properties
**Triggers**: "what does this item do", "magic item properties", "weapon stats"
**Entity**: Item name (required)
**Entity Type**: `"item"` or `"weapon"`
**Functions Called**:
- `character_handler.get_equipment()`
- `rulebook_handler.search_by_keywords([entity])`

**Scope**: `"comprehensive"` for full item details
**Search Keywords**: [entity, "properties", "magic", "stats"] for item rules
**Context Needed**: `false` (self-contained item explanation)

#### `equipment_management`
**Description**: Equipping, attuning, carrying capacity
**Triggers**: "can I equip this", "attunement slots", "carrying capacity"
**Entity**: Item name (optional)
**Entity Type**: `"item"`
**Functions Called**:
- `character_handler.get_equipment()`
- `character_handler.get_basic_info()` (for strength/carrying capacity)
- `rulebook_handler.search_by_keywords(["attunement", "equipment"])`

**Scope**: `"focused"` for specific equipment rules
**Search Keywords**: ["attunement", "equipment", "carrying capacity"] for relevant rules
**Context Needed**: `false` (self-contained equipment rules)

### 5. Character Features & Abilities Intents

#### `class_features`
**Description**: Class-specific features and abilities
**Triggers**: "class features", "what can my paladin do", "warlock abilities"
**Entity**: Class name or feature name (optional)
**Entity Type**: `"class"` or `"feature"`
**Functions Called**:
- `character_handler.get_abilities_and_features()`
- `character_handler.get_basic_info()` (for class levels)
- `rulebook_handler.get_spells_by_class()` if spellcaster

**Scope**: `"comprehensive"` for all class features
**Search Keywords**: [entity, "class", "features", "abilities"] for class rules
**Context Needed**: `false` (self-contained class feature lookup)

#### `racial_traits`
**Description**: Racial traits and heritage abilities
**Triggers**: "racial traits", "drow abilities", "darkvision range"
**Entity**: Race name or trait name (optional)
**Entity Type**: `"race"` or `"trait"`
**Functions Called**:
- `character_handler.get_abilities_and_features()`
- `character_handler.get_basic_info()` (for race info)

**Scope**: `"comprehensive"` for all racial traits
**Search Keywords**: [entity, "racial", "traits", "heritage"] for racial rules
**Context Needed**: `false` (self-contained racial trait lookup)

#### `feat_details`
**Description**: Feat descriptions and mechanical effects
**Triggers**: "what does this feat do", "feat benefits", "sharpshooter"
**Entity**: Feat name (required)
**Entity Type**: `"feat"`
**Functions Called**:
- `character_handler.get_abilities_and_features()`
- `rulebook_handler.search_by_keywords([entity])`

**Scope**: `"comprehensive"` for full feat mechanics
**Search Keywords**: [entity, "feat", "benefits", "mechanics"] for feat rules
**Context Needed**: `false` (self-contained feat explanation)

#### `feature_usage`
**Description**: Limited-use feature tracking and recovery
**Triggers**: "how many uses left", "when does this recharge", "short rest features"
**Entity**: Feature name (required)
**Entity Type**: `"feature"`
**Functions Called**:
- `character_handler.get_abilities_and_features()`
- `character_handler.get_basic_info()` (for level-dependent uses)

**Scope**: `"focused"` for specific feature usage
**Search Keywords**: [entity, "usage", "recharge", "recovery"] for usage rules
**Context Needed**: `false` (self-contained feature usage lookup)

### 6. Story & Campaign Intents

#### `story_recap`
**Description**: Recent session events and story summary
**Triggers**: "what happened last session", "story so far", "recap"
**Entity**: Session date or event name (optional)
**Entity Type**: `"session"` or `"event"`
**Functions Called**:
- `session_handler.get_latest_session()`
- `session_handler.get_session_summaries()`
- `character_handler.get_basic_info()` for character context

**Scope**: `"comprehensive"` for full story context
**Search Keywords**: [entity, "session", "events", "story"] for session search
**Context Needed**: `false` (self-contained story recap)

#### `quest_status`
**Description**: Current objectives and quest progress
**Triggers**: "current quests", "objectives", "what am I supposed to do"
**Entity**: Quest name (optional)
**Entity Type**: `"objective"` or `"quest"`
**Functions Called**:
- `character_handler.get_active_objectives()`
- `character_handler.get_objectives_and_contracts()`
- `session_handler.search_by_keywords([entity])` if specific quest

**Scope**: `"comprehensive"` for all active quests
**Search Keywords**: [entity, "quest", "objective", "mission"] for quest search
**Context Needed**: `false` (self-contained quest status)

#### `npc_information`
**Description**: Information about NPCs and relationships
**Triggers**: "who is Thaldrin", "NPCs we've met", "enemy information"
**Entity**: NPC name (required)
**Entity Type**: `"npc"`
**Functions Called**:
- `session_handler.get_npcs_mentioned()`
- `session_handler.search_by_keywords([entity])`
- `character_handler.get_background_info()` for personal connections

**Scope**: `"comprehensive"` for full NPC context
**Search Keywords**: [entity, "npc", alternate_names, titles] for session search
**Context Needed**: `false` (self-contained NPC information)

#### `location_information`
**Description**: Information about places and geography
**Triggers**: "where are we", "what do we know about this place", "location details"
**Entity**: Location name (required)
**Entity Type**: `"location"`
**Functions Called**:
- `session_handler.get_locations_visited()`
- `session_handler.search_by_keywords([entity])`

**Scope**: `"comprehensive"` for location history and details
**Search Keywords**: [entity, "location", "place", regional_terms] for thorough session search
**Context Needed**: `false` (self-contained location information)

#### `covenant_details`
**Description**: Divine covenant information and obligations
**Triggers**: "covenant", "Ghul-Ghoth", "divine contract", "celestial obligations"
**Entity**: Covenant aspect (optional)
**Entity Type**: `"objective"` or `"contract"`
**Functions Called**:
- `character_handler.get_covenant_details()`
- `character_handler.get_objectives_and_contracts()`
- `session_handler.search_by_keywords(["covenant", "Ghul-Ghoth"])`

**Scope**: `"comprehensive"` for full covenant understanding
**Search Keywords**: ["covenant", "Ghul-Ghoth", "divine", "celestial", "obligation", entity] for session search
**Context Needed**: `false` (self-contained covenant information)

### 7. Rules & Mechanics Intents

#### `rule_lookup`
**Description**: General D&D rules and mechanics
**Triggers**: "how does X work", "rules for", "mechanics of"
**Entity**: Rule topic (required)
**Entity Type**: `"rule"`
**Functions Called**:
- `rulebook_handler.search_by_keywords([entity])`
- `rulebook_handler.search_by_content(entity)`

**Scope**: `"comprehensive"` for complete rule explanation
**Search Keywords**: [entity, "mechanics", "rules"] for thorough rule search
**Context Needed**: `false` (self-contained rule explanation)

#### `class_mechanics`
**Description**: How specific classes work
**Triggers**: "how do paladins work", "warlock mechanics", "multiclassing rules"
**Entity**: Class name (required)
**Entity Type**: `"class"`
**Functions Called**:
- `rulebook_handler.search_by_keywords([entity])`
- `rulebook_handler.get_spells_by_class(entity)`
- `character_handler.get_basic_info()` for character context

**Scope**: `"comprehensive"` for full class mechanics
**Search Keywords**: [entity, "class", "mechanics", "features"] for class rules
**Context Needed**: `false` (self-contained class explanation)

#### `rule_clarification`
**Description**: Complex rule interactions and edge cases
**Triggers**: "can I do X and Y", "what happens if", "rule interaction"
**Entity**: Rule concepts (required)
**Entity Type**: `"rule"`
**Functions Called**:
- `rulebook_handler.search_by_keywords([entity])`
- `rulebook_handler.search_by_content(entity)`

**Scope**: `"context_heavy"` for edge cases and interactions
**Search Keywords**: [entity, "interaction", "exception", "special"] for complex rule search
**Context Needed**: `true` if clarifying previously discussed rules, `false` for new rule questions

### 8. Character Building & Optimization Intents

#### `build_optimization`
**Description**: Character build advice and optimization
**Triggers**: "how to optimize", "best spells for my level", "feat recommendations"
**Entity**: Optimization focus (optional)
**Entity Type**: `"optimization"`
**Functions Called**:
- `character_handler.get_basic_info()`
- `character_handler.get_abilities_and_features()`
- `character_handler.get_spells()`
- `rulebook_handler.search_by_keywords([class_name, "optimization"])`

**Scope**: `"comprehensive"` for optimization advice
**Search Keywords**: [entity, "optimization", "build", class_name] for build advice
**Context Needed**: `false` (self-contained optimization advice)

#### `multiclass_planning`
**Description**: Multiclassing considerations and planning
**Triggers**: "multiclass options", "should I take levels in", "multiclass requirements"
**Entity**: Target class (optional)
**Entity Type**: `"class"`
**Functions Called**:
- `character_handler.get_basic_info()`
- `rulebook_handler.search_by_keywords(["multiclassing"])`
- `rulebook_handler.search_by_keywords([entity])` if target class specified

**Scope**: `"comprehensive"` for multiclass planning
**Search Keywords**: ["multiclass", "requirements", entity] for multiclass rules
**Context Needed**: `false` (self-contained multiclass information)

#### `spell_selection`
**Description**: Spell choice recommendations and analysis
**Triggers**: "what spells should I take", "spell recommendations", "best cantrips"
**Entity**: Spell level or type (optional)
**Entity Type**: `"spell_level"` or `"spell_type"`
**Functions Called**:
- `character_handler.get_spells()`
- `character_handler.get_basic_info()`
- `rulebook_handler.get_spells_by_class(class_name)`

**Scope**: `"comprehensive"` for spell recommendations
**Search Keywords**: [entity, "spells", "recommendations", class_name] for spell advice
**Context Needed**: `false` (self-contained spell selection advice)

### 9. Social & Roleplay Intents

#### `social_interaction`
**Description**: Roleplay guidance and social mechanics
**Triggers**: "how should I roleplay", "social skills", "persuasion check"
**Entity**: Social skill or situation (optional)
**Entity Type**: `"skill"` or `"social_situation"`
**Functions Called**:
- `character_handler.get_background_info()`
- `character_handler.get_basic_info()` (for social stats)
- `rulebook_handler.search_by_keywords(["social", entity])`

**Scope**: `"comprehensive"` for roleplay guidance
**Search Keywords**: [entity, "social", "roleplay", "interaction"] for social rules
**Context Needed**: `false` (self-contained roleplay advice)

#### `personality_guidance`
**Description**: Character personality and motivation guidance
**Triggers**: "how would my character react", "personality traits", "character motivation"
**Entity**: Situation or trait (optional)
**Entity Type**: `"personality"` or `"situation"`
**Functions Called**:
- `character_handler.get_background_info()`
- `character_handler.get_objectives_and_contracts()`

**Scope**: `"comprehensive"` for personality context
**Search Keywords**: [entity, "personality", "motivation", "background"] for character context
**Context Needed**: `true` if asking about reaction to previously discussed situation, `false` for general personality questions

### 10. Meta & System Intents

#### `character_comparison`
**Description**: Compare character abilities or options
**Triggers**: "compare spells", "which is better", "spell vs spell"
**Entity**: Comparison subjects (required)
**Entity Type**: `"comparison"`
**Functions Called**:
- `character_handler.get_spells()`
- `character_handler.get_equipment()`
- `rulebook_handler.search_by_keywords([entity])`

**Scope**: `"comprehensive"` for thorough comparison
**Search Keywords**: [entity, "comparison", "vs", "better"] for comparison rules
**Context Needed**: `true` if comparing options from previous discussion, `false` for new comparisons

#### `quick_reference`
**Description**: Quick lookup of basic information
**Triggers**: "quick stats", "spell save DC", "proficiency bonus"
**Entity**: Specific stat (required)
**Entity Type**: `"stat"` or `"reference"`
**Functions Called**:
- Based on entity: various `get_*` methods from character_handler
- `character_handler.get_spell_save_dc()` for spell DCs
- `character_handler.get_proficiency_bonus()` for proficiency

**Scope**: `"focused"` for quick lookup
**Search Keywords**: None needed (direct stat lookup)
**Context Needed**: `false` (self-contained stat lookup)

#### `session_planning`
**Description**: Preparation for upcoming sessions
**Triggers**: "prepare for session", "what should I prepare", "spell preparation"
**Entity**: Preparation type (optional)
**Entity Type**: `"preparation"`
**Functions Called**:
- `character_handler.get_spells()`
- `character_handler.get_equipment()`
- `character_handler.get_active_objectives()`
- `session_handler.get_latest_session()`

**Scope**: `"comprehensive"` for session preparation
**Search Keywords**: [entity, "preparation", "planning", "session"] for preparation advice
**Context Needed**: `false` (self-contained preparation advice)

---

## Implementation Strategy

### Intent Classification Process

1. **Keyword Matching**: Use trigger phrases to identify likely intents
2. **Entity Extraction**: Parse query for specific entities (spells, items, NPCs)
3. **Context Analysis**: Determine what additional context is needed
4. **Function Mapping**: Route to appropriate knowledge base functions
5. **Response Generation**: Combine retrieved data into natural language

### Context Inclusion Logic

The `context_needed` boolean determines whether to include previous conversation history.

Set to `true` when:
- Follow-up questions: "why is that?", "explain more", "what about X?"
- References to previous answers: "like you said before", "the spell you mentioned"
- Clarification requests: "can you elaborate?", "what do you mean?"
- Comparison requests: "which is better?", "what's the difference?"

Set to `false` when:
- Self-contained questions: "what's my AC?", "how does fireball work?"
- New topic questions that don't reference previous conversation
- Simple lookups that stand alone

### Enhanced Search Capabilities

#### `entity_type` Benefits:
- **Faster routing**: Direct knowledge base selection
- **Smarter searches**: Type-specific search strategies
- **Better caching**: Group similar entities for performance
- **Cross-reference**: Link related entities automatically

#### `scope` Benefits:
- **Performance tuning**: Choose data depth vs speed
- **Response length**: Control output verbosity
- **Context awareness**: Include related information when needed
- **User preference**: Allow preference for quick vs detailed answers

#### `search_keywords` Benefits:
- **Better rulebook hits**: Include synonyms and related mechanics
- **Session search enhancement**: Find references using alternate names/terms
- **Disambiguation**: Help distinguish between similar entities
- **Completeness**: Ensure all relevant information is retrieved

### Benefits of Intent-Based Routing

1. **Performance**: Single LLM call instead of 4-pass system
2. **Precision**: Exact function mapping for each intent type
3. **Consistency**: Standardized data retrieval patterns
4. **Maintainability**: Clear mapping between intents and functions
5. **Extensibility**: Easy to add new intents and routing rules
6. **Context Awareness**: Smart inclusion of relevant context only when needed

### Migration Considerations

- Start with high-confidence intent patterns
- Maintain fallback to current system for unclear queries
- Gradually expand intent coverage based on usage patterns
- Use query logs to identify new intent patterns
- A/B test performance against current 4-pass system

This intent-based system would dramatically simplify the query routing architecture while providing more precise and faster responses through direct function mapping.
