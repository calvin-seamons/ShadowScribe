
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from typing import Optional

from api.main import app
from api.auth import get_current_user, get_db
from api.database.firestore_models import UserDocument
from api.database.repositories.character_repo import CharacterRepository

# Mock dependencies
async def mock_get_current_user():
    return UserDocument(id="user123", email="test@example.com")

async def mock_get_db():
    mock_db = AsyncMock()
    # Setup collection/document structure
    mock_collection = MagicMock()
    mock_doc_ref = MagicMock()
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_doc_ref

    # Mock behavior for "get" (finding character)
    # We will control this via side_effect in the test if needed,
    # but here we set a default that can be overridden

    return mock_db

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_db] = mock_get_db
    yield TestClient(app)
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_update_character_ownership_check(client):
    """
    Test that updating another user's character returns 403 Forbidden.
    """

    # We need to patch CharacterRepository to return a character owned by someone else
    with patch("api.routers.characters.CharacterRepository") as MockRepoClass:
        mock_repo = MockRepoClass.return_value

        # Mock get_by_id to return character owned by "other_user"
        mock_character = MagicMock()
        mock_character.user_id = "other_user"
        mock_character.id = "char1"
        mock_repo.get_by_id = AsyncMock(return_value=mock_character)

        # Mock update to just return the character (if it were called)
        mock_repo.update = AsyncMock(return_value=mock_character)

        # Payload for update
        payload = {
            "character": {
                "character_base": {
                    "name": "Updated Name",
                    "race": "Human",
                    "character_class": "Fighter",
                    "total_level": 1
                }
            }
        }

        response = client.put("/api/characters/char1", json=payload)

        # Expect 403 Forbidden because user123 != other_user
        # Currently this will fail (likely return 200 or 422) because the check is missing
        assert response.status_code == 403
        assert "Cannot update another user's character" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_character_section_ownership_check(client):
    """
    Test that updating another user's character section returns 403 Forbidden.
    """

    with patch("api.routers.characters.CharacterRepository") as MockRepoClass:
        mock_repo = MockRepoClass.return_value

        mock_character = MagicMock()
        mock_character.user_id = "other_user"
        mock_character.id = "char1"
        mock_repo.get_by_id = AsyncMock(return_value=mock_character)

        mock_repo.update_section = AsyncMock(return_value=mock_character)

        payload = {
            "data": {"some": "data"}
        }

        response = client.patch("/api/characters/char1/notes", json=payload)

        assert response.status_code == 403
        assert "Cannot update another user's character" in response.json()["detail"]
