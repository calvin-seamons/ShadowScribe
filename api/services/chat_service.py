"""Chat service for processing queries through CentralEngine.

Uses local model for routing (tool/intent classification) and
Gazetteer-based NER for entity extraction by default.
"""
import sys
from pathlib import Path
from typing import AsyncGenerator, Callable, Optional, Dict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.central_engine import CentralEngine
from src.llm.central_prompt_manager import CentralPromptManager
from src.rag.context_assembler import ContextAssembler
from src.rag.rulebook.rulebook_storage import RulebookStorage
from src.rag.session_notes.session_notes_storage import SessionNotesStorage
from src.rag.character.character_types import Character
from src.config import get_config
from api.database.firestore_client import get_firestore_client
from api.database.repositories.character_repo import CharacterRepository


class ChatService:
    """Service for handling chat queries.

    Uses local model for routing (tool/intent classification) and
    Gazetteer-based NER for entity extraction. Entity extraction
    automatically includes character names, party members, NPCs,
    and other entities from the selected campaign's session notes.

    Routing behavior is controlled by config.routing_mode:
    - "haiku": Use Claude Haiku API for routing
    - "local": Use local DeBERTa classifier
    - "comparison": Run both classifiers for comparison
    """

    def __init__(self):
        """Initialize chat service with CentralEngine.

        Routing mode is determined by config.routing_mode.
        """
        self._engines: Dict[str, CentralEngine] = {}
        self._rulebook_storage = None
        self._session_notes_storage_instance = None
        self._campaign_caches: Dict[str, any] = {}  # Cache for campaign session notes
        self._initialize_storage()

    def _initialize_storage(self):
        """Initialize rulebook storage."""
        try:
            # Load rulebook storage (shared across all characters)
            self._rulebook_storage = RulebookStorage()
            rulebook_path = Path(project_root) / "knowledge_base" / "processed_rulebook" / "rulebook_storage.json"
            if rulebook_path.exists():
                self._rulebook_storage.load_from_disk(str(rulebook_path))
                print(f"[ChatService] Loaded rulebook storage")

            # Session notes storage is initialized lazily with Firestore client
            self._session_notes_storage_instance = None
            print(f"[ChatService] Session notes storage will be initialized on first request")
        except Exception as e:
            print(f"[ChatService] Warning: Could not load storage: {e}")

    async def _get_campaign_session_notes(self, campaign_id: str):
        """Get campaign session notes from Firestore, using cache if available.

        Args:
            campaign_id: The campaign ID to load.

        Returns:
            CampaignSessionNotesStorage or None if not found.
        """
        if campaign_id in self._campaign_caches:
            return self._campaign_caches[campaign_id]

        # Initialize session notes storage with Firestore client if not already done
        if self._session_notes_storage_instance is None:
            db = get_firestore_client()
            self._session_notes_storage_instance = SessionNotesStorage(db)
            print(f"[ChatService] Session notes storage initialized with Firestore")

        campaign_notes = await self._session_notes_storage_instance.get_campaign(campaign_id)
        if campaign_notes:
            self._campaign_caches[campaign_id] = campaign_notes
            print(f"[ChatService] Loaded campaign session notes from Firestore: {campaign_id}")
            return campaign_notes

        print(f"[ChatService] No sessions found for campaign: {campaign_id}")
        return None

    async def _get_or_create_engine(self, character_name: str) -> CentralEngine:
        """Get or create CentralEngine for character.

        The engine is keyed by both character_name and campaign_id, so changing
        either will create a new engine with the appropriate context for
        entity extraction (gazetteer NER).

        Args:
            character_name: Name of the character to use

        Returns:
            Configured CentralEngine instance
        """
        # Get Firestore client and load character first to check their campaign_id
        db = get_firestore_client()
        repo = CharacterRepository(db)

        # Load from Firestore by name
        char_doc = await repo.get_by_name(character_name)
        if not char_doc:
            raise ValueError(f"Character '{character_name}' not found in Firestore")

        # Convert Firestore data to Character using Pydantic
        character = Character.model_validate(char_doc.data)
        # Use the character's actual campaign_id from Firestore
        # If character has no campaign, don't load any session notes
        actual_campaign_id = char_doc.campaign_id

        # Key engines by both character and their actual campaign
        engine_key = f"{character_name}::{actual_campaign_id or 'no_campaign'}"

        if engine_key in self._engines:
            return self._engines[engine_key]

        # Get campaign session notes only if character has a campaign
        campaign_session_notes = None
        if actual_campaign_id:
            campaign_session_notes = await self._get_campaign_session_notes(actual_campaign_id)
            print(f"[ChatService] Character '{character_name}' belongs to campaign '{actual_campaign_id}'")
        else:
            print(f"[ChatService] Character '{character_name}' has no campaign association")

        # Create engine components
        context_assembler = ContextAssembler()
        prompt_manager = CentralPromptManager(context_assembler)

        # Create engine - routing mode determined by config.routing_mode
        engine = CentralEngine.create_from_config(
            prompt_manager,
            character=character,
            rulebook_storage=self._rulebook_storage,
            campaign_session_notes=campaign_session_notes
        )

        config = get_config()
        # Map routing_mode to display label
        routing_labels = {
            "local": "LOCAL MODEL",
            "haiku": "HAIKU LLM",
            "comparison": "COMPARISON (Haiku + Local)"
        }
        routing_label = routing_labels.get(config.routing_mode, config.routing_mode.upper())
        campaign_label = actual_campaign_id or "no campaign"
        print(f"[ChatService] Created engine for {character_name} in {campaign_label}")
        print(f"[ChatService] Routing: {routing_label}, Entity extraction: GAZETTEER NER")

        self._engines[engine_key] = engine
        return engine

    def clear_conversation_history(self, character_name: str, campaign_id: str = "main_campaign"):
        """Clear conversation history for a character/campaign combination.

        Args:
            character_name: Name of the character
            campaign_id: Campaign ID (defaults to "main_campaign")
        """
        engine_key = f"{character_name}::{campaign_id}"
        if engine_key in self._engines:
            self._engines[engine_key].clear_conversation_history()

    async def process_query_stream(
        self,
        user_query: str,
        character_name: str,
        campaign_id: str = "main_campaign",
        metadata_callback: Optional[Callable] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process query and stream response chunks.

        Uses local model for routing and Gazetteer NER for entity extraction.
        Entity extraction automatically includes:
        - Character name and aliases
        - Party member names from session notes
        - NPC names from session notes
        - Locations, items, factions from session notes
        - SRD entities (spells, monsters, items, conditions, etc.)

        Args:
            user_query: User's question
            character_name: Name of character
            campaign_id: Campaign ID for session notes context (defaults to "main_campaign")
            metadata_callback: Optional async callback for metadata events

        Yields:
            Response chunks as they are generated
        """
        engine = await self._get_or_create_engine(character_name)

        async for chunk in engine.process_query_stream(user_query, character_name, metadata_callback):
            yield chunk

    def invalidate_engine(self, character_name: str, campaign_id: str = "main_campaign"):
        """Invalidate cached engine to force reload on next query.

        Use this when character or campaign data has changed and the
        engine needs to reload with fresh context.

        Args:
            character_name: Name of the character
            campaign_id: Campaign ID (defaults to "main_campaign")
        """
        engine_key = f"{character_name}::{campaign_id}"
        if engine_key in self._engines:
            del self._engines[engine_key]
            print(f"[ChatService] Invalidated engine for {engine_key}")
