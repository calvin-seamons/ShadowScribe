"""
Gazetteer-based Entity Extractor using Fuzzy Matching.

Uses fuzzy string matching against known D&D 5e SRD entities for reliable
entity extraction in a closed domain.

Supports dynamic entity sources:
- SRD entities (spells, monsters, items, etc.)
- Character name and aliases
- Party member names
- Session notes NPCs, locations, items
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Any, TYPE_CHECKING
from dataclasses import dataclass
from difflib import SequenceMatcher

if TYPE_CHECKING:
    from src.rag.character.character_types import Character
    from src.rag.session_notes.campaign_session_notes_storage import CampaignSessionNotesStorage

# Use try/except for sklearn as it may not be installed
try:
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
except ImportError:
    # Fallback minimal set of stop words
    ENGLISH_STOP_WORDS = frozenset({
        'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
        'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
        'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'between', 'under', 'again', 'further', 'then', 'once', 'here',
        'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
        'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also', 'now',
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
        'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
        'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
        'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
        'who', 'whom', 'this', 'that', 'these', 'those', 'am'
    })


@dataclass
class Entity:
    """Extracted entity with type and confidence."""
    text: str           # The matched text from the query
    canonical: str      # The canonical entity name
    type: str          # Entity type (SPELL, CLASS, etc.)
    confidence: float  # Match confidence (0.0 - 1.0)
    start: int         # Start position in query
    end: int           # End position in query


class GazetteerEntityExtractor:
    """
    Extract D&D entities from text using fuzzy matching against known gazetteers.
    
    Uses a two-phase approach:
    1. Exact substring matching (fast, high precision)
    2. Fuzzy matching for misspellings (slower, catches typos)
    
    Supports dynamic entity sources:
    - SRD entities loaded at init
    - Character/party/NPC entities added via add_character_context()
    """
    
    # Mapping from SRD cache file to entity type
    GAZETTEER_MAPPING = {
        'spells': 'SPELL',
        'classes': 'CLASS',
        'subclasses': 'CLASS',
        'races': 'RACE',
        'monsters': 'CREATURE',
        'equipment': 'ITEM',
        'magic-items': 'ITEM',
        'conditions': 'CONDITION',
        'damage-types': 'DAMAGE_TYPE',
        'skills': 'SKILL',
        'features': 'FEAT',
        'traits': 'FEAT',
        'backgrounds': 'BACKGROUND',
        'ability-scores': 'ABILITY',
    }
    
    # Dynamic entity types (not from SRD files)
    DYNAMIC_ENTITY_TYPES = {
        'CHARACTER',       # The player's character
        'PARTY_MEMBER',    # Other party members from session notes  
        'NPC',             # Non-player characters from session notes
        'LOCATION',        # Locations from session notes
        'SESSION_ITEM',    # Named items from session notes
        'FACTION',         # Factions/organizations from session notes
    }
    
    # D&D-specific common words that aren't entity names
    DND_SKIP_WORDS: Set[str] = {
        'cast', 'casting', 'casts', 'damage', 'damages', 'damaging',
        'range', 'ranged', 'attack', 'attacks', 'attacking',
        'spell', 'spells', 'class', 'classes', 'level', 'levels',
        'roll', 'rolls', 'rolling', 'hit', 'hits', 'hitting',
        'save', 'saves', 'saving', 'check', 'checks', 'checking',
        'ability', 'abilities', 'score', 'scores', 'modifier', 'modifiers',
        'bonus', 'bonuses', 'action', 'actions', 'reaction', 'reactions',
        'target', 'targets', 'targeting', 'creature', 'creatures',
        'character', 'characters', 'player', 'players', 'enemy', 'enemies',
        'effect', 'effects', 'duration', 'concentration', 'concentrating',
        'weapon', 'weapons', 'armor', 'armors', 'shield', 'shields',
        'melee', 'dice', 'die', 'round', 'rounds', 'turn', 'turns',
        'slot', 'slots', 'component', 'components', 'verbal', 'somatic',
        'material', 'ritual', 'cantrip', 'cantrips', 'feature', 'features',
        'trait', 'traits', 'proficiency', 'proficiencies', 'proficient',
        'resistance', 'resistances', 'immunity', 'immunities', 'vulnerable',
        'advantage', 'disadvantage', 'succeed', 'fail', 'success', 'failure',
        # Common verbs that match creature names (e.g., 'work' -> 'worg')
        'work', 'works', 'working', 'worked',
        'know', 'knows', 'knowing', 'knew', 'known',
        'help', 'helps', 'helping', 'helped',
        'like', 'likes', 'liking', 'liked',
        'make', 'makes', 'making', 'made',
        'take', 'takes', 'taking', 'took', 'taken',
        'give', 'gives', 'giving', 'gave', 'given',
        'tell', 'tells', 'telling', 'told',
        'find', 'finds', 'finding', 'found',
        'come', 'comes', 'coming', 'came',
        'want', 'wants', 'wanting', 'wanted',
        'look', 'looks', 'looking', 'looked',
        'think', 'thinks', 'thinking', 'thought',
    }
    
    def __init__(self, cache_path: Path, min_similarity: float = 0.85):
        """
        Initialize with path to SRD cache directory.
        
        Args:
            cache_path: Path to data/srd_cache/
            min_similarity: Minimum similarity score for fuzzy matching (0.0-1.0)
        """
        self.cache_path = Path(cache_path)
        self.min_similarity = min_similarity
        self.gazetteers: Dict[str, Tuple[str, str]] = {}  # {lowercase_name: (canonical_name, type)}
        self.skip_words: Set[str] = set(ENGLISH_STOP_WORDS) | self.DND_SKIP_WORDS
        self._load_gazetteers()
    
    def _load_gazetteers(self) -> None:
        """Load all entity gazetteers from SRD cache."""
        self.gazetteers = {}
        
        for filename, entity_type in self.GAZETTEER_MAPPING.items():
            filepath = self.cache_path / f"{filename}.json"
            if not filepath.exists():
                continue
            
            try:
                with open(filepath) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue
            
            # Handle different file structures
            if 'results' in data:
                entities = data['results']
            elif isinstance(data, list):
                entities = data
            else:
                continue
            
            for entity in entities:
                if isinstance(entity, dict) and 'name' in entity:
                    name = entity['name']
                    self.gazetteers[name.lower()] = (name, entity_type)
        
        print(f"[GazetteerNER] Loaded {len(self.gazetteers)} entities from gazetteers")
    
    def add_entities(
        self, 
        names: List[str], 
        entity_type: str,
        aliases: Optional[Dict[str, List[str]]] = None
    ) -> int:
        """
        Add entities dynamically at runtime.
        
        Also automatically adds first-name/short-name aliases for multi-word names
        to improve matching (e.g., "Duskryn" -> "Duskryn Nightwarden").
        
        Args:
            names: List of canonical entity names to add
            entity_type: The entity type (CHARACTER, NPC, PARTY_MEMBER, etc.)
            aliases: Optional mapping of canonical_name -> list of aliases
            
        Returns:
            Number of entities added
        """
        added = 0
        for name in names:
            if not name or not name.strip():
                continue
            canonical = name.strip()
            self.gazetteers[canonical.lower()] = (canonical, entity_type)
            added += 1
            
            # Auto-generate first-name alias for multi-word names
            # This helps match "Duskryn" to "Duskryn Nightwarden"
            # Also handles apostrophes/hyphens like "Ghul'Vor" -> "Ghul", "Shar-Kai" -> "Shar"
            words = canonical.split()
            if len(words) >= 2:
                first_word = words[0]
                # Only add if first word is significant (4+ chars, not common word)
                if len(first_word) >= 4 and first_word.lower() not in self.skip_words:
                    # Check it's not already in gazetteer with different meaning
                    if first_word.lower() not in self.gazetteers:
                        self.gazetteers[first_word.lower()] = (canonical, entity_type)
                        added += 1
            
            # Handle apostrophe/hyphen names (e.g., "Ghul'Vor" -> "Ghul", "Shar-Kai" -> "Shar")
            if "'" in canonical or "-" in canonical:
                parts = re.split(r"['\"'-]", canonical)
                if len(parts) >= 2:
                    first_part = parts[0].strip()
                    if len(first_part) >= 3 and first_part.lower() not in self.skip_words:
                        # Add first part as alias pointing to canonical
                        if first_part.lower() not in self.gazetteers:
                            self.gazetteers[first_part.lower()] = (canonical, entity_type)
                            added += 1
            
            # Add any explicit aliases for this entity
            if aliases and canonical in aliases:
                for alias in aliases[canonical]:
                    if alias and alias.strip():
                        self.gazetteers[alias.strip().lower()] = (canonical, entity_type)
                        added += 1
        
        return added
    
    def add_character_context(
        self,
        character: Optional["Character"] = None,
        session_storage: Optional["CampaignSessionNotesStorage"] = None
    ) -> Dict[str, int]:
        """
        Add character and session context to the gazetteer.
        
        This populates the gazetteer with:
        - The player's character name (CHARACTER type)
        - Party member names from session notes (PARTY_MEMBER type)
        - NPC names from session notes (NPC type)
        - Locations from session notes (LOCATION type)
        - Named items from session notes (SESSION_ITEM type)
        - Factions from session notes (FACTION type)
        
        Args:
            character: The Character object (optional)
            session_storage: The session notes storage (optional)
            
        Returns:
            Dict with counts of each entity type added
        """
        counts: Dict[str, int] = {}
        
        # Add character name and aliases
        if character and character.character_base:
            char_name = character.character_base.name
            # Get first name as an alias
            first_name = char_name.split()[0] if char_name else None
            aliases = {}
            if first_name and first_name.lower() != char_name.lower():
                char_aliases = [first_name]
                # Add 4-char truncated nickname if first name is long enough (e.g., "Dusk" from "Duskryn")
                if len(first_name) > 4:
                    char_aliases.append(first_name[:4])
                aliases[char_name] = char_aliases
            counts['CHARACTER'] = self.add_entities([char_name], 'CHARACTER', aliases)
        
        # Add entities from session notes
        if session_storage:
            # Map session note entity types to our gazetteer types
            session_type_mapping = {
                'player_character': 'PARTY_MEMBER',
                'non_player_character': 'NPC',
                'location': 'LOCATION',
                'item': 'SESSION_ITEM',
                'faction': 'FACTION',
                'organization': 'FACTION',
            }
            
            # Gather all entities from session storage
            # CampaignSessionNotesStorage has a flat entities dict at the top level
            entity_groups: Dict[str, List[str]] = {k: [] for k in session_type_mapping}
            alias_groups: Dict[str, Dict[str, List[str]]] = {k: {} for k in session_type_mapping}
            
            # Iterate over the flat entities dictionary
            if hasattr(session_storage, 'entities') and session_storage.entities:
                for entity_id, entity in session_storage.entities.items():
                    # Get entity type as string
                    entity_type_raw = None
                    if hasattr(entity, 'entity_type'):
                        et = entity.entity_type
                        entity_type_raw = et.value if hasattr(et, 'value') else str(et)
                    elif isinstance(entity, dict) and 'entity_type' in entity:
                        entity_type_raw = entity['entity_type']
                    
                    if not entity_type_raw:
                        continue
                    
                    # Normalize to our mapping keys
                    entity_type_key = entity_type_raw.lower().replace(' ', '_')
                    if entity_type_key not in session_type_mapping:
                        continue
                    
                    # Get entity name
                    entity_name = entity.name if hasattr(entity, 'name') else (
                        entity.get('name', '') if isinstance(entity, dict) else str(entity)
                    )
                    if not entity_name:
                        continue
                    
                    entity_groups[entity_type_key].append(entity_name)
                    
                    # Get aliases if available
                    aliases_list = []
                    if hasattr(entity, 'aliases') and entity.aliases:
                        aliases_list = entity.aliases
                    elif isinstance(entity, dict) and 'aliases' in entity:
                        aliases_list = entity['aliases']
                    
                    if aliases_list:
                        alias_groups[entity_type_key][entity_name] = aliases_list
            
            # Add to gazetteer
            for session_type, gazetteer_type in session_type_mapping.items():
                names = list(set(entity_groups.get(session_type, [])))  # Dedupe
                if names:
                    counts[gazetteer_type] = self.add_entities(
                        names, 
                        gazetteer_type,
                        alias_groups.get(session_type, {})
                    )
        
        print(f"[GazetteerNER] Added dynamic entities: {counts}")
        return counts
    
    def clear_dynamic_entities(self) -> int:
        """
        Remove all dynamically added entities (keeps SRD entities).
        
        Returns:
            Number of entities removed
        """
        removed = 0
        to_remove = []
        
        for key, (canonical, entity_type) in self.gazetteers.items():
            if entity_type in self.DYNAMIC_ENTITY_TYPES:
                to_remove.append(key)
        
        for key in to_remove:
            del self.gazetteers[key]
            removed += 1
        
        print(f"[GazetteerNER] Cleared {removed} dynamic entities")
        return removed
    
    def reload_context(
        self,
        character: Optional["Character"] = None,
        session_storage: Optional["CampaignSessionNotesStorage"] = None
    ) -> Dict[str, int]:
        """
        Clear dynamic entities and reload from character/session data.
        
        Use this when character or session data has changed.
        
        Args:
            character: The Character object (optional)
            session_storage: The session notes storage (optional)
            
        Returns:
            Dict with counts of each entity type added
        """
        self.clear_dynamic_entities()
        return self.add_character_context(character, session_storage)
    
    def _similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings."""
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
    
    def _find_exact_matches(self, text: str) -> List[Entity]:
        """Find exact substring matches (case-insensitive)."""
        entities = []
        text_lower = text.lower()
        
        # Sort by length (longest first) to prefer longer matches
        sorted_names = sorted(self.gazetteers.keys(), key=len, reverse=True)
        
        # Track matched spans to avoid overlaps
        matched_spans: List[Tuple[int, int]] = []
        
        for name_lower in sorted_names:
            canonical, entity_type = self.gazetteers[name_lower]
            
            # Find all occurrences
            start = 0
            while True:
                idx = text_lower.find(name_lower, start)
                if idx == -1:
                    break
                
                end = idx + len(name_lower)
                
                # Check word boundaries
                before_ok = idx == 0 or not text[idx-1].isalnum()
                after_ok = end == len(text) or not text[end].isalnum()
                
                # Check for overlap with existing matches
                overlaps = any(
                    not (end <= s or idx >= e) 
                    for s, e in matched_spans
                )
                
                if before_ok and after_ok and not overlaps:
                    entities.append(Entity(
                        text=text[idx:end],
                        canonical=canonical,
                        type=entity_type,
                        confidence=1.0,
                        start=idx,
                        end=end
                    ))
                    matched_spans.append((idx, end))
                
                start = end
        
        return entities
    
    def _find_fuzzy_matches(self, text: str, exact_spans: List[Tuple[int, int]]) -> List[Entity]:
        """Find fuzzy matches for words not already matched.
        
        Uses aggressive matching to avoid missing entities - prefer over-matching
        to under-matching since the LLM can filter irrelevant context.
        """
        entities = []
        
        # Tokenize into words with positions
        words = []
        for match in re.finditer(r'\b\w+\b', text):
            word = match.group()
            if word.lower() in self.skip_words:
                continue
            start, end = match.span()
            # Skip if overlaps with exact match
            if any(not (end <= s or start >= e) for s, e in exact_spans):
                continue
            words.append((word, start, end))
        
        # Build phrases (1-4 words for better NPC name matching)
        phrases = []
        for i in range(len(words)):
            phrases.append(words[i])
            if i + 1 < len(words):
                w1, s1, e1 = words[i]
                w2, s2, e2 = words[i+1]
                if s2 - e1 <= 2:
                    phrases.append((f"{w1} {w2}", s1, e2))
            if i + 2 < len(words):
                w1, s1, e1 = words[i]
                w2, s2, e2 = words[i+1]
                w3, s3, e3 = words[i+2]
                if s2 - e1 <= 2 and s3 - e2 <= 2:
                    phrases.append((f"{w1} {w2} {w3}", s1, e3))
            if i + 3 < len(words):
                w1, s1, e1 = words[i]
                w2, s2, e2 = words[i+1]
                w3, s3, e3 = words[i+2]
                w4, s4, e4 = words[i+3]
                if s2 - e1 <= 2 and s3 - e2 <= 2 and s4 - e3 <= 2:
                    phrases.append((f"{w1} {w2} {w3} {w4}", s1, e4))
        
        # Check each phrase against gazetteers
        for phrase, start, end in phrases:
            # Allow shorter single words for proper nouns (capitalized)
            is_capitalized = phrase[0].isupper() if phrase else False
            min_len = 3 if is_capitalized else 4
            
            if len(phrase) < min_len:
                continue
            if ' ' not in phrase and len(phrase) < 4 and not is_capitalized:
                continue
            
            best_match: Optional[Tuple[str, str, float]] = None
            best_score = 0.0
            
            for name_lower, (canonical, entity_type) in self.gazetteers.items():
                # More permissive length ratio check
                len_ratio = len(phrase) / len(name_lower) if len(name_lower) > 0 else 0
                if len_ratio < 0.4 or len_ratio > 2.5:
                    continue
                
                # Full fuzzy similarity
                score = self._similarity(phrase, name_lower)
                
                # Also check if phrase is a prefix/suffix of entity name (word-level)
                phrase_words = phrase.lower().split()
                name_words = name_lower.split()
                
                # Check if first word of phrase matches first word of entity
                if phrase_words and name_words:
                    first_word_sim = self._similarity(phrase_words[0], name_words[0])
                    if first_word_sim >= 0.85:
                        score = max(score, first_word_sim * 0.9)
                
                if score >= self.min_similarity and score > best_score:
                    best_score = score
                    best_match = (canonical, entity_type, score)
            
            if best_match:
                entities.append(Entity(
                    text=phrase,
                    canonical=best_match[0],
                    type=best_match[1],
                    confidence=best_match[2],
                    start=start,
                    end=end
                ))
        
        return entities
    
    def _deduplicate_overlapping(self, entities: List[Entity]) -> List[Entity]:
        """Remove overlapping entities, preferring higher confidence and longer spans."""
        if not entities:
            return []
        
        sorted_entities = sorted(
            entities,
            key=lambda e: (-e.confidence, -(e.end - e.start), e.start)
        )
        
        kept = []
        kept_spans: List[Tuple[int, int]] = []
        
        for entity in sorted_entities:
            overlaps = any(
                not (entity.end <= s or entity.start >= e)
                for s, e in kept_spans
            )
            
            if not overlaps:
                kept.append(entity)
                kept_spans.append((entity.start, entity.end))
        
        return kept
    
    def extract(self, text: str, use_fuzzy: bool = True) -> List[Entity]:
        """
        Extract all entities from text.
        
        Args:
            text: The query text to extract entities from
            use_fuzzy: Whether to use fuzzy matching for typos
            
        Returns:
            List of Entity objects, sorted by position
        """
        entities = self._find_exact_matches(text)
        exact_spans = [(e.start, e.end) for e in entities]
        
        if use_fuzzy:
            fuzzy_entities = self._find_fuzzy_matches(text, exact_spans)
            entities.extend(fuzzy_entities)
        
        entities = self._deduplicate_overlapping(entities)
        entities.sort(key=lambda e: e.start)
        
        return entities
    
    def extract_simple(self, text: str) -> List[Dict[str, Any]]:
        """
        Simple extraction returning just text and type.
        
        Returns:
            List of dicts with 'text', 'type', 'canonical', 'confidence', 
            and 'is_dynamic' keys
        """
        entities = self.extract(text)
        return [
            {
                'text': e.text,
                'type': e.type,
                'canonical': e.canonical,
                'confidence': e.confidence,
                'is_dynamic': e.type in self.DYNAMIC_ENTITY_TYPES
            }
            for e in entities
        ]
    
    def get_entity_count(self) -> Dict[str, int]:
        """Get count of entities by type."""
        counts: Dict[str, int] = {}
        for _, (_, entity_type) in self.gazetteers.items():
            counts[entity_type] = counts.get(entity_type, 0) + 1
        return counts
