"""
Central Engine & Query Processing Pipeline

Main orchestrator that makes LLM calls and coordinates the entire query processing pipeline.
Uses LLM call for tool selection + Gazetteer-based entity extraction.
Optionally runs local classifier in parallel for comparison logging.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path

# Import LLM client abstraction
from .llm.llm_client import LLMClient, LLMClientFactory
from .config import get_config
from .llm.json_repair import JSONRepair

# Import query router types
from .rag.character.character_query_router import CharacterQueryRouter, CharacterQueryResult
from .rag.character.character_query_types import UserIntention as CharacterIntention
from .rag.rulebook.rulebook_query_router import RulebookQueryRouter
from .rag.rulebook.rulebook_types import RulebookQueryIntent, SearchResult, QueryPerformanceMetrics
from .rag.session_notes.session_notes_query_router import SessionNotesQueryRouter
from .rag.session_notes.campaign_session_notes_storage import CampaignSessionNotesStorage
from .rag.session_notes.session_types import QueryEngineResult

# Import EntitySearchEngine for new architecture
from .utils.entity_search_engine import EntitySearchEngine

# Import query normalization for placeholder substitution
from .utils.query_normalization import apply_entity_placeholders

# Import tool intentions from single source of truth
from .rag.tool_intentions import get_fallback_intention

# Import Gazetteer-based entity extraction
from .classifiers.gazetteer_ner import GazetteerEntityExtractor, Entity

# ===== SINGLETON LOCAL CLASSIFIER =====
# Shared across all CentralEngine instances to avoid repeated model loading
_local_classifier_singleton: Optional[Any] = None
_local_classifier_lock = asyncio.Lock() if hasattr(asyncio, 'Lock') else None


def get_local_classifier():
    """Get or create the singleton local classifier instance.
    
    Uses config defaults for all paths and settings.
    """
    global _local_classifier_singleton
    
    if _local_classifier_singleton is not None:
        return _local_classifier_singleton
    
    try:
        from .classifiers.local_classifier import LocalClassifier
        config = get_config()
        
        print("[LocalClassifier] Loading singleton instance...")
        start = time.time()
        
        # LocalClassifier reads paths from config by default
        _local_classifier_singleton = LocalClassifier(
            device=config.local_classifier_device,
            gazetteer_min_similarity=config.gazetteer_min_similarity
        )
        
        elapsed = time.time() - start
        print(f"[LocalClassifier] Singleton loaded in {elapsed:.2f}s")
    except ImportError as e:
        print(f"[LocalClassifier] Could not import: {e}")
    except Exception as e:
        print(f"[LocalClassifier] Failed to initialize: {e}")
    
    return _local_classifier_singleton


# ===== ROUTER OUTPUT DATACLASSES =====

@dataclass
class ToolSelectorOutput:
    """Output from Tool & Intention Selector LLM call."""
    tools_needed: List[Dict[str, Any]] = field(default_factory=list)
    # Each tool dict: {"tool": "character_data", "intention": "combat_info", "confidence": 0.95}


@dataclass
class EntityExtractorOutput:
    """Output from Entity Extractor LLM call."""
    entities: List[Dict[str, Any]] = field(default_factory=list)
    # Each entity dict: {"name": "Eldaryth of Regret", "confidence": 1.0}


# ===== CENTRAL ENGINE =====

class CentralEngine:
    """Main orchestrator - makes all LLM calls and coordinates the pipeline."""
    
    def __init__(self, llm_clients: Dict[str, LLMClient], prompt_manager, 
                 character=None, rulebook_storage=None, campaign_session_notes=None,
                 entity_search_engine=None):
        """Initialize with LLM clients and prompt manager.
        
        Args:
            llm_clients: Dictionary of LLM client instances
            prompt_manager: CentralPromptManager instance
            character: Character object (optional)
            rulebook_storage: RulebookStorage instance (optional)
            campaign_session_notes: CampaignSessionNotesStorage instance (optional)
            entity_search_engine: EntitySearchEngine instance (optional)
        """
        self.llm_clients = llm_clients
        self.prompt_manager = prompt_manager
        self.config = get_config()

        # Store data sources for entity resolution
        self.character = character
        self.rulebook_storage = rulebook_storage
        self.campaign_session_notes = campaign_session_notes

        # Initialize EntitySearchEngine
        self.entity_search_engine = entity_search_engine or EntitySearchEngine()

        # Initialize Gazetteer-based entity extractor (replaces LLM entity extraction)
        self.entity_extractor = self._init_entity_extractor()

        # Initialize query routers with required storage instances
        self.character_router = CharacterQueryRouter(character) if character else None
        self.rulebook_router = RulebookQueryRouter(rulebook_storage) if rulebook_storage else None
        self.session_notes_router = SessionNotesQueryRouter(campaign_session_notes) if campaign_session_notes else None

        # Conversation history tracking
        self.conversation_history: List[Dict[str, str]] = []

        # Initialize local classifier if needed (for "local" or "comparison" routing modes)
        self.local_classifier = None
        if self.config.routing_mode in ("local", "comparison"):
            self._init_local_classifier()
    
    def _init_entity_extractor(self) -> Optional[GazetteerEntityExtractor]:
        """Initialize the Gazetteer-based entity extractor with all available data sources."""
        try:
            project_root = Path(__file__).parent.parent
            srd_cache_path = project_root / self.config.local_classifier_srd_cache
            
            if not srd_cache_path.exists():
                print(f"[CentralEngine] SRD cache not found at {srd_cache_path}")
                return None
            
            extractor = GazetteerEntityExtractor(
                cache_path=srd_cache_path,
                min_similarity=self.config.gazetteer_min_similarity
            )
            
            # Add character and session note context
            entity_counts = extractor.add_character_context(
                character=self.character,
                session_storage=self.campaign_session_notes
            )
            
            print(f"[CentralEngine] Gazetteer entity extractor initialized: {extractor.get_entity_count()}")
            return extractor
            
        except Exception as e:
            print(f"[CentralEngine] Failed to initialize entity extractor: {e}")
            return None
    
    def reload_entity_context(self) -> None:
        """Reload dynamic entities in the gazetteer when character/session data changes."""
        if self.entity_extractor:
            self.entity_extractor.reload_context(
                character=self.character,
                session_storage=self.campaign_session_notes
            )
    
    def _init_local_classifier(self) -> None:
        """Initialize the local classifier using singleton pattern."""
        self.local_classifier = get_local_classifier()
        if self.local_classifier:
            print("[CentralEngine] Using shared local classifier instance")
    
    @classmethod
    def create_from_config(cls, prompt_manager, character=None, 
                          rulebook_storage=None, campaign_session_notes=None):
        """Create CentralEngine instance using default configuration.
        
        Args:
            prompt_manager: CentralPromptManager instance
            character: Character object (optional)
            rulebook_storage: RulebookStorage instance (optional)
            campaign_session_notes: CampaignSessionNotesStorage instance (optional)
        """
        llm_clients = LLMClientFactory.create_default_clients()
        return cls(llm_clients, prompt_manager, character, rulebook_storage, campaign_session_notes)
    
    def add_conversation_turn(self, role: str, content: str):
        """Add a turn to the conversation history.
        
        Args:
            role: Either "user" or "assistant"
            content: The message content
        """
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def clear_conversation_history(self):
        """Clear all conversation history."""
        self.conversation_history = []
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history."""
        return self.conversation_history.copy()
    
    async def process_query(self, user_query: str, character_name: str) -> str:
        """
        Main processing pipeline:
        1. Call tool selector LLM + extract entities via Gazetteer (fast, parallel)
        2. Resolve entities using EntitySearchEngine with selected tools
        3. Distribute entities to appropriate RAG tools
        4. Execute needed query routers in parallel
        5. Generate final response
        """
        print(f"🔧 DEBUG: Processing query: '{user_query}'")
        
        # Step 1: Tool selector LLM call + Gazetteer entity extraction (in parallel)
        print("🔧 DEBUG: Step 1 - Tool selector LLM + Gazetteer entity extraction")
        
        # Run LLM call async, gazetteer is fast and runs sync
        tool_selector_task = self._call_tool_selector(user_query, character_name)
        
        # Extract entities using Gazetteer (fast, <1ms typically)
        entity_extractor_output = self._extract_entities_gazetteer(user_query)
        
        # Wait for tool selector
        tool_selector_output = await tool_selector_task
        
        print(f"🔧 DEBUG: Tool selector returned {len(tool_selector_output.tools_needed)} tools")
        print(f"🔧 DEBUG: Gazetteer extracted {len(entity_extractor_output.entities)} entities")
        for e in entity_extractor_output.entities[:5]:  # Show first 5
            print(f"   - {e.get('name')} ({e.get('type')}, conf={e.get('confidence', 1.0):.2f})")
        
        # Step 2: Derive selected tools from tool selector output
        selected_tools = [t["tool"] for t in tool_selector_output.tools_needed]
        print(f"🔧 DEBUG: Step 2 - Selected tools: {selected_tools}")
        
        # Step 3: Resolve entities across ALL tools (not just selected)
        # This ensures we find every bit of context that matches, regardless of classifier routing
        print(f"🔧 DEBUG: Step 3 - Resolving entities across ALL tools...")
        all_tools = ['character_data', 'session_notes', 'rulebook']
        entity_results = {}
        if entity_extractor_output.entities:
            entity_results = self.entity_search_engine.resolve_entities(
                entities=entity_extractor_output.entities,
                selected_tools=all_tools,  # Always search ALL tools
                character=self.character,
                session_notes_storage=self.campaign_session_notes,
                rulebook_storage=self.rulebook_storage
            )
            print(f"🔧 DEBUG: Entity resolution found {len(entity_results)} entities")
            print(f"🔧 DEBUG: Entity results detail: {entity_results}")
        else:
            print("🔧 DEBUG: No entities to resolve")
        
        # Step 4: Distribute entities to RAG tools based on where they were found
        print(f"🔧 DEBUG: Step 4 - Distributing entities to RAG tools...")
        entity_distribution = self._distribute_entities_to_rag_queries(
            entity_results, 
            tool_selector_output.tools_needed
        )
        print(f"🔧 DEBUG: Entity distribution: {entity_distribution}")
        print(f"🔧 DEBUG: Tools needed: {tool_selector_output.tools_needed}")
        
        # Step 4.5: Add fallback tools if entities were found there but tool wasn't selected
        tools_with_entities = set(entity_distribution.keys())
        selected_tool_names = {t["tool"] for t in tool_selector_output.tools_needed}
        new_tools_needed = tools_with_entities - selected_tool_names
        
        if new_tools_needed:
            print(f"🔧 DEBUG: Step 4.5 - Adding fallback tools with entities: {new_tools_needed}")
            for tool in new_tools_needed:
                # Add tool with fallback intention from single source of truth
                tool_selector_output.tools_needed.append({
                    "tool": tool,
                    "intention": get_fallback_intention(tool),
                    "confidence": 0.75
                })
            print(f"🔧 DEBUG: Updated tools needed: {tool_selector_output.tools_needed}")
        
        # Step 5: Execute RAG queries for selected tools
        print(f"🔧 DEBUG: Step 5 - Executing RAG queries...")
        raw_results = await self._execute_rag_queries(
            tool_selector_output.tools_needed,
            entity_distribution,
            entity_results,
            user_query
        )
        
        # Step 6: Generate final response
        print(f"🔧 DEBUG: Step 6 - Generating final response...")
        final_response = await self.generate_final_response(raw_results, user_query)
        
        return final_response
    
    async def process_query_stream(self, user_query: str, character_name: str, metadata_callback=None):
        """
        Main processing pipeline with streaming final response.
        Performs all routing and RAG queries, then streams the final response.
        
        Args:
            user_query: User's question
            character_name: Name of the character
            metadata_callback: Optional async callback function for emitting metadata events.
                              Called with (event_type: str, data: dict)
        
        Yields:
            str: Chunks of the final response as they are generated
        """
        print(f"🔧 DEBUG: Processing query (streaming): '{user_query}'")

        # Track timing for performance metrics
        start_time = time.time()
        timing = {}

        # Add user query to conversation history
        self.add_conversation_turn("user", user_query)

        # ===== NEW PIPELINE: Entity extraction FIRST, then normalize, then route =====

        # Step 1a: Extract entities using Gazetteer (fast, synchronous)
        print("🔧 DEBUG: Step 1a - Gazetteer entity extraction")
        step1_start = time.time()
        entity_extractor_output = self._extract_entities_gazetteer(user_query)

        print(f"🔧 DEBUG: Gazetteer extracted {len(entity_extractor_output.entities)} entities")
        for e in entity_extractor_output.entities[:5]:  # Show first 5
            print(f"   - {e.get('name')} ({e.get('type')}, conf={e.get('confidence', 1.0):.2f})")

        # Step 1b: Apply placeholders to create normalized query for routing
        print("🔧 DEBUG: Step 1b - Applying entity placeholders")
        normalized_query = apply_entity_placeholders(
            user_query,
            character_name,
            entity_extractor_output.entities
        )
        print(f"🔧 DEBUG: Normalized query: '{normalized_query}'")

        # Step 1c: Run classifier(s) based on routing_mode config
        routing_mode = self.config.routing_mode
        print(f"🔧 DEBUG: Step 1c - Routing mode: {routing_mode}")

        local_classifier_result = None
        tool_selector_output = None

        if routing_mode == "local":
            # Local classifier only - fast, no API calls
            print("🧠 LOCAL CLASSIFIER ROUTING:")
            if self.local_classifier:
                local_classifier_result = await self._run_local_classifier(normalized_query)
                if local_classifier_result:
                    tool_selector_output = ToolSelectorOutput(tools_needed=local_classifier_result.tools_needed)
                    print(f"   ⏱️ {local_classifier_result.inference_time_ms:.1f}ms")
                    for tool in local_classifier_result.tools_needed:
                        conf = tool.get('confidence', 0)
                        print(f"   - {tool['tool']}: {tool['intention']} ({conf:.1%})")
                else:
                    print("   ⚠️ Local classifier failed, falling back to Haiku")
                    tool_selector_output = await self._call_tool_selector(normalized_query, character_name)
            else:
                print("   ⚠️ Local classifier not available, falling back to Haiku")
                tool_selector_output = await self._call_tool_selector(normalized_query, character_name)

        elif routing_mode == "comparison":
            # Run BOTH classifiers in parallel - Haiku is primary, local for UI comparison
            print("🔧 DEBUG: Running Haiku + Local classifier in parallel")
            tasks = [self._call_tool_selector(normalized_query, character_name)]
            if self.local_classifier:
                tasks.append(self._run_local_classifier(normalized_query))

            results = await asyncio.gather(*tasks)
            tool_selector_output = results[0]
            local_classifier_result = results[1] if len(results) > 1 else None

            print(f"🤖 HAIKU ROUTING (PRIMARY):")
            for tool in tool_selector_output.tools_needed:
                conf = tool.get('confidence', 0)
                print(f"   - {tool['tool']}: {tool['intention']} ({conf:.1%})")

            if local_classifier_result:
                print(f"🧠 LOCAL CLASSIFIER (COMPARISON, ⏱️ {local_classifier_result.inference_time_ms:.1f}ms):")
                for tool in local_classifier_result.tools_needed:
                    conf = tool.get('confidence', 0)
                    print(f"   - {tool['tool']}: {tool['intention']} ({conf:.1%})")

        else:  # "haiku" (default)
            # Haiku only - for collecting training data
            print("🤖 HAIKU ROUTING:")
            tool_selector_output = await self._call_tool_selector(normalized_query, character_name)
            for tool in tool_selector_output.tools_needed:
                conf = tool.get('confidence', 0)
                print(f"   - {tool['tool']}: {tool['intention']} ({conf:.1%})")

        timing['routing_and_entities'] = (time.time() - step1_start) * 1000  # Convert to ms

        # Emit routing metadata
        if metadata_callback:
            # Determine classifier backend based on what was actually used for routing
            classifier_backend = 'local' if routing_mode == 'local' else 'llm'

            routing_metadata = {
                'tools_needed': [dict(t) for t in tool_selector_output.tools_needed],
                'classifier_backend': classifier_backend,
                'normalized_query': normalized_query,  # The placeholder-ized query
                'extracted_entities': [
                    {
                        'name': e.get('name', ''),
                        'text': e.get('text', ''),
                        'type': e.get('type', ''),
                        'confidence': e.get('confidence', 1.0)
                    }
                    for e in (entity_extractor_output.entities or [])
                ]
            }

            # Include local classifier results for UI comparison (only in comparison mode)
            if local_classifier_result and routing_mode == "comparison":
                routing_metadata['local_tools_needed'] = [dict(t) for t in local_classifier_result.tools_needed]
                routing_metadata['local_inference_time_ms'] = local_classifier_result.inference_time_ms

            await metadata_callback('routing_metadata', routing_metadata)
        
        # Step 2: Derive selected tools from tool selector output
        selected_tools = [t["tool"] for t in tool_selector_output.tools_needed]
        print(f"🔧 DEBUG: Step 2 - Selected tools: {selected_tools}")
        
        # Step 3: Resolve entities across ALL tools (not just selected)
        # This ensures we find every bit of context that matches, regardless of classifier routing
        print(f"🔧 DEBUG: Step 3 - Resolving entities across ALL tools...")
        step3_start = time.time()
        all_tools = ['character_data', 'session_notes', 'rulebook']
        entity_results = {}
        if entity_extractor_output.entities:
            entity_results = self.entity_search_engine.resolve_entities(
                entities=entity_extractor_output.entities,
                selected_tools=all_tools,  # Always search ALL tools
                character=self.character,
                session_notes_storage=self.campaign_session_notes,
                rulebook_storage=self.rulebook_storage
            )
            print(f"🔧 DEBUG: Entity resolution found {len(entity_results)} entities")
            print(f"🔧 DEBUG: Entity results detail: {entity_results}")
        else:
            print("🔧 DEBUG: No entities to resolve")
        
        # Step 4: Distribute entities to RAG tools based on where they were found
        print(f"🔧 DEBUG: Step 4 - Distributing entities to RAG tools...")
        entity_distribution = self._distribute_entities_to_rag_queries(
            entity_results, 
            tool_selector_output.tools_needed
        )
        print(f"🔧 DEBUG: Entity distribution: {entity_distribution}")
        print(f"🔧 DEBUG: Tools needed: {tool_selector_output.tools_needed}")
        
        # Step 4.5: Add fallback tools if entities were found there but tool wasn't selected
        tools_with_entities = set(entity_distribution.keys())
        selected_tool_names = {t["tool"] for t in tool_selector_output.tools_needed}
        new_tools_needed = tools_with_entities - selected_tool_names
        
        if new_tools_needed:
            print(f"🔧 DEBUG: Step 4.5 - Adding fallback tools with entities: {new_tools_needed}")
            for tool in new_tools_needed:
                # Add tool with fallback intention from single source of truth
                tool_selector_output.tools_needed.append({
                    "tool": tool,
                    "intention": get_fallback_intention(tool),
                    "confidence": 0.75
                })
            print(f"🔧 DEBUG: Updated tools needed: {tool_selector_output.tools_needed}")
        
        timing['entity_resolution'] = (time.time() - step3_start) * 1000
        
        # Emit entities metadata
        if metadata_callback:
            await metadata_callback('entities_metadata', {
                'entities': [
                    {
                        'name': name,
                        'found_in_sections': [r.found_in_sections for r in results],
                        'match_confidence': [r.match_confidence for r in results],
                        'match_strategy': [r.match_strategy for r in results]
                    }
                    for name, results in entity_results.items()
                ]
            })
        
        # Step 5: Execute RAG queries for selected tools
        print(f"🔧 DEBUG: Step 5 - Executing RAG queries...")
        step5_start = time.time()
        raw_results = await self._execute_rag_queries(
            tool_selector_output.tools_needed,
            entity_distribution,
            entity_results,
            user_query
        )
        timing['rag_queries'] = (time.time() - step5_start) * 1000
        
        # Emit context sources metadata
        if metadata_callback:
            context_sources = self._extract_context_sources(raw_results)
            await metadata_callback('context_sources', context_sources)
        
        # Step 6: Stream final response
        print(f"🔧 DEBUG: Step 6 - Streaming final response...")
        step6_start = time.time()
        
        # Determine model being used for metadata
        provider = self.config.final_response_llm_provider
        if provider == "openai":
            model_used = self.config.openai_final_model
        elif provider == "anthropic":
            model_used = self.config.anthropic_final_model
        else:
            model_used = None
        
        # Capture the full response as we stream it
        full_response = ""
        async for chunk in self.generate_final_response_stream(raw_results, user_query):
            full_response += chunk
            yield chunk
        
        timing['response_generation'] = (time.time() - step6_start) * 1000
        timing['total'] = (time.time() - start_time) * 1000
        
        # Emit performance metrics
        if metadata_callback:
            await metadata_callback('performance_metrics', {'timing': timing})
        
        # Emit response metadata for query logging
        if metadata_callback:
            await metadata_callback('response_metadata', {
                'assistant_response': full_response,
                'response_time_ms': timing['total'],
                'model_used': model_used
            })
        
        # Add assistant response to conversation history
        self.add_conversation_turn("assistant", full_response)
    
    async def generate_final_response(self, raw_results: Dict[str, Any], user_query: str) -> str:
        """
        Get final response prompt from Prompt Manager and make final LLM call.
        Returns completed response to user.
        """
        # Get final response prompt from Prompt Manager/Context Assembler
        final_prompt = self.prompt_manager.get_final_response_prompt(raw_results, user_query)
        
        # Make final LLM call for response generation using configured provider and model
        try:
            # Use configured final response provider
            provider = self.config.final_response_llm_provider
            final_client = self.llm_clients.get(provider)
            
            if not final_client:
                # Fallback to available clients using new naming convention
                final_client = (self.llm_clients.get("openai") or 
                               self.llm_clients.get("anthropic"))
                if not final_client:
                    return "Error: No suitable LLM client available for final response generation"
            
            # Select appropriate model based on provider
            if provider == "openai":
                model = self.config.openai_final_model
            elif provider == "anthropic":
                model = self.config.anthropic_final_model
            else:
                model = None  # Use client default
            
            # Get LLM parameters from config
            llm_params = self.config.get_final_llm_params(model)
            
            response = await final_client.generate_response(
                final_prompt,
                model=model,
                **llm_params
            )
            
            if response.success:
                return response.content
            else:
                return f"Error generating final response: {response.error}"
        except Exception as e:
            return f"Error generating final response: {str(e)}"
    
    async def generate_final_response_stream(self, raw_results: Dict[str, Any], user_query: str):
        """
        Get final response prompt from Prompt Manager and stream the LLM response.
        Yields response chunks as they arrive.
        
        Yields:
            str: Chunks of the response as they are generated
        """
        # Get final response prompt from Prompt Manager/Context Assembler
        final_prompt = self.prompt_manager.get_final_response_prompt(raw_results, user_query)
        
        try:
            # Use configured final response provider
            provider = self.config.final_response_llm_provider
            final_client = self.llm_clients.get(provider)
            
            if not final_client:
                # Fallback to available clients
                final_client = (self.llm_clients.get("openai") or 
                               self.llm_clients.get("anthropic"))
                if not final_client:
                    yield "Error: No suitable LLM client available for final response generation"
                    return
            
            # Select appropriate model based on provider
            if provider == "openai":
                model = self.config.openai_final_model
            elif provider == "anthropic":
                model = self.config.anthropic_final_model
            else:
                model = None  # Use client default
            
            # Get LLM parameters from config
            llm_params = self.config.get_final_llm_params(model)
            
            # Stream the response with conversation history
            async for chunk in final_client.generate_response_stream(
                final_prompt,
                model=model,
                conversation_history=self.conversation_history[:-1],  # Exclude current user query (already in prompt)
                **llm_params
            ):
                yield chunk
                
        except Exception as e:
            yield f"\n[Error generating final response: {str(e)}]"
    
    
    # ===== HELPER METHODS =====
    
    async def _call_tool_selector(self, user_query: str, character_name: str) -> ToolSelectorOutput:
        """
        Make LLM call for Tool & Intention Selector.
        Determines which RAG tools are needed and what intention to use for each.
        """
        start_time = time.time()
        try:
            history = self.conversation_history[:-1] if len(self.conversation_history) > 0 else []
            
            prompt = self.prompt_manager.get_tool_and_intention_selector_prompt(
                user_query, 
                character_name,
                character=self.character,
                conversation_history=history
            )
            
            provider = self.config.router_llm_provider
            client = self.llm_clients.get(provider) or self.llm_clients.get("openai") or self.llm_clients.get("anthropic")
            
            if not client:
                raise RuntimeError("No suitable LLM client available for tool selector")
            
            model = self.config.openai_router_model if provider == "openai" else self.config.anthropic_router_model if provider == "anthropic" else None
            llm_params = self.config.get_router_llm_params(model)
            
            response = await client.generate_json_response(prompt, model=model, **llm_params)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Debug: Print raw response with timing
            print(f"🔍 RAW TOOL SELECTOR RESPONSE (⏱️ {elapsed_ms:.0f}ms):")
            print(f"   Type: {type(response)}")
            if hasattr(response, 'content'):
                print(f"   Content: {response.content}")
            elif isinstance(response, dict):
                print(f"   Dict: {response}")
            else:
                print(f"   Value: {response}")
            
            repair_result = JSONRepair.repair_tool_selector_response(response)
            
            if repair_result.was_repaired:
                print(f"🔧 JSON REPAIR: Tool selector response was repaired")
                for detail in repair_result.repair_details:
                    print(f"   • {detail}")
            
            return ToolSelectorOutput(tools_needed=repair_result.data.get("tools_needed", []))
            
        except Exception as e:
            raise RuntimeError(f"Tool selector LLM call failed: {str(e)}") from e
    
    def _extract_entities_gazetteer(self, user_query: str) -> EntityExtractorOutput:
        """
        Extract entities using the Gazetteer-based NER system.
        
        This is the primary entity extraction method, replacing the LLM call.
        Uses fuzzy matching against:
        - SRD entities (spells, monsters, items, conditions, etc.)
        - Character name and aliases
        - Party member names from session notes
        - NPC names from session notes
        - Locations, items, factions from session notes
        
        Returns EntityExtractorOutput compatible with the existing pipeline.
        """
        if not self.entity_extractor:
            print("⚠️ Gazetteer entity extractor not available")
            return EntityExtractorOutput(entities=[])
        
        start_time = time.time()
        
        # Extract entities using gazetteer
        raw_entities = self.entity_extractor.extract_simple(user_query)
        
        # Convert to format expected by EntitySearchEngine (needs 'name' field)
        entities = []
        for e in raw_entities:
            entities.append({
                'name': e['canonical'],  # Use canonical name for lookups
                'text': e['text'],       # Original text from query
                'type': e['type'],       # Entity type (SPELL, CHARACTER, NPC, etc.)
                'confidence': e['confidence'],
                'is_dynamic': e.get('is_dynamic', False)  # Whether from SRD or session data
            })
        
        elapsed_ms = (time.time() - start_time) * 1000
        print(f"🔍 GAZETTEER ENTITY EXTRACTION (⏱️ {elapsed_ms:.1f}ms): {len(entities)} entities found")
        
        return EntityExtractorOutput(entities=entities)
    
    async def _run_local_classifier(self, user_query: str) -> Optional[Any]:
        """
        Run local classifier for comparison logging.
        Returns ClassificationResult or None if local classifier not available.
        
        Passes character name and known names for placeholder normalization.
        The model was trained on {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholders.
        """
        if not self.local_classifier:
            return None
        
        try:
            # Extract character name and aliases
            character_name = None
            character_aliases = []
            if self.character and hasattr(self.character, 'character_base'):
                character_name = self.character.character_base.name
                # Extract first name as an alias
                if character_name and ' ' in character_name:
                    first_name = character_name.split()[0]
                    character_aliases.append(first_name)
                    # Common nickname patterns (first 4 chars if name is long enough)
                    if len(first_name) > 4:
                        character_aliases.append(first_name[:4])
            
            # Extract party members from session notes entities
            party_members = self._extract_party_members()
            
            # Extract known NPCs from session notes entities
            known_npcs = self._extract_known_npcs()
            
            # Get classification result
            result = await self.local_classifier.classify(
                user_query,
                character_name=character_name,
                character_aliases=character_aliases,
                conversation_history=self.conversation_history,
                party_members=party_members,
                known_npcs=known_npcs
            )
            
            # Use gazetteer entities for comparison (same as main pipeline)
            if result and self.entity_extractor:
                gazetteer_output = self._extract_entities_gazetteer(user_query)
                result.entities = gazetteer_output.entities
            
            return result
        except Exception as e:
            print(f"⚠️ Local classifier error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_party_members(self) -> List[str]:
        """Extract party member names from session notes storage.
        
        Uses the entities stored in campaign session notes, filtering by
        'player_character' entity type. Returns names and aliases.
        """
        party_members = []
        if not self.campaign_session_notes:
            return party_members
        
        # Check for entities in the campaign storage
        if hasattr(self.campaign_session_notes, 'entities') and self.campaign_session_notes.entities:
            for entity_id, entity in self.campaign_session_notes.entities.items():
                # Get entity type
                entity_type = None
                if hasattr(entity, 'entity_type'):
                    entity_type = str(entity.entity_type.value) if hasattr(entity.entity_type, 'value') else str(entity.entity_type)
                elif isinstance(entity, dict) and 'entity_type' in entity:
                    entity_type = entity['entity_type']
                
                # Only include player characters (party members)
                if entity_type and 'player_character' in entity_type.lower():
                    # Get name
                    name = entity.name if hasattr(entity, 'name') else entity.get('name', '')
                    if name:
                        party_members.append(name)
                    
                    # Get aliases
                    aliases = []
                    if hasattr(entity, 'aliases'):
                        aliases = entity.aliases
                    elif isinstance(entity, dict) and 'aliases' in entity:
                        aliases = entity['aliases']
                    
                    party_members.extend([a for a in aliases if a])
        
        return list(set(party_members))  # Remove duplicates
    
    def _extract_known_npcs(self) -> List[str]:
        """Extract known NPC names from session notes storage.
        
        Uses the entities stored in campaign session notes, filtering by
        'non_player_character' or 'npc' entity type. Returns names and aliases.
        """
        known_npcs = []
        if not self.campaign_session_notes:
            return known_npcs
        
        # Check for entities in the campaign storage
        if hasattr(self.campaign_session_notes, 'entities') and self.campaign_session_notes.entities:
            for entity_id, entity in self.campaign_session_notes.entities.items():
                # Get entity type
                entity_type = None
                if hasattr(entity, 'entity_type'):
                    entity_type = str(entity.entity_type.value) if hasattr(entity.entity_type, 'value') else str(entity.entity_type)
                elif isinstance(entity, dict) and 'entity_type' in entity:
                    entity_type = entity['entity_type']
                
                # Only include NPCs
                if entity_type and ('non_player_character' in entity_type.lower() or 'npc' in entity_type.lower()):
                    # Get name
                    name = entity.name if hasattr(entity, 'name') else entity.get('name', '')
                    if name:
                        known_npcs.append(name)
                    
                    # Get aliases
                    aliases = []
                    if hasattr(entity, 'aliases'):
                        aliases = entity.aliases
                    elif isinstance(entity, dict) and 'aliases' in entity:
                        aliases = entity['aliases']
                    
                    known_npcs.extend([a for a in aliases if a])
        
        return list(set(known_npcs))  # Remove duplicates
    
    async def _log_classifier_comparison(
        self,
        user_query: str,
        llm_tools: ToolSelectorOutput,
        llm_entities: EntityExtractorOutput,
        local_result: Any,
        metadata_callback: Optional[Any] = None
    ) -> None:
        """
        Log comparison between LLM and local classifier results.
        
        Emits comparison metadata and prints debug info.
        """
        print("\n" + "=" * 70)
        print("🔬 CLASSIFIER COMPARISON")
        print("=" * 70)
        print(f"Query: \"{user_query}\"")
        print()
        
        # Compare tools
        llm_tool_names = set(t["tool"] for t in llm_tools.tools_needed)
        local_tool_names = set(t["tool"] for t in local_result.tools_needed)
        
        print("📊 TOOL SELECTION:")
        print(f"   LLM Tools:   {sorted(llm_tool_names) or '(none)'}")
        print(f"   Local Tools: {sorted(local_tool_names) or '(none)'}")
        
        if llm_tool_names == local_tool_names:
            print("   ✅ MATCH")
        else:
            only_llm = llm_tool_names - local_tool_names
            only_local = local_tool_names - llm_tool_names
            if only_llm:
                print(f"   ⚠️ Only in LLM: {sorted(only_llm)}")
            if only_local:
                print(f"   ⚠️ Only in Local: {sorted(only_local)}")
        
        # Compare intents per tool
        print("\n🎯 INTENTS:")
        llm_intents = {t["tool"]: t.get("intention", "?") for t in llm_tools.tools_needed}
        local_intents = {t["tool"]: t.get("intention", "?") for t in local_result.tools_needed}
        all_tools = llm_tool_names | local_tool_names
        for tool in sorted(all_tools):
            llm_intent = llm_intents.get(tool, "-")
            local_intent = local_intents.get(tool, "-")
            match = "✅" if llm_intent == local_intent else "⚠️"
            print(f"   {tool}: LLM={llm_intent}, Local={local_intent} {match}")
        
        # Compare entities
        print("\n🏷️ ENTITIES:")
        llm_entity_names = set(e.get("name", "") for e in llm_entities.entities)
        local_entity_names = set(e.get("name", "") for e in local_result.entities)
        
        print(f"   LLM Entities:   {sorted(llm_entity_names) or '(none)'}")
        print(f"   Local Entities: {sorted(local_entity_names) or '(none)'}")
        
        if llm_entity_names == local_entity_names:
            print("   ✅ MATCH")
        else:
            only_llm = llm_entity_names - local_entity_names
            only_local = local_entity_names - llm_entity_names
            if only_llm:
                print(f"   ⚠️ Only in LLM: {sorted(only_llm)}")
            if only_local:
                print(f"   ⚠️ Only in Local: {sorted(only_local)}")
        
        # Show local classifier confidence scores
        print("\n📈 LOCAL CONFIDENCE:")
        for tool, conf in sorted(local_result.tool_confidences.items()):
            marker = "✓" if conf > self.config.local_classifier_tool_threshold else "✗"
            print(f"   {tool}: {conf:.2%} {marker}")
        
        print(f"\n⏱️ Local inference time: {local_result.inference_time_ms:.1f}ms")
        print("=" * 70 + "\n")
        
        # Emit comparison metadata if callback provided
        if metadata_callback:
            await metadata_callback('classifier_comparison', {
                'query': user_query,
                'llm': {
                    'tools': list(llm_tool_names),
                    'intents': llm_intents,
                    'entities': list(llm_entity_names)
                },
                'local': {
                    'tools': list(local_tool_names),
                    'intents': local_intents,
                    'entities': list(local_entity_names),
                    'tool_confidences': local_result.tool_confidences,
                    'inference_time_ms': local_result.inference_time_ms
                },
                'matches': {
                    'tools': llm_tool_names == local_tool_names,
                    'entities': llm_entity_names == local_entity_names
                }
            })
    
    def _section_to_tool(self, section_name: str) -> str:
        """
        Map a section name to its parent tool.
        
        Examples:
            "inventory" -> "character_data"
            "session_notes.npc" -> "session_notes"
            "session_notes_non_player_character" -> "session_notes"
            "rulebook.combat.grappling" -> "rulebook"
        """
        # Handle both dot notation and underscore notation
        if section_name.startswith("rulebook.") or section_name.startswith("rulebook_") or section_name == "rulebook":
            return "rulebook"
        elif section_name.startswith("session_notes.") or section_name.startswith("session_notes_") or section_name == "session_notes":
            return "session_notes"
        else:
            return "character_data"
    
    def _distribute_entities_to_rag_queries(
        self,
        entity_results: Dict[str, List[Any]],
        tools_needed: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        Map entities to tools based on where they were found.
        Multi-location entities are passed to all relevant tools for richer context.
        
        NOTE: This returns ALL tools where entities were found, not just selected tools.
        The caller (Step 4.5) uses this to add tools that have relevant entity context.
        """
        tool_entities = {}
        
        for entity_name, results in entity_results.items():
            for result in results:
                # EntitySearchResult has found_in_sections (list), not section (single)
                for section in result.found_in_sections:
                    tool = self._section_to_tool(section)
                    
                    if tool not in tool_entities:
                        tool_entities[tool] = []
                    
                    if entity_name not in tool_entities[tool]:
                        tool_entities[tool].append(entity_name)
        
        return tool_entities
    
    def _extract_context_sources(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured context sources from RAG results for metadata display.
        
        Returns:
            dict with character_fields, rulebook_sections, session_notes keys
        """
        # DEBUG: Log raw_results structure
        print(f"🔍 DEBUG _extract_context_sources: raw_results keys = {list(raw_results.keys())}")
        for key, value in raw_results.items():
            print(f"🔍 DEBUG: raw_results['{key}'] type = {type(value).__name__}")
            if hasattr(value, '__dict__'):
                print(f"🔍 DEBUG: raw_results['{key}'] attrs = {list(vars(value).keys()) if hasattr(value, '__dict__') else 'N/A'}")
        
        context_sources = {
            'character_fields': [],
            'rulebook_sections': [],
            'session_notes': []
        }
        
        # Extract character data fields - check both 'character' and 'character_data' keys
        char_result = raw_results.get('character') or raw_results.get('character_data')
        if char_result:
            print(f"🔍 DEBUG: char_result type = {type(char_result).__name__}")
            if hasattr(char_result, 'metadata'):
                print(f"🔍 DEBUG: char_result.metadata = {char_result.metadata}")
                if 'required_fields' in char_result.metadata:
                    context_sources['character_fields'] = char_result.metadata['required_fields']
            elif isinstance(char_result, dict) and 'metadata' in char_result:
                print(f"🔍 DEBUG: char_result['metadata'] = {char_result['metadata']}")
                if 'required_fields' in char_result['metadata']:
                    context_sources['character_fields'] = char_result['metadata']['required_fields']
        
        # Extract rulebook sections
        if 'rulebook' in raw_results:
            rulebook_results = raw_results['rulebook']
            print(f"🔍 DEBUG: rulebook_results type = {type(rulebook_results).__name__}")
            if isinstance(rulebook_results, list):
                for i, result in enumerate(rulebook_results):
                    print(f"🔍 DEBUG: rulebook_results[{i}] type = {type(result).__name__}, has section = {hasattr(result, 'section')}")
                    if hasattr(result, 'section'):
                        context_sources['rulebook_sections'].append({
                            'title': result.section.title,
                            'id': result.section.id,
                            'score': getattr(result, 'score', 0)
                        })
        
        # Extract session notes
        if 'session_notes' in raw_results:
            session_result = raw_results['session_notes']
            print(f"🔍 DEBUG: session_result type = {type(session_result).__name__}")
            if hasattr(session_result, 'contexts'):
                print(f"🔍 DEBUG: session_result.contexts = {len(session_result.contexts)} items")
                for ctx in session_result.contexts:
                    context_sources['session_notes'].append({
                        'session_number': ctx.session_number,
                        'relevance_score': getattr(ctx, 'relevance_score', 0)
                    })
            elif isinstance(session_result, dict) and 'contexts' in session_result:
                print(f"🔍 DEBUG: session_result['contexts'] = {len(session_result['contexts'])} items")
                for ctx in session_result['contexts']:
                    context_sources['session_notes'].append({
                        'session_number': ctx.get('session_number'),
                        'relevance_score': ctx.get('relevance_score', 0)
                    })
        
        print(f"🔍 DEBUG: Final context_sources = {context_sources}")
        return context_sources
    
    async def _execute_rag_queries(
        self,
        tools_needed: List[Dict[str, Any]],
        entity_distribution: Dict[str, List[str]],
        entity_results: Dict[str, List[Any]],
        user_query: str
    ) -> Dict[str, Any]:
        """
        Execute RAG queries for selected tools with distributed entities.
        Includes auto-include sections derived from entity resolution results.
        """
        results = {}
        
        for tool_info in tools_needed:
            tool = tool_info["tool"]
            intention = tool_info["intention"]
            entities = entity_distribution.get(tool, [])
            
            # Extract auto-include sections from entity resolution
            auto_include_sections = self._extract_auto_include_sections(
                entities, entity_results, tool
            )
            
            print(f"🔧 DEBUG: Executing {tool} with intention='{intention}', entities={entities}")
            if auto_include_sections:
                print(f"🔧 DEBUG: Auto-include sections: {auto_include_sections}")
            
            if tool == "character_data" and self.character_router:
                results["character"] = self.character_router.query_character(
                    user_intentions=[intention],
                    entities=[{"name": e, "confidence": 1.0} for e in entities],
                    auto_include_sections=auto_include_sections
                )
                
            elif tool == "session_notes" and self.session_notes_router:
                results["session_notes"] = self.session_notes_router.query(
                    character_name=self.character.character_base.name if self.character else "",
                    original_query=user_query,
                    intention=intention,
                    entities=[{"name": e} for e in entities],
                    context_hints=[],
                    top_k=self.config.max_results
                )
                
            elif tool == "rulebook" and self.rulebook_router:
                try:
                    intention_enum = RulebookQueryIntent(intention.lower())
                    results["rulebook"] = self.rulebook_router.query(
                        intention=intention_enum,
                        user_query=user_query,
                        entities=entities,
                        context_hints=[],
                        k=self.config.max_results
                    )
                except ValueError:
                    print(f"🔧 WARNING: Invalid rulebook intention '{intention}', skipping")
        
        # Step 2: Add entity-based context (independent of intentions)
        # This retrieves raw context for ALL entities found, regardless of intention routing
        entity_context = self._retrieve_entity_context(entity_results)
        if entity_context:
            results["entity_context"] = entity_context
            print(f"🔧 DEBUG: Added entity context for {len(entity_context)} entities")
        
        return results
    
    def _retrieve_entity_context(
        self,
        entity_results: Dict[str, List[Any]]
    ) -> Dict[str, Dict[str, str]]:
        """
        Retrieve raw context for all resolved entities, independent of intention routing.
        
        This method directly extracts the relevant content for each entity from
        the data sources where they were found. This context is additive to the
        intention-based RAG results.
        
        Args:
            entity_results: Mapping of entity names to EntitySearchResult lists
            
        Returns:
            Dict mapping entity names to their context:
            {
                "Ghul'Vor": {
                    "session_notes": "- **Ghul'Vor** - Ex-god of darkness...",
                    "character_data": "...",
                    ...
                }
            }
        """
        entity_context = {}
        
        for entity_name, results in entity_results.items():
            if not results:
                continue
                
            context_for_entity = {}
            
            for result in results:
                for section in result.found_in_sections:
                    tool = self._section_to_tool(section)
                    
                    if tool == "session_notes" and self.campaign_session_notes:
                        # Get session notes context for this entity
                        context = self._get_session_notes_entity_context(entity_name, section)
                        if context:
                            context_for_entity["session_notes"] = context
                            
                    elif tool == "character_data" and self.character:
                        # Get character data context for this entity
                        context = self._get_character_entity_context(entity_name, section)
                        if context:
                            context_for_entity["character_data"] = context
                            
                    elif tool == "rulebook" and self.rulebook_storage:
                        # Get rulebook context for this entity  
                        context = self._get_rulebook_entity_context(entity_name, section)
                        if context:
                            context_for_entity["rulebook"] = context
            
            if context_for_entity:
                entity_context[entity_name] = context_for_entity
        
        return entity_context
    
    def _get_session_notes_entity_context(self, entity_name: str, section: str) -> Optional[str]:
        """Get raw session notes context for an entity by searching all sessions."""
        if not self.campaign_session_notes:
            return None

        entity_lower = entity_name.lower()
        context_parts = []

        # Map section types to raw_sections keys
        section_key = section.split('.')[-1] if '.' in section else section.replace('session_notes_', '')
        section_key_map = {
            'non_player_character': 'NPCs Encountered',
            'npc': 'NPCs Encountered',
            'player_character': 'Player Characters Present',
            'pc': 'Player Characters Present',
            'location': 'Locations Visited',
            'event': 'Key Events',
            'combat': 'Combat Encounters',
            'quest': 'Quest Tracking'
        }
        raw_section_key = section_key_map.get(section_key, 'Summary')

        # Search through all sessions for entity mentions
        for session in self.campaign_session_notes.get_sessions_sorted():
            session_num = session.session_number

            # Check if entity appears in this session's entity lists
            entity_found = self._session_has_entity(session, entity_lower)

            # Also check raw_sections for entity mention
            raw_sections = session.raw_sections or {}
            section_content = raw_sections.get(raw_section_key, '')

            if entity_found or (section_content and entity_lower in section_content.lower()):
                if section_content and entity_lower in section_content.lower():
                    context_parts.append(f"Session {session_num} - {raw_section_key}:\n{section_content}")
                elif entity_found and session.summary and entity_lower in session.summary.lower():
                    # Fallback to summary if entity found but not in specific section
                    context_parts.append(f"Session {session_num} - Summary:\n{session.summary}")

        return "\n\n".join(context_parts) if context_parts else None

    def _session_has_entity(self, session, entity_lower: str) -> bool:
        """Check if a session contains references to an entity in its entity lists."""
        all_entities = (
            (session.player_characters or []) +
            (session.npcs or []) +
            (session.locations or []) +
            (session.items or [])
        )

        for entity in all_entities:
            if not isinstance(entity, dict):
                continue

            # Check name
            name = entity.get('name', '').lower()
            if entity_lower in name or name in entity_lower:
                return True

            # Check aliases
            aliases = entity.get('aliases', [])
            for alias in aliases:
                alias_lower = alias.lower() if isinstance(alias, str) else ''
                if entity_lower in alias_lower or alias_lower in entity_lower:
                    return True

        return False
    
    def _get_character_entity_context(self, entity_name: str, section: str) -> Optional[str]:
        """Get raw character data context for an entity."""
        if not self.character:
            return None
        
        # Use entity search engine to get the actual content
        # This is already handled by the character_router.query_character with auto_include_sections
        # So we don't need to duplicate that logic here
        return None
    
    def _get_rulebook_entity_context(self, entity_name: str, section: str) -> Optional[str]:
        """Get raw rulebook context for an entity."""
        if not self.rulebook_storage:
            return None
        
        # Rulebook router already handles entity-based search well
        # So we don't need to duplicate that logic here
        return None
    
    def _extract_auto_include_sections(
        self,
        entity_names: List[str],
        entity_results: Dict[str, List[Any]],
        tool: str
    ) -> List[str]:
        """
        Extract section names from entity resolution results for auto-inclusion.
        
        Args:
            entity_names: List of entity names for this tool
            entity_results: Full entity resolution results
            tool: Tool name to filter by
            
        Returns:
            List of unique section names to auto-include in the query
            
        Example:
            If "Eldaryth of Regret" found in ["inventory", "backstory"],
            returns ["inventory", "backstory"] for character_data tool.
        """
        sections = set()
        
        for entity_name in entity_names:
            if entity_name in entity_results:
                for result in entity_results[entity_name]:
                    # EntitySearchResult has found_in_sections (list)
                    for section in result.found_in_sections:
                        # Only include sections that belong to this tool
                        if self._section_to_tool(section) == tool:
                            sections.add(section)
        
        return list(sections)

