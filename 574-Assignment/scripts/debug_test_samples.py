"""Debug - test on actual samples from test set."""
import json
import torch
import torch.nn as nn
from pathlib import Path
from transformers import DebertaV2TokenizerFast, DebertaV2Model, DebertaV2PreTrainedModel, AutoConfig

MODEL_PATH = Path('models/two_stage_joint')
DATA_PATH = Path('data/generated')

with open(MODEL_PATH / 'label_mappings.json') as f:
    mappings = json.load(f)
idx_to_tag = {int(k): v for k, v in mappings['idx_to_tag'].items()}
TAG_TO_IDX = mappings['tag_to_idx']

# Load test data
test_data = json.load(open(DATA_PATH / 'test.json'))

# Model
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

# Test on actual test samples
print("\n" + "="*70)
print("Testing on ACTUAL test set samples")
print("="*70)

# Find samples with entities
test_samples_with_entities = [s for s in test_data if any(t != 'O' for t in s['bio_tags'])][:5]

for sample in test_samples_with_entities:
    text = sample['query']
    expected_bio = sample['bio_tags']
    expected_entities = sample['entities']
    
    encoding = tokenizer(text, max_length=128, padding='max_length', truncation=True, return_tensors='pt')
    
    with torch.no_grad():
        outputs = model(encoding['input_ids'], encoding['attention_mask'])
        ner_preds = outputs['ner_logits'].argmax(dim=-1)[0].tolist()
    
    tokens = tokenizer.convert_ids_to_tokens(encoding['input_ids'][0])
    
    print(f"\nQuery: {text}")
    print(f"Expected entities: {[e['text'] + ':' + e['type'] for e in expected_entities]}")
    
    # Find predicted entities
    pred_entities = []
    for tok, pred in zip(tokens, ner_preds):
        if tok in ['[CLS]', '[SEP]', '[PAD]', '<pad>']:
            continue
        tag = idx_to_tag[pred]
        if tag != 'O':
            pred_entities.append((tok.replace('▁', ''), tag))
    
    if pred_entities:
        print(f"Predicted: {pred_entities}")
    else:
        print(f"Predicted: NONE (all O)")
