"""
Test local inference with the trained Two-Stage Joint Model.
Combines neural tool/intent classification with gazetteer-based NER.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import torch
import torch.nn as nn
from transformers import DebertaV2TokenizerFast, DebertaV2Model, DebertaV2PreTrainedModel

# Import gazetteer NER
from scripts.gazetteer_ner import GazetteerEntityExtractor

MODEL_PATH = project_root / "models" / "two_stage_joint"
SRD_CACHE_PATH = project_root / "data" / "srd_cache"


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
    """Inference wrapper for the Two-Stage Joint Model with Gazetteer NER."""
    
    def __init__(self, model_path, device='auto', use_gazetteer_ner=True):
        if device == 'auto':
            if torch.cuda.is_available():
                self.device = torch.device('cuda')
            elif torch.backends.mps.is_available():
                self.device = torch.device('mps')
            else:
                self.device = torch.device('cpu')
        else:
            self.device = torch.device(device)
        
        print(f"Using device: {self.device}")
        
        model_path = Path(model_path)
        
        # Load mappings
        with open(model_path / 'label_mappings.json') as f:
            self.mappings = json.load(f)
        
        self.tools = list(self.mappings['tool_to_idx'].keys())
        self.idx_to_tag = {int(k): v for k, v in self.mappings['idx_to_tag'].items()}
        self.idx_to_intent_per_tool = self.mappings['idx_to_intent_per_tool']
        
        # Load config
        with open(model_path / 'training_config.json') as f:
            self.config = json.load(f)
        
        # Load model
        print("Loading tokenizer...")
        self.tokenizer = DebertaV2TokenizerFast.from_pretrained(model_path)
        
        print("Loading model...")
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
        print("Model loaded successfully!")
        
        # Load gazetteer NER
        self.use_gazetteer_ner = use_gazetteer_ner
        if use_gazetteer_ner and SRD_CACHE_PATH.exists():
            print("Loading gazetteer NER...")
            self.gazetteer_ner = GazetteerEntityExtractor(SRD_CACHE_PATH, min_similarity=0.80)
        else:
            self.gazetteer_ner = None
            if use_gazetteer_ner:
                print("Warning: SRD cache not found, gazetteer NER disabled")
    
    def predict(self, text, include_neural_ner=False):
        """
        Run inference on a query.
        
        Args:
            text: The query text
            include_neural_ner: Also include neural NER results (for comparison)
        """
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
        tool_confidences = {self.tools[i]: float(p) for i, p in enumerate(tool_probs)}
        
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
        
        # Entities - prefer gazetteer NER
        if self.use_gazetteer_ner and self.gazetteer_ner:
            entities = self.gazetteer_ner.extract_simple(text)
        else:
            # Fall back to neural NER
            ner_preds = self.model.decode_ner(outputs['ner_logits'], attention_mask)[0]
            entities = self._extract_entities(input_ids[0], ner_preds)
        
        result = {
            'query': text,
            'tools': predicted_tools,
            'tool_confidences': tool_confidences,
            'intents': intents,
            'entities': entities
        }
        
        # Optionally include neural NER for comparison
        if include_neural_ner:
            ner_preds = self.model.decode_ner(outputs['ner_logits'], attention_mask)[0]
            result['neural_entities'] = self._extract_entities(input_ids[0], ner_preds)
        
        return result
    
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


def main():
    print("=" * 60)
    print("Two-Stage Joint Model - Local Inference Test")
    print("=" * 60)
    
    # Load model
    inference = TwoStageInference(MODEL_PATH)
    
    # Test queries
    test_queries = [
        "What is my armor class?",
        "How does Fireball work?",
        "What happened in the last session with the dragon?",
        "What's my AC and how does the Shield spell affect it?",
        "Can my half-orc fighter use Thunderwave while raging?",
        "What did the shopkeeper say about the cursed sword?",
        "List my inventory",
        "Explain how sneak attack damage works for rogues",
    ]
    
    print("\n" + "-" * 60)
    print("Running inference on test queries...")
    print("-" * 60)
    
    for query in test_queries:
        print(f"\n📝 Query: \"{query}\"")
        result = inference.predict(query)
        
        print(f"   🔧 Tools: {result['tools']}")
        print(f"   🎯 Intents: {result['intents']}")
        
        # Format entities nicely
        if result['entities']:
            ent_strs = []
            for e in result['entities']:
                conf = f" ({e['confidence']:.0%})" if e['confidence'] < 1.0 else ""
                canon = f"→{e['canonical']}" if e['text'].lower() != e['canonical'].lower() else ""
                ent_strs.append(f"{e['text']}:{e['type']}{canon}{conf}")
            print(f"   🏷️  Entities: {', '.join(ent_strs)}")
        else:
            print(f"   🏷️  Entities: (none)")
        
        print(f"   📊 Tool Confidences: {', '.join(f'{k}={v:.2f}' for k, v in result['tool_confidences'].items())}")
    
    # Interactive mode
    print("\n" + "=" * 60)
    print("Interactive Mode (type 'quit' to exit)")
    print("=" * 60)
    
    while True:
        try:
            query = input("\n🎮 Enter query: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            if not query:
                continue
                
            result = inference.predict(query)
            print(f"   🔧 Tools: {result['tools']}")
            print(f"   🎯 Intents: {result['intents']}")
            
            # Format entities nicely
            if result['entities']:
                ent_strs = []
                for e in result['entities']:
                    conf = f" ({e['confidence']:.0%})" if e['confidence'] < 1.0 else ""
                    canon = f"→{e['canonical']}" if e['text'].lower() != e['canonical'].lower() else ""
                    ent_strs.append(f"{e['text']}:{e['type']}{canon}{conf}")
                print(f"   🏷️  Entities: {', '.join(ent_strs)}")
            else:
                print(f"   🏷️  Entities: (none)")
            
        except KeyboardInterrupt:
            break
    
    print("\nGoodbye!")


if __name__ == "__main__":
    main()
