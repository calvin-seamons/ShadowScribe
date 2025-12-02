# Two-Stage Joint DeBERTa Model Architecture

## Overview

This document describes the architecture of our multi-task transformer model for D&D query understanding. The model jointly performs three tasks:

1. **Tool Classification** - Which knowledge sources are needed? (multi-label)
2. **Intent Classification** - What does the user want from each tool? (per-tool multi-class)
3. **Named Entity Recognition (NER)** - What entities are mentioned? (token-level BIO tagging)

---

## Architecture Diagram

```
                            Input Query
                                │
                    "What's my AC and how does Fireball work?"
                                │
                                ▼
                    ┌───────────────────────┐
                    │   DeBERTa-v3-base     │
                    │   (Shared Encoder)    │
                    │   768 hidden dims     │
                    └───────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
        [CLS] Token                      All Token States
      (Sentence Rep)                    (Sequence Rep)
                │                               │
    ┌───────────┼───────────┐                   │
    │           │           │                   │
    ▼           ▼           ▼                   ▼
┌────────┐ ┌────────┐ ┌────────┐         ┌──────────┐
│  Tool  │ │  Tool  │ │  Tool  │         │   NER    │
│  Head  │ │ Intent │ │ Intent │         │   Head   │
│(3 cls) │ │ Heads  │ │ Heads  │         │(25 tags) │
└────────┘ └────────┘ └────────┘         └──────────┘
    │           │                              │
    ▼           ▼                              ▼
[char, sess,  [per-tool                   [O, O, B-STAT,
 rulebook]    intents]                     I-STAT, O, ...]
```

---

## Why DeBERTa-v3-base?

We chose DeBERTa-v3-base over other transformer encoders for several reasons:

### Compared Alternatives

| Model | Parameters | Pros | Cons | Decision |
|-------|------------|------|------|----------|
| **BERT-base** | 110M | Well-understood, fast | Older architecture, lower accuracy | ❌ |
| **RoBERTa-base** | 125M | Strong baseline | No disentangled attention | ❌ |
| **DeBERTa-v3-base** | 86M | SOTA on GLUE, efficient, disentangled attention | Slightly slower tokenization | ✅ |
| **DeBERTa-v3-large** | 304M | Even better accuracy | Too large for our use case | ❌ |
| **DistilBERT** | 66M | Fast, small | Lower accuracy | ❌ |

### Key DeBERTa Advantages

1. **Disentangled Attention** - Separates content and position information, leading to better understanding of word relationships

2. **Enhanced Mask Decoder** - Better pre-training objective than BERT's MLM

3. **Smaller but Smarter** - 86M params outperforms 125M RoBERTa on most benchmarks

4. **GLUE SOTA** - Achieved state-of-the-art on the GLUE benchmark, indicating strong sentence understanding

---

## Two-Stage Training Architecture

### Why Two Stages?

We separate training into stages because the tasks have different characteristics:

| Stage | Tasks | Rationale |
|-------|-------|-----------|
| **Stage 1** | Tools + NER | Query-intrinsic tasks - can be determined from the query alone |
| **Stage 2** | Intents | Context-dependent tasks - what you want depends on which tools are selected |

### Stage 1: Tool + NER (Query-Intrinsic)

**Tool Classification:**
- Answers: "Which knowledge sources does this query need?"
- Multi-label (can select multiple): `[character_data, session_notes, rulebook]`
- Uses **sigmoid + BCE loss** (each tool is independent)

**NER:**
- Answers: "What entities are mentioned?"
- Token-level BIO tagging with 25 tags
- Uses **CrossEntropyLoss with ignore_index=-100**

**Why together?** Both tasks depend only on the query text itself. You can identify "Fireball" as a spell and know you need the rulebook without any external context.

### Stage 2: Per-Tool Intent (Context-Dependent)

**Intent Classification (Gated by Tool Selection):**
- Answers: "What does the user want from each selected tool?"
- Three separate heads with different numbers of classes:
  - `character_data`: 10 intents (e.g., `query_combat_stats`, `list_inventory`)
  - `session_notes`: 20 intents (e.g., `recall_npc_interaction`, `summarize_quest`)
  - `rulebook`: 30 intents (e.g., `explain_spell_mechanics`, `clarify_rule`)

**Why separate heads per tool?**
- Each tool has semantically different intents
- A single 60-class head would conflate unrelated concepts
- Per-tool heads allow specialized learning

**Why gated?**
- Only compute loss for tools that are actually selected
- Samples with `tool=character_data` don't contribute to rulebook intent loss
- Implemented via `ignore_index=-100` masking

---

## Model Components

### Shared Encoder

```python
self.deberta = DebertaV2Model(config)  # 768 hidden dimensions
self.dropout = nn.Dropout(0.1)         # Regularization
```

The encoder is shared across all tasks, allowing:
- Efficient parameter usage
- Transfer learning between tasks
- Single forward pass for all outputs

### Tool Classification Head

```python
self.tool_classifier = nn.Sequential(
    nn.Linear(768, 768),      # Project
    nn.GELU(),                # Non-linearity
    nn.Dropout(0.1),          # Regularize
    nn.Linear(768, 3)         # 3 tools
)
```

- Input: CLS token (sentence representation)
- Output: 3 logits → sigmoid → multi-label prediction
- Loss: Binary Cross-Entropy

### NER Head

```python
self.ner_classifier = nn.Sequential(
    nn.Linear(768, 384),      # Compress
    nn.GELU(),
    nn.Dropout(0.1),
    nn.Linear(384, 25)        # 25 BIO tags
)
```

- Input: All token representations (batch, seq_len, 768)
- Output: Per-token logits → argmax → BIO tags
- Loss: CrossEntropy with ignore_index=-100

**Why not CRF?**
We initially used a CRF layer but removed it because:
1. CRF had numerical instability with special tokens (-100 labels)
2. Standard CrossEntropy with proper masking achieved 98%+ NER F1
3. Simpler architecture, faster training, same accuracy

### Per-Tool Intent Heads

```python
self.character_intent_head = nn.Sequential(
    nn.Linear(768, 384),
    nn.GELU(),
    nn.Dropout(0.1),
    nn.Linear(384, 10)        # 10 character intents
)

self.session_intent_head = nn.Sequential(
    nn.Linear(768, 384),
    nn.GELU(),
    nn.Dropout(0.1),
    nn.Linear(384, 20)        # 20 session intents
)

self.rulebook_intent_head = nn.Sequential(
    nn.Linear(768, 384),
    nn.GELU(),
    nn.Dropout(0.1),
    nn.Linear(384, 30)        # 30 rulebook intents
)
```

- Input: CLS token
- Output: Softmax over tool-specific intents
- Loss: CrossEntropy with ignore_index=-100 (for non-selected tools)

---

## Training Strategy

### Stage 1: Tools + NER (3 epochs)

```python
model.freeze_intent_heads()  # Don't train intents yet
optimizer = AdamW(lr=2e-5)   # Standard fine-tuning rate

loss = tool_loss_weight * tool_loss + ner_loss_weight * ner_loss
```

**Purpose:** Build a solid foundation for understanding what tools and entities are in the query.

### Stage 2: Joint Training (7 epochs)

```python
model.unfreeze_intent_heads()  # Now train everything
optimizer = AdamW(lr=2e-5)

loss = tool_loss + ner_loss + intent_loss  # All tasks
```

**Purpose:** Learn intent classification while maintaining tool/NER performance.

### Stage 3: Fine-tuning (5 epochs)

```python
optimizer = AdamW(lr=1e-6)  # 20x smaller learning rate
```

**Purpose:** Final polish with minimal disruption to learned weights.

---

## Loss Function Design

### Multi-Task Loss Weighting

```python
CONFIG = {
    'tool_loss_weight': 1.0,
    'ner_loss_weight': 1.0,
    'intent_loss_weight': 1.0,
}
```

We use equal weights because:
1. All tasks are equally important for the final system
2. The tasks naturally balance (tool has 3 classes, NER has 25, intent varies)
3. No single task dominates the gradient

### Intent Loss Masking

```python
# Only compute loss for tools that are selected in this sample
if intent_label_character != -100:
    character_intent_loss = CrossEntropy(pred, label)
```

This prevents:
- Confusing the model with irrelevant intent labels
- Gradients from non-selected tools affecting training
- Class imbalance issues

---

## Alternatives Considered

### Single Intent Head (61 classes)

```
❌ REJECTED
```

**Why not:** Conflates unrelated concepts. "query_combat_stats" (character) has nothing to do with "explain_spell_mechanics" (rulebook). Separate heads allow specialized learning.

### Hierarchical Classification

```
Query → Tools → Intent per tool (separate forward passes)
```

**Why not:** Requires multiple forward passes. Our gated approach gets all outputs in one pass while still maintaining task separation.

### Separate Models per Task

```
Model 1: Tools
Model 2: NER  
Model 3: Intents
```

**Why not:** 
- 3x the parameters
- No shared learning between tasks
- Slower inference (3 forward passes)

### Encoder-Decoder (T5/BART)

```
❌ REJECTED
```

**Why not:** Seq2seq is overkill for classification. We're not generating text, just selecting from predefined classes. Encoder-only is more efficient.

---

## Output Format

### Raw Model Output

```python
{
    'tool_logits': [batch, 3],           # Sigmoid → multi-label
    'ner_logits': [batch, seq_len, 25],  # Argmax → BIO tags
    'character_intent_logits': [batch, 10],
    'session_intent_logits': [batch, 20],
    'rulebook_intent_logits': [batch, 30],
}
```

### Decoded Output

```python
{
    'tools': ['character_data', 'rulebook'],
    'intents': {
        'character_data': 'query_combat_stats',
        'rulebook': 'explain_spell_mechanics'
    },
    'entities': [
        {'text': 'AC', 'type': 'STAT'},
        {'text': 'Fireball', 'type': 'SPELL'}
    ]
}
```

---

## Performance Summary

| Task | Metric | Score |
|------|--------|-------|
| Tool Classification | F1 | 99.6% |
| Tool Classification | Exact Match | 99.5% |
| NER | Entity F1 | 98.3% |
| Intent (Character) | Accuracy | 93.8% |
| Intent (Session) | Accuracy | 89.4% |
| Intent (Rulebook) | Accuracy | 92.7% |

---

## Key Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Base Model | DeBERTa-v3-base | Best accuracy/size ratio, SOTA on GLUE |
| Architecture | Multi-task joint | Shared encoder, efficient inference |
| Tool Output | Multi-label sigmoid | Tools are independent |
| Intent Output | Per-tool softmax heads | Intents are tool-specific |
| NER Output | Token classification | Standard, stable, 98%+ F1 |
| Training | 3-stage curriculum | Gradual task introduction |
| Loss | Equally weighted | Tasks naturally balance |
