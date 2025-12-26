"""Routing feedback repository for Firestore operations."""
from google.cloud.firestore_v1 import AsyncClient
from google.cloud.firestore_v1 import Increment
from typing import List, Optional
from datetime import datetime
import uuid

from api.database.firestore_client import (
    ROUTING_FEEDBACK_COLLECTION,
    METADATA_COLLECTION,
    STATS_DOCUMENT
)
from api.database.firestore_models import RoutingFeedbackDocument, FeedbackStats


class FeedbackRepository:
    """Repository for routing feedback CRUD operations using Firestore."""

    def __init__(self, db: AsyncClient):
        self.db = db
        self.collection = db.collection(ROUTING_FEEDBACK_COLLECTION)
        self.stats_ref = db.collection(METADATA_COLLECTION).document(STATS_DOCUMENT)

    async def _ensure_stats_doc(self):
        """Ensure stats document exists with default values."""
        doc = await self.stats_ref.get()
        if not doc.exists:
            await self.stats_ref.set({
                'feedback_total': 0,
                'feedback_pending': 0,
                'feedback_correct': 0,
                'feedback_corrected': 0,
                'feedback_exported': 0
            })

    async def create(self, feedback: RoutingFeedbackDocument) -> RoutingFeedbackDocument:
        """Create a new routing feedback record."""
        await self._ensure_stats_doc()

        doc_id = feedback.id or str(uuid.uuid4())
        feedback.id = doc_id

        await self.collection.document(doc_id).set(feedback.to_dict())

        # Update counters atomically
        await self.stats_ref.update({
            'feedback_total': Increment(1),
            'feedback_pending': Increment(1)
        })

        return feedback

    async def get_by_id(self, feedback_id: str) -> Optional[RoutingFeedbackDocument]:
        """Get feedback by ID."""
        doc_ref = self.collection.document(feedback_id)
        doc = await doc_ref.get()

        if not doc.exists:
            return None

        return RoutingFeedbackDocument.from_firestore(doc.id, doc.to_dict())

    async def get_pending_review(self, limit: int = 50) -> List[RoutingFeedbackDocument]:
        """Get feedback records pending user review."""
        query = (
            self.collection
            .where('is_correct', '==', None)
            .order_by('created_at', direction='DESCENDING')
            .limit(limit)
        )
        docs = await query.get()
        return [RoutingFeedbackDocument.from_firestore(doc.id, doc.to_dict()) for doc in docs]

    async def get_recent(self, limit: int = 100) -> List[RoutingFeedbackDocument]:
        """Get most recent feedback records."""
        query = (
            self.collection
            .order_by('created_at', direction='DESCENDING')
            .limit(limit)
        )
        docs = await query.get()
        return [RoutingFeedbackDocument.from_firestore(doc.id, doc.to_dict()) for doc in docs]

    async def get_corrected(self, limit: int = 1000, unexported_only: bool = False) -> List[RoutingFeedbackDocument]:
        """Get feedback records with user corrections."""
        query = self.collection.where('is_correct', '==', False)

        if unexported_only:
            query = query.where('exported_for_training', '==', False)

        query = query.order_by('created_at', direction='DESCENDING').limit(limit)
        docs = await query.get()

        # Filter for records that have corrections (Firestore can't query for != null easily)
        results = []
        for doc in docs:
            data = doc.to_dict()
            if data.get('corrected_tools') is not None:
                results.append(RoutingFeedbackDocument.from_firestore(doc.id, data))

        return results

    async def get_confirmed_correct(self, limit: int = 1000, unexported_only: bool = False) -> List[RoutingFeedbackDocument]:
        """Get feedback records confirmed as correct by user."""
        query = self.collection.where('is_correct', '==', True)

        if unexported_only:
            query = query.where('exported_for_training', '==', False)

        query = query.order_by('created_at', direction='DESCENDING').limit(limit)
        docs = await query.get()
        return [RoutingFeedbackDocument.from_firestore(doc.id, doc.to_dict()) for doc in docs]

    async def submit_feedback(
        self,
        feedback_id: str,
        is_correct: bool,
        corrected_tools: Optional[List[dict]] = None,
        feedback_notes: Optional[str] = None
    ) -> Optional[RoutingFeedbackDocument]:
        """Submit user feedback on a routing decision."""
        await self._ensure_stats_doc()

        doc_ref = self.collection.document(feedback_id)
        doc = await doc_ref.get()

        if not doc.exists:
            return None

        # Check previous state for counter updates
        prev_data = doc.to_dict()
        was_pending = prev_data.get('is_correct') is None

        update_data = {
            'is_correct': is_correct,
            'corrected_tools': corrected_tools,
            'feedback_notes': feedback_notes,
            'feedback_at': datetime.utcnow()
        }

        await doc_ref.update(update_data)

        # Update counters atomically
        counter_updates = {}
        if was_pending:
            counter_updates['feedback_pending'] = Increment(-1)

        if is_correct:
            counter_updates['feedback_correct'] = Increment(1)
        elif corrected_tools is not None:
            counter_updates['feedback_corrected'] = Increment(1)

        if counter_updates:
            await self.stats_ref.update(counter_updates)

        return await self.get_by_id(feedback_id)

    async def mark_as_exported(self, feedback_ids: List[str]) -> int:
        """Mark feedback records as exported for training."""
        if not feedback_ids:
            return 0

        await self._ensure_stats_doc()
        exported_count = 0

        for feedback_id in feedback_ids:
            doc_ref = self.collection.document(feedback_id)
            doc = await doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                if not data.get('exported_for_training', False):
                    await doc_ref.update({
                        'exported_for_training': True,
                        'exported_at': datetime.utcnow()
                    })
                    exported_count += 1

        # Update exported counter
        if exported_count > 0:
            await self.stats_ref.update({
                'feedback_exported': Increment(exported_count)
            })

        return exported_count

    async def get_stats(self) -> dict:
        """Get statistics about feedback collection from counter document."""
        await self._ensure_stats_doc()

        doc = await self.stats_ref.get()
        if not doc.exists:
            return FeedbackStats().to_response()

        stats = FeedbackStats.from_firestore(doc.to_dict())
        return stats.to_response()

    async def get_for_training_export(
        self,
        include_corrections_only: bool = False,
        include_confirmed_correct: bool = True,
        unexported_only: bool = True
    ) -> List[RoutingFeedbackDocument]:
        """Get feedback records suitable for training export."""
        records = []

        # Get corrections
        corrected = await self.get_corrected(limit=10000, unexported_only=unexported_only)
        records.extend(corrected)

        # Get confirmed correct (if requested)
        if include_confirmed_correct and not include_corrections_only:
            correct = await self.get_confirmed_correct(limit=10000, unexported_only=unexported_only)
            records.extend(correct)

        return records
