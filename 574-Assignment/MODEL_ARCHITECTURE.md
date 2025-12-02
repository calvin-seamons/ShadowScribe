# Joint Sentence Classifier for D&D Query Understanding

## Project Overview

### ShadowScribe: An AI-Powered D&D Assistant

**ShadowScribe** is a comprehensive D&D/RPG character management and game assistant system. At its core is a **Retrieval-Augmented Generation (RAG)** pipeline that answers player questions by retrieving relevant context from three knowledge sources:

1. **Character Data** - The player's character sheet (stats, spells, inventory, backstory)
2. **Session Notes** - Campaign history, NPC interactions, past events
3. **Rulebook** - D&D 5e rules, spell descriptions, monster stats

### The Routing Problem

When a player asks a question like *"What's my AC and how does Fireball work?"*, the system must:

1. **Route the query** to the correct knowledge sources (character data + rulebook)
2. **Classify the intent** within each source (combat_info + spell_details)
3. **Extract entities** mentioned (Fireball → SPELL)

This routing decision is critical - sending a query to the wrong source wastes compute and produces irrelevant context.

---

## The Problem: LLM Routing is Expensive

### Original Architecture (LLM-Based Routing)

In the original ShadowScribe system, **every user query required a live API call** to an LLM (GPT-4 or Claude) just to decide where to route the query:

```
User Query → [LLM API Call] → Tool Selection + Intent Classification
                   ↓
            ~500-1000ms latency
            ~$0.01-0.03 per query
```

**Problems with LLM Routing:**
- **Latency**: 500-1000ms just for routing, before any actual retrieval
- **Cost**: $0.01-0.03 per query adds up with thousands of users
- **Reliability**: API rate limits, network issues, model updates
- **Overkill**: Routing is a classification task, not a generation task

### Solution: Local Sentence Classifier

Replace the LLM routing call with a **fine-tuned transformer model** that runs locally:

```
User Query → [Local DeBERTa Model] → Tool Selection + Intent Classification
                    ↓
             ~10-50ms latency
             $0 per query (after training)
```

This is fundamentally a **sentence transformer** approach: encode the full query into a dense vector, then use that representation for classification.

---

## Architecture

### Design Philosophy

The model uses DeBERTa-v3 as a **sentence encoder** - the entire query is encoded into a single [CLS] vector, which is then fed to classification heads. This is the core "sentence transformers" concept: represent a sentence as a fixed-size embedding for downstream tasks.

| Component | Purpose |
|-----------|---------|
| **Shared Encoder** | Encode query → 768-dim sentence embedding |
| **Tool Head** | Which RAG sources to query (3-class) |
| **Intent Heads** | What information is needed per source (10+20+30 classes) |

**Key Design Decision**: Entity extraction is handled separately by a **gazetteer-based system** at inference time, not by the neural model. This keeps the model focused on classification.

### Model Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         INPUT                                     │
│         "What's my AC and how does Fireball work?"               │
└─────────────────────────────┬────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    SHARED ENCODER                                 │
│                    DeBERTa-v3-base                                │
│                                                                   │
│    Full query → Transformer layers → [CLS] embedding (768d)      │
│                                                                   │
│    This IS the "sentence transformer" step: encode the full      │
│    sentence into a fixed-size vector representation              │
└──────────────────────────────┬────────────────────────────────────┘
                              ↓
                    [CLS] Token (768 dims)
                              ↓
         ┌────────────────────┴────────────────────┐
         ↓                                         ↓
┌─────────────────────┐                 ┌─────────────────────────┐
│   TOOL HEAD         │                 │   INTENT HEADS          │
│                     │                 │   (3 separate heads)    │
│  Linear(768→256)    │                 │                         │
│  GELU + Dropout     │                 │  character: 768→256→10  │
│  Linear(256→3)      │                 │  session:   768→256→20  │
│  Softmax            │                 │  rulebook:  768→256→30  │
│                     │                 │                         │
│  Output: tool probs │                 │  Output: intent probs   │
└─────────────────────┘                 └─────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                        FINAL OUTPUT                               │
│                                                                   │
│  {                                                                │
│    "tool": "character_data",                                     │
│    "tool_confidence": 0.95,                                      │
│    "intent": "combat_info",                                      │
│    "intent_confidence": 0.89                                     │
│  }                                                                │
└──────────────────────────────────────────────────────────────────┘
```

### Model Components

#### Shared Encoder (Sentence Embedding)
- **Model**: `microsoft/deberta-v3-base` (~86M params, 768 hidden dim)
- **Why DeBERTa**: State-of-the-art on GLUE/SuperGLUE benchmarks, disentangled attention mechanism
- **Output**: [CLS] token embedding as the **sentence representation**

#### Tool Classification Head
- **Input**: [CLS] embedding (768 dims)
- **Architecture**: `Linear(768→256) → GELU → Dropout → Linear(256→3)`
- **Activation**: Softmax (single tool per query in current implementation)
- **Output**: 3 class probabilities

#### Intent Classification Heads (3 separate)
- **Input**: [CLS] embedding (768 dims)
- **Architecture**: Same as tool head, different output sizes
  - `character_intent`: outputs 10 classes
  - `session_intent`: outputs 20 classes
  - `rulebook_intent`: outputs 30 classes
- **Gating**: Only the intent head for the predicted tool is used at inference

#### Temperature Scaling (Calibration)
- **Learned parameter** that scales logits before softmax
- Optimized post-training to minimize Expected Calibration Error (ECE)
- Ensures confidence scores are meaningful, not overconfident

---

## Synthetic Dataset Generation

### The Data Challenge

Training a classifier requires labeled data, but manually labeling thousands of D&D queries is impractical. Instead, we generate **synthetic training data** using template-based generation with entity slot-filling.

### Template-Based Generation

Each intent has 15-30 hand-crafted templates with placeholder slots:

```python
CHARACTER_BASICS_TEMPLATES = [
    {"template": "What is my character's race?", "slots": {}},
    {"template": "What's my {ability} score?", "slots": {"ability": "ability"}},
    {"template": "What level is {CHARACTER}?", "slots": {}},
    {"template": "Am I a {class_name}?", "slots": {"class_name": "class"}},
    ...
]
```

### Entity Gazetteers

Slots are filled from curated lists of D&D entities (gazetteers):

```python
SPELL_NAMES = ["Fireball", "Magic Missile", "Cure Wounds", ...]  # 300+ spells
CLASS_NAMES = ["Fighter", "Wizard", "Cleric", "Rogue", ...]      # 13 classes
CREATURE_NAMES = ["Beholder", "Dragon", "Goblin", ...]           # 500+ creatures
WEAPON_NAMES = ["Longsword", "Longbow", "Dagger", ...]           # 50+ weapons
...
```

### Preserved Placeholders

Some placeholders are **not** filled - they remain as literal tokens:
- `{CHARACTER}` - The player's character name
- `{PARTY_MEMBER}` - Another player's character
- `{NPC}` - A non-player character name

This teaches the model that these are **context-dependent** references, not fixed D&D entities.

### Data Augmentation

Each generated sample is augmented to increase robustness:

1. **Typo injection** (15% probability) - Simulate user typing errors
2. **Case variation** (30% probability) - MiXeD cAsE, lowercase, UPPERCASE
3. **Contractions** (20% probability) - "What is" → "What's"

### K-Expansion Strategy

Each template generates **K** samples with different entity fills:
- K = 10 expansions per template
- 3 augmentations per expansion
- Total: ~40 samples per template

### Dataset Statistics

| Split | Samples |
|-------|---------|
| Train | ~80% |
| Validation | ~10% |
| Test | ~10% |

**Intent Distribution:**
- 10 character intents (character_basics, combat_info, abilities_info, ...)
- 20 session intents (event_sequence, npc_info, combat_recap, ...)
- 30 rulebook intents (spell_details, monster_stats, combat_rules, ...)

---

## Training Strategy

### Two-Stage Training

Training proceeds in two stages with gradual unfreezing:

#### Stage 1: Tool Classification Only (Epochs 1-3)
- **Freeze** intent classification heads
- Train only tool head + encoder
- Focus: Learn to distinguish between character/session/rulebook queries

#### Stage 2: Joint Training (Epochs 4-14)
- **Unfreeze** all intent heads
- Train tool + intent heads together
- Early stopping on combined validation score

### Loss Function

**Focal Loss** with label smoothing, addressing class imbalance:

```python
# Focal Loss: FL(p_t) = -α_t * (1 - p_t)^γ * log(p_t)
focal_loss = FocalLoss(gamma=2.0, label_smoothing=0.1)

# Combined loss
total_loss = tool_loss + intent_loss
```

**Why Focal Loss?**
- γ=2.0 focusing parameter down-weights easy examples
- Automatically addresses class imbalance without explicit weighting
- Label smoothing (0.1) improves calibration

### Masked Intent Loss

Intent loss is only computed for the **ground-truth tool**:

```python
for tool_name in ['character_data', 'session_notes', 'rulebook']:
    mask = intent_labels[tool_name] != -100  # -100 = ignore
    if mask.any():
        loss += focal_loss(intent_logits[tool_name][mask], intent_targets[mask])
```

### Differential Learning Rates

- **Encoder (DeBERTa)**: 1e-5 (preserve pretrained knowledge)
- **Classification Heads**: 1e-4 (learn task-specific patterns faster)

### Hyperparameters

| Parameter | Value |
|-----------|-------|
| Encoder | `microsoft/deberta-v3-base` |
| Batch Size | 32 |
| Max Sequence Length | 128 |
| Encoder Learning Rate | 1e-5 |
| Head Learning Rate | 1e-4 |
| Weight Decay | 0.01 |
| Warmup Ratio | 10% |
| Stage 1 Epochs | 3 |
| Stage 2 Epochs | 11 |
| Early Stopping Patience | 3 |
| Focal γ | 2.0 |
| Label Smoothing | 0.1 |

---

## Calibration: Temperature Scaling

### The Problem: Overconfident Predictions

Neural networks are often **overconfident** - they output 99% probability even when wrong. This is problematic for routing decisions where we might want to query multiple sources if confidence is low.

### Solution: Post-Training Temperature Scaling

After training, optimize a single **temperature parameter** T on the validation set:

```python
calibrated_probs = softmax(logits / T)
```

The optimal T is found by minimizing **Negative Log-Likelihood**:

```python
def nll_with_temperature(T):
    scaled_logits = logits / T
    log_probs = F.log_softmax(scaled_logits, dim=-1)
    return F.nll_loss(log_probs, labels)

optimal_T = minimize_scalar(nll_with_temperature, bounds=(0.1, 5.0))
```

### Expected Calibration Error (ECE)

Measures how well confidence matches accuracy:

```
ECE = Σ |accuracy(bin) - confidence(bin)| × proportion(bin)
```

A well-calibrated model has ECE close to 0.

---

## Entity Extraction: Gazetteer Approach

### Why Not Neural NER?

The original architecture planned a neural NER head, but this was **replaced** with a gazetteer-based approach:

| Neural NER | Gazetteer |
|------------|-----------|
| Requires labeled entity spans | Uses existing D&D entity lists |
| Subword alignment complexity | Simple string matching |
| May hallucinate entities | Only matches known entities |
| Requires retraining for new entities | Just add to gazetteer |

### Gazetteer Entity Extractor

At inference time, a separate `GazetteerEntityExtractor` identifies D&D entities:

```python
class GazetteerEntityExtractor:
    """Fuzzy matching against D&D entity gazetteers."""
    
    def extract(self, query: str) -> List[Entity]:
        # Match against spell names, creature names, etc.
        # Uses fuzzy matching to handle typos
        ...
```

This runs **in parallel** with the classifier, keeping concerns separate.

---

## Inference Pipeline

### Full Flow

```
1. Input: "What level is Duskryn?"

2. Name Normalization (external):
   → "What level is {CHARACTER}?"

3. Tokenization:
   → DeBERTa tokenizer → input_ids, attention_mask

4. Sentence Encoding:
   → DeBERTa forward pass → [CLS] embedding (768d)

5. Tool Classification:
   → tool_head([CLS]) → softmax/T → "character_data" (0.95)

6. Intent Classification:
   → character_intent_head([CLS]) → softmax/T → "character_basics" (0.91)

7. Output:
   {
     "tool": "character_data",
     "tool_confidence": 0.95,
     "intent": "character_basics", 
     "intent_confidence": 0.91,
     "combined_confidence": 0.86
   }
```

### Integration with ShadowScribe

The local classifier implements the `ClassifierBackend` protocol:

```python
class ClassifierBackend(Protocol):
    async def classify(
        self,
        query: str,
        character_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> ClassificationResult:
        ...
```

This allows **hot-swapping** between LLM and local classifiers.

---

## Evaluation Metrics

### Tool Classification
- **Accuracy**: Exact match on tool prediction
- **F1 (macro)**: Balanced across all 3 tools

### Intent Classification
- **Per-tool accuracy**: Accuracy within each tool's intent space
- **Average intent accuracy**: Mean across all tools

### Combined Score

```python
combined_score = 0.4 * tool_accuracy + 0.6 * avg_intent_accuracy
```

Intent accuracy weighted higher because it's the harder task.

### Calibration
- **ECE (before/after)**: Expected Calibration Error
- **Temperature**: Optimal calibration parameter

---

## Results Summary

After training with the configuration above:

| Metric | Target | Notes |
|--------|--------|-------|
| Tool Accuracy | >95% | High priority - wrong tool = irrelevant context |
| Intent Accuracy | >85% | Per-tool, harder task with more classes |
| Combined Score | >90% | Primary optimization target |
| ECE (calibrated) | <0.05 | Trustworthy confidence scores |

---

## Artifacts & Deployment

### Saved Artifacts

```
results/
├── model/
│   ├── joint_classifier.pt     # Model weights + temperature
│   ├── tokenizer/              # DeBERTa tokenizer
│   └── label_mappings.json     # Tool/intent indices
├── training_history.json       # Metrics per epoch
├── training_history.png        # Visualization
└── test_results.json           # Final test metrics
```

### Loading for Inference

```python
# Load model
checkpoint = torch.load('joint_classifier.pt')
model.load_state_dict(checkpoint['model_state_dict'])
model.temperature.data = torch.tensor(checkpoint['temperature'])

# Load label mappings
with open('label_mappings.json') as f:
    mappings = json.load(f)
```

---

## Comparison: LLM vs Local Classifier

| Aspect | LLM Routing | Local Classifier |
|--------|-------------|------------------|
| **Latency** | 500-1000ms | 10-50ms |
| **Cost per query** | $0.01-0.03 | $0 |
| **Reliability** | API-dependent | Local, always available |
| **Flexibility** | Can handle novel queries | Limited to trained patterns |
| **Maintenance** | None | Requires retraining for new intents |
| **Accuracy** | ~95-98% | ~90-95% |

### Hybrid Approach

The system supports **comparison logging** to run both classifiers and log disagreements:

```python
if config.comparison_logging:
    llm_result = await llm_classifier.classify(query)
    local_result = await local_classifier.classify(query)
    log_comparison(llm_result, local_result)
```

This enables continuous evaluation and model improvement.

---

## Future Improvements

1. **Multi-tool classification**: Current model predicts single tool; extend to multi-label
2. **Conversation history**: Incorporate prior turns for context-aware routing
3. **Active learning**: Use disagreements between LLM and local classifier to identify training gaps
4. **Quantization**: INT8/FP16 for faster inference on CPU
5. **ONNX export**: For deployment without PyTorch dependency
