from typing import Dict, List
from fastapi import WebSocket
import json


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        # Store active connections by session ID
        self.active_connections: Dict[str, WebSocket] = {}
        self.active_session_id: str = None
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"✅ WebSocket connected: {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"❌ WebSocket disconnected: {session_id}")
    
    def set_active_session(self, session_id: str):
        """Set the currently active session for progress updates."""
        self.active_session_id = session_id
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        await websocket.send_json(message)
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        """Send a message to a specific session."""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)
    
    async def broadcast_progress(self, stage: str, message: str, data: dict = None):
        """
        Broadcast progress updates to the active session.
        This is used as the debug callback for the ShadowScribe engine.
        """
        if not self.active_session_id or self.active_session_id not in self.active_connections:
            return
        
        # Map stage to pass number
        pass_mapping = {
            "PASS_1_START": 1,
            "PASS_1_COMPLETE": 1,
            "PASS_2_START": 2,
            "PASS_2_COMPLETE": 2,
            "PASS_3_START": 3,
            "PASS_3_COMPLETE": 3,
            "PASS_4_START": 4,
            "PASS_4_COMPLETE": 4,
        }
        
        pass_number = pass_mapping.get(stage, 0)
        
        progress_message = {
            "type": "progress",
            "sessionId": self.active_session_id,
            "data": {
                "progress": {
                    "pass": pass_number,
                    "status": stage,
                    "details": message,
                    "metadata": data or {}
                }
            }
        }
        
        await self.broadcast_to_session(self.active_session_id, progress_message)
