"""
Direct JSON Query Router - Uses direct JSON parsing for all LLM interactions
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from ..utils.direct_llm_client import DirectLLMClient
from ..utils.response_models import SourceTypeEnum


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
    confidence: float  # 0.0 to 1.0


@dataclass
class ContentTarget:
    """Specific content to retrieve from a source."""
    source_type: SourceType
    specific_targets: Dict[str, Any]
    reasoning: str


class QueryRouter:
    """
    Direct JSON router that uses direct JSON parsing for all LLM interactions.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize the query router with direct JSON client."""
        self.direct_client = DirectLLMClient(model=model)
    
    def set_debug_callback(self, callback):
        """Set debug callback for the direct client."""
        self.direct_client.set_debug_callback(callback)
    
    def update_model(self, model: str):
        """Update the OpenAI model used by the direct client."""
        old_callback = self.direct_client.debug_callback if hasattr(self.direct_client, 'debug_callback') else None
        self.direct_client = DirectLLMClient(model=model)
        if old_callback:
            self.direct_client.set_debug_callback(old_callback)
    
    async def _call_debug_callback(self, event_type: str, message: str, data: Dict[str, Any] = None):
        """Call debug callback if available."""
        if hasattr(self.direct_client, '_call_debug_callback'):
            try:
                await self.direct_client._call_debug_callback(event_type, message, data or {})
            except Exception as e:
                # Don't let debug callback errors break the main flow
                print(f"Debug callback error in query router: {e}")
    
    async def select_sources(self, user_query: str) -> SourceSelection:
        """
        Pass 1: Use direct JSON approach for source selection.
        Keywords provide hints to improve prompting.
        """
        await self._call_debug_callback("PASS_1_START", "Starting source selection", {"query": user_query})
        
        try:
            # Use the direct client's source selection
            result = await self.direct_client.select_sources(user_query)
            
            # Convert string source names to SourceType enums
            source_types = []
            for source_name in result["sources_needed"]:
                if source_name == "character_data":
                    source_types.append(SourceType.CHARACTER_DATA)
                elif source_name == "dnd_rulebook":
                    source_types.append(SourceType.DND_RULEBOOK)
                elif source_name == "session_notes":
                    source_types.append(SourceType.SESSION_NOTES)
            
            selection = SourceSelection(
                sources_needed=source_types,
                reasoning=result["reasoning"],
                confidence=0.8  # High confidence for direct client
            )
            
            await self._call_debug_callback("PASS_1_SUCCESS", 
                f"Selected {len(selection.sources_needed)} sources",
                {"sources": [s.value for s in selection.sources_needed],
                 "reasoning": selection.reasoning,
                 "confidence": selection.confidence})
            
            return selection
            
        except Exception as e:
            await self._call_debug_callback("PASS_1_ERROR", f"Source selection failed: {str(e)}", {"error": str(e)})
            # Use keyword-based fallback
            return self._create_keyword_fallback(user_query, str(e))
    
    async def target_content(self, user_query: str, sources: SourceSelection) -> List[ContentTarget]:
        """
        Pass 2: Use function calling for precise targeting.
        High confidence = more focused, low confidence = broader retrieval.
        """
        targets = []
        
        for source_type in sources.sources_needed:
            try:
                if source_type == SourceType.DND_RULEBOOK:
                    target = await self._target_rulebook_content(user_query, sources.confidence)
                elif source_type == SourceType.CHARACTER_DATA:
                    target = await self._target_character_content(user_query, sources.confidence)
                elif source_type == SourceType.SESSION_NOTES:
                    target = await self._target_session_content(user_query, sources.confidence)
                else:
                    continue
                    
                targets.append(target)
                
            except Exception as e:
                # Create broad fallback target
                targets.append(self._create_broad_target(source_type, user_query))
        
        return targets
    
    async def _target_rulebook_content(self, query: str, confidence: float) -> ContentTarget:
        """Target rulebook content using direct JSON approach."""
        try:
            # Use the direct client's rulebook targeting
            result = await self.direct_client.target_rulebook_content(query)
            
            return ContentTarget(
                source_type=SourceType.DND_RULEBOOK,
                specific_targets={
                    "section_ids": result.get("section_ids", []),
                    "keywords": result.get("keywords", [])
                },
                reasoning=f"Direct targeting found {len(result.get('keywords', []))} keywords and {len(result.get('section_ids', []))} section IDs"
            )
            
        except Exception as e:
            # Fallback to broad search
            words = query.split()
            keywords = [w.lower() for w in words if len(w) > 3][:10]
            
            return ContentTarget(
                source_type=SourceType.DND_RULEBOOK,
                specific_targets={"keywords": keywords, "section_ids": []},
                reasoning=f"Fallback: Using keyword extraction due to targeting error: {str(e)}"
            )
    
    async def _target_character_content(self, query: str, confidence: float) -> ContentTarget:
        """Target character data using direct JSON parsing - no function calling."""
        
        # Use the direct client for character targeting
        file_fields = await self.direct_client.target_character_files(query)
        
        # Create reasoning based on what was selected
        selected_files = list(file_fields.keys())
        reasoning = f"Direct targeting selected {len(selected_files)} files: {', '.join(selected_files)}"
        
        # Add specific reasoning for backstory queries
        if any(word in query.lower() for word in ["backstory", "background", "family", "parent", "thaldrin", "brenna"]):
            if "character_background.json" in selected_files:
                reasoning += " - correctly included character_background.json for backstory/family query"
            else:
                reasoning += " - WARNING: backstory query but character_background.json not selected"
        
        return ContentTarget(
            source_type=SourceType.CHARACTER_DATA,
            specific_targets={"file_fields": file_fields},
            reasoning=reasoning
        )
    
    async def _target_session_content(self, query: str, confidence: float) -> ContentTarget:
        """Target session notes using direct JSON approach."""
        try:
            # Use the direct client's session targeting
            result = await self.direct_client.target_session_notes(query)
            
            return ContentTarget(
                source_type=SourceType.SESSION_NOTES,
                specific_targets={
                    "session_dates": result.get("session_dates", ["latest"]),
                    "keywords": result.get("keywords", [])
                },
                reasoning=f"Direct targeting found {len(result.get('keywords', []))} keywords for {len(result.get('session_dates', []))} sessions"
            )
            
        except Exception as e:
            # Fallback to latest session with query keywords
            words = query.split()
            keywords = [w.lower() for w in words if len(w) > 3][:5]
            
            return ContentTarget(
                source_type=SourceType.SESSION_NOTES,
                specific_targets={"session_dates": ["latest"], "keywords": keywords},
                reasoning=f"Fallback: Using latest session and keywords due to targeting error: {str(e)}"
            )
    
    def _create_broad_target(self, source_type: SourceType, query: str) -> ContentTarget:
        """
        Create broad target when specific targeting fails.
        FIXED: Now includes ALL 7 character files instead of just 4.
        """
        if source_type == SourceType.CHARACTER_DATA:
            # Get ALL character files - FIX for the backstory issue
            query_lower = query.lower()
            
            # Start with core files that are almost always needed
            targets = {
                "file_fields": {
                    "character.json": ["character_base", "combat_stats", "ability_scores"],
                    "inventory_list.json": ["inventory"],
                    "spell_list.json": ["character_spells"],
                    "action_list.json": ["character_actions"],
                    # ADD THE MISSING FILES HERE - THIS IS THE KEY FIX
                    "feats_and_traits.json": ["features_and_traits"],
                    "character_background.json": ["background", "characteristics", "backstory", "organizations", "allies", "enemies", "notes"],
                    "objectives_and_contracts.json": ["objectives_and_contracts"]
                }
            }
            
            # Add specific emphasis based on query keywords
            if any(word in query_lower for word in ['backstory', 'background', 'family', 'parents', 'father', 'mother', 'thaldrin', 'brenna', 'past', 'history']):
                # Emphasize backstory fields for family-related queries
                targets["file_fields"]["character_background.json"] = [
                    "background", 
                    "characteristics", 
                    "backstory",
                    "backstory.family_backstory",
                    "backstory.family_backstory.parents",
                    "organizations",
                    "allies",
                    "enemies",
                    "notes"
                ]
                
            if any(word in query_lower for word in ['objective', 'contract', 'quest', 'goal', 'covenant', 'ghul']):
                # Emphasize objectives for quest-related queries
                targets["file_fields"]["objectives_and_contracts.json"] = [
                    "objectives_and_contracts.active_contracts",
                    "objectives_and_contracts.current_objectives",
                    "objectives_and_contracts.completed_objectives"
                ]
                
            if any(word in query_lower for word in ['feat', 'trait', 'ability', 'feature', 'lucky', 'fey']):
                # Emphasize features for ability queries
                targets["file_fields"]["feats_and_traits.json"] = [
                    "features_and_traits.class_features",
                    "features_and_traits.species_traits",
                    "features_and_traits.feats"
                ]
                
        elif source_type == SourceType.DND_RULEBOOK:
            # Extract any potential keywords
            words = query.split()
            keywords = [w.lower() for w in words if len(w) > 3][:10]
            targets = {"keywords": keywords, "section_ids": []}
        else:  # SESSION_NOTES
            targets = {"session_dates": ["latest"], "keywords": []}
        
        return ContentTarget(
            source_type=source_type,
            specific_targets=targets,
            reasoning="Broad targeting fallback - including all available character files to ensure comprehensive data access"
        )
    
    def _create_keyword_fallback(self, user_query: str, error_msg: str) -> SourceSelection:
        """Create a keyword-based fallback when direct client fails."""
        sources = []
        
        # Get keyword hints
        query_lower = user_query.lower()
        
        # Character-related keywords
        if any(word in query_lower for word in [
            'my', 'i', 'character', 'duskryn', 'paladin', 'warlock', 'spell', 'inventory', 
            'equipment', 'stat', 'level', 'ability', 'feat', 'background', 'family', 
            'parent', 'thaldrin', 'brenna', 'backstory', 'objective', 'contract'
        ]):
            sources.append(SourceType.CHARACTER_DATA)
        
        # Rulebook keywords
        if any(word in query_lower for word in [
            'rule', 'mechanic', 'spell', 'combat', 'damage', 'attack', 'condition',
            'action', 'bonus action', 'movement', 'casting', 'concentration', 'save',
            'check', 'ability', 'skill', 'advantage', 'disadvantage', 'how do', 'how does'
        ]):
            sources.append(SourceType.DND_RULEBOOK)
        
        # Session/story keywords
        if any(word in query_lower for word in [
            'party', 'campaign', 'session', 'story', 'npc', 'ghul', 'elarion', 'pork',
            'albrit', 'willow', 'zivu', 'quest', 'adventure', 'happened', 'event',
            'character', 'other', 'who', 'member'
        ]):
            sources.append(SourceType.SESSION_NOTES)
        
        # Default to all sources if none detected or if it's a complex query
        if not sources or len(user_query) > 100:
            sources = [SourceType.CHARACTER_DATA, SourceType.DND_RULEBOOK, SourceType.SESSION_NOTES]
        
        return SourceSelection(
            sources_needed=sources,
            reasoning=f"Keyword-based fallback after error: {error_msg}. Selected {len(sources)} sources based on query keywords.",
            confidence=0.3  # Low confidence for fallback
        )