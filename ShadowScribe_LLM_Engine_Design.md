# ShadowScribe LLM Engine and Query Routing System Design

## Overview

ShadowScribe is an intelligent D&D 5e assistant that uses a multi-pass query routing system to efficiently retrieve and synthesize information from multiple knowledge sources. The system minimizes token usage while maximizing response accuracy by progressively narrowing down information needs through intelligent routing.

## Knowledge Base Architecture

### Data Sources

Our knowledge base consists of the following structured data sources:

#### 1. D&D 5e System Reference Document (SRD)
- **dnd5e_srd_full.json** (4.2 MB) - Complete hierarchical rulebook structure with 2,098 sections
- **dnd5e_srd_query_helper.json** (520 KB) - Optimized query interface with searchable index
- **dnd5rulebook.md** - Source markdown of the D&D 5e SRD

#### 2. Character Data (JSON Format)
- **character.json** - Core character stats, abilities, and characteristics for Duskryn Nightwarden (Level 13 Dwarf Warlock/Paladin)
- **inventory_list.json** - Equipment, weapons, armor, consumables, and magical items
- **feats_and_traits.json** - Class features, racial traits, feats, and calculated bonuses
- **spell_list.json** - Available spells organized by class (Paladin/Warlock) and level
- **action_list.json** - Combat actions, attack options, and special abilities
- **character_background.json** - Backstory, personality, allies, enemies, and roleplay elements

#### 3. Campaign Data
- **session_notes/** - Markdown files containing session summaries, key events, NPCs, and story hooks
  - Format: `MM-DD-YY.md` (e.g., `06-30-25.md`)
  - Contains: Summary, key events, NPCs, locations, combat encounters, character decisions, cliffhangers

## Multi-Pass Query Routing System

### System Architecture

```
User Query → Pass 1: Source Selection → Pass 2: Specific Targeting → Pass 3: Content Retrieval → Response Generation
```

### Pass 1: Knowledge Source Selection

**Purpose**: Determine which high-level data sources are needed to answer the user's query.

**Input**: Raw user query
**Output**: List of required knowledge sources

**LLM Prompt Structure**:
```
You are an intelligent D&D assistant. Analyze this query and determine which knowledge sources you need:

Available Sources:
- dnd_rulebook: D&D 5e System Reference Document (2,098 sections covering rules, spells, monsters, items)
- character_data: Current character information (stats, equipment, abilities, background)
- session_notes: Previous session summaries and campaign narrative (available dates: [dynamic list])

Query: "{user_query}"

Return a JSON response indicating which sources you need and why:
{
  "sources_needed": ["dnd_rulebook", "character_data", "session_notes"],
  "reasoning": "Explanation of why each source is needed"
}
```

**Example Scenarios**:
- "What's my character's AC?" → character_data only
- "How does counterspell work?" → dnd_rulebook only  
- "What happened with Ghul'Vor last session?" → session_notes only
- "Can I cast counterspell to stop that fireball?" → dnd_rulebook + character_data
- "Given what happened with Duskryn's ritual, what are my spell options?" → All three sources

### Pass 2: Specific Content Targeting

**Purpose**: For each required source, determine exactly which sections/data to retrieve.

#### 2A: D&D Rulebook Targeting

**Input**: User query + dnd5e_srd_query_helper.json structure
**Output**: List of specific section IDs to retrieve

**LLM Prompt Structure**:
```
Based on this query about D&D rules, select the specific sections you need from the SRD:

Query: "{user_query}"

Available sections (showing key categories):
{section_overview_from_query_helper}

Searchable index with keywords:
{relevant_index_entries}

Return section IDs you need:
{
  "section_ids": ["abc123", "def456"],
  "reasoning": "Why these specific sections"
}
```

#### 2B: Character Data Targeting

**Input**: User query + character data structure overview
**Output**: Specific data fields to retrieve

**Character Data Structure**:
```json
{
  "character.json": ["name", "race", "class", "level", "ability_scores", "combat_stats"],
  "inventory_list.json": ["equipped_items", "weapons", "armor", "consumables"],
  "feats_and_traits.json": ["class_features", "species_traits", "feats"],
  "spell_list.json": ["paladin_spells", "warlock_spells", "cantrips"],
  "action_list.json": ["attacks", "bonus_actions", "reactions", "special_abilities"],
  "character_background.json": ["backstory", "personality", "allies", "enemies"]
}
```

#### 2C: Session Notes Targeting

**Input**: User query + available session dates and summaries
**Output**: Specific session files to retrieve

### Pass 3: Content Retrieval

**Purpose**: Fetch the exact content identified in Pass 2.

**Retrieval Functions**:

```python
def retrieve_rulebook_sections(section_ids: List[str]) -> Dict[str, Any]:
    """Retrieve specific sections from dnd5e_srd_full.json"""
    
def retrieve_character_data(file_fields: Dict[str, List[str]]) -> Dict[str, Any]:
    """Retrieve specific fields from character JSON files"""
    
def retrieve_session_notes(session_dates: List[str]) -> Dict[str, str]:
    """Retrieve content from specific session note files"""
```

### Pass 4: Response Generation

**Purpose**: Synthesize retrieved information into a comprehensive, accurate response.

**LLM Prompt Structure**:
```
You are Duskryn Nightwarden's intelligent D&D assistant. Use the following information to answer the user's query accurately and helpfully.

User Query: "{user_query}"

Character Information:
{character_data}

D&D Rules:
{rulebook_sections}

Session Context:
{session_notes}

Provide a comprehensive answer that:
1. Directly addresses the user's question
2. Includes relevant mechanical details (stats, DCs, damage, etc.)
3. Considers character-specific modifiers and abilities
4. References recent session events when relevant
5. Suggests tactical options or roleplay considerations when appropriate
```

## Implementation Details

### Data Retrieval Optimization

#### Intelligent Caching
- Cache frequently accessed rulebook sections
- Pre-load character data on session start
- Store session summaries in memory for quick access

#### Progressive Loading
- Start with query helper for rulebook navigation
- Only load full sections when specifically needed
- Batch character data requests by file

### Query Pattern Recognition

**Common Query Types**:
1. **Rules Lookup**: "How does [spell/ability] work?"
2. **Character Status**: "What's my [stat/equipment/ability]?"
3. **Combat Planning**: "Can I [action] to [target]?"
4. **Session Recall**: "What happened with [NPC/event]?"
5. **Character Building**: "Should I take [feat/spell]?"

### Error Handling and Fallbacks

**Missing Data Scenarios**:
- Unknown spell → Search similar spells + suggest alternatives
- Ambiguous character reference → Ask for clarification
- Missing session data → Indicate uncertainty + provide general guidance

**Validation Checks**:
- Verify spell availability for character's classes/level
- Cross-reference equipment capabilities with character proficiencies
- Validate action economy usage

## Technical Architecture

### Core Components

```python
class ShadowScribeEngine:
    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        self.query_router = QueryRouter()
        self.content_retriever = ContentRetriever()
        self.response_generator = ResponseGenerator()
    
    async def process_query(self, user_query: str) -> str:
        # Pass 1: Source Selection
        sources = await self.query_router.select_sources(user_query)
        
        # Pass 2: Content Targeting  
        targets = await self.query_router.target_content(user_query, sources)
        
        # Pass 3: Content Retrieval
        content = await self.content_retriever.fetch_content(targets)
        
        # Pass 4: Response Generation
        response = await self.response_generator.generate_response(
            user_query, content
        )
        
        return response
```

### Integration with Existing Codebase

**File Structure Integration**:
```
src/
├── engine/
│   ├── __init__.py
│   ├── shadowscribe_engine.py
│   ├── query_router.py
│   ├── content_retriever.py
│   └── response_generator.py
├── knowledge/
│   ├── __init__.py
│   ├── rulebook_handler.py
│   ├── character_handler.py
│   └── session_handler.py
└── utils/
    ├── prompt_templates.py
    └── validation.py
```

## Performance Considerations

### Token Optimization
- **Pass 1**: ~500 tokens (source selection)
- **Pass 2**: ~1,000 tokens (content targeting)
- **Pass 3**: Variable based on content retrieved
- **Pass 4**: ~2,000-5,000 tokens (response generation)

**Total**: Typically 4,000-7,000 tokens vs 50,000+ tokens for naive full-context approach

### Response Time
- **Target**: < 3 seconds end-to-end
- **Caching**: Reduce repeated lookups by 80%
- **Parallel Processing**: Fetch multiple content sources simultaneously

### Accuracy Metrics
- **Factual Accuracy**: Verify mechanical calculations
- **Character Consistency**: Match retrieved data to character state
- **Session Continuity**: Reference appropriate narrative context

## Future Enhancements

### Advanced Features
1. **Conversation Memory**: Track multi-turn conversations for context
2. **Proactive Suggestions**: "You might also want to know..."
3. **Combat Assistant**: Real-time action tracking and suggestions
4. **Campaign Timeline**: Automatic session event indexing
5. **Character Progression**: Leveling recommendations and build optimization

### Data Expansion
1. **Additional Rulebooks**: Xanathar's, Tasha's, etc.
2. **Custom Content**: Homebrew rules and items
3. **Multiple Characters**: Party-wide assistance
4. **Campaign Management**: DM tools and NPC tracking

### Intelligence Improvements
1. **Semantic Search**: Better keyword matching for rulebook sections
2. **Context Awareness**: Understand implicit references
3. **Preference Learning**: Adapt to user's playstyle and interests
4. **Uncertainty Handling**: Graceful degradation when information is incomplete

## Usage Examples

### Example 1: Simple Rules Query
**Query**: "How does counterspell work?"
- **Pass 1**: dnd_rulebook only
- **Pass 2**: Search for "counterspell" → section ID found
- **Pass 3**: Retrieve counterspell section
- **Pass 4**: Explain spell mechanics

### Example 2: Character-Specific Combat Query  
**Query**: "Can I counterspell that fireball?"
- **Pass 1**: dnd_rulebook + character_data
- **Pass 2**: Counterspell rules + character's spell list + current spell slots
- **Pass 3**: Retrieve spell details + character's warlock spell capabilities
- **Pass 4**: Confirm availability, explain mechanics, calculate success chance

### Example 3: Complex Narrative Query
**Query**: "Given what happened with Duskryn's soul being trapped, what are my options for saving him?"
- **Pass 1**: All sources (rulebook + character + session_notes)
- **Pass 2**: Soul/resurrection magic + available spells + recent session about ritual
- **Pass 3**: Retrieve resurrection spells + character capabilities + session details
- **Pass 4**: Comprehensive analysis of magical options considering narrative context

## Conclusion

The ShadowScribe LLM Engine provides an intelligent, efficient, and contextually aware assistant for D&D gameplay. By leveraging structured data and multi-pass query routing, it delivers accurate, relevant responses while minimizing computational costs and maximizing player experience.

The system's modular design allows for easy expansion and customization, making it suitable for various campaign styles and character types while maintaining the deep, specific knowledge needed for complex D&D rule interactions.