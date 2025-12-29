"""
Character Manager

A class for saving and loading Character objects from database or pickle files.
Supports both database (primary) and pickle file (fallback) storage.
"""

import logging
import json
import pickle
from pathlib import Path
from typing import Optional
from datetime import datetime

from google.cloud.firestore_v1 import AsyncClient

import dacite
from dacite import DaciteError

from src.rag.character.character_types import Character

logger = logging.getLogger(__name__)


class CharacterManager:
    """Manager for saving and loading Character objects from database or files."""
    
    def __init__(
        self,
        save_directory: str = "knowledge_base/saved_characters",
        db_session: Optional[AsyncClient] = None
    ):
        """
        Create a CharacterManager that persists Character objects to disk and optionally to a database.
        
        Parameters:
            save_directory (str): Filesystem path where pickle files will be stored; the directory is created if it does not exist.
            db_session (Optional[Any]): Optional database session; if provided a CharacterRepository is instantiated for database operations.
        """
        self.save_directory = Path(save_directory)
        self.save_directory.mkdir(parents=True, exist_ok=True)
        self.db_session = db_session
        self._repository = None
        
        # Import repository only if db_session is provided
        if db_session:
            from api.database.repositories.character_repo import CharacterRepository
            self._repository = CharacterRepository(db_session)
    
    async def load_character_from_db(self, name: str) -> Optional[Character]:
        """
        Load a Character object from the database.
        
        Args:
            name: The character name to load
            
        Returns:
            The loaded Character object or None if not found
        """
        if not self._repository:
            return None
            
        db_character = await self._repository.get_by_name(name)
        if not db_character:
            return None
        
        data = db_character.data
        
        # Helper to recursively convert datetime ISO strings to datetime objects
        def convert_datetimes(obj):
            if isinstance(obj, dict):
                return {k: convert_datetimes(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetimes(item) for item in obj]
            elif isinstance(obj, str):
                # Try to parse ISO datetime strings
                if len(obj) >= 19 and 'T' in obj:
                    try:
                        return datetime.fromisoformat(obj.replace('Z', '+00:00'))
                    except ValueError:
                        return obj
                return obj
            elif isinstance(obj, datetime):
                # Already a datetime, keep as-is
                return obj
            return obj
        
        data = convert_datetimes(data)
        
        # Use dacite for proper nested dataclass reconstruction
        config = dacite.Config(
            check_types=False,  # Allow flexible type matching
        )
        
        try:
            character = dacite.from_dict(
                data_class=Character,
                data=data,
                config=config
            )
            return character
        except DaciteError as e:
            logger.warning(f"Error reconstructing character from database with dacite: {e}")
            # Fall back to legacy reconstruction
            return self._legacy_load_character_from_db(data)
    
    def _legacy_load_character_from_db(self, data: dict) -> Character:
        """Legacy fallback for character reconstruction without dacite."""
        from src.rag.character.character_types import (
            CharacterBase, PhysicalCharacteristics, AbilityScores, CombatStats,
            BackgroundInfo, PersonalityTraits, Backstory, BackstorySection,
            FamilyBackstory, Organization, Ally, Enemy, Proficiency, 
            DamageModifier, PassiveScores, Senses, ActionEconomy, 
            FeaturesAndTraits, Inventory, SpellList, ObjectivesAndContracts
        )
        
        # Helper to reconstruct Backstory with nested dataclasses
        def reconstruct_backstory(bs_data):
            if not bs_data:
                return None
            
            # Reconstruct sections
            sections = []
            for section_data in bs_data.get('sections', []):
                if isinstance(section_data, dict):
                    sections.append(BackstorySection(**section_data))
                else:
                    sections.append(section_data)
            
            # Reconstruct family_backstory
            fb_data = bs_data.get('family_backstory', {})
            if fb_data:
                fb_sections = []
                for section_data in fb_data.get('sections', []):
                    if isinstance(section_data, dict):
                        fb_sections.append(BackstorySection(**section_data))
                    else:
                        fb_sections.append(section_data)
                family_backstory = FamilyBackstory(
                    parents=fb_data.get('parents', ''),
                    sections=fb_sections
                )
            else:
                family_backstory = FamilyBackstory(parents='', sections=[])
            
            return Backstory(
                title=bs_data.get('title', ''),
                family_backstory=family_backstory,
                sections=sections
            )
        
        return Character(
            character_base=CharacterBase(**data['character_base']),
            characteristics=PhysicalCharacteristics(**data['characteristics']),
            ability_scores=AbilityScores(**data['ability_scores']),
            combat_stats=CombatStats(**data['combat_stats']),
            background_info=BackgroundInfo(**data['background_info']),
            personality=PersonalityTraits(**data['personality']),
            backstory=reconstruct_backstory(data.get('backstory')),
            organizations=[Organization(**org) for org in data.get('organizations', [])],
            allies=[Ally(**ally) for ally in data.get('allies', [])],
            enemies=[Enemy(**enemy) for enemy in data.get('enemies', [])],
            proficiencies=[Proficiency(**prof) for prof in data.get('proficiencies', [])],
            damage_modifiers=[DamageModifier(**mod) for mod in data.get('damage_modifiers', [])],
            passive_scores=PassiveScores(**data['passive_scores']) if data.get('passive_scores') else None,
            senses=Senses(**data['senses']) if data.get('senses') else None,
            action_economy=ActionEconomy(**data['action_economy']) if data.get('action_economy') else None,
            features_and_traits=FeaturesAndTraits(**data['features_and_traits']) if data.get('features_and_traits') else None,
            inventory=Inventory(**data['inventory']) if data.get('inventory') else None,
            spell_list=SpellList(**data['spell_list']) if data.get('spell_list') else None,
            objectives_and_contracts=ObjectivesAndContracts(**data['objectives_and_contracts']) if data.get('objectives_and_contracts') else None,
            notes=data.get('notes', {}),
            created_date=datetime.fromisoformat(data['created_date']) if data.get('created_date') and isinstance(data['created_date'], str) else data.get('created_date'),
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') and isinstance(data['last_updated'], str) else datetime.now()
        )
    
    async def save_character_to_db(self, character: Character, user_id: str, campaign_id: str = "") -> str:
        """
        Save a Character object to the database.
        
        Args:
            character: The Character object to save
            user_id: The Firebase UID of the user who owns this character
            campaign_id: Optional campaign ID the character belongs to
            
        Returns:
            The character ID in the database
        """
        if not self._repository:
            raise ValueError("Database session not configured")
        
        # Update the last_updated timestamp
        character.last_updated = datetime.now()
        
        # Check if character exists
        existing = await self._repository.get_by_name(character.character_base.name)
        
        if existing:
            # Update existing character
            await self._repository.update(existing.id, character)
            await self.db_session.commit()
            return existing.id
        else:
            # Create new character
            db_character = await self._repository.create(character, user_id=user_id, campaign_id=campaign_id)
            await self.db_session.commit()
            return db_character.id
    
    async def load_character_async(self, name: str) -> Character:
        """
        Load a Character object from database (preferred) or pickle file (fallback).
        
        Args:
            name: The character name to load
            
        Returns:
            The loaded Character object
            
        Raises:
            FileNotFoundError: If character not found in database or files
        """
        # Try database first if available
        if self._repository:
            character = await self.load_character_from_db(name)
            if character:
                return character
        
        # Fallback to pickle file
        return self.load_character(name)
    
    def save_character(self, character: Character, filename: Optional[str] = None) -> str:
        """
        Save a Character object to a pickle file.
        
        Args:
            character: The Character object to save
            filename: Optional filename. If not provided, uses character name
            
        Returns:
            The filepath where the character was saved
        """
        if filename is None:
            # Use character name as filename, sanitized for filesystem
            safe_name = "".join(c for c in character.character_base.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_name}.pkl"
        
        if not filename.endswith('.pkl'):
            filename += '.pkl'
            
        filepath = self.save_directory / filename
        
        # Update the last_updated timestamp
        character.last_updated = datetime.now()
        
        with open(filepath, 'wb') as f:
            pickle.dump(character, f)
            
        return str(filepath)
    
    def load_character(self, filename: str) -> Character:
        """
        Load a Character object from a pickle file.
        
        Args:
            filename: The filename to load from
            
        Returns:
            The loaded Character object
            
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if not filename.endswith('.pkl'):
            filename += '.pkl'
            
        filepath = self.save_directory / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Character file not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            character = pickle.load(f)
            
        return character
    
    def list_saved_characters(self) -> list[str]:
        """
        List all saved character files.
        
        Returns:
            List of character filenames (without .pkl extension)
        """
        character_files = []
        for pkl_file in self.save_directory.glob("*.pkl"):
            character_files.append(pkl_file.stem)
        
        return sorted(character_files)
    
    def delete_character(self, filename: str) -> bool:
        """
        Delete a saved character file.
        
        Args:
            filename: The filename to delete
            
        Returns:
            True if deleted successfully, False if file didn't exist
        """
        if not filename.endswith('.pkl'):
            filename += '.pkl'
            
        filepath = self.save_directory / filename
        
        if filepath.exists():
            filepath.unlink()
            return True
        
        return False