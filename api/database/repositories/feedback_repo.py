"""Query log repository for Firestore operations."""
from google.cloud.firestore_v1 import AsyncClient
from google.cloud.firestore_v1 import Increment
from typing import List, Optional
from datetime import datetime
import uuid

from api.database.firestore_client import (
    QUERY_LOGS_COLLECTION,
    METADATA_COLLECTION,
    STATS_DOCUMENT
)
from api.database.firestore_models import QueryLogDocument, QueryLogStats


class QueryLogRepository:
    """Repository for query log CRUD operations using Firestore."""

    def __init__(self, db: AsyncClient):
        self.db = db
        self.collection = db.collection(QUERY_LOGS_COLLECTION)
        self.stats_ref = db.collection(METADATA_COLLECTION).document(STATS_DOCUMENT)

    async def _ensure_stats_doc(self):
        """Ensure stats document exists with default values."""
        doc = await self.stats_ref.get()
        if not doc.exists:
            await self.stats_ref.set({
                'queries_total': 0,
                'queries_pending': 0,
                'queries_correct': 0,
                'queries_corrected': 0,
                'queries_exported': 0
            })

    async def create(self, query_log: QueryLogDocument) -> QueryLogDocument:
        """Create a new query log record."""
        await self._ensure_stats_doc()

        doc_id = query_log.id or str(uuid.uuid4())
        query_log.id = doc_id

        await self.collection.document(doc_id).set(query_log.to_dict())

        # Update counters atomically
        await self.stats_ref.update({
            'queries_total': Increment(1),
            'queries_pending': Increment(1)
        })

        return query_log

    async def get_by_id(self, log_id: str) -> Optional[QueryLogDocument]:
        """Get query log by ID."""
        doc_ref = self.collection.document(log_id)
        doc = await doc_ref.get()

        if not doc.exists:
            return None

        return QueryLogDocument.from_firestore(doc.id, doc.to_dict())

    async def get_pending_review(self, limit: int = 50) -> List[QueryLogDocument]:
        """Get query log records pending user review."""
        query = (
            self.collection
            .where('is_correct', '==', None)
            .order_by('created_at', direction='DESCENDING')
            .limit(limit)
        )
        docs = await query.get()
        return [QueryLogDocument.from_firestore(doc.id, doc.to_dict()) for doc in docs]

    async def get_recent(self, limit: int = 100) -> List[QueryLogDocument]:
        """Get most recent query log records."""
        query = (
            self.collection
            .order_by('created_at', direction='DESCENDING')
            .limit(limit)
        )
        docs = await query.get()
        return [QueryLogDocument.from_firestore(doc.id, doc.to_dict()) for doc in docs]

    async def get_corrected(self, limit: int = 1000, unexported_only: bool = False) -> List[QueryLogDocument]:
        """Get query log records with user corrections."""
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
                results.append(QueryLogDocument.from_firestore(doc.id, data))

        return results

    async def get_confirmed_correct(self, limit: int = 1000, unexported_only: bool = False) -> List[QueryLogDocument]:
        """Get query log records confirmed as correct by user."""
        query = self.collection.where('is_correct', '==', True)

        if unexported_only:
            query = query.where('exported_for_training', '==', False)

        query = query.order_by('created_at', direction='DESCENDING').limit(limit)
        docs = await query.get()
        return [QueryLogDocument.from_firestore(doc.id, doc.to_dict()) for doc in docs]

    async def submit_feedback(
        self,
        log_id: str,
        is_correct: bool,
        corrected_tools: Optional[List[dict]] = None,
        feedback_notes: Optional[str] = None
    ) -> Optional[QueryLogDocument]:
        """Submit user feedback on a routing decision."""
        await self._ensure_stats_doc()

        doc_ref = self.collection.document(log_id)
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
            counter_updates['queries_pending'] = Increment(-1)

        if is_correct:
            counter_updates['queries_correct'] = Increment(1)
        elif corrected_tools is not None:
            counter_updates['queries_corrected'] = Increment(1)

        if counter_updates:
            await self.stats_ref.update(counter_updates)

        return await self.get_by_id(log_id)

    async def mark_as_exported(self, log_ids: List[str]) -> int:
        """Mark query log records as exported for training."""
        if not log_ids:
            return 0

        await self._ensure_stats_doc()
        exported_count = 0

        for log_id in log_ids:
            doc_ref = self.collection.document(log_id)
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
                'queries_exported': Increment(exported_count)
            })

        return exported_count

    async def get_stats(self) -> dict:
        """Get statistics about query logs from counter document."""
        await self._ensure_stats_doc()

        doc = await self.stats_ref.get()
        if not doc.exists:
            return QueryLogStats().to_response()

        stats = QueryLogStats.from_firestore(doc.to_dict())
        return stats.to_response()

    async def get_for_training_export(
        self,
        include_corrections_only: bool = False,
        include_confirmed_correct: bool = True,
        unexported_only: bool = True
    ) -> List[QueryLogDocument]:
        """Get query log records suitable for training export."""
        records = []

        # Get corrections
        corrected = await self.get_corrected(limit=10000, unexported_only=unexported_only)
        records.extend(corrected)

        # Get confirmed correct (if requested)
        if include_confirmed_correct and not include_corrections_only:
            correct = await self.get_confirmed_correct(limit=10000, unexported_only=unexported_only)
            records.extend(correct)

        return records


# Backward compatibility alias
FeedbackRepository = QueryLogRepository
