"""Character REST API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from google.cloud.firestore_v1 import AsyncClient
from typing import List, Optional
from dacite import from_dict
import dacite

from api.database.firestore_client import get_db
from api.database.repositories.character_repo import CharacterRepository
from api.database.firestore_models import UserDocument
from api.auth import get_current_user
from api.schemas.character import (
    CharacterResponse,
    CharacterListResponse,
    FetchCharacterRequest,
    FetchCharacterResponse,
    CharacterCreateRequest,
    CharacterUpdateRequest,
    SectionUpdateRequest,
    SectionUpdateResponse
)
from api.services.dndbeyond_service import DndBeyondService
from src.rag.character.character_types import Character

router = APIRouter()


@router.get("/characters", response_model=CharacterListResponse)
async def list_characters(
    db: AsyncClient = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user)
):
    """List all characters belonging to the current user."""
    repo = CharacterRepository(db)
    characters = await repo.get_all_by_user(current_user.id)

    return {
        'characters': [char.to_response() for char in characters]
    }


@router.get("/characters/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: str,
    db: AsyncClient = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Get character by ID.

    Restricted to the character's owner.
    """
    repo = CharacterRepository(db)
    character = await repo.get_by_id(character_id)

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    if character.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot access another user's character")

    return character.to_response()


@router.delete("/characters/{character_id}")
async def delete_character(
    character_id: str,
    db: AsyncClient = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user)
):
    """Delete character by ID. Users can only delete their own characters."""
    repo = CharacterRepository(db)
    character = await repo.get_by_id(character_id)

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    if character.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's character")

    await repo.delete(character_id)

    return {'status': 'deleted', 'id': character_id}


@router.post("/characters/fetch", response_model=FetchCharacterResponse)
async def fetch_character_from_dndbeyond(request: FetchCharacterRequest):
    """
    Fetch character data from D&D Beyond URL.

    This endpoint extracts the character ID from a D&D Beyond URL
    and fetches the complete character JSON from the D&D Beyond API.

    Args:
        request: Request containing D&D Beyond character URL

    Returns:
        Complete character JSON data from D&D Beyond

    Raises:
        HTTPException: If URL is invalid or fetching fails
    """
    # Extract character ID from URL
    character_id = DndBeyondService.extract_character_id(request.url)

    if not character_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid D&D Beyond URL. Expected format: https://dndbeyond.com/characters/{id}"
        )

    # Fetch character data from D&D Beyond
    json_data = await DndBeyondService.fetch_character_json(character_id)

    return {
        'json_data': json_data,
        'character_id': character_id
    }


@router.post("/characters", response_model=CharacterResponse)
async def create_character(
    request: CharacterCreateRequest,
    db: AsyncClient = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Create a new character from parsed Character dataclass.

    This endpoint accepts a complete Character dataclass (as JSON dictionary)
    and saves it to the database. Typically used after parsing D&D Beyond JSON
    via the character creation wizard.

    Args:
        request: Request containing complete Character data and optional campaign_id
        db: Firestore client
        current_user: Authenticated user

    Returns:
        Created character with database ID and timestamps

    Raises:
        HTTPException: If character data is invalid or creation fails
    """
    try:
        # Convert dict to Character dataclass using from_dict with lenient type checking
        character = from_dict(
            data_class=Character,
            data=request.character,
            config=dacite.Config(
                strict=False,
                check_types=False  # Allow type flexibility for nested structures
            )
        )

        # Create in database (or update if already exists)
        repo = CharacterRepository(db)

        # Check if character already exists by name for this user
        existing = await repo.get_by_name(character.character_base.name)

        if existing and existing.user_id == current_user.id:
            # Update existing character
            print(f"⚠️  Character '{character.character_base.name}' already exists, updating...")
            db_character = await repo.update(existing.id, character)
        else:
            # Create new character with user_id and campaign_id
            db_character = await repo.create(
                character,
                user_id=current_user.id,
                campaign_id=request.campaign_id
            )

        return db_character.to_response()

    except Exception as e:
        # Log detailed error for debugging
        import traceback
        print(f"❌ Error creating/updating character: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create character: {str(e)}"
        )


@router.put("/characters/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: str,
    request: CharacterUpdateRequest,
    db: AsyncClient = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Perform full character update (replace entire character).

    This endpoint replaces the entire character record with new data.
    Use PATCH /api/characters/{id}/{section} for partial section updates.

    Args:
        character_id: Character ID to update
        request: Request containing complete Character data
        db: Firestore client
        current_user: Authenticated user

    Returns:
        Updated character with new timestamps

    Raises:
        HTTPException: If character not found or update fails
    """
    try:
        repo = CharacterRepository(db)

        # Check ownership
        existing_char = await repo.get_by_id(character_id)
        if not existing_char:
            raise HTTPException(status_code=404, detail="Character not found")

        if existing_char.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot update another user's character")

        # Convert dict to Character dataclass with lenient type checking
        character = from_dict(
            data_class=Character,
            data=request.character,
            config=dacite.Config(
                strict=False,
                check_types=False  # Allow type flexibility for nested structures
            )
        )

        # Update in database
        db_character = await repo.update(character_id, character)

        if not db_character:
            raise HTTPException(status_code=404, detail="Character not found")

        return db_character.to_response()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update character: {str(e)}"
        )


@router.patch("/characters/{character_id}/{section}", response_model=SectionUpdateResponse)
async def update_character_section(
    character_id: str,
    section: str,
    request: SectionUpdateRequest,
    db: AsyncClient = Depends(get_db),
    current_user: UserDocument = Depends(get_current_user)
):
    """
    Perform partial section update for incremental saves.

    This endpoint updates a specific section of a character without replacing
    the entire character. Useful for the wizard's section-by-section editing.

    Valid sections:
    - character_base
    - characteristics
    - ability_scores
    - combat_stats
    - background_info
    - personality
    - backstory
    - organizations
    - allies
    - enemies
    - proficiencies
    - damage_modifiers
    - passive_scores
    - senses
    - action_economy
    - features_and_traits
    - inventory
    - spell_list
    - objectives_and_contracts
    - notes

    Args:
        character_id: Character ID to update
        section: Section name (e.g., 'ability_scores', 'inventory')
        request: Request containing section-specific data
        db: Firestore client

    Returns:
        Update status and section name

    Raises:
        HTTPException: If character not found, section invalid, or update fails
    """
    try:
        repo = CharacterRepository(db)

        # Check ownership
        existing_char = await repo.get_by_id(character_id)
        if not existing_char:
            raise HTTPException(status_code=404, detail="Character not found")

        if existing_char.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot update another user's character")

        db_character = await repo.update_section(character_id, section, request.data)

        if not db_character:
            raise HTTPException(status_code=404, detail="Character not found")

        return {
            'updated': True,
            'section': section,
            'message': f"Successfully updated {section}"
        }

    except ValueError as e:
        # Invalid section name
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update section: {str(e)}"
        )
