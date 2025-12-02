"""Debug - detailed token-level analysis."""
import json
import torch
import torch.nn as nn
from pathlib import Path
from transformers import DebertaV2TokenizerFast, DebertaV2Model, DebertaV2PreTrainedModel, AutoConfig

MODEL_PATH = Path('models/two_stage_joint')

with open(MODEL_PATH / 'label_mappings.json') as f:
    mappings = json.load(f)
idx_to_tag = {int(k): v for k, v in mappings['idx_to_tag'].items()}

class TwoStageJointModel(DebertaV2PreTrainedModel):
    def __init__(self, config, num_tools=3, num_ner_tags=25, 
                 num_character_intents=10, num_session_intents=20, num_rulebook_intents=30):
        super().__init__(config)
        self.deberta = DebertaV2Model(config)
        classifier_dropout = config.classifier_dropout if hasattr(config, 'classifier_dropout') else 0.1
        self.dropout = nn.Dropout(classifier_dropout)
        self.tool_classifier = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size), nn.GELU(), 
            nn.Dropout(classifier_dropout), nn.Linear(config.hidden_size, num_tools))
        self.ner_classifier = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size // 2), nn.GELU(),
            nn.Dropout(classifier_dropout), nn.Linear(config.hidden_size // 2, num_ner_tags))
        self.character_intent_head = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size // 2), nn.GELU(),
            nn.Dropout(classifier_dropout), nn.Linear(config.hidden_size // 2, num_character_intents))
        self.session_intent_head = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size // 2), nn.GELU(),
            nn.Dropout(classifier_dropout), nn.Linear(config.hidden_size // 2, num_session_intents))
        self.rulebook_intent_head = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size // 2), nn.GELU(),
            nn.Dropout(classifier_dropout), nn.Linear(config.hidden_size // 2, num_rulebook_intents))
        self.post_init()
        
    def forward(self, input_ids=None, attention_mask=None, **kwargs):
        outputs = self.deberta(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state
        cls_output = self.dropout(sequence_output[:, 0, :])
        return {
            'tool_logits': self.tool_classifier(cls_output),
            'ner_logits': self.ner_classifier(sequence_output),
        }

print("Loading model...")
tokenizer = DebertaV2TokenizerFast.from_pretrained(MODEL_PATH)
config = AutoConfig.from_pretrained(MODEL_PATH)
model = TwoStageJointModel.from_pretrained(MODEL_PATH, config=config, num_tools=3, num_ner_tags=25, 
    num_character_intents=10, num_session_intents=20, num_rulebook_intents=30)
model.eval()

# Test query
text = "Bludgeoning vs Cold damage?"
print(f"\nQuery: {text}")
print("="*60)

encoding = tokenizer(text, max_length=128, padding='max_length', truncation=True, return_tensors='pt')

with torch.no_grad():
    outputs = model(encoding['input_ids'], encoding['attention_mask'])
    ner_logits = outputs['ner_logits'][0]

tokens = tokenizer.convert_ids_to_tokens(encoding['input_ids'][0])

print("\nToken-by-token analysis:")
print(f"{'Token':<15} {'Pred':<15} {'O logit':<10} {'B-* logit':<15} {'I-* logit':<15}")
print("-" * 70)

for i, (tok, logits) in enumerate(zip(tokens[:15], ner_logits[:15])):
    if tok == '[PAD]':
        break
    
    pred_idx = logits.argmax().item()
    pred_tag = idx_to_tag[pred_idx]
    
    o_logit = logits[0].item()
    
    # Find highest B- and I- logits
    b_logits = {idx_to_tag[j]: logits[j].item() for j in range(len(logits)) if idx_to_tag[j].startswith('B-')}
    i_logits = {idx_to_tag[j]: logits[j].item() for j in range(len(logits)) if idx_to_tag[j].startswith('I-')}
    
    max_b = max(b_logits.items(), key=lambda x: x[1])
    max_i = max(i_logits.items(), key=lambda x: x[1])
    
    print(f"{tok:<15} {pred_tag:<15} {o_logit:<10.2f} {max_b[0]}: {max_b[1]:<6.2f}   {max_i[0]}: {max_i[1]:<6.2f}")
