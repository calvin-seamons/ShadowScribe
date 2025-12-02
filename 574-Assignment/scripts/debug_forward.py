"""Debug - trace NER forward pass step by step."""
import json
import torch
import torch.nn as nn
from pathlib import Path
from transformers import DebertaV2TokenizerFast, DebertaV2Model, DebertaV2PreTrainedModel

MODEL_PATH = Path('models/two_stage_joint')

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
        
    def forward_debug(self, input_ids=None, attention_mask=None):
        """Debug forward pass with step-by-step output."""
        outputs = self.deberta(input_ids=input_ids, attention_mask=attention_mask)
        seq = outputs.last_hidden_state  # (1, seq_len, 768)
        
        print(f"1. DeBERTa output shape: {seq.shape}")
        print(f"   DeBERTa output mean/std: {seq.mean():.4f} / {seq.std():.4f}")
        
        # Step through NER classifier
        x = seq
        for i, layer in enumerate(self.ner_classifier):
            x = layer(x)
            print(f"2.{i}. After {layer.__class__.__name__}: shape={x.shape}, mean={x.mean():.4f}, std={x.std():.4f}")
        
        return x

print("Loading model...")
tokenizer = DebertaV2TokenizerFast.from_pretrained(MODEL_PATH)
model = TwoStageJointModel.from_pretrained(MODEL_PATH, num_tools=3, num_ner_tags=25, 
    num_character_intents=10, num_session_intents=20, num_rulebook_intents=30)
model.eval()

text = "Can Fireball target multiple creatures?"
encoding = tokenizer(text, max_length=128, padding='max_length', truncation=True, return_tensors='pt')

print(f"\nQuery: {text}")
print("="*60)

with torch.no_grad():
    ner_logits = model.forward_debug(encoding['input_ids'], encoding['attention_mask'])

print(f"\nFinal NER logits shape: {ner_logits.shape}")
print(f"\nPredictions for first 8 tokens:")
tokens = tokenizer.convert_ids_to_tokens(encoding['input_ids'][0])
for i, (tok, logits) in enumerate(zip(tokens[:8], ner_logits[0][:8])):
    pred = logits.argmax().item()
    print(f"  {tok:15} -> {idx_to_tag[pred]} (max logit: {logits.max():.4f}, O logit: {logits[0]:.4f})")
