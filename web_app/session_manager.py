from typing import Dict, List, Optional
from datetime import datetime
import json
import os
from dataclasses import dataclass, asdict


@dataclass
class ChatMessage:
    """Represents a single chat message."""
    query: str
    response: str
    timestamp: datetime
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "response": self.response,
            "timestamp": self.timestamp.isoformat()
        }


class SessionManager:
    """Manages user sessions and chat history."""
    
    def __init__(self, storage_path: str = "./sessions"):
        self.storage_path = storage_path
        self.sessions: Dict[str, List[ChatMessage]] = {}
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing sessions
        self._load_sessions()
    
    def _load_sessions(self):
        """Load existing sessions from disk."""
        for filename in os.listdir(self.storage_path):
            if filename.endswith(".json"):
                session_id = filename[:-5]  # Remove .json extension
                try:
                    with open(os.path.join(self.storage_path, filename), 'r') as f:
                        data = json.load(f)
                        self.sessions[session_id] = [
                            ChatMessage(
                                query=msg["query"],
                                response=msg["response"],
                                timestamp=datetime.fromisoformat(msg["timestamp"])
                            )
                            for msg in data
                        ]
                except Exception as e:
                    print(f"Error loading session {session_id}: {e}")
    
    def add_to_history(self, session_id: str, query: str, response: str):
        """Add a query-response pair to session history."""
        message = ChatMessage(
            query=query,
            response=response,
            timestamp=datetime.now()
        )
        
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append(message)
        
        # Save to disk
        self._save_session(session_id)
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get history for a specific session."""
        if session_id in self.sessions:
            return [msg.to_dict() for msg in self.sessions[session_id]]
        return []
    
    def _save_session(self, session_id: str):
        """Save session to disk."""
        if session_id in self.sessions:
            filepath = os.path.join(self.storage_path, f"{session_id}.json")
            with open(filepath, 'w') as f:
                json.dump(
                    [msg.to_dict() for msg in self.sessions[session_id]],
                    f,
                    indent=2
                )
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Get the most recent sessions."""
        all_sessions = []
        
        for session_id, messages in self.sessions.items():
            if messages:
                last_message = messages[-1]
                all_sessions.append({
                    "session_id": session_id,
                    "last_activity": last_message.timestamp.isoformat(),
                    "message_count": len(messages)
                })
        
        # Sort by last activity
        all_sessions.sort(key=lambda x: x["last_activity"], reverse=True)
        
        return all_sessions[:limit]
