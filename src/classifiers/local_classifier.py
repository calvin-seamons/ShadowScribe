"""
Local Joint Classifier for Tool + Intent Classification.

Uses a trained DeBERTa-v3 model with:
- Tool classification head (3 classes: character_data, session_notes, rulebook)
- Per-tool intent heads (10, 20, 30 intents respectively)
- Temperature scaling for calibrated confidence scores
- Name normalization to align runtime queries with placeholder-based training data

The model was trained on templates with {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholders.
At inference, we normalize actual names to these placeholders before classification.
"""

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import DebertaV2TokenizerFast, DebertaV2Model, DebertaV2PreTrainedModel, AutoConfig

from .base import ClassificationResult
from .gazetteer_ner import GazetteerEntityExtractor


@dataclass
class SingleClassificationResult:
    """Result from classifying a single query."""
    tool: str
    tool_confidence: float
    intent: str
    intent_confidence: float
    normalized_query: str
    combined_confidence: float


class JointClassifier(DebertaV2PreTrainedModel):
    """
    Joint Tool + Intent Classifier using DeBERTa-v3.
    
    Architecture matches the trained model:
    - Shared DeBERTa encoder
    - Tool classification head (3 classes)
    - Per-tool intent heads (character: 10, session: 20, rulebook: 30)
    - Learnable temperature parameter for confidence calibration
    """
    
    def __init__(self, config, num_tools=3,
                 num_character_intents=10,
                 num_session_intents=20,
                 num_rulebook_intents=30):
        super().__init__(config)
        
        self.num_tools = num_tools
        self.num_character_intents = num_character_intents
        self.num_session_intents = num_session_intents
        self.num_rulebook_intents = num_rulebook_intents
        
        # Shared encoder
        self.deberta = DebertaV2Model(config)
        
        # Dropout
        classifier_dropout = getattr(config, 'classifier_dropout', 0.1)
        self.dropout = nn.Dropout(classifier_dropout)
        
        # Learnable temperature for calibration (scalar)
        self.temperature = nn.Parameter(torch.tensor(1.0))
        
        # Tool classification head
        self.tool_head = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size),
            nn.GELU(),
            nn.Dropout(classifier_dropout),
            nn.Linear(config.hidden_size, num_tools)
        )
        
        # Per-tool intent heads
        self.character_intent_head = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size),
            nn.GELU(),
            nn.Dropout(classifier_dropout),
            nn.Linear(config.hidden_size, num_character_intents)
        )
        self.session_intent_head = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size),
            nn.GELU(),
            nn.Dropout(classifier_dropout),
            nn.Linear(config.hidden_size, num_session_intents)
        )
        self.rulebook_intent_head = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size),
            nn.GELU(),
            nn.Dropout(classifier_dropout),
            nn.Linear(config.hidden_size, num_rulebook_intents)
        )
        
        self.post_init()
    
    def forward(self, input_ids=None, attention_mask=None, **kwargs):
        """
        Forward pass matching training notebook.
        
        Returns:
            tuple of (tool_logits, intent_logits_dict) where intent_logits_dict has
            keys 'character', 'session_notes', 'rulebook'
        """
        outputs = self.deberta(input_ids, attention_mask=attention_mask)
        
        # Get [CLS] token representation
        cls_output = self.dropout(outputs.last_hidden_state[:, 0, :])
        
        # Tool logits
        tool_logits = self.tool_head(cls_output)
        
        # Intent logits for all tools (using same keys as training notebook)
        intent_logits = {
            'character': self.character_intent_head(cls_output),
            'session_notes': self.session_intent_head(cls_output),
            'rulebook': self.rulebook_intent_head(cls_output),
        }
        
        return tool_logits, intent_logits


class LocalClassifier:
    """
    Local classifier using the trained Joint Tool+Intent model.
    
    Key features:
    - Name normalization: replaces character/party/NPC names with placeholders
    - Temperature-scaled confidence scores for calibration
    - Gazetteer NER for entity extraction (optional)
    
    Training vs Inference Flow:
        TRAINING: Templates with {CHARACTER} → Train model on placeholder patterns
        INFERENCE: "What level is Duskryn?" → normalize → "What level is {CHARACTER}?" → Classify
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        srd_cache_path: Optional[str] = None,
        device: str = 'auto',
        use_gazetteer: bool = True,
        gazetteer_min_similarity: float = 0.80,
    ):
        """
        Initialize the local classifier.
        
        Args:
            model_path: Path to the trained model directory. If None, uses config default.
            srd_cache_path: Path to SRD cache for gazetteer NER. If None, uses config default.
            device: Device to use ('auto', 'cuda', 'mps', 'cpu')
            use_gazetteer: Whether to use gazetteer NER for entity extraction.
            gazetteer_min_similarity: Minimum similarity for gazetteer matching.
        """
        from src.config import get_config
        config = get_config()
        
        # Use config defaults if not provided
        project_root = Path(__file__).parent.parent.parent
        if model_path:
            self.model_path = Path(model_path)
        else:
            self.model_path = project_root / config.local_classifier_model_path
        
        if srd_cache_path:
            self.srd_cache_path = Path(srd_cache_path)
        else:
            self.srd_cache_path = project_root / config.local_classifier_srd_cache
        
        self.gazetteer_min_similarity = gazetteer_min_similarity
        
        # Determine device
        if device == 'auto':
            if torch.cuda.is_available():
                self.device = torch.device('cuda')
            elif torch.backends.mps.is_available():
                self.device = torch.device('mps')
            else:
                self.device = torch.device('cpu')
        else:
            self.device = torch.device(device)
        
        print(f"[LocalClassifier] Using device: {self.device}")
        print(f"[LocalClassifier] Model path: {self.model_path}")
        
        # Load components
        self._load_mappings()
        self._load_model()
        
        # Load gazetteer if enabled and cache exists
        self.use_gazetteer = use_gazetteer and self.srd_cache_path.exists()
        if self.use_gazetteer:
            self._load_gazetteer()
        else:
            self.gazetteer_ner = None
    
    def _load_mappings(self) -> None:
        """Load label mappings from training."""
        mappings_path = self.model_path / 'label_mappings.json'
        with open(mappings_path) as f:
            self.mappings = json.load(f)
        
        self.tool_to_idx = self.mappings['tool_to_idx']
        self.idx_to_tool = {int(k): v for k, v in self.mappings['idx_to_tool'].items()}
        self.tools = list(self.tool_to_idx.keys())
        
        self.intent_to_idx_per_tool = self.mappings['intent_to_idx_per_tool']
        self.idx_to_intent_per_tool = {
            tool: {int(k): v for k, v in intents.items()}
            for tool, intents in self.mappings['idx_to_intent_per_tool'].items()
        }
        self.num_intents_per_tool = self.mappings['num_intents_per_tool']
        
        # Preserved placeholders from training
        self.preserved_placeholders = self.mappings.get('preserved_placeholders', [
            '{CHARACTER}', '{PARTY_MEMBER}', '{NPC}'
        ])
        
        print(f"[LocalClassifier] Loaded mappings: {len(self.tools)} tools")
        for tool, num in self.num_intents_per_tool.items():
            print(f"  - {tool}: {num} intents")
    
    def _load_model(self) -> None:
        """Load the trained model, tokenizer, and checkpoint."""
        # Load tokenizer - try local first, fall back to HuggingFace
        tokenizer_path = self.model_path / 'tokenizer'
        try:
            if tokenizer_path.exists():
                print(f"[LocalClassifier] Loading tokenizer from {tokenizer_path}")
                self.tokenizer = DebertaV2TokenizerFast.from_pretrained(str(tokenizer_path))
            else:
                raise FileNotFoundError("No local tokenizer")
        except Exception as e:
            print(f"[LocalClassifier] Local tokenizer failed ({e}), using HuggingFace")
            self.tokenizer = DebertaV2TokenizerFast.from_pretrained('microsoft/deberta-v3-base')
        
        # Load checkpoint
        checkpoint_path = self.model_path / 'joint_classifier.pt'
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"No checkpoint found at {checkpoint_path}")
        
        print(f"[LocalClassifier] Loading checkpoint from {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        
        # Extract config from checkpoint
        self.training_config = checkpoint.get('config', {})
        self.max_length = self.training_config.get('max_length', 128)
        
        # Get calibrated temperature from checkpoint
        self.calibrated_temperature = checkpoint.get('temperature', 1.0)
        print(f"[LocalClassifier] Calibrated temperature: {self.calibrated_temperature:.4f}")
        
        # Initialize model architecture
        config = AutoConfig.from_pretrained(
            self.training_config.get('model_name', 'microsoft/deberta-v3-base')
        )
        config.classifier_dropout = self.training_config.get('classifier_dropout', 0.1)
        
        self.model = JointClassifier(
            config,
            num_tools=len(self.tools),
            num_character_intents=self.num_intents_per_tool['character_data'],
            num_session_intents=self.num_intents_per_tool['session_notes'],
            num_rulebook_intents=self.num_intents_per_tool['rulebook']
        )
        
        # Load state dict (includes calibrated temperature)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        
        self.model.to(self.device)
        self.model.eval()
        
        # Model stats
        total_params = sum(p.numel() for p in self.model.parameters())
        print(f"[LocalClassifier] Model loaded: {total_params:,} parameters")
    
    def _load_gazetteer(self) -> None:
        """Load gazetteer-based NER for entity extraction."""
        if self.srd_cache_path and self.srd_cache_path.exists():
            print(f"[LocalClassifier] Loading gazetteer NER from {self.srd_cache_path}")
            self.gazetteer_ner = GazetteerEntityExtractor(
                str(self.srd_cache_path),
                min_similarity=self.gazetteer_min_similarity
            )
        else:
            print("[LocalClassifier] Gazetteer NER not available (no SRD cache)")
            self.gazetteer_ner = None
    
    def _normalize_names(
        self,
        query: str,
        character_name: Optional[str] = None,
        character_aliases: Optional[List[str]] = None,
        party_members: Optional[List[str]] = None,
        known_npcs: Optional[List[str]] = None
    ) -> str:
        """
        Replace known names with placeholder tokens.
        
        This aligns runtime queries with the placeholder-based training data.
        The model was trained on patterns like "What level is {CHARACTER}?"
        so we need to normalize "What level is Duskryn?" to match.
        
        Args:
            query: The original query text
            character_name: The player's character name (can be full name like "Duskryn Nightwarden")
            character_aliases: Optional list of aliases/nicknames (e.g., ["Dusk", "DN"])
            party_members: List of party member names
            known_npcs: List of known NPC names
            
        Returns:
            Query with names replaced by placeholders
        """
        normalized = query
        
        # Helper for case-insensitive whole-word replacement
        def replace_name(text: str, name: str, placeholder: str) -> str:
            if not name or len(name) < 2:  # Skip empty or single-char names
                return text
            # Match whole word, case-insensitive
            pattern = re.compile(rf'\b{re.escape(name)}\b', re.IGNORECASE)
            return pattern.sub(placeholder, text)
        
        # Build list of character name variants to match
        character_variants = []
        if character_name:
            # Add full name
            character_variants.append(character_name)
            # Add first name (split on space)
            name_parts = character_name.split()
            if len(name_parts) > 1:
                character_variants.append(name_parts[0])  # First name
                # Optionally add last name too
                if len(name_parts[-1]) > 2:  # Skip short suffixes like "Jr"
                    character_variants.append(name_parts[-1])
        
        # Add explicit aliases
        if character_aliases:
            character_variants.extend(character_aliases)
        
        # Replace character name variants (highest priority, longest first)
        # Sort by length descending to match longer names first (e.g., "Duskryn Nightwarden" before "Duskryn")
        character_variants = sorted(set(character_variants), key=len, reverse=True)
        for variant in character_variants:
            normalized = replace_name(normalized, variant, '{CHARACTER}')
        
        # Replace party member names
        if party_members:
            for member in party_members:
                if member:
                    # Also handle first names for party members
                    member_parts = member.split()
                    names_to_check = [member]
                    if len(member_parts) > 1:
                        names_to_check.append(member_parts[0])
                    for name in names_to_check:
                        # Don't replace if already a placeholder
                        if '{CHARACTER}' not in name:
                            normalized = replace_name(normalized, name, '{PARTY_MEMBER}')
        
        # Replace NPC names
        if known_npcs:
            for npc in known_npcs:
                if npc:
                    # Also handle first names for NPCs
                    npc_parts = npc.split()
                    names_to_check = [npc]
                    if len(npc_parts) > 1:
                        names_to_check.append(npc_parts[0])
                    for name in names_to_check:
                        normalized = replace_name(normalized, name, '{NPC}')
        
        return normalized
    
    def classify_single(
        self,
        query: str,
        character_name: Optional[str] = None,
        character_aliases: Optional[List[str]] = None,
        party_members: Optional[List[str]] = None,
        known_npcs: Optional[List[str]] = None
    ) -> SingleClassificationResult:
        """
        Classify a query and return the single best tool + intent.
        
        Args:
            query: The user's query text
            character_name: Optional character name for normalization (can be full name)
            character_aliases: Optional list of character aliases/nicknames
            party_members: Optional list of party member names
            known_npcs: Optional list of known NPC names
            
        Returns:
            SingleClassificationResult with tool, intent, and confidence scores
        """
        # Normalize names to placeholders
        normalized_query = self._normalize_names(
            query, character_name, character_aliases, party_members, known_npcs
        )
        
        # Tokenize
        encoding = self.tokenizer(
            normalized_query,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Run inference (matching training notebook predict() function)
        with torch.no_grad():
            tool_logits, intent_logits_dict = self.model(input_ids, attention_mask)
            
            # Align dict keys (notebook uses 'character', we need 'character_data')
            if 'character' in intent_logits_dict:
                intent_logits_dict['character_data'] = intent_logits_dict['character']
            
            # Apply temperature scaling for calibrated probabilities
            tool_probs = F.softmax(tool_logits / self.model.temperature, dim=-1)
            tool_pred = torch.argmax(tool_probs, dim=-1).item()
            tool_conf = tool_probs[0, tool_pred].item()
            tool_name = self.idx_to_tool[tool_pred]
            
            # Get intent logits for predicted tool
            intent_logits = intent_logits_dict[tool_name]
            intent_probs = F.softmax(intent_logits / self.model.temperature, dim=-1)
            intent_pred = torch.argmax(intent_probs, dim=-1).item()
            intent_conf = intent_probs[0, intent_pred].item()
            intent_name = self.idx_to_intent_per_tool[tool_name][intent_pred]
        
        return SingleClassificationResult(
            tool=tool_name,
            tool_confidence=tool_conf,
            intent=intent_name,
            intent_confidence=intent_conf,
            normalized_query=normalized_query,
            combined_confidence=tool_conf * intent_conf
        )
    
    def predict_sync(
        self,
        query: str,
        character_name: Optional[str] = None,
        character_aliases: Optional[List[str]] = None,
        party_members: Optional[List[str]] = None,
        known_npcs: Optional[List[str]] = None,
        tool_threshold: Optional[float] = None
    ) -> ClassificationResult:
        """
        Synchronous prediction returning ClassificationResult for integration.
        
        Returns ALL tools with confidence above the threshold, each with their
        best intent. This allows multi-tool queries like "What spells do I have
        and how does fireball work?" to route to both character_data AND rulebook.
        
        Args:
            query: The user's query text
            character_name: Optional character name for normalization
            character_aliases: Optional list of character aliases/nicknames
            party_members: Optional list of party member names
            known_npcs: Optional list of known NPC names
            tool_threshold: Confidence threshold for tool selection (uses config default if None)
            
        Returns:
            ClassificationResult with tools_needed, tool_confidences, entities
        """
        from src.config import get_config
        config = get_config()
        threshold = tool_threshold if tool_threshold is not None else config.local_classifier_tool_threshold
        
        start_time = time.time()
        
        # Normalize names to placeholders
        normalized_query = self._normalize_names(
            query, character_name, character_aliases, party_members, known_npcs
        )
        
        # Tokenize
        encoding = self.tokenizer(
            normalized_query,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        with torch.no_grad():
            tool_logits, intent_logits_dict = self.model(input_ids, attention_mask)
            
            # Align dict keys (notebook uses 'character', we need 'character_data')
            if 'character' in intent_logits_dict:
                intent_logits_dict['character_data'] = intent_logits_dict['character']
            
            temp = self.model.temperature.item()
            tool_probs = F.softmax(tool_logits / temp, dim=-1)[0]
        
        # Get confidence for all tools
        tool_confidences = {
            self.idx_to_tool[i]: float(tool_probs[i].item())
            for i in range(len(self.tools))
        }
        
        # Build tools_needed list with ALL tools above threshold
        tools_needed = []
        for tool_idx in range(len(self.tools)):
            tool_name = self.idx_to_tool[tool_idx]
            tool_conf = float(tool_probs[tool_idx].item())
            
            if tool_conf >= threshold:
                # Get best intent for this tool
                with torch.no_grad():
                    intent_logits = intent_logits_dict[tool_name]
                    intent_probs = F.softmax(intent_logits / temp, dim=-1)
                    intent_pred = torch.argmax(intent_probs, dim=-1).item()
                    intent_name = self.idx_to_intent_per_tool[tool_name][intent_pred]
                
                tools_needed.append({
                    'tool': tool_name,
                    'intention': intent_name,
                    'confidence': tool_conf
                })
        
        # Sort by confidence descending
        tools_needed.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Fallback: if no tools above threshold, include the best one anyway
        if not tools_needed:
            best_tool_idx = torch.argmax(tool_probs).item()
            best_tool_name = self.idx_to_tool[best_tool_idx]
            best_tool_conf = float(tool_probs[best_tool_idx].item())
            
            with torch.no_grad():
                intent_logits = intent_logits_dict[best_tool_name]
                intent_probs = F.softmax(intent_logits / temp, dim=-1)
                intent_pred = torch.argmax(intent_probs, dim=-1).item()
                intent_name = self.idx_to_intent_per_tool[best_tool_name][intent_pred]
            
            tools_needed.append({
                'tool': best_tool_name,
                'intention': intent_name,
                'confidence': best_tool_conf
            })
        
        # Extract entities using gazetteer NER (if available)
        entities = []
        if self.gazetteer_ner:
            raw_entities = self.gazetteer_ner.extract_simple(query)
            entities = [
                {
                    'name': e['canonical'],
                    'text': e['text'],
                    'type': e['type'],
                    'confidence': e['confidence']
                }
                for e in raw_entities
            ]
        
        inference_time = (time.time() - start_time) * 1000
        
        return ClassificationResult(
            tools_needed=tools_needed,
            tool_confidences=tool_confidences,
            entities=entities,
            backend='local',
            inference_time_ms=inference_time
        )
    
    async def classify(
        self,
        query: str,
        character_name: Optional[str] = None,
        character_aliases: Optional[List[str]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        party_members: Optional[List[str]] = None,
        known_npcs: Optional[List[str]] = None
    ) -> ClassificationResult:
        """
        Async classification method (required by ClassifierBackend protocol).
        
        Args:
            query: The user's query text
            character_name: Optional character name for normalization
            character_aliases: Optional list of character aliases/nicknames
            conversation_history: Optional prior conversation (not used by local model)
            party_members: Optional list of party member names
            known_npcs: Optional list of known NPC names
            
        Returns:
            ClassificationResult with tools, intents, and entities
        """
        return self.predict_sync(query, character_name, character_aliases, party_members, known_npcs)
    
    def get_all_tool_confidences(
        self,
        query: str,
        character_name: Optional[str] = None,
        character_aliases: Optional[List[str]] = None,
        party_members: Optional[List[str]] = None,
        known_npcs: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Get confidence scores for all tools."""
        result = self.predict_sync(query, character_name, character_aliases, party_members, known_npcs)
        return result.tool_confidences
