"""Campaign REST API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from google.cloud.firestore_v1 import AsyncClient
from typing import List, Optional
from pydantic import BaseModel
import uuid

from api.database.firestore_client import get_db, CAMPAIGNS_COLLECTION
from api.database.firestore_models import CampaignDocument, UserDocument
from api.auth import get_current_user, get_optional_user

router = APIRouter()


# Pydantic schemas
class CampaignResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    campaigns: List[CampaignResponse]


class CampaignCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


@router.get("/campaigns", response_model=CampaignListResponse)
async def list_campaigns(
    db: AsyncClient = Depends(get_db),
    _: Optional[UserDocument] = Depends(get_optional_user)  # Optional auth for now
):
    """
    List all available campaigns.

    Returns all campaigns in the shared campaign pool.
    Authentication is optional for listing.
    """
    collection = db.collection(CAMPAIGNS_COLLECTION)
    query = collection.order_by('name')
    docs = await query.get()

    campaigns = [CampaignDocument.from_firestore(doc.id, doc.to_dict()) for doc in docs]

    return {
        'campaigns': [c.to_response() for c in campaigns]
    }


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    db: AsyncClient = Depends(get_db)
):
    """Get a specific campaign by ID."""
    doc_ref = db.collection(CAMPAIGNS_COLLECTION).document(campaign_id)
    doc = await doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign = CampaignDocument.from_firestore(doc.id, doc.to_dict())
    return campaign.to_response()


@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    request: CampaignCreateRequest,
    db: AsyncClient = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user)  # Requires auth
):
    """
    Create a new campaign.

    Note: This is a simplified implementation for initial setup.
    Future versions will have more elaborate campaign creation workflows.
    """
    campaign_id = str(uuid.uuid4())

    campaign = CampaignDocument(
        id=campaign_id,
        name=request.name,
        description=request.description
    )

    doc_ref = db.collection(CAMPAIGNS_COLLECTION).document(campaign_id)
    await doc_ref.set(campaign.to_dict())

    return campaign.to_response()
