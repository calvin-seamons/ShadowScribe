"""Debug - check if model weights are loaded correctly."""
import json
import torch
import torch.nn as nn
from pathlib import Path
from transformers import DebertaV2TokenizerFast, DebertaV2Model, DebertaV2PreTrainedModel
from safetensors import safe_open

MODEL_PATH = Path('models/two_stage_joint')

# Load saved weights directly
print("=== Saved Weights ===")
with safe_open(MODEL_PATH / 'model.safetensors', framework='pt') as f:
    saved_ner_weight = f.get_tensor('ner_classifier.0.weight')
    saved_ner_bias = f.get_tensor('ner_classifier.0.bias')
    print(f"ner_classifier.0.weight shape: {saved_ner_weight.shape}")
    print(f"ner_classifier.0.weight mean: {saved_ner_weight.mean():.6f}, std: {saved_ner_weight.std():.6f}")

# Define model class
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

# Load model
print("\n=== Loading Model ===")
model = TwoStageJointModel.from_pretrained(MODEL_PATH, num_tools=3, num_ner_tags=25, 
    num_character_intents=10, num_session_intents=20, num_rulebook_intents=30)

print(f"\n=== Loaded Weights ===")
loaded_ner_weight = model.ner_classifier[0].weight.data
loaded_ner_bias = model.ner_classifier[0].bias.data
print(f"ner_classifier.0.weight shape: {loaded_ner_weight.shape}")
print(f"ner_classifier.0.weight mean: {loaded_ner_weight.mean():.6f}, std: {loaded_ner_weight.std():.6f}")

# Check if they match
print(f"\n=== Comparison ===")
match = torch.allclose(saved_ner_weight, loaded_ner_weight)
print(f"Weights match: {match}")

if not match:
    diff = (saved_ner_weight - loaded_ner_weight).abs().max()
    print(f"Max difference: {diff:.6f}")
