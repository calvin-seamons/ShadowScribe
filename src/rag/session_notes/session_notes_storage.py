"""
Session Notes Storage System

Loads session documents from Firestore and provides access to campaign-specific storage.
"""

from typing import Dict, Optional
from google.cloud.firestore import AsyncClient

from api.database.firestore_models import SessionDocument
from .campaign_session_notes_storage import CampaignSessionNotesStorage


class SessionNotesStorage:
    """
    Manager for campaign session notes storage.
    Loads session documents from Firestore and caches them in memory.
    """

    def __init__(self, db: AsyncClient):
        self.db = db
        self._cache: Dict[str, CampaignSessionNotesStorage] = {}

    async def get_campaign(self, campaign_id: str) -> Optional[CampaignSessionNotesStorage]:
        """
        Get a campaign's session notes storage.
        Loads from Firestore if not already cached.

        Args:
            campaign_id: The campaign ID to load sessions for

        Returns:
            CampaignSessionNotesStorage with all sessions, or None if no sessions exist
        """
        if campaign_id in self._cache:
            return self._cache[campaign_id]

        storage = await self._load_from_firestore(campaign_id)
        if storage:
            self._cache[campaign_id] = storage

        return storage

    async def _load_from_firestore(self, campaign_id: str) -> Optional[CampaignSessionNotesStorage]:
        """Load all sessions for a campaign from Firestore."""
        storage = CampaignSessionNotesStorage(campaign_id=campaign_id)

        sessions_ref = self.db.collection('campaigns').document(campaign_id).collection('sessions')
        async for doc in sessions_ref.stream():
            session = SessionDocument.from_firestore(doc.id, campaign_id, doc.to_dict())
            storage.sessions[doc.id] = session

        # Return None if no sessions found
        if not storage.sessions:
            return None

        return storage

    def invalidate(self, campaign_id: str) -> None:
        """
        Invalidate cached data for a campaign.
        Call this when sessions are added/modified/deleted.
        """
        self._cache.pop(campaign_id, None)

    def invalidate_all(self) -> None:
        """Invalidate all cached campaign data."""
        self._cache.clear()

    def is_cached(self, campaign_id: str) -> bool:
        """Check if a campaign's data is currently cached."""
        return campaign_id in self._cache
