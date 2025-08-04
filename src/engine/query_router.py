"""
Query Router - Handles Pass 1 (Source Selection) and Pass 2 (Content Targeting).
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json

from ..utils.prompt_templates.router_prompts import RouterPrompts
from ..utils.llm_client import LLMClient
from ..utils.response_models import (
    SourceSelectionResponse, 
    RulebookTargetResponse,
    CharacterTargetResponse, 
    SessionTargetResponse,
    SourceTypeEnum
)


class SourceType(Enum):
    """Available knowledge source types."""
    DND_RULEBOOK = "dnd_rulebook"
    CHARACTER_DATA = "character_data"
    SESSION_NOTES = "session_notes"


@dataclass
class SourceSelection:
    """Result of Pass 1 - which sources are needed."""
    sources_needed: List[SourceType]
    reasoning: str


@dataclass
class ContentTarget:
    """Specific content to retrieve from a source."""
    source_type: SourceType
    specific_targets: Dict[str, Any]
    reasoning: str


class QueryRouter:
    """
    Handles the first two passes of the query routing system:
    - Pass 1: Determine which knowledge sources are needed
    - Pass 2: Target specific content within those sources
    """
    
    def __init__(self, model: str = "gpt-4.1-nano"):
        """Initialize the query router with LLM client and prompt templates."""
        self.llm_client = LLMClient(model=model)
        self.router_prompts = RouterPrompts()
    
    def set_debug_callback(self, callback):
        """Set a callback function for debug logging."""
        self.llm_client.set_debug_callback(callback)
    
    async def select_sources(self, user_query: str) -> SourceSelection:
        """
        Pass 1: Analyze query and determine which knowledge sources are needed.
        
        Args:
            user_query: The user's question or request
            
        Returns:
            SourceSelection indicating which sources to use
        """
        prompt = self.router_prompts.get_source_selection_prompt(user_query)
        
        try:
            # Use structured response with function calling for better reliability
            validated_response = await self.llm_client.generate_structured_response(
                prompt, SourceSelectionResponse, use_function_calling=True
            )
            
            # Convert enum values back to our internal SourceType enum
            sources = [SourceType(source.value) for source in validated_response.sources_needed]
            
            return SourceSelection(
                sources_needed=sources, 
                reasoning=validated_response.reasoning
            )
            
        except Exception as e:
            # Fallback: assume all sources needed if routing fails
            return SourceSelection(
                sources_needed=[SourceType.DND_RULEBOOK, SourceType.CHARACTER_DATA],
                reasoning=f"Error in source selection, using fallback: {str(e)}"
            )
    
    async def target_content(self, user_query: str, sources: SourceSelection) -> List[ContentTarget]:
        """
        Pass 2: For each selected source, determine specific content to retrieve.
        
        Args:
            user_query: The user's question or request
            sources: Result from Pass 1 indicating which sources to target
            
        Returns:
            List of ContentTarget objects specifying what to retrieve
        """
        targets = []
        
        for source_type in sources.sources_needed:
            try:
                if source_type == SourceType.DND_RULEBOOK:
                    target = await self._target_rulebook_content(user_query)
                elif source_type == SourceType.CHARACTER_DATA:
                    target = await self._target_character_content(user_query)
                elif source_type == SourceType.SESSION_NOTES:
                    target = await self._target_session_content(user_query)
                else:
                    continue
                    
                targets.append(target)
                
            except Exception as e:
                # Continue with other sources if one fails
                print(f"Warning: Failed to target content for {source_type}: {str(e)}")
                continue
        
        return targets
    
    async def _target_rulebook_content(self, user_query: str) -> ContentTarget:
        """Target specific sections within the D&D rulebook."""
        prompt = self.router_prompts.get_rulebook_targeting_prompt(user_query)
        
        try:
            # Use structured response with function calling for better reliability
            validated_response = await self.llm_client.generate_structured_response(
                prompt, RulebookTargetResponse, use_function_calling=True
            )
            
            return ContentTarget(
                source_type=SourceType.DND_RULEBOOK,
                specific_targets={
                    "section_ids": validated_response.section_ids,
                    "keywords": validated_response.keywords
                },
                reasoning=validated_response.reasoning
            )
            
        except Exception as e:
            # Fallback: search by keywords extracted from query
            keywords = self._extract_keywords_from_query(user_query)
            return ContentTarget(
                source_type=SourceType.DND_RULEBOOK,
                specific_targets={"keywords": keywords},
                reasoning=f"Fallback keyword search due to validation error: {str(e)}"
            )
    
    async def _target_character_content(self, user_query: str) -> ContentTarget:
        """Target specific data within character files."""
        prompt = self.router_prompts.get_character_targeting_prompt(user_query)
        
        try:
            # Use structured response with function calling for better reliability
            validated_response = await self.llm_client.generate_structured_response(
                prompt, CharacterTargetResponse, use_function_calling=True
            )
            
            return ContentTarget(
                source_type=SourceType.CHARACTER_DATA,
                specific_targets=validated_response.file_fields,
                reasoning=validated_response.reasoning
            )
            
        except Exception as e:
            # Improved fallback: include inventory and other relevant files based on query
            fallback_targets = self._get_smart_fallback_targets(user_query)
            return ContentTarget(
                source_type=SourceType.CHARACTER_DATA,
                specific_targets=fallback_targets,
                reasoning=f"Fallback character data due to validation error: {str(e)}"
            )
    
    async def _target_session_content(self, user_query: str) -> ContentTarget:
        """Target specific session notes."""
        prompt = self.router_prompts.get_session_targeting_prompt(user_query)
        
        try:
            # Use structured response with function calling for better reliability
            validated_response = await self.llm_client.generate_structured_response(
                prompt, SessionTargetResponse, use_function_calling=True
            )
            
            return ContentTarget(
                source_type=SourceType.SESSION_NOTES,
                specific_targets={
                    "session_dates": validated_response.session_dates,
                    "keywords": validated_response.keywords
                },
                reasoning=validated_response.reasoning
            )
            
        except Exception as e:
            # Fallback: get most recent session
            return ContentTarget(
                source_type=SourceType.SESSION_NOTES,
                specific_targets={"session_dates": ["latest"]},
                reasoning=f"Fallback to latest session due to validation error: {str(e)}"
            )
    
    def _get_smart_fallback_targets(self, user_query: str) -> Dict[str, List[str]]:
        """Generate smart fallback targets based on query content."""
        query_lower = user_query.lower()
        targets = {
            "character.json": ["name", "class", "level", "ability_scores", "combat_stats"]
        }
        
        # Inventory/equipment related queries
        if any(word in query_lower for word in ["weapon", "inventory", "equipment", "armor", "item", "gear", "eldaryth"]):
            targets["inventory_list.json"] = ["all"]
        
        # Spell related queries
        if any(word in query_lower for word in ["spell", "cantrip", "magic", "cast", "slot"]):
            targets["spell_list.json"] = ["all"]
        
        # Combat/action related queries
        if any(word in query_lower for word in ["attack", "action", "combat", "damage", "smite", "hex"]):
            targets["action_list.json"] = ["all"]
            if "inventory_list.json" not in targets:  # Include weapons for combat
                targets["inventory_list.json"] = ["inventory.equipped_items.weapons"]
        
        # Character abilities/traits
        if any(word in query_lower for word in ["feat", "trait", "ability", "feature", "class", "paladin", "warlock"]):
            targets["feats_and_traits.json"] = ["all"]
        
        # Background/roleplay queries
        if any(word in query_lower for word in ["background", "story", "personality", "history", "ally", "enemy"]):
            targets["character_background.json"] = ["all"]
        
        # Objectives/contracts/quest related queries
        if any(word in query_lower for word in ["objective", "contract", "quest", "goal", "mission", "covenant", "ghul'vor", "patron", "obligation"]):
            targets["objectives_and_contracts.json"] = ["all"]
        
        # Default fallback - if nothing specific matched, include inventory anyway
        if len(targets) == 1:  # Only has basic character.json
            targets["inventory_list.json"] = ["all"]
            targets["spell_list.json"] = ["all"]
        
        return targets
    
    def _extract_keywords_from_query(self, query: str) -> List[str]:
        """Extract potential D&D keywords from the query."""
        # Simple keyword extraction - can be enhanced later
        dnd_keywords = [
            "spell", "cantrip", "attack", "damage", "ac", "armor class",
            "hit points", "hp", "saving throw", "ability check", "proficiency",
            "advantage", "disadvantage", "action", "bonus action", "reaction",
            "movement", "speed", "range", "duration", "concentration",
            "paladin", "warlock", "counterspell", "smite", "hex", "eldritch blast"
        ]
        
        query_lower = query.lower()
        found_keywords = [kw for kw in dnd_keywords if kw in query_lower]
        
        # Also extract words that might be spell or ability names
        words = query.split()
        potential_names = [word for word in words if len(word) > 3 and word.isalpha()]
        
        return found_keywords + potential_names[:5]  # Limit to avoid too many keywords