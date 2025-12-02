"""
Campaign Session Notes Storage

In-memory data container for a specific campaign's session notes.
This class holds all the processed data (embeddings, entities, sessions, etc.)
for a single campaign. The main SessionNotesStorage class handles loading/saving
and manages multiple CampaignSessionNotesStorage instances.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .session_types import (
    SessionMetadata, ProcessedSession, SessionEntity, 
    QueryEngineResult, SessionNotesQueryPerformanceMetrics
)


@dataclass
class CampaignSessionNotesStorage:
    """
    In-memory storage for a single campaign's session notes data.
    Contains all the processed data needed for querying session notes.
    """
    campaign_name: str
    sessions: Dict[str, ProcessedSession] = field(default_factory=dict)
    entities: Dict[str, SessionEntity] = field(default_factory=dict) 
    embeddings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, SessionMetadata] = field(default_factory=dict)
    
    # Campaign-specific settings
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    def get_all_sessions(self) -> List[ProcessedSession]:
        """Get all sessions for this campaign."""
        return list(self.sessions.values())
    
    def get_session(self, session_id: str) -> Optional[ProcessedSession]:
        """Get a specific session by ID."""
        return self.sessions.get(session_id)
    
    def get_entities_by_type(self, entity_type: str) -> List[SessionEntity]:
        """Get all entities of a specific type."""
        return [entity for entity in self.entities.values() 
                if entity.entity_type == entity_type]
    
    def get_entities_by_session(self, session_id: str) -> List[SessionEntity]:
        """Get all entities that appear in a specific session."""
        return [entity for entity in self.entities.values() 
                if session_id in entity.session_mentions]
    
    def search_entities(self, query: str) -> List[SessionEntity]:
        """Search entities by name or description."""
        query_lower = query.lower()
        return [entity for entity in self.entities.values()
                if query_lower in entity.name.lower() or 
                   query_lower in entity.description.lower()]
    
    def get_session_count(self) -> int:
        """Get total number of sessions."""
        return len(self.sessions)
    
    def get_entity_count(self) -> int:
        """Get total number of entities.""" 
        return len(self.entities)
    
    def get_latest_session(self) -> Optional[ProcessedSession]:
        """Get the most recent session by date."""
        if not self.sessions:
            return None
        return max(self.sessions.values(), key=lambda s: s.metadata.session_date)
    
    def get_session_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get the date range of all sessions."""
        if not self.sessions:
            return None, None
        
        dates = [session.metadata.session_date for session in self.sessions.values()]
        return min(dates), max(dates)
    
    def search_sessions_by_keyword(self, keyword: str) -> List[ProcessedSession]:
        """Search sessions that contain a specific keyword."""
        keyword_lower = keyword.lower()
        matching_sessions = []
        
        for session in self.sessions.values():
            # Search in session content fields
            if (keyword_lower in session.content.lower() if hasattr(session, 'content') else False or
                keyword_lower in session.summary.lower() if hasattr(session, 'summary') else False):
                matching_sessions.append(session)
                continue
                
            # Search in entities mentioned in this session
            for entity in self.get_entities_by_session(session.metadata.session_id):
                if (keyword_lower in entity.name.lower() or 
                    keyword_lower in entity.description.lower()):
                    matching_sessions.append(session)
                    break
        
        return matching_sessions
    
    def get_sessions_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ProcessedSession]:
        """Get all sessions within a date range."""
        return [session for session in self.sessions.values()
                if start_date <= session.metadata.session_date <= end_date]
    
    def get_sessions_with_entity(self, entity_name: str) -> List[ProcessedSession]:
        """Get all sessions that mention a specific entity."""
        entity_name_lower = entity_name.lower()
        matching_sessions = []
        
        for session in self.sessions.values():
            session_entities = self.get_entities_by_session(session.metadata.session_id)
            if any(entity_name_lower in entity.name.lower() for entity in session_entities):
                matching_sessions.append(session)
        
        return matching_sessions
    
    def get_entity(self, entity_name: str) -> Optional[SessionEntity]:
        """Get a specific entity by name (case-insensitive)."""
        # Try exact match first
        if entity_name in self.entities:
            return self.entities[entity_name]
        # Try lowercase match
        return self.entities.get(entity_name.lower())
    
    def get_campaign_summary(self) -> Dict[str, Any]:
        """Get a summary of the campaign data."""
        start_date, end_date = self.get_session_date_range()
        
        entity_types = {}
        for entity in self.entities.values():
            entity_type = entity.entity_type
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        return {
            'campaign_name': self.campaign_name,
            'session_count': self.get_session_count(),
            'entity_count': self.get_entity_count(),
            'entity_types': entity_types,
            'date_range': {
                'start': start_date,
                'end': end_date
            },
            'latest_session': self.get_latest_session().metadata.session_id if self.sessions else None,
            'embedding_model': self.embedding_model,
            'chunk_settings': {
                'size': self.chunk_size,
                'overlap': self.chunk_overlap
            }
        }
