"""
Campaign Session Notes Storage

In-memory cache for a specific campaign's session documents.
Loaded from Firestore, used directly for RAG queries.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from api.database.firestore_models import SessionDocument


@dataclass
class CampaignSessionNotesStorage:
    """
    In-memory cache of session documents for a single campaign.
    Sessions are loaded from Firestore and used directly for RAG queries.
    """
    campaign_id: str
    sessions: Dict[str, SessionDocument] = field(default_factory=dict)

    def get_all_sessions(self) -> List[SessionDocument]:
        """Get all sessions for this campaign."""
        return list(self.sessions.values())

    def get_session(self, session_id: str) -> Optional[SessionDocument]:
        """Get a specific session by ID."""
        return self.sessions.get(session_id)

    def get_session_count(self) -> int:
        """Get total number of sessions."""
        return len(self.sessions)

    def get_latest_session(self) -> Optional[SessionDocument]:
        """Get the most recent session by session number."""
        if not self.sessions:
            return None
        return max(self.sessions.values(), key=lambda s: s.session_number)

    def get_sessions_sorted(self) -> List[SessionDocument]:
        """Get all sessions sorted by session number."""
        return sorted(self.sessions.values(), key=lambda s: s.session_number)

    def get_session_date_range(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """Get the date range of all sessions."""
        if not self.sessions:
            return None, None

        dates = [s.date for s in self.sessions.values() if s.date]
        if not dates:
            return None, None
        return min(dates), max(dates)
