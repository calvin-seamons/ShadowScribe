"""
Two-Stage Joint DeBERTa Model - Inference Module

Usage:
    from inference import TwoStageInference
    
    model = TwoStageInference("path/to/model")
    result = model.predict("What's my AC and how does Fireball work?")
    print(result)
"""

import json
import torch
import torch.nn as nn
from transformers import DebertaV2TokenizerFast, DebertaV2Model, DebertaV2PreTrainedModel


class TwoStageJointModel(DebertaV2PreTrainedModel):
    """Two-Stage Joint DeBERTa-v3 Model."""
    
    def __init__(self, config, num_tools=3, num_ner_tags=25, 
                 num_character_intents=10, num_session_intents=20, num_rulebook_intents=30):
        super().__init__(config)
        
        self.num_tools = num_tools
        self.num_ner_tags = num_ner_tags
        self.num_character_intents = num_character_intents
        self.num_session_intents = num_session_intents
        self.num_rulebook_intents = num_rulebook_intents
        
        self.deberta = DebertaV2Model(config)
        
        classifier_dropout = (
            config.classifier_dropout 
            if hasattr(config, 'classifier_dropout') and config.classifier_dropout is not None
            else config.hidden_dropout_prob
        )
        self.dropout = nn.Dropout(classifier_dropout)
        
        # Stage 1 heads
        self.tool_classifier = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size),
            nn.GELU(),
            nn.Dropout(classifier_dropout),
            nn.Linear(config.hidden_size, num_tools)
        )
        
        self.ner_classifier = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size // 2),
            nn.GELU(),
            nn.Dropout(classifier_dropout),
            nn.Linear(config.hidden_size // 2, num_ner_tags)
        )
        
        # Stage 2 heads
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
        
        self.post_init()
        
    def forward(self, input_ids=None, attention_mask=None, **kwargs):
        outputs = self.deberta(input_ids=input_ids, attention_mask=attention_mask)
        
        sequence_output = outputs.last_hidden_state
        cls_output = self.dropout(sequence_output[:, 0, :])
        
        return {
            'tool_logits': self.tool_classifier(cls_output),
            'ner_logits': self.ner_classifier(sequence_output),
            'character_intent_logits': self.character_intent_head(cls_output),
            'session_intent_logits': self.session_intent_head(cls_output),
            'rulebook_intent_logits': self.rulebook_intent_head(cls_output),
        }
    
    def decode_ner(self, ner_logits, attention_mask):
        """Decode NER predictions using argmax."""
        return ner_logits.argmax(dim=-1).tolist()


class TwoStageInference:
    """Inference wrapper for the Two-Stage Joint Model."""
    
    def __init__(self, model_path, device='cuda'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        # Load mappings
        with open(f'{model_path}/label_mappings.json') as f:
            self.mappings = json.load(f)
        
        self.tools = list(self.mappings['tool_to_idx'].keys())
        self.idx_to_tag = {int(k): v for k, v in self.mappings['idx_to_tag'].items()}
        self.idx_to_intent_per_tool = self.mappings['idx_to_intent_per_tool']
        
        # Load config
        with open(f'{model_path}/training_config.json') as f:
            self.config = json.load(f)
        
        # Load model
        self.tokenizer = DebertaV2TokenizerFast.from_pretrained(model_path)
        self.model = TwoStageJointModel.from_pretrained(
            model_path,
            num_tools=len(self.tools),
            num_ner_tags=len(self.mappings['tag_to_idx']),
            num_character_intents=self.mappings['num_intents_per_tool']['character_data'],
            num_session_intents=self.mappings['num_intents_per_tool']['session_notes'],
            num_rulebook_intents=self.mappings['num_intents_per_tool']['rulebook']
        )
        self.model.to(self.device)
        self.model.eval()
    
    def predict(self, text):
        """Run inference on a query."""
        encoding = self.tokenizer(
            text,
            max_length=self.config['max_length'],
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
        
        # Tools
        tool_probs = torch.sigmoid(outputs['tool_logits']).cpu().numpy()[0]
        predicted_tools = [self.tools[i] for i, p in enumerate(tool_probs) if p > 0.5]
        
        # Intents (per selected tool)
        intents = {}
        if 'character_data' in predicted_tools:
            idx = outputs['character_intent_logits'].argmax(dim=-1).item()
            intents['character_data'] = self.idx_to_intent_per_tool['character_data'][str(idx)]
        if 'session_notes' in predicted_tools:
            idx = outputs['session_intent_logits'].argmax(dim=-1).item()
            intents['session_notes'] = self.idx_to_intent_per_tool['session_notes'][str(idx)]
        if 'rulebook' in predicted_tools:
            idx = outputs['rulebook_intent_logits'].argmax(dim=-1).item()
            intents['rulebook'] = self.idx_to_intent_per_tool['rulebook'][str(idx)]
        
        # Entities
        ner_preds = self.model.decode_ner(outputs['ner_logits'], attention_mask)[0]
        entities = self._extract_entities(input_ids[0], ner_preds)
        
        return {
            'tools': predicted_tools,
            'intents': intents,
            'entities': entities
        }
    
    def _extract_entities(self, input_ids, ner_preds):
        tokens = self.tokenizer.convert_ids_to_tokens(input_ids)
        entities = []
        current_entity = None
        current_type = None
        
        for token, tag_idx in zip(tokens, ner_preds):
            if token in ['[CLS]', '[SEP]', '[PAD]', '<s>', '</s>', '<pad>']:
                continue
            
            tag = self.idx_to_tag[tag_idx]
            
            if tag.startswith('B-'):
                if current_entity:
                    entities.append({'text': current_entity.strip(), 'type': current_type})
                current_entity = token.replace('▁', ' ').replace('##', '')
                current_type = tag[2:]
            elif tag.startswith('I-') and current_type == tag[2:]:
                current_entity += token.replace('▁', ' ').replace('##', '')
            else:
                if current_entity:
                    entities.append({'text': current_entity.strip(), 'type': current_type})
                current_entity = None
                current_type = None
        
        if current_entity:
            entities.append({'text': current_entity.strip(), 'type': current_type})
        
        return entities


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python inference.py 'Your query here'")
        sys.exit(1)
    
    model = TwoStageInference(".")
    result = model.predict(sys.argv[1])
    print(json.dumps(result, indent=2))
