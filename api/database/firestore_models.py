"""Firestore document models and helpers."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Any, List
import uuid


def _serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO string for JSON serialization."""
    return dt.isoformat() if dt else None


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime from Firestore timestamp or ISO string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if hasattr(value, 'timestamp'):  # Firestore Timestamp
        return value.timestamp().replace(tzinfo=None)
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    return None


@dataclass
class UserDocument:
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
        """Create from Firestore document."""
        return cls(
            id=doc_id,
            email=data.get('email', ''),
            display_name=data.get('display_name'),
            created_at=_parse_datetime(data.get('created_at')),
        )


@dataclass
class CampaignDocument:
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
        """Create from Firestore document."""
        return cls(
            id=doc_id,
            name=data.get('name', ''),
            description=data.get('description'),
            created_at=_parse_datetime(data.get('created_at')),
        )


@dataclass
class SessionDocument:
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
    player_characters: List[dict] = field(default_factory=list)  # [{name, entity_type, aliases, description, ...}]
    npcs: List[dict] = field(default_factory=list)
    locations: List[dict] = field(default_factory=list)
    items: List[dict] = field(default_factory=list)

    # Structured RAG fields
    key_events: List[dict] = field(default_factory=list)
    combat_encounters: List[dict] = field(default_factory=list)
    spells_abilities_used: List[dict] = field(default_factory=list)
    character_decisions: List[dict] = field(default_factory=list)
    character_statuses: dict = field(default_factory=dict)  # {character_name: status_dict}
    memories_visions: List[dict] = field(default_factory=list)
    quest_updates: List[dict] = field(default_factory=list)
    loot_obtained: dict = field(default_factory=dict)  # {character: [items]}
    deaths: List[dict] = field(default_factory=list)
    revivals: List[dict] = field(default_factory=list)
    party_conflicts: List[str] = field(default_factory=list)
    party_bonds: List[str] = field(default_factory=list)
    quotes: List[dict] = field(default_factory=list)  # [{speaker, quote, context}]
    funny_moments: List[str] = field(default_factory=list)
    puzzles_encountered: dict = field(default_factory=dict)  # {puzzle: solution/status}
    mysteries_revealed: List[str] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    divine_interventions: List[str] = field(default_factory=list)
    religious_elements: List[str] = field(default_factory=list)
    rules_clarifications: List[str] = field(default_factory=list)
    dice_rolls: List[dict] = field(default_factory=list)
    cliffhanger: Optional[str] = None
    next_session_hook: Optional[str] = None
    dm_notes: List[str] = field(default_factory=list)
    raw_sections: dict = field(default_factory=dict)  # {section_name: text}

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
        """Create from Firestore document."""
        return cls(
            id=doc_id,
            campaign_id=campaign_id,
            user_id=data.get('user_id', ''),
            session_number=data.get('session_number', 0),
            session_name=data.get('session_name', ''),
            raw_content=data.get('raw_content', ''),
            processed_markdown=data.get('processed_markdown', ''),
            title=data.get('title', ''),
            summary=data.get('summary', ''),
            player_characters=data.get('player_characters', []),
            npcs=data.get('npcs', []),
            locations=data.get('locations', []),
            items=data.get('items', []),
            key_events=data.get('key_events', []),
            combat_encounters=data.get('combat_encounters', []),
            spells_abilities_used=data.get('spells_abilities_used', []),
            character_decisions=data.get('character_decisions', []),
            character_statuses=data.get('character_statuses', {}),
            memories_visions=data.get('memories_visions', []),
            quest_updates=data.get('quest_updates', []),
            loot_obtained=data.get('loot_obtained', {}),
            deaths=data.get('deaths', []),
            revivals=data.get('revivals', []),
            party_conflicts=data.get('party_conflicts', []),
            party_bonds=data.get('party_bonds', []),
            quotes=data.get('quotes', []),
            funny_moments=data.get('funny_moments', []),
            puzzles_encountered=data.get('puzzles_encountered', {}),
            mysteries_revealed=data.get('mysteries_revealed', []),
            unresolved_questions=data.get('unresolved_questions', []),
            divine_interventions=data.get('divine_interventions', []),
            religious_elements=data.get('religious_elements', []),
            rules_clarifications=data.get('rules_clarifications', []),
            dice_rolls=data.get('dice_rolls', []),
            cliffhanger=data.get('cliffhanger'),
            next_session_hook=data.get('next_session_hook'),
            dm_notes=data.get('dm_notes', []),
            raw_sections=data.get('raw_sections', {}),
            date=_parse_datetime(data.get('date')),
            created_at=_parse_datetime(data.get('created_at')),
            updated_at=_parse_datetime(data.get('updated_at')),
        )


@dataclass
class CharacterDocument:
    """Character document for Firestore."""
    id: str
    user_id: str
    name: str
    data: dict  # Full character dataclass serialized
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
        """Create from Firestore document."""
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


@dataclass
class RoutingFeedbackDocument:
    """Routing feedback document for Firestore."""
    id: str
    user_query: str
    character_name: str
    predicted_tools: list  # List of {tool, intention, confidence}
    campaign_id: str = 'main_campaign'
    predicted_entities: Optional[list] = None
    classifier_backend: str = 'local'
    classifier_inference_time_ms: Optional[float] = None
    is_correct: Optional[bool] = None
    corrected_tools: Optional[list] = None
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
    def from_firestore(cls, doc_id: str, data: dict) -> 'RoutingFeedbackDocument':
        """Create from Firestore document."""
        return cls(
            id=doc_id,
            user_query=data.get('user_query', ''),
            character_name=data.get('character_name', ''),
            campaign_id=data.get('campaign_id', 'main_campaign'),
            predicted_tools=data.get('predicted_tools', []),
            predicted_entities=data.get('predicted_entities'),
            classifier_backend=data.get('classifier_backend', 'local'),
            classifier_inference_time_ms=data.get('classifier_inference_time_ms'),
            is_correct=data.get('is_correct'),
            corrected_tools=data.get('corrected_tools'),
            feedback_notes=data.get('feedback_notes'),
            created_at=_parse_datetime(data.get('created_at')),
            feedback_at=_parse_datetime(data.get('feedback_at')),
            exported_for_training=data.get('exported_for_training', False),
            exported_at=_parse_datetime(data.get('exported_at')),
        )


@dataclass
class FeedbackStats:
    """Statistics for routing feedback."""
    total_records: int = 0
    pending_review: int = 0
    confirmed_correct: int = 0
    corrected: int = 0
    exported: int = 0

    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            'total_records': self.total_records,
            'pending_review': self.pending_review,
            'confirmed_correct': self.confirmed_correct,
            'corrected': self.corrected,
            'exported': self.exported,
        }

    @classmethod
    def from_firestore(cls, data: dict) -> 'FeedbackStats':
        """Create from Firestore stats document."""
        return cls(
            total_records=data.get('feedback_total', 0),
            pending_review=data.get('feedback_pending', 0),
            confirmed_correct=data.get('feedback_correct', 0),
            corrected=data.get('feedback_corrected', 0),
            exported=data.get('feedback_exported', 0),
        )
