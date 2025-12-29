"""Firestore document models and helpers.

These are Pydantic models that serve as the single source of truth for Firestore documents.
TypeScript types are auto-generated from these models using pydantic-to-typescript.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any


def _serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """
    Serialize a datetime to an ISO 8601 string suitable for JSON responses.
    
    Parameters:
        dt (Optional[datetime]): The datetime to serialize; may be timezone-aware or naive.
    
    Returns:
        Optional[str]: ISO 8601 string representation of `dt`, or `None` if `dt` is `None`.
    """
    return dt.isoformat() if dt else None


def _parse_datetime(value: Any) -> Optional[datetime]:
    """
    Convert a Firestore Timestamp, ISO 8601 string, or datetime object to a timezone-naive datetime.
    
    Parameters:
        value (Any): A value that may be a datetime, a Firestore-like Timestamp (object with a `timestamp()` method), an ISO 8601 string, or None.
    
    Returns:
        Optional[datetime]: A timezone-naive `datetime` parsed from `value`, or `None` if `value` is `None` or cannot be parsed.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if hasattr(value, 'timestamp'):  # Firestore Timestamp
        return value.timestamp().replace(tzinfo=None)
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    return None


class UserDocument(BaseModel):
    """User document for Firestore."""
    id: str  # Firebase UID (document ID)
    email: str
    display_name: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to Firestore document data (excludes id)."""
        return {
            'email': self.email,
            'display_name': self.display_name,
            'created_at': self.created_at or datetime.utcnow(),
        }

    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            'id': self.id,
            'email': self.email,
            'display_name': self.display_name,
            'created_at': _serialize_datetime(self.created_at),
        }

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> 'UserDocument':
        """
        Construct a UserDocument from Firestore document data.
        
        Parameters:
            doc_id (str): Firestore document ID to use as the user's `id`.
            data (dict): Firestore document fields; expected keys include 'email', 'display_name', and 'created_at'.
        
        Returns:
            UserDocument: Instance populated from the provided Firestore data.
        """
        return cls(
            id=doc_id,
            email=data.get('email', ''),
            display_name=data.get('display_name'),
            created_at=_parse_datetime(data.get('created_at')),
        )


class CampaignDocument(BaseModel):
    """Campaign document for Firestore."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to Firestore document data (excludes id)."""
        return {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at or datetime.utcnow(),
        }

    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': _serialize_datetime(self.created_at),
        }

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> 'CampaignDocument':
        """
        Create a CampaignDocument from Firestore document data.
        
        Parameters:
            doc_id (str): Firestore document ID.
            data (dict): Raw Firestore document data; may omit fields like `name`, `description`, or `created_at`.
        
        Returns:
            CampaignDocument: Instance populated from the provided Firestore fields.
        """
        return cls(
            id=doc_id,
            name=data.get('name', ''),
            description=data.get('description'),
            created_at=_parse_datetime(data.get('created_at')),
        )


class SessionDocument(BaseModel):
    """Session document for Firestore AND RAG queries.

    Stored at: campaigns/{campaign_id}/sessions/{session_id}

    This is the single source of truth for session data - used both for
    Firestore persistence and in-memory RAG queries. No serialization layer.
    """
    # Identity
    id: str
    campaign_id: str
    user_id: str
    session_number: int
    session_name: str

    # Content
    raw_content: str = ''  # Original transcript input
    processed_markdown: str = ''  # LLM-generated structured markdown
    title: str = ''
    summary: str = ''

    # Entities (per-session for chronological context)
    player_characters: list[dict[str, Any]] = Field(default_factory=list)  # [{name, entity_type, aliases, description, ...}]
    npcs: list[dict[str, Any]] = Field(default_factory=list)
    locations: list[dict[str, Any]] = Field(default_factory=list)
    items: list[dict[str, Any]] = Field(default_factory=list)

    # Structured RAG fields
    key_events: list[dict[str, Any]] = Field(default_factory=list)
    combat_encounters: list[dict[str, Any]] = Field(default_factory=list)
    spells_abilities_used: list[dict[str, Any]] = Field(default_factory=list)
    character_decisions: list[dict[str, Any]] = Field(default_factory=list)
    character_statuses: dict[str, Any] = Field(default_factory=dict)  # {character_name: status_dict}
    memories_visions: list[dict[str, Any]] = Field(default_factory=list)
    quest_updates: list[dict[str, Any]] = Field(default_factory=list)
    loot_obtained: dict[str, Any] = Field(default_factory=dict)  # {character: [items]}
    deaths: list[dict[str, Any]] = Field(default_factory=list)
    revivals: list[dict[str, Any]] = Field(default_factory=list)
    party_conflicts: list[str] = Field(default_factory=list)
    party_bonds: list[str] = Field(default_factory=list)
    quotes: list[dict[str, Any]] = Field(default_factory=list)  # [{speaker, quote, context}]
    funny_moments: list[str] = Field(default_factory=list)
    puzzles_encountered: dict[str, Any] = Field(default_factory=dict)  # {puzzle: solution/status}
    mysteries_revealed: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    divine_interventions: list[str] = Field(default_factory=list)
    religious_elements: list[str] = Field(default_factory=list)
    rules_clarifications: list[str] = Field(default_factory=list)
    dice_rolls: list[dict[str, Any]] = Field(default_factory=list)
    cliffhanger: Optional[str] = None
    next_session_hook: Optional[str] = None
    dm_notes: list[str] = Field(default_factory=list)
    raw_sections: dict[str, Any] = Field(default_factory=dict)  # {section_name: text}

    # Timestamps
    date: Optional[datetime] = None  # In-game or real session date
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to Firestore document data (excludes id and campaign_id)."""
        now = datetime.utcnow()
        return {
            'user_id': self.user_id,
            'session_number': self.session_number,
            'session_name': self.session_name,
            'raw_content': self.raw_content,
            'processed_markdown': self.processed_markdown,
            'title': self.title,
            'summary': self.summary,
            'player_characters': self.player_characters,
            'npcs': self.npcs,
            'locations': self.locations,
            'items': self.items,
            'key_events': self.key_events,
            'combat_encounters': self.combat_encounters,
            'spells_abilities_used': self.spells_abilities_used,
            'character_decisions': self.character_decisions,
            'character_statuses': self.character_statuses,
            'memories_visions': self.memories_visions,
            'quest_updates': self.quest_updates,
            'loot_obtained': self.loot_obtained,
            'deaths': self.deaths,
            'revivals': self.revivals,
            'party_conflicts': self.party_conflicts,
            'party_bonds': self.party_bonds,
            'quotes': self.quotes,
            'funny_moments': self.funny_moments,
            'puzzles_encountered': self.puzzles_encountered,
            'mysteries_revealed': self.mysteries_revealed,
            'unresolved_questions': self.unresolved_questions,
            'divine_interventions': self.divine_interventions,
            'religious_elements': self.religious_elements,
            'rules_clarifications': self.rules_clarifications,
            'dice_rolls': self.dice_rolls,
            'cliffhanger': self.cliffhanger,
            'next_session_hook': self.next_session_hook,
            'dm_notes': self.dm_notes,
            'raw_sections': self.raw_sections,
            'date': self.date,
            'created_at': self.created_at or now,
            'updated_at': now,
        }

    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'user_id': self.user_id,
            'session_number': self.session_number,
            'session_name': self.session_name,
            'title': self.title,
            'summary': self.summary,
            'date': _serialize_datetime(self.date),
            'created_at': _serialize_datetime(self.created_at),
            'updated_at': _serialize_datetime(self.updated_at),
        }

    @classmethod
    def from_firestore(cls, doc_id: str, campaign_id: str, data: dict) -> 'SessionDocument':
        """
        Create a SessionDocument instance from Firestore document data.

        Constructs a SessionDocument with id set to `doc_id` and campaign_id set to `campaign_id`, populating all session fields from `data`. Missing keys are filled with sensible defaults (empty strings, empty lists/dicts, or zeros) and the `date`, `created_at`, and `updated_at` fields are converted using _parse_datetime.

        Parameters:
            doc_id (str): Firestore document identifier to use as the session `id`.
            campaign_id (str): Campaign identifier to associate with the session.
            data (dict): Firestore document data containing session fields.

        Returns:
            SessionDocument: A populated SessionDocument instance.
        """
        return cls(
            id=doc_id,
            campaign_id=campaign_id,
            user_id=data.get('user_id') or '',
            session_number=data.get('session_number') or 0,
            session_name=data.get('session_name') or '',
            raw_content=data.get('raw_content') or '',
            processed_markdown=data.get('processed_markdown') or '',
            title=data.get('title') or '',
            summary=data.get('summary') or '',
            player_characters=data.get('player_characters') or [],
            npcs=data.get('npcs') or [],
            locations=data.get('locations') or [],
            items=data.get('items') or [],
            key_events=data.get('key_events') or [],
            combat_encounters=data.get('combat_encounters') or [],
            spells_abilities_used=data.get('spells_abilities_used') or [],
            character_decisions=data.get('character_decisions') or [],
            character_statuses=data.get('character_statuses') or {},
            memories_visions=data.get('memories_visions') or [],
            quest_updates=data.get('quest_updates') or [],
            loot_obtained=data.get('loot_obtained') or {},
            deaths=data.get('deaths') or [],
            revivals=data.get('revivals') or [],
            party_conflicts=data.get('party_conflicts') or [],
            party_bonds=data.get('party_bonds') or [],
            quotes=data.get('quotes') or [],
            funny_moments=data.get('funny_moments') or [],
            puzzles_encountered=data.get('puzzles_encountered') or {},
            mysteries_revealed=data.get('mysteries_revealed') or [],
            unresolved_questions=data.get('unresolved_questions') or [],
            divine_interventions=data.get('divine_interventions') or [],
            religious_elements=data.get('religious_elements') or [],
            rules_clarifications=data.get('rules_clarifications') or [],
            dice_rolls=data.get('dice_rolls') or [],
            cliffhanger=data.get('cliffhanger'),
            next_session_hook=data.get('next_session_hook'),
            dm_notes=data.get('dm_notes') or [],
            raw_sections=data.get('raw_sections') or {},
            date=_parse_datetime(data.get('date')),
            created_at=_parse_datetime(data.get('created_at')),
            updated_at=_parse_datetime(data.get('updated_at')),
        )


class CharacterDocument(BaseModel):
    """Character document for Firestore."""
    id: str
    user_id: str
    name: str
    data: dict[str, Any]  # Full character dataclass serialized
    campaign_id: str  # Required - all characters belong to a campaign
    race: Optional[str] = None
    character_class: Optional[str] = None
    level: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to Firestore document data (excludes id)."""
        now = datetime.utcnow()
        return {
            'user_id': self.user_id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'race': self.race,
            'character_class': self.character_class,
            'level': self.level,
            'data': self.data,
            'created_at': self.created_at or now,
            'updated_at': now,
        }

    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'race': self.race,
            'character_class': self.character_class,
            'level': self.level,
            'data': self.data,
            'created_at': _serialize_datetime(self.created_at),
            'updated_at': _serialize_datetime(self.updated_at),
        }

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> 'CharacterDocument':
        """
        Constructs a CharacterDocument instance from Firestore document data.
        
        Parameters:
            doc_id (str): Firestore document ID to use as the CharacterDocument.id.
            data (dict): Firestore document fields; missing keys fall back to defaults.
        
        Returns:
            CharacterDocument: Instance populated from `data`. `created_at` and `updated_at` are parsed into datetimes; `campaign_id` is set to an empty string when missing (for legacy documents).
        """
        return cls(
            id=doc_id,
            user_id=data.get('user_id', ''),
            campaign_id=data.get('campaign_id', ''),  # Empty string for legacy docs without campaign
            name=data.get('name', ''),
            race=data.get('race'),
            character_class=data.get('character_class'),
            level=data.get('level'),
            data=data.get('data', {}),
            created_at=_parse_datetime(data.get('created_at')),
            updated_at=_parse_datetime(data.get('updated_at')),
        )


class QueryLogDocument(BaseModel):
    """Query log document for Firestore - captures full query/response cycle."""
    id: str
    user_query: str  # Normalized query with placeholders
    character_name: str
    predicted_tools: list[dict[str, Any]]  # List of {tool, intention, confidence}
    campaign_id: str = 'main_campaign'
    predicted_entities: Optional[list[dict[str, Any]]] = None
    classifier_backend: str = 'local'
    classifier_inference_time_ms: Optional[float] = None
    
    # New fields for complete query logging
    original_query: Optional[str] = None  # Raw query before placeholder normalization
    assistant_response: Optional[str] = None  # Full LLM response
    context_sources: Optional[dict[str, Any]] = None  # {character_fields, rulebook_sections, session_notes}
    response_time_ms: Optional[float] = None  # Total query-to-response time
    model_used: Optional[str] = None  # e.g., "claude-sonnet-4-20250514"
    
    # Feedback fields
    is_correct: Optional[bool] = None
    corrected_tools: Optional[list[dict[str, Any]]] = None
    feedback_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    feedback_at: Optional[datetime] = None
    exported_for_training: bool = False
    exported_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to Firestore document data (excludes id)."""
        return {
            'user_query': self.user_query,
            'character_name': self.character_name,
            'campaign_id': self.campaign_id,
            'predicted_tools': self.predicted_tools,
            'predicted_entities': self.predicted_entities,
            'classifier_backend': self.classifier_backend,
            'classifier_inference_time_ms': self.classifier_inference_time_ms,
            # New fields
            'original_query': self.original_query,
            'assistant_response': self.assistant_response,
            'context_sources': self.context_sources,
            'response_time_ms': self.response_time_ms,
            'model_used': self.model_used,
            # Feedback fields
            'is_correct': self.is_correct,
            'corrected_tools': self.corrected_tools,
            'feedback_notes': self.feedback_notes,
            'created_at': self.created_at or datetime.utcnow(),
            'feedback_at': self.feedback_at,
            'exported_for_training': self.exported_for_training,
            'exported_at': self.exported_at,
        }

    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            'id': self.id,
            'user_query': self.user_query,
            'character_name': self.character_name,
            'campaign_id': self.campaign_id,
            'predicted_tools': self.predicted_tools,
            'predicted_entities': self.predicted_entities,
            'classifier_backend': self.classifier_backend,
            'classifier_inference_time_ms': self.classifier_inference_time_ms,
            # New fields
            'original_query': self.original_query,
            'assistant_response': self.assistant_response,
            'context_sources': self.context_sources,
            'response_time_ms': self.response_time_ms,
            'model_used': self.model_used,
            # Feedback fields
            'is_correct': self.is_correct,
            'corrected_tools': self.corrected_tools,
            'feedback_notes': self.feedback_notes,
            'created_at': _serialize_datetime(self.created_at),
            'feedback_at': _serialize_datetime(self.feedback_at),
        }

    def to_training_example(self) -> list:
        """Convert to training data format for fine-tuning."""
        examples = []
        tools = self.corrected_tools if self.corrected_tools else self.predicted_tools

        for tool_info in tools:
            examples.append({
                'query': self.user_query,
                'tool': tool_info['tool'],
                'intent': tool_info['intention'],
                'is_correction': self.corrected_tools is not None
            })

        return examples

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> 'QueryLogDocument':
        """
        Constructs a QueryLogDocument from a Firestore document.
        
        Parameters:
            doc_id (str): Firestore document ID to use as the model's `id`.
            data (dict): Firestore document data mapping used to populate fields.
        
        Returns:
            QueryLogDocument: Instance populated from the provided Firestore data.
        """
        return cls(
            id=doc_id,
            user_query=data.get('user_query', ''),
            character_name=data.get('character_name', ''),
            campaign_id=data.get('campaign_id', 'main_campaign'),
            predicted_tools=data.get('predicted_tools', []),
            predicted_entities=data.get('predicted_entities'),
            classifier_backend=data.get('classifier_backend', 'local'),
            classifier_inference_time_ms=data.get('classifier_inference_time_ms'),
            # New fields
            original_query=data.get('original_query'),
            assistant_response=data.get('assistant_response'),
            context_sources=data.get('context_sources'),
            response_time_ms=data.get('response_time_ms'),
            model_used=data.get('model_used'),
            # Feedback fields
            is_correct=data.get('is_correct'),
            corrected_tools=data.get('corrected_tools'),
            feedback_notes=data.get('feedback_notes'),
            created_at=_parse_datetime(data.get('created_at')),
            feedback_at=_parse_datetime(data.get('feedback_at')),
            exported_for_training=data.get('exported_for_training', False),
            exported_at=_parse_datetime(data.get('exported_at')),
        )


class QueryLogStats(BaseModel):
    """Statistics for query logs."""
    queries_total: int = 0
    queries_pending_review: int = 0
    queries_confirmed_correct: int = 0
    queries_corrected: int = 0
    queries_exported: int = 0

    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            'queries_total': self.queries_total,
            'queries_pending_review': self.queries_pending_review,
            'queries_confirmed_correct': self.queries_confirmed_correct,
            'queries_corrected': self.queries_corrected,
            'queries_exported': self.queries_exported,
        }

    @classmethod
    def from_firestore(cls, data: dict) -> 'QueryLogStats':
        """Create from Firestore stats document."""
        return cls(
            queries_total=data.get('queries_total', 0),
            queries_pending_review=data.get('queries_pending', 0),
            queries_confirmed_correct=data.get('queries_correct', 0),
            queries_corrected=data.get('queries_corrected', 0),
            queries_exported=data.get('queries_exported', 0),
        )


# Backward compatibility aliases
RoutingFeedbackDocument = QueryLogDocument
FeedbackStats = QueryLogStats
