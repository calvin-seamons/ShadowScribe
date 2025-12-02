"""Debug NER predictions - compare training samples vs novel queries."""
import json
import torch
import torch.nn as nn
from pathlib import Path
from transformers import DebertaV2TokenizerFast, DebertaV2Model, DebertaV2PreTrainedModel

MODEL_PATH = Path('models/two_stage_joint')

# Load mappings
with open(MODEL_PATH / 'label_mappings.json') as f:
    mappings = json.load(f)
idx_to_tag = {int(k): v for k, v in mappings['idx_to_tag'].items()}

class TwoStageJointModel(DebertaV2PreTrainedModel):
    def __init__(self, config, num_tools=3, num_ner_tags=25, 
                 num_character_intents=10, num_session_intents=20, num_rulebook_intents=30):
        super().__init__(config)
        self.deberta = DebertaV2Model(config)
        dropout = config.classifier_dropout if hasattr(config, 'classifier_dropout') else 0.1
        self.dropout = nn.Dropout(dropout)
        self.tool_classifier = nn.Sequential(nn.Linear(768, 768), nn.GELU(), nn.Dropout(dropout), nn.Linear(768, num_tools))
        self.ner_classifier = nn.Sequential(nn.Linear(768, 384), nn.GELU(), nn.Dropout(dropout), nn.Linear(384, num_ner_tags))
        self.character_intent_head = nn.Sequential(nn.Linear(768, 384), nn.GELU(), nn.Dropout(dropout), nn.Linear(384, num_character_intents))
        self.session_intent_head = nn.Sequential(nn.Linear(768, 384), nn.GELU(), nn.Dropout(dropout), nn.Linear(384, num_session_intents))
        self.rulebook_intent_head = nn.Sequential(nn.Linear(768, 384), nn.GELU(), nn.Dropout(dropout), nn.Linear(384, num_rulebook_intents))
        self.post_init()
    def forward(self, input_ids=None, attention_mask=None, **kwargs):
        outputs = self.deberta(input_ids=input_ids, attention_mask=attention_mask)
        seq = outputs.last_hidden_state
        cls = self.dropout(seq[:, 0, :])
        return {'tool_logits': self.tool_classifier(cls), 'ner_logits': self.ner_classifier(seq)}

print("Loading model...")
tokenizer = DebertaV2TokenizerFast.from_pretrained(MODEL_PATH)
model = TwoStageJointModel.from_pretrained(MODEL_PATH, num_tools=3, num_ner_tags=25, 
    num_character_intents=10, num_session_intents=20, num_rulebook_intents=30)
model.eval()

# Test on EXACT training samples vs novel queries
test_queries = [
    # FROM TRAINING DATA (should work)
    ("Can Fireball target multiple creatures?", "TRAINING"),
    ("Can I twin Fireball?", "TRAINING"),
    ("Which is better, Rogue or Sorcerer?", "TRAINING"),
    
    # NOVEL QUERIES (might not work)
    ("How does Fireball work?", "NOVEL"),
    ("Tell me about the Rogue class", "NOVEL"),
    ("What is a Longsword?", "NOVEL"),
]

print("\n" + "="*60)
print("Testing NER on training samples vs novel queries")
print("="*60)

for text, source in test_queries:
    encoding = tokenizer(text, max_length=128, padding='max_length', truncation=True, return_tensors='pt')
    
    with torch.no_grad():
        outputs = model(**encoding)
        ner_preds = outputs['ner_logits'].argmax(dim=-1)[0].tolist()
    
    tokens = tokenizer.convert_ids_to_tokens(encoding['input_ids'][0])
    
    # Find entities
    entities = []
    for tok, pred in zip(tokens, ner_preds):
        if tok in ['[PAD]', '<pad>', '[CLS]', '[SEP]']:
            continue
        tag = idx_to_tag[pred]
        if tag != 'O':
            entities.append((tok.replace('▁', ''), tag))
    
    print(f"\n[{source}] {text}")
    if entities:
        print(f"  ✓ Entities: {entities}")
    else:
        print(f"  ✗ No entities detected")
