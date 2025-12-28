"""
Session Notes Query Router

Advanced query router for searching and retrieving information from D&D session notes.
Supports natural language queries with entity resolution and contextual understanding.
"""

import re
import time
from typing import List, Dict, Optional, Any
from difflib import SequenceMatcher

from api.database.firestore_models import SessionDocument
from .session_types import (
    UserIntention, SessionNotesContext, QueryEngineResult,
    SessionNotesQueryPerformanceMetrics
)
from .campaign_session_notes_storage import CampaignSessionNotesStorage


class SessionNotesQueryRouter:
    """Advanced query router for session notes with entity resolution and contextual search"""

    def __init__(self, campaign_storage: CampaignSessionNotesStorage):
        self.campaign_storage = campaign_storage
        self.fuzzy_threshold = 0.50  # Very low threshold - prefer over-matching to missing content

    def query(self, character_name: str, original_query: str, intention: str,
              entities: List[Dict[str, str]], context_hints: List[str], top_k: int = 5) -> QueryEngineResult:
        """Main query method that orchestrates the entire search process"""
        start_time = time.perf_counter()

        # Initialize performance tracking
        performance = SessionNotesQueryPerformanceMetrics()
        performance.entities_input = len(entities)
        performance.total_sessions_available = len(self.campaign_storage.get_all_sessions())

        # Step 1: Get relevant sessions based on intention and entities
        filter_start = time.perf_counter()
        relevant_sessions = self._get_relevant_sessions(intention, entities, context_hints)
        filter_end = time.perf_counter()
        performance.session_filtering_ms = (filter_end - filter_start) * 1000
        performance.sessions_searched = len(relevant_sessions)

        # Step 2: Build contexts for each relevant session
        context_start = time.perf_counter()
        contexts = []
        for session in relevant_sessions:
            context = self._build_session_context(
                session, intention, entities, context_hints
            )
            if context.relevance_score > 0:
                contexts.append(context)
        context_end = time.perf_counter()
        performance.context_building_ms = (context_end - context_start) * 1000
        performance.contexts_built = len(contexts)

        # Step 3: Score and sort contexts
        scoring_start = time.perf_counter()
        contexts = sorted(contexts, key=lambda c: c.relevance_score, reverse=True)
        scoring_end = time.perf_counter()
        performance.scoring_sorting_ms = (scoring_end - scoring_start) * 1000

        # Step 4: Limit to top_k results
        limiting_start = time.perf_counter()
        contexts = contexts[:top_k]
        limiting_end = time.perf_counter()
        performance.result_limiting_ms = (limiting_end - limiting_start) * 1000
        performance.results_returned = len(contexts)

        # Finalize performance metrics
        performance.total_time_ms = (time.perf_counter() - start_time) * 1000

        return QueryEngineResult(
            contexts=contexts,
            total_sessions_searched=len(relevant_sessions),
            entities_resolved=[],  # No longer resolving to Entity dataclass
            query_summary=self._generate_query_summary(character_name, original_query, intention, entities, context_hints),
            performance_metrics=performance
        )

    def _get_relevant_sessions(self, intention: str, entities: List[Dict[str, str]], context_hints: List[str]) -> List[SessionDocument]:
        """Get sessions relevant to the query based on intention and entities"""
        all_sessions = self.campaign_storage.get_all_sessions()

        # Handle temporal filters
        sessions = self._apply_temporal_filters(all_sessions, context_hints)

        # Filter by entity presence if entities specified
        if entities:
            relevant_sessions = []
            for session in sessions:
                if any(self._session_contains_entity(session, entity) for entity in entities):
                    relevant_sessions.append(session)
            sessions = relevant_sessions

        # If no entities or temporal filters, return all sessions
        if not sessions:
            sessions = all_sessions

        return sessions

    def _apply_temporal_filters(self, sessions: List[SessionDocument], context_hints: List[str]) -> List[SessionDocument]:
        """Apply temporal filters based on context hints"""
        sessions_sorted = sorted(sessions, key=lambda s: s.session_number)

        for hint in context_hints:
            hint_lower = hint.lower()

            if hint_lower in ["recent", "recently", "latest", "last"]:
                return sessions_sorted[-5:]  # Last 5 sessions
            elif hint_lower in ["early", "beginning", "first"]:
                return sessions_sorted[:5]   # First 5 sessions
            elif "between" in hint_lower:
                # Extract session range
                match = re.search(r'(\d+).*?(\d+)', hint)
                if match:
                    start, end = int(match.group(1)), int(match.group(2))
                    return [s for s in sessions if start <= s.session_number <= end]

        return sessions

    def _session_contains_entity(self, session: SessionDocument, entity: Dict[str, str]) -> bool:
        """Check if a session contains references to an entity"""
        entity_name = entity.get("name", "").lower()
        if not entity_name:
            return False

        # Check in entity lists (now List[dict])
        all_entities = session.player_characters + session.npcs + session.locations + session.items

        for session_entity in all_entities:
            session_entity_name = session_entity.get('name', '').lower()
            if entity_name in session_entity_name or session_entity_name in entity_name:
                return True
            # Check aliases
            aliases = session_entity.get('aliases', [])
            if any(entity_name in alias.lower() or alias.lower() in entity_name for alias in aliases):
                return True

        # Check in text content
        text_fields = [
            session.summary, session.cliffhanger or "",
            session.next_session_hook or ""
        ]

        for field in text_fields:
            if entity_name in field.lower():
                return True

        # Check in raw sections
        for section_text in session.raw_sections.values():
            if entity_name in section_text.lower():
                return True

        return False

    def _build_session_context(self, session: SessionDocument, intention: str, entities: List[Dict[str, str]], context_hints: List[str]) -> SessionNotesContext:
        """Build a SessionNotesContext for a specific session based on the query intention"""
        context = SessionNotesContext(
            session_number=session.session_number,
            session_summary=session.summary
        )

        # Route to intention-specific handlers
        intention_handlers = {
            "character_status": self._handle_character_status,
            "event_sequence": self._handle_event_sequence,
            "npc_info": self._handle_npc_info,
            "location_details": self._handle_location_details,
            "item_tracking": self._handle_item_tracking,
            "combat_recap": self._handle_combat_recap,
            "spell_ability_usage": self._handle_spell_ability_usage,
            "character_decisions": self._handle_character_decisions,
            "party_dynamics": self._handle_party_dynamics,
            "quest_tracking": self._handle_quest_tracking,
            "puzzle_solutions": self._handle_puzzle_solutions,
            "loot_rewards": self._handle_loot_rewards,
            "death_revival": self._handle_death_revival,
            "divine_religious": self._handle_divine_religious,
            "memory_vision": self._handle_memory_vision,
            "rules_mechanics": self._handle_rules_mechanics,
            "humor_moments": self._handle_humor_moments,
            "unresolved_mysteries": self._handle_unresolved_mysteries,
            "future_implications": self._handle_future_implications,
            "cross_session": self._handle_cross_session
        }

        handler = intention_handlers.get(intention, self._handle_generic)
        handler(session, context, entities, context_hints)

        # Calculate relevance score
        context.relevance_score = self._calculate_relevance_score(
            session, context, entities, context_hints, intention
        )

        return context

    def _handle_character_status(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle character status queries"""
        for entity in entities:
            entity_name = entity.get("name", "")
            entity_type = entity.get("type", "")

            if entity_type in ["PC", "NPC", "pc", "npc", ""]:
                # Get character status
                if entity_name in session.character_statuses:
                    context.relevant_sections["status"] = session.character_statuses[entity_name]
                    context.entities_found.append(entity_name)

                # Get recent decisions
                decisions = [d for d in session.character_decisions
                            if d.get('character', '').lower() == entity_name.lower()]
                if decisions:
                    context.relevant_sections["decisions"] = decisions

                # Get combat participation
                for encounter in session.combat_encounters:
                    enemies = encounter.get('enemies', [])
                    damage_dealt = encounter.get('damage_dealt', {})
                    damage_taken = encounter.get('damage_taken', {})
                    if (entity_name.lower() in [e.get('name', '').lower() for e in enemies] or
                        entity_name.lower() in damage_dealt or
                        entity_name.lower() in damage_taken):
                        context.relevant_sections["recent_combat"] = encounter
                        break

    def _handle_event_sequence(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle event sequence queries"""
        relevant_events = []

        for event in session.key_events:
            if entities:
                for entity in entities:
                    entity_name = entity.get("name", "")
                    # Check participants list
                    participants = event.get('participants', [])
                    if any(self._name_matches(entity_name, p.get('name', '')) for p in participants):
                        relevant_events.append(event)
                        if entity_name not in context.entities_found:
                            context.entities_found.append(entity_name)
                        break

                    # Also check if entity is mentioned in event description or location
                    description = event.get('description', '')
                    location = event.get('location', '')
                    if self._entity_mentioned_in_text(entity_name, description) or self._entity_mentioned_in_text(entity_name, location):
                        relevant_events.append(event)
                        if entity_name not in context.entities_found:
                            context.entities_found.append(entity_name)
                        break
            else:
                relevant_events.append(event)

        if relevant_events:
            context.relevant_sections["events"] = sorted(relevant_events, key=lambda e: e.get('session_number', 0))

    def _handle_npc_info(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle character information queries (NPCs and PCs)"""
        entities_found_count = 0

        for entity in entities:
            entity_name = entity.get("name", "")
            character_entity = None

            # Search in NPCs
            for npc in session.npcs:
                if self._name_matches(entity_name, npc.get('name', '')):
                    character_entity = npc
                    context.entities_found.append(entity_name)
                    entities_found_count += 1
                    break

            # If not found in NPCs, try player characters
            if not character_entity:
                for pc in session.player_characters:
                    if self._name_matches(entity_name, pc.get('name', '')):
                        character_entity = pc
                        context.entities_found.append(entity_name)
                        entities_found_count += 1
                        break

            if character_entity:
                context.relevant_sections["character"] = character_entity

                # Find quotes from this character
                character_quotes = [q for q in session.quotes
                                  if self._name_matches(entity_name, q.get("speaker", ""))]
                if character_quotes:
                    context.relevant_sections["quotes"] = character_quotes

                # Find events involving this character
                character_events = [e for e in session.key_events
                                  if any(self._name_matches(entity_name, p.get('name', '')) for p in e.get('participants', []))]
                if character_events:
                    context.relevant_sections["events"] = character_events

                # Find character status
                for status_name, status in session.character_statuses.items():
                    if self._name_matches(entity_name, status_name):
                        context.relevant_sections["status"] = status
                        break

            # Fallback: search in raw text content
            elif len(entities) <= 2:
                for section_name, section_text in session.raw_sections.items():
                    if self._entity_mentioned_in_text(entity_name, section_text):
                        if "text_mentions" not in context.relevant_sections:
                            context.relevant_sections["text_mentions"] = {}
                        context.relevant_sections["text_mentions"][section_name] = section_text
                        if entity_name not in context.entities_found:
                            context.entities_found.append(entity_name)
                            entities_found_count += 1

        # Fallback to party dynamics if multiple characters involved
        if len(entities) >= 2 and entities_found_count >= 1:
            self._add_party_dynamics_fallback(session, context, entities)

    def _handle_location_details(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle location detail queries"""
        for entity in entities:
            entity_name = entity.get("name", "")
            entity_type = entity.get("type", "")

            if entity_type in ["LOCATION", "location", ""]:
                # Find location in session
                location_entity = None
                for location in session.locations:
                    if location.get('name', '').lower() == entity_name.lower():
                        location_entity = location
                        context.entities_found.append(entity_name)
                        break

                if location_entity:
                    context.relevant_sections["location"] = location_entity

                    # Find events at this location
                    location_events = [e for e in session.key_events
                                     if e.get('location', '').lower() == entity_name.lower()]
                    if location_events:
                        context.relevant_sections["events"] = location_events

                    # Check raw sections for description
                    for section_name, section_text in session.raw_sections.items():
                        if entity_name.lower() in section_text.lower():
                            context.relevant_sections["description"] = section_text
                            break

    def _handle_item_tracking(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle item tracking queries"""
        for entity in entities:
            entity_name = entity.get("name", "")
            entity_type = entity.get("type", "")

            if entity_type in ["ITEM", "ARTIFACT", "item", "artifact", ""]:
                # Check loot obtained
                for character, items in session.loot_obtained.items():
                    if any(item.lower() == entity_name.lower() for item in items):
                        if "loot" not in context.relevant_sections:
                            context.relevant_sections["loot"] = {}
                        context.relevant_sections["loot"][character] = items
                        context.entities_found.append(entity_name)

                # Check equipment changes in character statuses
                for char_name, status in session.character_statuses.items():
                    equipment_changes = status.get('equipment_changes', [])
                    if any(entity_name.lower() in change.lower() for change in equipment_changes):
                        context.relevant_sections["equipment_changes"] = {char_name: equipment_changes}
                        context.entities_found.append(entity_name)

    def _handle_combat_recap(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle combat recap queries"""
        relevant_encounters = []

        for encounter in session.combat_encounters:
            if entities:
                for entity in entities:
                    entity_name = entity.get("name", "")
                    damage_dealt = encounter.get('damage_dealt', {})
                    damage_taken = encounter.get('damage_taken', {})
                    enemies = encounter.get('enemies', [])

                    if (entity_name.lower() in damage_dealt or
                        entity_name.lower() in damage_taken or
                        any(e.get('name', '').lower() == entity_name.lower() for e in enemies)):
                        relevant_encounters.append(encounter)
                        if entity_name not in context.entities_found:
                            context.entities_found.append(entity_name)
                        break
            else:
                relevant_encounters.append(encounter)

        if relevant_encounters:
            context.relevant_sections["encounters"] = relevant_encounters

            # Get related spells used
            related_spells = []
            for encounter in relevant_encounters:
                spells_used = encounter.get('spells_used', [])
                for spell in session.spells_abilities_used:
                    if spell.get('name', '') in spells_used:
                        related_spells.append(spell)

            if related_spells:
                context.relevant_sections["spells_used"] = related_spells

    def _handle_spell_ability_usage(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle spell and ability usage queries"""
        relevant_spells = []

        for spell_use in session.spells_abilities_used:
            if entities:
                for entity in entities:
                    entity_name = entity.get("name", "")
                    caster = spell_use.get('caster', '')
                    targets = spell_use.get('targets', [])

                    if (self._name_matches(entity_name, caster) or
                        any(self._name_matches(entity_name, target) for target in targets)):
                        relevant_spells.append(spell_use)
                        if entity_name not in context.entities_found:
                            context.entities_found.append(entity_name)
                        break
            else:
                relevant_spells.append(spell_use)

        # Filter by context hints (e.g., "combat")
        if "combat" in context_hints:
            combat_spells = []
            for spell in relevant_spells:
                for encounter in session.combat_encounters:
                    if spell.get('name', '') in encounter.get('spells_used', []):
                        combat_spells.append(spell)
                        break
            relevant_spells = combat_spells

        if relevant_spells:
            context.relevant_sections["spells"] = relevant_spells

    def _handle_character_decisions(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle character decision queries"""
        relevant_decisions = []

        for decision in session.character_decisions:
            if entities:
                for entity in entities:
                    entity_name = entity.get("name", "")
                    if self._name_matches(entity_name, decision.get('character', '')):
                        relevant_decisions.append(decision)
                        if entity_name not in context.entities_found:
                            context.entities_found.append(entity_name)
                        break
            else:
                relevant_decisions.append(decision)

        if relevant_decisions:
            context.relevant_sections["decisions"] = relevant_decisions

    def _handle_party_dynamics(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle party dynamics queries"""
        dynamics = {}

        # Include player characters information
        if session.player_characters:
            dynamics["party_members"] = session.player_characters

        if session.party_conflicts:
            dynamics["conflicts"] = session.party_conflicts

        if session.party_bonds:
            dynamics["bonds"] = session.party_bonds

        # Get relevant quotes
        if entities:
            relevant_quotes = []
            for quote in session.quotes:
                speaker = quote.get("speaker", "").lower()
                if any(entity.get("name", "").lower() == speaker for entity in entities):
                    relevant_quotes.append(quote)
            if relevant_quotes:
                dynamics["quotes"] = relevant_quotes

        # Get group-affecting decisions
        group_decisions = [d for d in session.character_decisions
                          if d.get('party_reaction') or (d.get('consequences') and "party" in d.get('consequences', '').lower())]
        if group_decisions:
            dynamics["group_decisions"] = group_decisions

        if dynamics:
            context.relevant_sections["dynamics"] = dynamics

    def _handle_quest_tracking(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle quest tracking queries"""
        quest_info = {}

        if session.quest_updates:
            quest_info["quests"] = session.quest_updates

        if session.unresolved_questions:
            quest_info["mysteries"] = session.unresolved_questions

        if session.next_session_hook:
            quest_info["next_hook"] = session.next_session_hook

        if quest_info:
            context.relevant_sections["quest_info"] = quest_info

    def _handle_puzzle_solutions(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle puzzle solution queries"""
        puzzle_info = {}

        if session.puzzles_encountered:
            puzzle_info["puzzles"] = session.puzzles_encountered

        if session.mysteries_revealed:
            puzzle_info["revealed"] = session.mysteries_revealed

        if puzzle_info:
            context.relevant_sections["puzzles"] = puzzle_info

    def _handle_loot_rewards(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle loot and rewards queries"""
        if entities:
            relevant_loot = {}
            for entity in entities:
                entity_name = entity.get("name", "")
                if entity_name in session.loot_obtained:
                    relevant_loot[entity_name] = session.loot_obtained[entity_name]
                    context.entities_found.append(entity_name)
            if relevant_loot:
                context.relevant_sections["loot"] = relevant_loot
        else:
            if session.loot_obtained:
                context.relevant_sections["loot"] = session.loot_obtained

    def _handle_death_revival(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle death and revival queries"""
        death_revival_info = {}

        if session.deaths:
            death_revival_info["deaths"] = session.deaths

        if session.revivals:
            death_revival_info["revivals"] = session.revivals

        # Check character statuses for death
        dead_characters = {name: status for name, status in session.character_statuses.items()
                          if not status.get('is_alive', True)}
        if dead_characters:
            death_revival_info["dead_status"] = dead_characters

        if death_revival_info:
            context.relevant_sections["death_revival"] = death_revival_info

    def _handle_divine_religious(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle divine and religious element queries"""
        divine_info = {}

        if session.divine_interventions:
            divine_info["interventions"] = session.divine_interventions

        if session.religious_elements:
            divine_info["religious"] = session.religious_elements

        if divine_info:
            context.relevant_sections["divine"] = divine_info

    def _handle_memory_vision(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle memory and vision queries"""
        relevant_memories = []

        for memory in session.memories_visions:
            if entities:
                for entity in entities:
                    entity_name = entity.get("name", "")
                    if self._name_matches(entity_name, memory.get('character', '')):
                        relevant_memories.append(memory)
                        if entity_name not in context.entities_found:
                            context.entities_found.append(entity_name)
                        break
            else:
                relevant_memories.append(memory)

        if relevant_memories:
            context.relevant_sections["memories"] = relevant_memories

    def _handle_rules_mechanics(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle rules and mechanics queries"""
        rules_info = {}

        if session.rules_clarifications:
            rules_info["clarifications"] = session.rules_clarifications

        if session.dice_rolls:
            rules_info["dice_rolls"] = session.dice_rolls

        if rules_info:
            context.relevant_sections["rules"] = rules_info

    def _handle_humor_moments(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle humor and fun moments queries"""
        humor_info = {}

        if session.funny_moments:
            humor_info["funny_moments"] = session.funny_moments

        # Get humorous quotes
        humorous_quotes = [q for q in session.quotes if any(word in q.get("quote", "").lower()
                          for word in ["laugh", "funny", "joke", "hilarious", "comedy"])]
        if humorous_quotes:
            humor_info["funny_quotes"] = humorous_quotes

        if humor_info:
            context.relevant_sections["humor"] = humor_info

    def _handle_unresolved_mysteries(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle unresolved mysteries queries"""
        mystery_info = {}

        if session.unresolved_questions:
            mystery_info["unresolved"] = session.unresolved_questions

        if session.mysteries_revealed:
            mystery_info["revealed"] = session.mysteries_revealed

        if mystery_info:
            context.relevant_sections["mysteries"] = mystery_info

    def _handle_future_implications(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle future implications queries"""
        future_info = {}

        if session.cliffhanger:
            future_info["cliffhanger"] = session.cliffhanger

        if session.next_session_hook:
            future_info["next_hook"] = session.next_session_hook

        if session.dm_notes:
            future_info["dm_notes"] = session.dm_notes

        if future_info:
            context.relevant_sections["future"] = future_info

    def _handle_cross_session(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Handle cross-session queries (aggregated data)"""
        self._handle_generic(session, context, entities, context_hints)

    def _handle_generic(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]], context_hints: List[str]) -> None:
        """Generic handler for unknown intentions - uses keyword search"""
        relevant_sections = {}

        # Search through all text content for context hints
        for hint in context_hints:
            hint_lower = hint.lower()

            # Check summary
            if hint_lower in session.summary.lower():
                relevant_sections["summary_match"] = session.summary

            # Check raw sections
            for section_name, section_text in session.raw_sections.items():
                if hint_lower in section_text.lower():
                    if "text_matches" not in relevant_sections:
                        relevant_sections["text_matches"] = {}
                    relevant_sections["text_matches"][section_name] = section_text

        if relevant_sections:
            context.relevant_sections.update(relevant_sections)

    def _calculate_relevance_score(self, session: SessionDocument, context: SessionNotesContext,
                                 entities: List[Dict[str, str]], context_hints: List[str], intention: str) -> float:
        """Calculate relevance score for a session context"""
        score = 0.0

        # Entity matching
        score += len(context.entities_found) * 1.0  # Primary entities

        # Content relevance
        if context.relevant_sections:
            score += 0.8

        # Context hints found
        for hint in context_hints:
            hint_lower = hint.lower()
            if any(hint_lower in str(section).lower() for section in context.relevant_sections.values()):
                score += 0.3

        # Recency bonus if requested
        if any(hint in ["recent", "recently", "latest", "last"] for hint in context_hints):
            all_sessions = self.campaign_storage.get_all_sessions()
            if all_sessions and session.date:
                max_session_date = max((s.date for s in all_sessions if s.date), default=None)
                if max_session_date:
                    days_diff = (max_session_date - session.date).days
                    score -= 0.1 * (days_diff / 30)  # Penalty based on months old

        # Completeness bonus
        if len(context.relevant_sections) > 1:
            score += 0.2

        return max(0.0, score)  # Ensure non-negative

    def _generate_query_summary(self, character_name: str, original_query: str, intention: str,
                               entities: List[Dict[str, str]], context_hints: List[str]) -> str:
        """Generate a summary of what the query was looking for"""
        entity_names = [e.get("name", "unknown") for e in entities] if entities else ["any entity"]
        entity_str = ", ".join(entity_names)

        return f"Searched for {intention} related to {entity_str} with context: {', '.join(context_hints)} for character: {character_name}"

    def _name_matches(self, search_name: str, target_name: str) -> bool:
        """Check if two names match using flexible matching"""
        search_lower = search_name.lower()
        target_lower = target_name.lower()

        # Exact match
        if search_lower == target_lower:
            return True

        # Substring matches (both directions)
        if search_lower in target_lower or target_lower in search_lower:
            return True

        return False

    def _entity_mentioned_in_text(self, entity_name: str, text: str) -> bool:
        """Check if an entity is mentioned in a text string"""
        if not text or not entity_name:
            return False

        text_lower = text.lower()
        entity_name_lower = entity_name.lower()

        # Check main name
        if entity_name_lower in text_lower:
            return True

        # For compound names like "Duskryn Nightwarden", also check first name
        name_parts = entity_name_lower.split()
        if len(name_parts) > 1:
            for part in name_parts:
                if len(part) > 2 and part in text_lower:  # Avoid matching very short parts
                    return True

        return False

    def _add_party_dynamics_fallback(self, session: SessionDocument, context: SessionNotesContext, entities: List[Dict[str, str]]) -> None:
        """Add party dynamics information as fallback when multiple characters are involved"""
        dynamics = {}

        # Get party conflicts involving any of the entities
        if session.party_conflicts:
            relevant_conflicts = []
            for conflict in session.party_conflicts:
                if any(self._entity_mentioned_in_text(e.get("name", ""), conflict) for e in entities):
                    relevant_conflicts.append(conflict)
            if relevant_conflicts:
                dynamics["conflicts"] = relevant_conflicts

        # Get party bonds involving any of the entities
        if session.party_bonds:
            relevant_bonds = []
            for bond in session.party_bonds:
                if any(self._entity_mentioned_in_text(e.get("name", ""), bond) for e in entities):
                    relevant_bonds.append(bond)
            if relevant_bonds:
                dynamics["bonds"] = relevant_bonds

        # Get quotes between the entities
        relevant_quotes = []
        for quote in session.quotes:
            speaker = quote.get("speaker", "")
            quote_text = quote.get("quote", "") + " " + quote.get("context", "")

            # Check if quote involves any of our entities
            entity_mentioned = any(
                self._name_matches(e.get("name", ""), speaker) or
                self._entity_mentioned_in_text(e.get("name", ""), quote_text)
                for e in entities
            )
            if entity_mentioned:
                relevant_quotes.append(quote)

        if relevant_quotes:
            dynamics["interaction_quotes"] = relevant_quotes

        # Get group decisions involving these entities
        relevant_decisions = []
        for decision in session.character_decisions:
            if any(self._name_matches(e.get("name", ""), decision.get('character', '')) for e in entities):
                relevant_decisions.append(decision)

        if relevant_decisions:
            dynamics["character_decisions"] = relevant_decisions

        # Add dynamics if we found anything
        if dynamics:
            if "party_dynamics" not in context.relevant_sections:
                context.relevant_sections["party_dynamics"] = {}
            context.relevant_sections["party_dynamics"].update(dynamics)
