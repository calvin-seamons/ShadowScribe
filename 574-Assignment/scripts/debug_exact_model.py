"""Debug - use EXACT model architecture from notebook."""
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path
from transformers import DebertaV2TokenizerFast, DebertaV2Model, DebertaV2PreTrainedModel, AutoConfig

MODEL_PATH = Path('models/two_stage_joint')

with open(MODEL_PATH / 'label_mappings.json') as f:
    mappings = json.load(f)
idx_to_tag = {int(k): v for k, v in mappings['idx_to_tag'].items()}

# EXACT model from notebook
class TwoStageJointModel(DebertaV2PreTrainedModel):
    """
    Two-Stage Joint DeBERTa-v3 Model - EXACT COPY from notebook
    """
    
    def __init__(self, config, num_tools=3, num_ner_tags=25, 
                 num_character_intents=10, num_session_intents=20, num_rulebook_intents=30):
        super().__init__(config)
        
        self.num_tools = num_tools
        self.num_ner_tags = num_ner_tags
        self.num_character_intents = num_character_intents
        self.num_session_intents = num_session_intents
        self.num_rulebook_intents = num_rulebook_intents
        
        # Shared encoder
        self.deberta = DebertaV2Model(config)
        
        # Dropout
        classifier_dropout = (
            config.classifier_dropout 
            if hasattr(config, 'classifier_dropout') and config.classifier_dropout is not None
            else config.hidden_dropout_prob
        )
        self.dropout = nn.Dropout(classifier_dropout)
        
        # ========== STAGE 1 HEADS ==========
        # Tool classification head (multi-label with sigmoid)
        self.tool_classifier = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size),
            nn.GELU(),
            nn.Dropout(classifier_dropout),
            nn.Linear(config.hidden_size, num_tools)
        )
        
        # NER head (standard token classification, no CRF for stability)
        self.ner_classifier = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size // 2),
            nn.GELU(),
            nn.Dropout(classifier_dropout),
            nn.Linear(config.hidden_size // 2, num_ner_tags)
        )
        
        # ========== STAGE 2 HEADS (Per-Tool Intent) ==========
        self.character_intent_head = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size // 2),
            nn.GELU(),
            nn.Dropout(classifier_dropout),
            nn.Linear(config.hidden_size // 2, num_character_intents)
        )
        
        self.session_intent_head = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size // 2),
            nn.GELU(),
            nn.Dropout(classifier_dropout),
            nn.Linear(config.hidden_size // 2, num_session_intents)
        )
        
        self.rulebook_intent_head = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size // 2),
            nn.GELU(),
            nn.Dropout(classifier_dropout),
            nn.Linear(config.hidden_size // 2, num_rulebook_intents)
        )
        
        # Initialize weights
        self.post_init()
        
    def forward(
        self,
        input_ids=None,
        attention_mask=None,
        stage='all',
        **kwargs
    ):
        # Get encoder outputs (shared for both stages)
        outputs = self.deberta(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        
        sequence_output = outputs.last_hidden_state  # (batch, seq_len, hidden)
        cls_output = sequence_output[:, 0, :]  # (batch, hidden)
        cls_output = self.dropout(cls_output)
        
        # ========== STAGE 1: Tools + NER ==========
        tool_logits = self.tool_classifier(cls_output)  # (batch, num_tools)
        ner_logits = self.ner_classifier(sequence_output)  # (batch, seq_len, num_tags)
        
        return {
            'tool_logits': tool_logits,
            'ner_logits': ner_logits,
        }

print("Loading model with EXACT architecture from notebook...")
tokenizer = DebertaV2TokenizerFast.from_pretrained(MODEL_PATH)
config = AutoConfig.from_pretrained(MODEL_PATH)
model = TwoStageJointModel.from_pretrained(
    MODEL_PATH,
    config=config,
    num_tools=3, 
    num_ner_tags=25, 
    num_character_intents=10, 
    num_session_intents=20, 
    num_rulebook_intents=30
)
model.eval()

# Test
text = "Can Fireball target multiple creatures?"
encoding = tokenizer(text, max_length=128, padding='max_length', truncation=True, return_tensors='pt')

with torch.no_grad():
    outputs = model(encoding['input_ids'], encoding['attention_mask'])
    ner_logits = outputs['ner_logits'][0]

tokens = tokenizer.convert_ids_to_tokens(encoding['input_ids'][0])

print(f"\nQuery: {text}")
print("\nPredictions:")
for i, (tok, logits) in enumerate(zip(tokens[:10], ner_logits[:10])):
    if tok in ['[PAD]', '<pad>']:
        break
    pred = logits.argmax().item()
    tag = idx_to_tag[pred]
    o_logit = logits[0].item()
    max_logit = logits.max().item()
    
    marker = " <-- ENTITY" if tag != 'O' else ""
    print(f"  {tok:15} -> {tag:12} (O: {o_logit:.2f}, max: {max_logit:.2f}){marker}")
