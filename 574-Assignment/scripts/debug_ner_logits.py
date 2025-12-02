"""Debug NER - check if model is predicting almost all O."""
import json
import torch
import torch.nn as nn
from pathlib import Path
from transformers import DebertaV2TokenizerFast, DebertaV2Model, DebertaV2PreTrainedModel
from collections import Counter

MODEL_PATH = Path('models/two_stage_joint')

with open(MODEL_PATH / 'label_mappings.json') as f:
    mappings = json.load(f)
idx_to_tag = {int(k): v for k, v in mappings['idx_to_tag'].items()}
tag_to_idx = mappings['tag_to_idx']

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

text = "Can Fireball target multiple creatures?"

encoding = tokenizer(text, max_length=128, padding='max_length', truncation=True, return_tensors='pt')

with torch.no_grad():
    outputs = model(**encoding)
    ner_logits = outputs['ner_logits'][0]  # (seq_len, num_tags)

tokens = tokenizer.convert_ids_to_tokens(encoding['input_ids'][0])

print(f"\nQuery: {text}")
print(f"Tokens: {[t for t in tokens if t not in ['[PAD]', '<pad>']]}")
print()

# Look at the logits for each token
print("NER Logits Analysis (first 10 tokens):")
for i, (tok, logits) in enumerate(zip(tokens[:10], ner_logits[:10])):
    probs = torch.softmax(logits, dim=0)
    top3_idx = torch.topk(probs, 3).indices.tolist()
    top3_probs = torch.topk(probs, 3).values.tolist()
    
    pred_tag = idx_to_tag[logits.argmax().item()]
    
    print(f"  {tok:15} -> {pred_tag:10}")
    print(f"     Top3: {[(idx_to_tag[i], f'{p:.3f}') for i, p in zip(top3_idx, top3_probs)]}")

# Check the output bias
print("\n\nNER Classifier Output Bias (last layer):")
bias = model.ner_classifier[3].bias.data
print(f"  O tag bias: {bias[tag_to_idx['O']].item():.4f}")
print(f"  B-SPELL bias: {bias[tag_to_idx['B-SPELL']].item():.4f}")
print(f"  B-CLASS bias: {bias[tag_to_idx['B-CLASS']].item():.4f}")
print(f"  B-ITEM bias: {bias[tag_to_idx['B-ITEM']].item():.4f}")
