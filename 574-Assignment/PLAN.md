# 574 NLP Assignment: D&D Query Understanding with Transformers

## Project Overview

Train two transformer models to replace LLM-based query routing in the ShadowScribe D&D RAG system:
1. **Model 1: Tool & Intent Classifier** - Multi-label tool selection + intent classification
2. **Model 2: Entity Extractor** - NER for D&D-specific entities

**Scope**: Training + Evaluation (Colab notebook deliverable)
**Timeline**: 1-2 weeks

---

## Part 1: Data Generation

### Approach: Pre-built Template Files (No MD Parsing)

We will **manually create** comprehensive template files based on reviewing the existing test questions. No parsing logic - just well-structured JSON/Python files with all templates pre-defined.

### Key Requirement: Multi-Tool Queries

**Most queries should require 2+ tools.** This reflects real-world usage where users ask compound questions.

Examples:
- "What's my AC and how does the Shield spell work?" → `character_data` + `rulebook`
- "Tell me about Eldaryth of Regret and what happened when I found it" → `character_data` + `session_notes`
- "How does grappling work and what's my Athletics bonus?" → `rulebook` + `character_data`

### File Structure for Templates

```
574-assignment/
├── data/
│   ├── templates/
│   │   ├── character_templates.py      # 10 intents, 15-20 templates each
│   │   ├── session_templates.py        # 20 intents, 10-15 templates each
│   │   ├── rulebook_templates.py       # 31 intents, 10-15 templates each
│   │   ├── multi_tool_templates.py     # Compound queries (2-3 tools)
│   │   └── entity_gazetteers.py        # Spell, item, NPC, location lists
│   ├── generated/
│   │   ├── train.json
│   │   ├── val.json
│   │   └── test.json
```

### Template File Format

```python
# multi_tool_templates.py
MULTI_TOOL_TEMPLATES = [
    {
        "template": "What's my {stat} and how does {spell} work?",
        "tools": ["character_data", "rulebook"],
        "intents": {"character_data": "combat_info", "rulebook": "spell_details"},
        "slots": {"stat": "combat_stats", "spell": "spell_names"}
    },
    {
        "template": "Tell me about {item} and what {npc} said about it",
        "tools": ["character_data", "session_notes"],
        "intents": {"character_data": "inventory_info", "session_notes": "npc_info"},
        "slots": {"item": "item_names", "npc": "npc_names"}
    },
    # ... 200+ multi-tool templates
]
```

### Target Dataset Composition

| Type | Count | % of Dataset |
|------|-------|--------------|
| 2-tool queries | 5,000 | 50% |
| 3-tool queries | 2,000 | 20% |
| 1-tool queries | 3,000 | 30% |
| **Total** | **10,000** | 100% |

### Entity Gazetteers (Pre-defined Lists)

**IMPORTANT: Use ONLY D&D 5e SRD/rulebook entities for generalizability.**

Do NOT use entities specific to my character (Duskryn) or campaign:
- ❌ "Eldaryth of Regret" (my weapon)
- ❌ "High Acolyte Aldric", "Ghul'vor" (my NPCs)
- ❌ "Soul Cairn", "Theater of Blood" (my locations)

Instead, use generic D&D 5e content that applies to any campaign:

```python
# entity_gazetteers.py

# From D&D 5e SRD - spells (all official spells)
SPELL_NAMES = [
    "Fireball", "Lightning Bolt", "Shield", "Cure Wounds", "Counterspell",
    "Magic Missile", "Thunderwave", "Healing Word", "Hold Person",
    "Dispel Magic", "Fly", "Haste", "Polymorph", "Wish", ...
]

# From D&D 5e SRD - standard equipment & magic items
ITEM_NAMES = [
    "Bag of Holding", "Potion of Healing", "Longsword", "Chain Mail",
    "Holy Symbol", "Rope of Climbing", "Cloak of Elvenkind",
    "Ring of Protection", "Staff of the Magi", "Vorpal Sword", ...
]

# From D&D 5e SRD - monsters/creatures (used as generic NPC types)
CREATURE_NAMES = [
    "Goblin", "Orc", "Dragon", "Lich", "Beholder", "Mind Flayer",
    "Vampire", "Werewolf", "Giant", "Demon", "Devil", ...
]

# From D&D 5e SRD - standard locations/planes
LOCATION_NAMES = [
    "Shadowfell", "Feywild", "Astral Plane", "Ethereal Plane",
    "Nine Hells", "Abyss", "Mount Celestia", "Underdark", ...
]

# From D&D 5e SRD - class features (all classes)
FEATURE_NAMES = [
    "Sneak Attack", "Divine Smite", "Wild Shape", "Action Surge",
    "Rage", "Bardic Inspiration", "Channel Divinity", "Metamagic",
    "Eldritch Invocations", "Ki Points", "Lay on Hands", ...
]

# From D&D 5e SRD - classes and races
CLASS_NAMES = ["Fighter", "Wizard", "Rogue", "Cleric", "Paladin", ...]
RACE_NAMES = ["Human", "Elf", "Dwarf", "Halfling", "Dragonborn", ...]
```

### Source for Gazetteers

Pull entity lists directly from:
- `knowledge_base/source/dnd5rulebook.md` - The D&D 5e SRD content
- Official spell lists, monster manual entries, equipment tables

This ensures the model generalizes to ANY D&D character/campaign, not just mine.

### NER Annotation (Auto-generated from gazetteers)

BIO tagging scheme:
- `B-SPELL`, `I-SPELL`
- `B-ITEM`, `I-ITEM`
- `B-NPC`, `I-NPC`
- `B-LOCATION`, `I-LOCATION`
- `B-FEATURE`, `I-FEATURE`
- `B-CLASS`, `I-CLASS`
- `O` (outside)

---

## Part 2: Model 1 - Tool & Intent Classifier

### Architecture

```
Input: [CLS] query [SEP]
         ↓
    RoBERTa-base Encoder (768 dim)
         ↓
    Shared Dense Layer (768 → 256)
         ↓
    ┌────────────────────────────────────────────┐
    │                                            │
    ↓                ↓                ↓          ↓
Tool Head      Char Intent      Session Intent   Rulebook Intent
(3, sigmoid)   (10, softmax)    (20, softmax)    (31, softmax)
```

### Label Schema

```python
# Output format (matches current LLM output)
{
    "tools": [0, 1, 0],  # [character_data, session_notes, rulebook]
    "character_intent": 2,   # index into 10 intents, or -1 if tool not selected
    "session_intent": -1,
    "rulebook_intent": 15,
    "confidence": 0.92
}
```

### Intent Lists

**Character Data (10)**:
`character_basics`, `combat_info`, `abilities_info`, `inventory_info`, `magic_info`, `story_info`, `social_info`, `progress_info`, `full_character`, `character_summary`

**Session Notes (20)**:
`character_status`, `event_sequence`, `npc_info`, `location_details`, `item_tracking`, `combat_recap`, `spell_ability_usage`, `character_decisions`, `party_dynamics`, `quest_tracking`, `puzzle_solutions`, `loot_rewards`, `death_revival`, `divine_religious`, `memory_vision`, `rules_mechanics`, `humor_moments`, `unresolved_mysteries`, `future_implications`, `cross_session`

**Rulebook (31)**:
`describe_entity`, `compare_entities`, `level_progression`, `action_options`, `rule_mechanics`, `calculate_values`, `spell_details`, `class_spell_access`, `monster_stats`, `condition_effects`, `character_creation`, `multiclass_rules`, `equipment_properties`, `damage_types`, `rest_mechanics`, `skill_usage`, `find_by_criteria`, `prerequisite_check`, `interaction_rules`, `tactical_usage`, `environmental_rules`, `creature_abilities`, `saving_throws`, `magic_item_usage`, `planar_properties`, `downtime_activities`, `subclass_features`, `cost_lookup`, `legendary_mechanics`, `optimization_advice`

### Loss Function

```python
def compute_loss(tool_logits, char_logits, session_logits, rule_logits, labels):
    # Multi-label BCE for tool selection
    tool_loss = F.binary_cross_entropy_with_logits(tool_logits, labels['tools'])

    # Masked CE for intents (only compute if tool is selected)
    char_loss = masked_cross_entropy(char_logits, labels['char_intent'],
                                      mask=labels['tools'][:, 0])
    session_loss = masked_cross_entropy(session_logits, labels['session_intent'],
                                         mask=labels['tools'][:, 1])
    rule_loss = masked_cross_entropy(rule_logits, labels['rule_intent'],
                                      mask=labels['tools'][:, 2])

    return tool_loss + char_loss + session_loss + rule_loss
```

### Training Config

```python
config = {
    "base_model": "roberta-base",
    "learning_rate": 2e-5,
    "batch_size": 16,
    "epochs": 10,
    "warmup_ratio": 0.1,
    "weight_decay": 0.01,
    "max_seq_length": 128,
}
```

---

## Part 3: Model 2 - Entity Extractor (NER)

### Architecture

```
Input: [CLS] query tokens [SEP]
         ↓
    RoBERTa-base Encoder
         ↓
    Token Hidden States (batch, seq_len, 768)
         ↓
    Linear Classifier (768 → 13 labels)
         ↓
    CRF Layer (enforces valid BIO sequences)
```

### Entity Types (13 labels)

```
O, B-SPELL, I-SPELL, B-ITEM, I-ITEM, B-NPC, I-NPC,
B-LOCATION, I-LOCATION, B-FEATURE, I-FEATURE, B-CLASS, I-CLASS
```

### Training Config

```python
config = {
    "base_model": "roberta-base",
    "learning_rate": 3e-5,
    "batch_size": 32,
    "epochs": 15,
    "max_seq_length": 64,
    "use_crf": True,
}
```

---

## Part 4: Evaluation Strategy

### Model 1 Metrics

| Metric | Description |
|--------|-------------|
| Tool Exact Match | All 3 tools correctly predicted |
| Tool F1 (micro) | Per-tool precision/recall |
| Intent Accuracy | Correct intent given correct tool |
| Combined Accuracy | Tool + Intent both correct |

### Model 2 Metrics (using `seqeval`)

| Metric | Description |
|--------|-------------|
| Entity F1 (strict) | Exact boundary + type match |
| Entity F1 (partial) | Overlapping spans |
| Per-type F1 | SPELL, ITEM, NPC, etc. separately |

### Baselines

1. **Random** - Random tool/intent selection
2. **Majority class** - Always predict most common
3. **Keyword rules** - Regex-based classification
4. **Zero-shot** - Current LLM (Claude Haiku) for comparison

---

## Part 5: Deliverables

### Local Development with VS Code Colab Extension

Notebooks use **relative paths** for portability. When using VS Code with the Google Colab extension, your local files are accessible directly - no Google Drive mounting needed.

```python
# At the top of every notebook
import os
from pathlib import Path

# Get project root (notebooks/ -> 574-Assignment/)
NOTEBOOK_DIR = Path(os.getcwd())
PROJECT_ROOT = NOTEBOOK_DIR.parent if NOTEBOOK_DIR.name == 'notebooks' else NOTEBOOK_DIR
DATA_PATH = PROJECT_ROOT / 'data' / 'generated'
MODEL_PATH = PROJECT_ROOT / 'models' / 'joint_deberta'
```

### Directory Structure

```
574-Assignment/
├── notebooks/
│   ├── 01_data_generation.ipynb      # Generate training data
│   ├── 02_joint_model_training.ipynb # Joint DeBERTa model (Tool + Intent + NER)
│   └── 03_evaluation.ipynb           # Metrics, baselines, analysis
├── data/
│   ├── templates/                    # Pre-built template files
│   │   ├── character_templates.py
│   │   ├── session_templates.py
│   │   ├── rulebook_templates.py
│   │   ├── multi_tool_templates.py
│   │   └── entity_gazetteers.py
│   └── generated/                    # Generated datasets
│       ├── train.json
│       ├── val.json
│       ├── test.json
│       └── label_mappings.json
├── scripts/
│   └── generate_dataset.py           # Data generation script
├── models/                           # Saved model checkpoints
│   └── joint_deberta/
│       ├── pytorch_model.bin
│       ├── config.json
│       ├── training_config.json
│       └── label_mappings.json
├── results/
│   ├── evaluation_results.csv
│   └── figures/
├── config.py                         # Project configuration
├── PLAN.md
├── README.md
├── pyproject.toml
└── requirements.txt
```

### Notebook Data Flow

```
Notebook 1 (Data Generation)
    ↓ saves locally
    data/generated/train.json, val.json, test.json
    ↓
Notebook 2 (Joint Model Training)
    ↓ loads data, saves checkpoints
    models/joint_deberta/
    ↓
Notebook 3 (Evaluation)
    ↓ loads model + data, outputs results
    results/
```

### Report Outline

1. **Introduction** - Problem, motivation (D&D RAG context)
2. **Dataset** - Generation methodology, statistics
3. **Methods** - Model architectures, training approach
4. **Experiments** - Setup, hyperparameters
5. **Results** - Performance tables, baseline comparisons
6. **Analysis** - Error analysis, confusion matrices
7. **Conclusion** - Findings, limitations, future work

---

## Part 6: Timeline

### Week 1
- **Day 1-2**: Data generation pipeline + create training dataset
- **Day 3-4**: Model 1 implementation + training
- **Day 5-6**: Model 2 implementation + training
- **Day 7**: Initial evaluation

### Week 2
- **Day 1-2**: Hyperparameter tuning
- **Day 3-4**: Full evaluation + baselines
- **Day 5-6**: Error analysis + visualizations
- **Day 7**: Report writing

---

## Critical Files to Reference

| File | Purpose |
|------|---------|
| `docs/test_questions/character-data-testqs.md` | Labeled character queries |
| `docs/test_questions/session-notes-testqs.md` | Labeled session queries |
| `src/rag/character/character_query_types.py` | Intent definitions (10 character intents) |
| `src/rag/session_notes/session_types.py` | Intent definitions (20 session intents) |
| `src/rag/rulebook/rulebook_types.py` | Intent definitions (31 rulebook intents) |
| `src/llm/central_prompt_manager.py` | Example queries in prompts |
| `knowledge_base/source/dnd5rulebook.md` | D&D entities for gazetteers |
