"""
Entity Search Engine

Unified search system for finding entities across all data sources:
- Character data (inventory, spells, features, proficiencies, backstory)
- Session notes (NPCs, locations, organizations, quests)
- Rulebook (spells, items, creatures, conditions, rules)

Provides consistent fuzzy matching and result formatting across all sources.
"""

import re
from typing import List, Optional, Dict, TYPE_CHECKING
from difflib import SequenceMatcher

if TYPE_CHECKING:
    from src.rag.character.character_types import Character
    from src.rag.character.character_query_types import EntitySearchResult, SearchContext
    from src.rag.session_notes.campaign_session_notes_storage import CampaignSessionNotesStorage
    from src.rag.rulebook.rulebook_storage import RulebookStorage
    from src.rag.rulebook.rulebook_types import RulebookSection


class EntitySearchEngine:
    """
    Unified entity search engine across all data sources.
    
    Provides consistent fuzzy matching with 3-strategy approach:
    1. Exact match (case-insensitive) - confidence 1.0
    2. Substring match (partial name) - confidence 0.9
    3. Fuzzy similarity match - confidence based on similarity score
    """
    
    def __init__(self, threshold: float = 0.60):
        """Initialize the entity search engine.
        
        Args:
            threshold: Minimum similarity score for fuzzy matching (default 0.60 - permissive to avoid missing content)
        """
        self.threshold = threshold
        self._rulebook_cache: Dict[str, List['EntitySearchResult']] = {}  # Cache for rulebook lookups
    
    # ===== HIGH-LEVEL ENTITY RESOLUTION =====
    
    def resolve_entities(
        self,
        entities: List[Dict[str, any]],
        selected_tools: List[str],
        character: 'Character',
        session_notes_storage: Optional['CampaignSessionNotesStorage'] = None,
        rulebook_storage: Optional['RulebookStorage'] = None
    ) -> Dict[str, List['EntitySearchResult']]:
        """
        Resolve entities by searching ONLY in selected tools.
        
        Tool selection determines which data sources to search, providing
        efficient entity resolution without redundant searches.
        
        Args:
            entities: List of entity dicts with 'name' and 'confidence' fields
            selected_tools: Which tools to search ('character_data', 'session_notes', 'rulebook')
            character: Character object to search
            session_notes_storage: Optional session notes storage for entity search
            rulebook_storage: Optional rulebook storage for entity search
        
        Returns:
            Dictionary mapping entity names to lists of EntitySearchResult objects
        """
        entity_resolution_results = {}
        
        for entity_dict in entities:
            entity_name = entity_dict.get('name', '')
            
            # Skip if no name
            if not entity_name:
                continue
            
            all_results = []
            
            # 1. Search character data if selected
            if 'character_data' in selected_tools:
                char_results = self.search_all_character_sections(character, entity_name)
                all_results.extend(char_results)
            
            # 2. Search session notes if selected (returns list of matches)
            if 'session_notes' in selected_tools and session_notes_storage:
                session_results = self.search_session_notes(
                    session_notes_storage, 
                    entity_name
                )
                all_results.extend(session_results)
            
            # 3. Search rulebook if selected (with caching)
            if 'rulebook' in selected_tools and rulebook_storage:
                # Check cache first
                if entity_name in self._rulebook_cache:
                    rulebook_results = self._rulebook_cache[entity_name]
                else:
                    # Search and cache
                    rulebook_results = self.search_rulebook(
                        rulebook_storage,
                        entity_name,
                        max_results=5
                    )
                    self._rulebook_cache[entity_name] = rulebook_results
                
                all_results.extend(rulebook_results)
            
            # Store all results (even if empty list)
            entity_resolution_results[entity_name] = all_results
        
        return entity_resolution_results
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison (lowercase, remove special chars)."""
        return re.sub(r'[^\w\s]', '', text.lower().strip())
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate similarity ratio between two strings."""
        norm1 = EntitySearchEngine.normalize_text(text1)
        norm2 = EntitySearchEngine.normalize_text(text2)
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def match_entity_name(
        self,
        entity_name: str,
        candidate_name: str,
        threshold: Optional[float] = None
    ) -> Optional[tuple]:
        """Match an entity name against a candidate using multi-strategy approach.
        
        Philosophy: More context is better. We prefer to match too much (let LLM filter)
        rather than miss relevant entities.
        
        Args:
            entity_name: Name to search for
            candidate_name: Candidate name to match against
            threshold: Optional override for fuzzy threshold
        
        Returns:
            Tuple of (confidence, strategy, matched_text) if match found, None otherwise
        """
        if not candidate_name:
            return None
        
        threshold = threshold or self.threshold
        normalized_search = self.normalize_text(entity_name)
        normalized_candidate = self.normalize_text(candidate_name)
        
        # Strategy 1: Exact match (case-insensitive)
        if normalized_search == normalized_candidate:
            return (1.0, "exact", candidate_name)
        
        # Strategy 2: Substring match (partial name) - handles "Ghul" in "Ghul'Vor"
        if normalized_search in normalized_candidate or normalized_candidate in normalized_search:
            return (0.9, "substring", candidate_name)
        
        # Strategy 3: Word-level partial match - handles "Duskryn" matching "Duskryn Nightwarden"
        # Also handles possessives like "Ghul'Vor's servants"
        search_words = normalized_search.split()
        candidate_words = normalized_candidate.split()
        
        # Check if any search word matches any candidate word
        for search_word in search_words:
            if len(search_word) >= 3:  # Only for words 3+ chars
                for candidate_word in candidate_words:
                    if search_word == candidate_word:
                        return (0.85, "word_match", candidate_name)
                    # Partial word match (start of word)
                    if len(search_word) >= 4 and candidate_word.startswith(search_word):
                        return (0.80, "word_prefix", candidate_name)
                    if len(candidate_word) >= 4 and search_word.startswith(candidate_word):
                        return (0.80, "word_prefix", candidate_name)
        
        # Strategy 4: Component matching for apostrophe/hyphen names
        # "Ghul" should match "Ghul'Vor", "Ghul'Vor's Twin Servants", "Ghul-kin", etc.
        # Extract components by splitting on apostrophes, hyphens, and spaces
        search_components = re.split(r"['\"'\s-]+", entity_name.lower())
        candidate_components = re.split(r"['\"'\s-]+", candidate_name.lower())
        
        for search_comp in search_components:
            if len(search_comp) >= 3:
                for cand_comp in candidate_components:
                    if len(cand_comp) >= 3:
                        # Exact component match
                        if search_comp == cand_comp:
                            return (0.85, "component_match", candidate_name)
                        # Component prefix match
                        if len(search_comp) >= 4 and cand_comp.startswith(search_comp):
                            return (0.75, "component_prefix", candidate_name)
                        if len(cand_comp) >= 4 and search_comp.startswith(cand_comp):
                            return (0.75, "component_prefix", candidate_name)
        
        # Strategy 5: First word/component match with fuzzy
        if len(search_words) >= 1 and len(candidate_words) >= 1:
            first_search = search_words[0]
            first_candidate = candidate_words[0]
            if len(first_search) >= 4 and len(first_candidate) >= 4:
                first_similarity = SequenceMatcher(None, first_search, first_candidate).ratio()
                if first_similarity >= 0.75:
                    return (first_similarity * 0.9, "first_word_fuzzy", candidate_name)
        
        # Strategy 6: Fuzzy similarity match on full name
        similarity = self.calculate_similarity(entity_name, candidate_name)
        if similarity >= threshold:
            return (similarity, "fuzzy", candidate_name)
        
        return None
    
    # ===== CHARACTER DATA SEARCH =====
    
    def search_character_inventory(
        self,
        character: 'Character',
        entity_name: str
    ) -> Optional['EntitySearchResult']:
        """Search character inventory for an entity."""
        from src.rag.character.character_query_types import EntitySearchResult
        
        if not character.inventory:
            return None
        
        items = self._get_all_inventory_items(character)
        best_match = self._find_best_match_in_items(
            entity_name,
            items
        )
        
        if best_match:
            confidence, strategy, matched_text = best_match
            return EntitySearchResult(
                entity_name=entity_name,
                found_in_sections=['inventory'],
                match_confidence=confidence,
                matched_text=matched_text,
                match_strategy=strategy
            )
        
        return None
    
    def search_character_spells(
        self,
        character: 'Character',
        entity_name: str
    ) -> Optional['EntitySearchResult']:
        """Search character spell list for an entity."""
        from src.rag.character.character_query_types import EntitySearchResult
        
        if not character.spell_list or not character.spell_list.spells:
            return None
        
        spells = self._get_all_spells(character)
        best_match = self._find_best_match_in_items(entity_name, spells)
        
        if best_match:
            confidence, strategy, matched_text = best_match
            return EntitySearchResult(
                entity_name=entity_name,
                found_in_sections=['spell_list'],
                match_confidence=confidence,
                matched_text=matched_text,
                match_strategy=strategy
            )
        
        return None
    
    def search_character_features(
        self,
        character: 'Character',
        entity_name: str
    ) -> Optional['EntitySearchResult']:
        """Search character features and traits for an entity."""
        from src.rag.character.character_query_types import EntitySearchResult
        
        if not character.features_and_traits:
            return None
        
        features = self._get_all_features_traits(character)
        best_match = self._find_best_match_in_items(entity_name, features)
        
        if best_match:
            confidence, strategy, matched_text = best_match
            return EntitySearchResult(
                entity_name=entity_name,
                found_in_sections=['features_and_traits'],
                match_confidence=confidence,
                matched_text=matched_text,
                match_strategy=strategy
            )
        
        return None
    
    def search_character_proficiencies(
        self,
        character: 'Character',
        entity_name: str
    ) -> Optional['EntitySearchResult']:
        """Search character proficiencies for an entity."""
        from src.rag.character.character_query_types import EntitySearchResult
        
        if not hasattr(character, 'proficiencies') or not character.proficiencies:
            return None
        
        proficiencies = character.proficiencies if isinstance(character.proficiencies, list) else []
        best_match = self._find_best_match_in_items(entity_name, proficiencies)
        
        if best_match:
            confidence, strategy, matched_text = best_match
            return EntitySearchResult(
                entity_name=entity_name,
                found_in_sections=['proficiencies'],
                match_confidence=confidence,
                matched_text=matched_text,
                match_strategy=strategy
            )
        
        return None
    
    def search_character_backstory(
        self,
        character: 'Character',
        entity_name: str
    ) -> Optional['EntitySearchResult']:
        """Search character backstory entities for a match."""
        from src.rag.character.character_query_types import EntitySearchResult
        
        if not character.backstory:
            return None
        
        # Search within backstory sections
        # Actual Backstory fields: title (str), family_backstory (FamilyBackstory), sections (List[BackstorySection])
        best_match = None
        best_confidence = 0.0
        best_section = None
        best_strategy = None
        
        # Search in backstory title
        match_result = self.match_entity_name(entity_name, character.backstory.title)
        if match_result:
            confidence, strategy, matched_text = match_result
            if confidence > best_confidence:
                best_match = matched_text
                best_confidence = confidence
                best_section = 'backstory.title'
                best_strategy = strategy
        
        # Search in backstory sections
        if character.backstory.sections:
            for idx, section in enumerate(character.backstory.sections):
                # Handle both dict and object access (database vs pickle loading)
                section_heading = section.get('heading') if isinstance(section, dict) else getattr(section, 'heading', None)
                section_content = section.get('content') if isinstance(section, dict) else getattr(section, 'content', None)
                
                # Search in section heading
                if section_heading:
                    match_result = self.match_entity_name(entity_name, section_heading)
                    if match_result:
                        confidence, strategy, matched_text = match_result
                        if confidence > best_confidence:
                            best_match = matched_text
                            best_confidence = confidence
                            best_section = f'backstory.sections[{idx}].heading'
                            best_strategy = strategy
                
                # Search in section content
                if section_content:
                    # Check if entity_name appears in content
                    normalized_entity = self.normalize_text(entity_name)
                    normalized_content = self.normalize_text(section_content)
                    if normalized_entity in normalized_content:
                        confidence = 0.85  # High confidence for content matches
                        if confidence > best_confidence:
                            best_match = section_heading or f"Section {idx}"
                            best_confidence = confidence
                            best_section = f'backstory.sections[{idx}].content'
                            best_strategy = "content_match"
        
        # Return result if confidence above threshold
        if best_match and best_confidence >= self.threshold:
            return EntitySearchResult(
                entity_name=entity_name,
                found_in_sections=[best_section],
                match_confidence=best_confidence,
                matched_text=best_match,
                match_strategy=best_strategy
            )
        
        return None
    
    def search_all_character_sections(
        self,
        character: 'Character',
        entity_name: str
    ) -> List['EntitySearchResult']:
        """Search all character data sections for an entity.
        
        Returns all matches sorted by confidence (highest first).
        """
        results = []
        
        search_functions = [
            self.search_character_inventory,
            self.search_character_spells,
            self.search_character_features,
            self.search_character_proficiencies,
            self.search_character_backstory
        ]
        
        for search_func in search_functions:
            result = search_func(character, entity_name)
            if result:
                results.append(result)
        
        # Sort by confidence (highest first)
        results.sort(key=lambda r: r.match_confidence, reverse=True)
        
        return results
    
    # ===== SESSION NOTES SEARCH =====
    
    def search_session_notes(
        self,
        campaign_storage: 'CampaignSessionNotesStorage',
        entity_name: str,
        max_results: int = 10
    ) -> List['EntitySearchResult']:
        """Search session notes for an entity (NPCs, locations, quests, etc.).
        
        Uses multiple search strategies:
        1. Search indexed entities (NPCs, locations, etc.)
        2. Search entity aliases
        3. Search raw session content for text mentions (fallback)
        
        Returns up to max_results matches sorted by confidence (highest first).
        More context is better - prefer returning too many matches over too few.
        """
        from src.rag.character.character_query_types import EntitySearchResult
        
        if not campaign_storage:
            return []
        
        all_matches = []
        
        # Strategy 1 & 2: Search indexed entities and aliases
        if campaign_storage.entities:
            for entity_id, entity in campaign_storage.entities.items():
                # Get entity name
                name = self._get_item_name(entity)
                if not name:
                    continue
                
                # Get entity type for section identification
                entity_type = None
                if hasattr(entity, 'entity_type'):
                    entity_type = str(entity.entity_type.value) if hasattr(entity.entity_type, 'value') else str(entity.entity_type)
                elif isinstance(entity, dict) and 'entity_type' in entity:
                    entity_type = entity['entity_type']
                
                section = f'session_notes.{entity_type}' if entity_type else 'session_notes.entity'
                
                # Check main name
                match_result = self.match_entity_name(entity_name, name)
                if match_result:
                    confidence, strategy, matched_text = match_result
                    all_matches.append((confidence, strategy, matched_text, section))
                
                # Check aliases
                aliases = []
                if hasattr(entity, 'aliases'):
                    aliases = entity.aliases
                elif isinstance(entity, dict) and 'aliases' in entity:
                    aliases = entity['aliases']
                
                for alias in aliases:
                    if not alias:
                        continue
                    
                    match_result = self.match_entity_name(entity_name, alias)
                    if match_result:
                        confidence, strategy, _ = match_result
                        # Slightly lower confidence for alias matches
                        confidence = min(confidence, 0.95)
                        all_matches.append((confidence, f"{strategy}_alias", f"{name} (alias: {alias})", section))
        
        # Strategy 3: Search raw session content for text mentions (if no high-confidence match found)
        high_confidence_found = any(m[0] >= 0.8 for m in all_matches)
        
        if not high_confidence_found and campaign_storage.sessions:
            normalized_entity = self.normalize_text(entity_name)
            
            for session_id, session in campaign_storage.sessions.items():
                # Check session content/summary
                content = None
                if hasattr(session, 'content'):
                    content = session.content
                elif hasattr(session, 'summary'):
                    content = session.summary
                
                if content and normalized_entity in self.normalize_text(content):
                    # Found in raw content
                    all_matches.append((0.75, "content_search", f"Found in session {session_id}", 'session_notes.content'))
                
                # Check raw_notes.raw_sections if available
                raw_notes = getattr(session, 'raw_notes', None)
                if raw_notes and hasattr(raw_notes, 'raw_sections'):
                    for section_name, section_content in raw_notes.raw_sections.items():
                        if normalized_entity in self.normalize_text(section_content):
                            # Determine section type from section name
                            section_type = 'content'
                            if 'npc' in section_name.lower():
                                section_type = 'non_player_character'
                            elif 'player' in section_name.lower() or 'character' in section_name.lower():
                                section_type = 'player_character'
                            elif 'location' in section_name.lower():
                                section_type = 'location'
                            elif 'combat' in section_name.lower():
                                section_type = 'combat'
                            elif 'event' in section_name.lower():
                                section_type = 'event'
                            
                            all_matches.append((0.75, "raw_section_search", f"Found in {section_name}", f'session_notes.{section_type}'))
                            break  # One match per session is enough
        
        # Return ALL matches above threshold, sorted by confidence
        if all_matches:
            all_matches.sort(key=lambda x: x[0], reverse=True)
            results = []
            seen_sections = set()
            for confidence, strategy, matched_text, section in all_matches[:max_results]:
                # Avoid duplicate sections but allow different entities in same section type
                section_key = f"{section}:{matched_text}"
                if section_key in seen_sections:
                    continue
                seen_sections.add(section_key)
                
                results.append(EntitySearchResult(
                    entity_name=entity_name,
                    found_in_sections=[section],
                    match_confidence=confidence,
                    matched_text=matched_text,
                    match_strategy=strategy
                ))
            return results
        
        return []
    
    # ===== RULEBOOK SEARCH =====
    
    def search_rulebook(
        self,
        rulebook_storage: 'RulebookStorage',
        entity_name: str,
        max_results: int = 5
    ) -> List['EntitySearchResult']:
        """Search rulebook for entities (spells, items, creatures, conditions, rules).
        
        Returns up to max_results matches sorted by confidence.
        """
        from src.rag.character.character_query_types import EntitySearchResult
        
        if not rulebook_storage or not rulebook_storage.sections:
            return []
        
        matches: Dict[str, tuple] = {}  # section_id -> (confidence, strategy, matched_text, section)
        
        for section_id, section in rulebook_storage.sections.items():
            # Extract entity names from section
            entity_names = self._extract_rulebook_entity_names(section)
            
            for candidate_name in entity_names:
                if not candidate_name:
                    continue
                
                match_result = self.match_entity_name(entity_name, candidate_name)
                if match_result:
                    confidence, strategy, matched_text = match_result
                    # Only keep if better than existing match for this section
                    if section_id not in matches or matches[section_id][0] < confidence:
                        matches[section_id] = (confidence, strategy, matched_text, section)
        
        # Convert to EntitySearchResult objects
        results = []
        for section_id, (confidence, strategy, matched_text, section) in matches.items():
            # Get category for section identification
            categories = []
            if hasattr(section, 'categories') and section.categories:
                categories = [cat.name.lower() for cat in section.categories]
            
            category_str = categories[0] if categories else 'general'
            section_identifier = f'rulebook.{category_str}.{section_id}'
            
            results.append(EntitySearchResult(
                entity_name=entity_name,
                found_in_sections=[section_identifier],
                match_confidence=confidence,
                matched_text=f"{matched_text} ({section.title})",
                match_strategy=strategy
            ))
        
        # Sort by confidence and limit
        results.sort(key=lambda r: r.match_confidence, reverse=True)
        return results[:max_results]
    
    # ===== HELPER METHODS =====
    
    def _get_item_name(self, item: any) -> Optional[str]:
        """Extract name from an item (handles both dataclass and dict).
        
        For inventory items, checks item.definition.name first (D&D Beyond structure),
        then falls back to item.name for other item types.
        """
        # Check for nested definition structure (inventory items from D&D Beyond)
        if hasattr(item, 'definition') and hasattr(item.definition, 'name'):
            return item.definition.name
        # Direct name attribute (spells, features, etc.)
        elif hasattr(item, 'name'):
            return item.name
        # Dict with definition
        elif isinstance(item, dict) and 'definition' in item and isinstance(item['definition'], dict) and 'name' in item['definition']:
            return item['definition']['name']
        # Dict with direct name
        elif isinstance(item, dict) and 'name' in item:
            return item['name']
        return None
    
    def _find_best_match_in_items(
        self,
        entity_name: str,
        items: List[any]
    ) -> Optional[tuple]:
        """Find best match among a list of items.
        
        Returns tuple of (confidence, strategy, matched_text) or None.
        """
        best_match = None
        best_confidence = 0.0
        
        for item in items:
            name = self._get_item_name(item)
            if not name:
                continue
            
            match_result = self.match_entity_name(entity_name, name)
            if match_result:
                confidence, strategy, matched_text = match_result
                if confidence > best_confidence:
                    best_match = (confidence, strategy, matched_text)
                    best_confidence = confidence
                    # Perfect match, stop searching
                    if confidence == 1.0:
                        break
        
        return best_match
    
    def _get_all_inventory_items(self, character: 'Character') -> List[any]:
        """Get all inventory items (equipped and backpack)."""
        items = []
        
        if character.inventory.equipped_items:
            for slot, slot_items in character.inventory.equipped_items.items():
                items.extend(slot_items)
        
        if character.inventory.backpack:
            items.extend(character.inventory.backpack)
        
        return items
    
    def _get_all_spells(self, character: 'Character') -> List[any]:
        """Get all spells from spell list."""
        spells = []
        
        for class_name, spell_levels in character.spell_list.spells.items():
            for level_name, spell_list in spell_levels.items():
                spells.extend(spell_list)
        
        return spells
    
    def _get_all_features_traits(self, character: 'Character') -> List[any]:
        """Get all features and traits."""
        features = []
        
        # Add racial traits
        if character.features_and_traits.racial_traits:
            features.extend(character.features_and_traits.racial_traits)
        
        # Add class features
        if character.features_and_traits.class_features:
            for class_name, level_dict in character.features_and_traits.class_features.items():
                for level, feature_list in level_dict.items():
                    features.extend(feature_list)
        
        # Add feats
        if character.features_and_traits.feats:
            features.extend(character.features_and_traits.feats)
        
        return features
    
    def _extract_rulebook_entity_names(self, section: 'RulebookSection') -> List[str]:
        """Extract potential entity names from a rulebook section."""
        names = []
        
        # Add section title
        names.append(section.title)
        
        # Extract bolded text (format: **Text**)
        bold_pattern = r'\*\*([^*]+)\*\*'
        bold_matches = re.findall(bold_pattern, section.content)
        names.extend(bold_matches)
        
        # Extract headings within content
        heading_pattern = r'^#+\s+(.+)$'
        for line in section.content.split('\n'):
            heading_match = re.match(heading_pattern, line.strip())
            if heading_match:
                names.append(heading_match.group(1))
        
        # Clean up names
        cleaned_names = []
        for name in names:
            name = re.sub(r'[:.;,]+$', '', name.strip())
            if name and len(name) > 2:
                cleaned_names.append(name)
        
        return cleaned_names
