"""Character repository for Firestore operations."""
from google.cloud.firestore_v1 import AsyncClient
from typing import List, Optional
from datetime import datetime
import re
import json
import uuid

from api.database.firestore_client import CHARACTERS_COLLECTION
from api.database.firestore_models import CharacterDocument
from src.rag.character.character_types import Character as CharacterDataclass


def _json_serialize(obj):
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class CharacterRepository:
    """Repository for character CRUD operations using Firestore."""

    def __init__(self, db: AsyncClient):
        self.db = db
        self.collection = db.collection(CHARACTERS_COLLECTION)

    async def create(self, character: CharacterDataclass, user_id: str, campaign_id: str) -> CharacterDocument:
        """Create a new character in Firestore."""
        character_data = character.model_dump()

        # Handle datetime serialization
        character_data_json = json.dumps(character_data, default=_json_serialize)
        character_data = json.loads(character_data_json)

        doc_id = self._generate_id(character.character_base.name)

        doc = CharacterDocument(
            id=doc_id,
            user_id=user_id,
            campaign_id=campaign_id,
            name=character.character_base.name,
            race=character.character_base.race,
            character_class=character.character_base.character_class,
            level=character.character_base.total_level,
            data=character_data
        )

        await self.collection.document(doc_id).set(doc.to_dict())
        return doc

    async def get_by_id(self, character_id: str) -> Optional[CharacterDocument]:
        """Get character by ID."""
        doc_ref = self.collection.document(character_id)
        doc = await doc_ref.get()

        if not doc.exists:
            return None

        return CharacterDocument.from_firestore(doc.id, doc.to_dict())

    async def get_by_name(self, name: str) -> Optional[CharacterDocument]:
        """Get character by name."""
        query = self.collection.where('name', '==', name).limit(1)
        docs = await query.get()

        for doc in docs:
            return CharacterDocument.from_firestore(doc.id, doc.to_dict())

        return None

    async def get_all(self) -> List[CharacterDocument]:
        """Get all characters."""
        docs = await self.collection.get()
        return [CharacterDocument.from_firestore(doc.id, doc.to_dict()) for doc in docs]

    async def get_all_by_user(self, user_id: str) -> List[CharacterDocument]:
        """Get all characters belonging to a specific user."""
        query = self.collection.where('user_id', '==', user_id)
        docs = await query.get()
        # Sort in Python to avoid needing composite index
        characters = [CharacterDocument.from_firestore(doc.id, doc.to_dict()) for doc in docs]
        return sorted(characters, key=lambda c: c.created_at or datetime.min)

    async def update(self, character_id: str, character: CharacterDataclass) -> Optional[CharacterDocument]:
        """Update character."""
        doc_ref = self.collection.document(character_id)
        doc = await doc_ref.get()

        if not doc.exists:
            return None

        character_data = character.model_dump()
        character_data_json = json.dumps(character_data, default=_json_serialize)
        character_data = json.loads(character_data_json)

        update_data = {
            'name': character.character_base.name,
            'race': character.character_base.race,
            'character_class': character.character_base.character_class,
            'level': character.character_base.total_level,
            'data': character_data,
            'updated_at': datetime.utcnow()
        }

        await doc_ref.update(update_data)
        return await self.get_by_id(character_id)

    async def delete(self, character_id: str) -> bool:
        """Delete character."""
        doc_ref = self.collection.document(character_id)
        doc = await doc_ref.get()

        if not doc.exists:
            return False

        await doc_ref.delete()
        return True

    async def update_section(self, character_id: str, section: str, data: dict) -> Optional[CharacterDocument]:
        """
        Update a specific section of a character.

        Args:
            character_id: Character ID to update
            section: Section name (e.g., 'ability_scores', 'inventory', 'spell_list')
            data: Dictionary containing the updated section data

        Returns:
            Updated CharacterDocument or None if character not found

        Raises:
            ValueError: If section name is invalid
        """
        valid_sections = {
            'character_base', 'characteristics', 'ability_scores', 'combat_stats',
            'background_info', 'personality', 'backstory', 'organizations',
            'allies', 'enemies', 'proficiencies', 'damage_modifiers',
            'passive_scores', 'senses', 'action_economy', 'features_and_traits',
            'inventory', 'spell_list', 'objectives_and_contracts', 'notes'
        }

        if section not in valid_sections:
            raise ValueError(
                f"Invalid section '{section}'. "
                f"Valid sections: {', '.join(sorted(valid_sections))}"
            )

        character = await self.get_by_id(character_id)
        if not character:
            return None

        # Update the specific section in the data
        character_data = character.data.copy()
        character_data[section] = data

        # Handle datetime serialization
        character_data_json = json.dumps(character_data, default=_json_serialize)
        character_data = json.loads(character_data_json)

        doc_ref = self.collection.document(character_id)
        await doc_ref.update({
            'data': character_data,
            'updated_at': datetime.utcnow()
        })

        return await self.get_by_id(character_id)

    @staticmethod
    def _generate_id(name: str) -> str:
        """Generate URL-safe ID from character name."""
        return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
