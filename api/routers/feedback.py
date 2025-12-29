"""API router for query log collection and export."""
from fastapi import APIRouter, Depends, HTTPException
from google.cloud.firestore_v1 import AsyncClient
import uuid

from api.database.firestore_client import get_db
from api.database.firestore_models import QueryLogDocument
from api.database.repositories.feedback_repo import QueryLogRepository
from api.schemas.feedback import (
    QueryLogRecord, QueryLogResponse, FeedbackSubmission,
    ToolIntentionOptions, TrainingExportRequest, TrainingExportResponse,
    TrainingExample, QueryLogStats
)
from src.rag.tool_intentions import TOOL_INTENTIONS, is_valid_intention

router = APIRouter(prefix="/query-logs", tags=["query-logs"])


@router.get("/tools", response_model=ToolIntentionOptions)
async def get_tool_intentions():
    """Get available tools and their valid intentions for the feedback UI."""
    return ToolIntentionOptions(tools=TOOL_INTENTIONS)


@router.post("/record", response_model=QueryLogResponse)
async def create_query_log(
    record: QueryLogRecord,
    db: AsyncClient = Depends(get_db)
):
    """
    Record a query log for later review.

    This is called automatically when a query is processed.
    Returns the record ID for associating feedback later.
    """
    repo = QueryLogRepository(db)

    query_log = QueryLogDocument(
        id=str(uuid.uuid4()),
        user_query=record.user_query,
        character_name=record.character_name,
        campaign_id=record.campaign_id,
        predicted_tools=[t.model_dump() for t in record.predicted_tools],
        predicted_entities=[e.model_dump() for e in record.predicted_entities] if record.predicted_entities else None,
        classifier_backend=record.classifier_backend,
        classifier_inference_time_ms=record.classifier_inference_time_ms,
        original_query=record.original_query,
        assistant_response=record.assistant_response,
        context_sources=record.context_sources,
        response_time_ms=record.response_time_ms,
        model_used=record.model_used,
    )

    created = await repo.create(query_log)

    return QueryLogResponse(**created.to_response())


@router.get("/pending", response_model=list[QueryLogResponse])
async def get_pending_logs(
    limit: int = 50,
    db: AsyncClient = Depends(get_db)
):
    """Get query logs pending user review."""
    repo = QueryLogRepository(db)
    records = await repo.get_pending_review(limit=limit)
    return [QueryLogResponse(**r.to_response()) for r in records]


@router.get("/recent", response_model=list[QueryLogResponse])
async def get_recent_logs(
    limit: int = 100,
    db: AsyncClient = Depends(get_db)
):
    """Get most recent query logs."""
    repo = QueryLogRepository(db)
    records = await repo.get_recent(limit=limit)
    return [QueryLogResponse(**r.to_response()) for r in records]


@router.get("/stats", response_model=QueryLogStats)
async def get_query_log_stats(db: AsyncClient = Depends(get_db)):
    """Get statistics about collected query logs."""
    repo = QueryLogRepository(db)
    stats = await repo.get_stats()
    return QueryLogStats(**stats)


@router.get("/{log_id}", response_model=QueryLogResponse)
async def get_query_log(
    log_id: str,
    db: AsyncClient = Depends(get_db)
):
    """Get a specific query log by ID."""
    repo = QueryLogRepository(db)
    record = await repo.get_by_id(log_id)

    if not record:
        raise HTTPException(status_code=404, detail="Query log not found")

    return QueryLogResponse(**record.to_response())


@router.post("/{log_id}/feedback", response_model=QueryLogResponse)
async def submit_feedback(
    log_id: str,
    submission: FeedbackSubmission,
    db: AsyncClient = Depends(get_db)
):
    """
    Submit user feedback on a query log's routing decision.

    - If is_correct=True: The routing was correct, no corrections needed
    - If is_correct=False: Provide corrected_tools with the correct routing
    """
    repo = QueryLogRepository(db)

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
        log_id=log_id,
        is_correct=submission.is_correct,
        corrected_tools=[c.model_dump() for c in submission.corrected_tools] if submission.corrected_tools else None,
        feedback_notes=submission.feedback_notes
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Query log not found")

    return QueryLogResponse(**updated.to_response())


@router.post("/export", response_model=TrainingExportResponse)
async def export_training_data(
    request: TrainingExportRequest,
    db: AsyncClient = Depends(get_db)
):
    """
    Export query log data in training format for fine-tuning.

    Returns examples in the format expected by the joint classifier training.
    """
    repo = QueryLogRepository(db)

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

    return TrainingExportResponse(
        examples=examples,
        total_records=len(records),
        corrections_count=corrections_count,
        confirmed_correct_count=confirmed_count
    )
