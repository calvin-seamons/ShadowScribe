"""API router for routing feedback collection and export."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api.database.connection import get_db
from api.database.feedback_models import RoutingFeedback
from api.database.repositories.feedback_repo import FeedbackRepository
from api.schemas.feedback import (
    RoutingRecord, RoutingRecordResponse, FeedbackSubmission,
    ToolIntentionOptions, TrainingExportRequest, TrainingExportResponse,
    TrainingExample, FeedbackStats
)
from src.rag.tool_intentions import TOOL_INTENTIONS, is_valid_intention

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("/tools", response_model=ToolIntentionOptions)
async def get_tool_intentions():
    """Get available tools and their valid intentions for the feedback UI."""
    return ToolIntentionOptions(tools=TOOL_INTENTIONS)


@router.post("/record", response_model=RoutingRecordResponse)
async def create_routing_record(
    record: RoutingRecord,
    db: AsyncSession = Depends(get_db)
):
    """
    Record a routing decision for later review.
    
    This is called automatically when a query is processed.
    Returns the record ID for associating feedback later.
    """
    repo = FeedbackRepository(db)
    
    feedback = RoutingFeedback(
        user_query=record.user_query,
        character_name=record.character_name,
        campaign_id=record.campaign_id,
        predicted_tools=[t.model_dump() for t in record.predicted_tools],
        predicted_entities=[e.model_dump() for e in record.predicted_entities] if record.predicted_entities else None,
        classifier_backend=record.classifier_backend,
        classifier_inference_time_ms=record.classifier_inference_time_ms
    )
    
    created = await repo.create(feedback)
    await db.commit()
    
    return RoutingRecordResponse(**created.to_dict())


@router.get("/pending", response_model=List[RoutingRecordResponse])
async def get_pending_feedback(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get routing records pending user review."""
    repo = FeedbackRepository(db)
    records = await repo.get_pending_review(limit=limit)
    return [RoutingRecordResponse(**r.to_dict()) for r in records]


@router.get("/recent", response_model=List[RoutingRecordResponse])
async def get_recent_records(
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get most recent routing records."""
    repo = FeedbackRepository(db)
    records = await repo.get_recent(limit=limit)
    return [RoutingRecordResponse(**r.to_dict()) for r in records]


@router.get("/record/{feedback_id}", response_model=RoutingRecordResponse)
async def get_routing_record(
    feedback_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific routing record by ID."""
    repo = FeedbackRepository(db)
    record = await repo.get_by_id(feedback_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Routing record not found")
    
    return RoutingRecordResponse(**record.to_dict())


@router.post("/record/{feedback_id}/submit", response_model=RoutingRecordResponse)
async def submit_feedback(
    feedback_id: str,
    submission: FeedbackSubmission,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit user feedback on a routing decision.
    
    - If is_correct=True: The routing was correct, no corrections needed
    - If is_correct=False: Provide corrected_tools with the correct routing
    """
    repo = FeedbackRepository(db)
    
    # Validate that correction is provided if marking as incorrect
    if not submission.is_correct and not submission.corrected_tools:
        raise HTTPException(
            status_code=400,
            detail="corrected_tools is required when is_correct=False"
        )
    
    # Validate tool/intention combinations if corrections provided
    if submission.corrected_tools:
        for correction in submission.corrected_tools:
            if correction.tool not in TOOL_INTENTIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid tool: {correction.tool}. Valid tools: {list(TOOL_INTENTIONS.keys())}"
                )
            if not is_valid_intention(correction.tool, correction.intention):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid intention '{correction.intention}' for tool '{correction.tool}'. Valid intentions: {TOOL_INTENTIONS[correction.tool]}"
                )
    
    updated = await repo.submit_feedback(
        feedback_id=feedback_id,
        is_correct=submission.is_correct,
        corrected_tools=[c.model_dump() for c in submission.corrected_tools] if submission.corrected_tools else None,
        feedback_notes=submission.feedback_notes
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Routing record not found")
    
    await db.commit()
    return RoutingRecordResponse(**updated.to_dict())


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(db: AsyncSession = Depends(get_db)):
    """Get statistics about collected feedback."""
    repo = FeedbackRepository(db)
    stats = await repo.get_stats()
    return FeedbackStats(**stats)


@router.post("/export", response_model=TrainingExportResponse)
async def export_training_data(
    request: TrainingExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Export feedback data in training format for fine-tuning.
    
    Returns examples in the format expected by the joint classifier training.
    """
    repo = FeedbackRepository(db)
    
    records = await repo.get_for_training_export(
        include_corrections_only=request.include_corrections_only,
        include_confirmed_correct=request.include_confirmed_correct,
        unexported_only=True  # Only get unexported records
    )
    
    # Convert to training examples
    examples = []
    corrections_count = 0
    confirmed_count = 0
    exported_ids = []
    
    for record in records:
        training_examples = record.to_training_example()
        for ex in training_examples:
            examples.append(TrainingExample(**ex))
        
        if record.corrected_tools:
            corrections_count += 1
        else:
            confirmed_count += 1
        
        exported_ids.append(record.id)
    
    # Mark as exported if requested
    if request.mark_as_exported and exported_ids:
        await repo.mark_as_exported(exported_ids)
        await db.commit()
    
    return TrainingExportResponse(
        examples=examples,
        total_records=len(records),
        corrections_count=corrections_count,
        confirmed_correct_count=confirmed_count
    )
