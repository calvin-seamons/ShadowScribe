"""
Main Knowledge Base - Centralized access to all data sources.
"""

from typing import Dict, Any, List, Optional
import os
import json

from .rulebook_handler import RulebookHandler
from .character_handler import CharacterHandler
from .session_handler import SessionHandler


class KnowledgeBase:
    """
    Central hub for accessing all knowledge sources:
    - D&D 5e SRD (rulebook)
    - Character data (stats, equipment, abilities)
    - Session notes (campaign history)
    """
    
    def __init__(self, knowledge_base_path: str = "./knowledge_base"):
        """Initialize knowledge base with all handlers."""
        self.base_path = knowledge_base_path
        
        # Initialize handlers for each data source
        self.rulebook = RulebookHandler(knowledge_base_path)
        self.character = CharacterHandler(knowledge_base_path)
        self.sessions = SessionHandler(knowledge_base_path)
        
        # Load core data
        self._initialize_sources()
    
    def _initialize_sources(self):
        """Initialize and validate all data sources."""
        try:
            self.rulebook.load_data()
            self.character.load_data()
            self.sessions.load_data()
        except Exception as e:
            print(f"Warning: Error initializing knowledge base: {str(e)}")
    
    def get_source_overview(self) -> Dict[str, Any]:
        """Get overview of all available knowledge sources."""
        return {
            "dnd_rulebook": {
                "description": "D&D 5e System Reference Document",
                "total_sections": self.rulebook.get_section_count(),
                "categories": self.rulebook.get_main_categories(),
                "status": "loaded" if self.rulebook.is_loaded() else "error"
            },
            "character_data": {
                "description": "Duskryn Nightwarden character information",
                "available_files": self.character.get_available_files(),
                "character_name": self.character.get_character_name(),
                "status": "loaded" if self.character.is_loaded() else "error"
            },
            "session_notes": {
                "description": "Campaign session history",
                "available_sessions": self.sessions.get_available_sessions(),
                "latest_session": self.sessions.get_latest_session_date(),
                "status": "loaded" if self.sessions.is_loaded() else "error"
            }
        }
    
    # Rulebook methods
    def get_sections_by_ids(self, section_ids: List[str]) -> List[Dict[str, Any]]:
        """Get specific rulebook sections by their IDs."""
        return self.rulebook.get_sections_by_ids(section_ids)
    
    def search_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Search rulebook sections by keywords."""
        return self.rulebook.search_by_keywords(keywords)
    
    def get_rulebook_query_helper(self) -> Dict[str, Any]:
        """Get the query helper structure for rulebook navigation."""
        return self.rulebook.get_query_helper()
    
    # Character methods
    def get_character_data(self, filename: str, fields: List[str] = None) -> Dict[str, Any]:
        """Get specific character data from a file."""
        return self.character.get_file_data(filename, fields)
    
    def get_basic_character_info(self) -> Dict[str, Any]:
        """Get essential character information."""
        return self.character.get_basic_info()
    
    def get_character_combat_info(self) -> Dict[str, Any]:
        """Get character's combat-related information."""
        return self.character.get_combat_info()
    
    def get_character_spells(self, spell_class: str = None) -> Dict[str, Any]:
        """Get character's available spells."""
        return self.character.get_spells(spell_class)
    
    # Session methods
    def get_session_by_date(self, date: str) -> Optional[Dict[str, Any]]:
        """Get session notes for a specific date."""
        return self.sessions.get_session_by_date(date)
    
    def get_latest_session(self) -> Optional[Dict[str, Any]]:
        """Get the most recent session notes."""
        return self.sessions.get_latest_session()
    
    def search_sessions_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Search session notes by keywords."""
        return self.sessions.search_by_keywords(keywords)
    
    def get_session_summaries(self) -> List[Dict[str, Any]]:
        """Get brief summaries of all sessions."""
        return self.sessions.get_session_summaries()
    
    # Utility methods
    def validate_data_integrity(self) -> Dict[str, Any]:
        """Validate the integrity of all data sources."""
        return {
            "rulebook": self.rulebook.validate(),
            "character": self.character.validate(),
            "sessions": self.sessions.validate()
        }
    
    def refresh_data(self):
        """Reload all data sources."""
        self._initialize_sources()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        return {
            "rulebook_sections": self.rulebook.get_section_count(),
            "character_files": len(self.character.get_available_files()),
            "session_count": len(self.sessions.get_available_sessions()),
            "total_data_size": self._calculate_data_size()
        }
    
    def _calculate_data_size(self) -> str:
        """Calculate approximate size of loaded data."""
        # This is a simple approximation
        try:
            total_size = 0
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if file.endswith(('.json', '.md')):
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
            
            # Convert to human readable format
            if total_size < 1024:
                return f"{total_size} B"
            elif total_size < 1024**2:
                return f"{total_size/1024:.1f} KB"
            else:
                return f"{total_size/1024**2:.1f} MB"
        except:
            return "Unknown"