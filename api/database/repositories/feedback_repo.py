"""Routing feedback repository for database operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from datetime import datetime

from api.database.feedback_models import RoutingFeedback


class FeedbackRepository:
    """Repository for routing feedback CRUD operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, feedback: RoutingFeedback) -> RoutingFeedback:
        """Create a new routing feedback record."""
        self.session.add(feedback)
        await self.session.flush()
        return feedback
    
    async def get_by_id(self, feedback_id: str) -> Optional[RoutingFeedback]:
        """Get feedback by ID."""
        result = await self.session.execute(
            select(RoutingFeedback).where(RoutingFeedback.id == feedback_id)
        )
        return result.scalar_one_or_none()
    
    async def get_pending_review(self, limit: int = 50) -> List[RoutingFeedback]:
        """Get feedback records pending user review."""
        result = await self.session.execute(
            select(RoutingFeedback)
            .where(RoutingFeedback.is_correct.is_(None))
            .order_by(RoutingFeedback.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_recent(self, limit: int = 100) -> List[RoutingFeedback]:
        """Get most recent feedback records."""
        result = await self.session.execute(
            select(RoutingFeedback)
            .order_by(RoutingFeedback.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_corrected(self, limit: int = 1000, unexported_only: bool = False) -> List[RoutingFeedback]:
        """Get feedback records with user corrections."""
        query = select(RoutingFeedback).where(
            RoutingFeedback.is_correct == False,
            RoutingFeedback.corrected_tools.isnot(None)
        )
        
        if unexported_only:
            query = query.where(RoutingFeedback.exported_for_training == False)
        
        result = await self.session.execute(
            query.order_by(RoutingFeedback.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_confirmed_correct(self, limit: int = 1000, unexported_only: bool = False) -> List[RoutingFeedback]:
        """Get feedback records confirmed as correct by user."""
        query = select(RoutingFeedback).where(RoutingFeedback.is_correct == True)
        
        if unexported_only:
            query = query.where(RoutingFeedback.exported_for_training == False)
        
        result = await self.session.execute(
            query.order_by(RoutingFeedback.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
    
    async def submit_feedback(
        self,
        feedback_id: str,
        is_correct: bool,
        corrected_tools: Optional[List[dict]] = None,
        feedback_notes: Optional[str] = None
    ) -> Optional[RoutingFeedback]:
        """Submit user feedback on a routing decision."""
        await self.session.execute(
            update(RoutingFeedback)
            .where(RoutingFeedback.id == feedback_id)
            .values(
                is_correct=is_correct,
                corrected_tools=corrected_tools,
                feedback_notes=feedback_notes,
                feedback_at=datetime.utcnow()
            )
        )
        return await self.get_by_id(feedback_id)
    
    async def mark_as_exported(self, feedback_ids: List[str]) -> int:
        """Mark feedback records as exported for training."""
        if not feedback_ids:
            return 0
        
        result = await self.session.execute(
            update(RoutingFeedback)
            .where(RoutingFeedback.id.in_(feedback_ids))
            .values(
                exported_for_training=True,
                exported_at=datetime.utcnow()
            )
        )
        return result.rowcount
    
    async def get_stats(self) -> dict:
        """Get statistics about feedback collection."""
        # Total records
        total_result = await self.session.execute(
            select(func.count(RoutingFeedback.id))
        )
        total = total_result.scalar() or 0
        
        # Pending review (is_correct is NULL)
        pending_result = await self.session.execute(
            select(func.count(RoutingFeedback.id))
            .where(RoutingFeedback.is_correct.is_(None))
        )
        pending = pending_result.scalar() or 0
        
        # Confirmed correct
        correct_result = await self.session.execute(
            select(func.count(RoutingFeedback.id))
            .where(RoutingFeedback.is_correct == True)
        )
        correct = correct_result.scalar() or 0
        
        # Corrected (is_correct = False and has corrections)
        corrected_result = await self.session.execute(
            select(func.count(RoutingFeedback.id))
            .where(
                RoutingFeedback.is_correct == False,
                RoutingFeedback.corrected_tools.isnot(None)
            )
        )
        corrected = corrected_result.scalar() or 0
        
        # Exported
        exported_result = await self.session.execute(
            select(func.count(RoutingFeedback.id))
            .where(RoutingFeedback.exported_for_training == True)
        )
        exported = exported_result.scalar() or 0
        
        return {
            'total_records': total,
            'pending_review': pending,
            'confirmed_correct': correct,
            'corrected': corrected,
            'exported': exported
        }
    
    async def get_for_training_export(
        self,
        include_corrections_only: bool = False,
        include_confirmed_correct: bool = True,
        unexported_only: bool = True
    ) -> List[RoutingFeedback]:
        """Get feedback records suitable for training export."""
        records = []
        
        # Get corrections
        if not include_corrections_only or include_corrections_only:
            corrected = await self.get_corrected(limit=10000, unexported_only=unexported_only)
            records.extend(corrected)
        
        # Get confirmed correct (if requested)
        if include_confirmed_correct and not include_corrections_only:
            correct = await self.get_confirmed_correct(limit=10000, unexported_only=unexported_only)
            records.extend(correct)
        
        return records
