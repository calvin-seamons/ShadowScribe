"""Session Notes REST API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from google.cloud.firestore_v1 import AsyncClient
from typing import List, Optional
from pydantic import BaseModel
import uuid

from api.database.firestore_client import get_db, CAMPAIGNS_COLLECTION, NOTES_SUBCOLLECTION
from api.database.firestore_models import SessionNoteDocument, CampaignDocument, UserDocument
from api.auth import get_current_user

router = APIRouter()


# Pydantic schemas
class SessionNoteResponse(BaseModel):
    id: str
    campaign_id: str
    user_id: str
    content: str
    processed_content: Optional[dict] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class SessionNoteListResponse(BaseModel):
    notes: List[SessionNoteResponse]


class SessionNoteCreateRequest(BaseModel):
    content: str


async def process_note_content(note_id: str, content: str):
    """
    Background task to parse and process note content.

    This will be expanded to integrate with the existing RAG/parsing systems.
    For now, it's a placeholder that stores the raw content.

    TODO:
    - Extract entities (characters, locations, items, events)
    - Generate embeddings for semantic search
    - Update campaign context in Cloud Storage
    """
    # Placeholder: In future, this will call the note parsing system
    print(f"[Notes] Processing note {note_id}: {len(content)} characters")
    # The actual processing will be implemented when we integrate with
    # the existing session_notes_storage and entity extraction systems


@router.get("/campaigns/{campaign_id}/notes", response_model=SessionNoteListResponse)
async def list_campaign_notes(
    campaign_id: str,
    db: AsyncClient = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    List all notes for a campaign.

    Requires authentication. Returns all notes in the campaign,
    not just the current user's notes.
    """
    # Verify campaign exists
    campaign_ref = db.collection(CAMPAIGNS_COLLECTION).document(campaign_id)
    campaign_doc = await campaign_ref.get()

    if not campaign_doc.exists:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get all notes for this campaign (subcollection)
    notes_collection = campaign_ref.collection(NOTES_SUBCOLLECTION)
    query = notes_collection.order_by('created_at', direction='DESCENDING')
    docs = await query.get()

    notes = [
        SessionNoteDocument.from_firestore(doc.id, campaign_id, doc.to_dict())
        for doc in docs
    ]

    return {
        'notes': [n.to_response() for n in notes]
    }


@router.post("/campaigns/{campaign_id}/notes", response_model=SessionNoteResponse)
async def create_note(
    campaign_id: str,
    request: SessionNoteCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncClient = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Submit session notes for a campaign.

    The note content will be saved immediately, and background processing
    will parse and structure the content for later retrieval.
    """
    # Verify campaign exists
    campaign_ref = db.collection(CAMPAIGNS_COLLECTION).document(campaign_id)
    campaign_doc = await campaign_ref.get()

    if not campaign_doc.exists:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Create the note
    note_id = str(uuid.uuid4())
    note = SessionNoteDocument(
        id=note_id,
        campaign_id=campaign_id,
        user_id=current_user.id,
        content=request.content,
        processed_content=None  # Will be filled by background task
    )

    # Save to subcollection
    note_ref = campaign_ref.collection(NOTES_SUBCOLLECTION).document(note_id)
    await note_ref.set(note.to_dict())

    # Reload to get server timestamp
    note_doc = await note_ref.get()
    saved_note = SessionNoteDocument.from_firestore(note_doc.id, campaign_id, note_doc.to_dict())

    # Schedule background processing
    background_tasks.add_task(process_note_content, note_id, request.content)

    return saved_note.to_response()


@router.get("/campaigns/{campaign_id}/notes/{note_id}", response_model=SessionNoteResponse)
async def get_note(
    campaign_id: str,
    note_id: str,
    db: AsyncClient = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user)
):
    """Get a specific note by ID."""
    campaign_ref = db.collection(CAMPAIGNS_COLLECTION).document(campaign_id)
    note_ref = campaign_ref.collection(NOTES_SUBCOLLECTION).document(note_id)
    note_doc = await note_ref.get()

    if not note_doc.exists:
        raise HTTPException(status_code=404, detail="Note not found")

    note = SessionNoteDocument.from_firestore(note_doc.id, campaign_id, note_doc.to_dict())
    return note.to_response()


@router.delete("/campaigns/{campaign_id}/notes/{note_id}")
async def delete_note(
    campaign_id: str,
    note_id: str,
    db: AsyncClient = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Delete a note.

    Users can only delete their own notes.
    """
    campaign_ref = db.collection(CAMPAIGNS_COLLECTION).document(campaign_id)
    note_ref = campaign_ref.collection(NOTES_SUBCOLLECTION).document(note_id)
    note_doc = await note_ref.get()

    if not note_doc.exists:
        raise HTTPException(status_code=404, detail="Note not found")

    note = SessionNoteDocument.from_firestore(note_doc.id, campaign_id, note_doc.to_dict())

    if note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's note")

    await note_ref.delete()

    return {'status': 'deleted', 'id': note_id}
