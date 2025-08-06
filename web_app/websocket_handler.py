from typing import Dict, List
from fastapi import WebSocket
import json
import asyncio
from enum import Enum


def make_json_serializable(obj):
    """Convert objects to JSON-serializable format."""
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Convert dataclass or object to dict, then recurse
        return make_json_serializable(obj.__dict__)
    else:
        # For basic types (str, int, float, bool, None), return as-is
        return obj
import asyncio


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        # Store active connections by session ID
        self.active_connections: Dict[str, WebSocket] = {}
        self.active_session_id: str = None
        
    def _sync_callback_wrapper(self, stage: str, message: str, data: dict = None):
        """
        Synchronous wrapper for the async broadcast_progress method.
        This allows the callback to be used in synchronous contexts.
        """
        try:
            # Get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, schedule the coroutine
                asyncio.create_task(self.broadcast_progress(stage, message, data))
            else:
                # If we're not in an async context, run the coroutine
                loop.run_until_complete(self.broadcast_progress(stage, message, data))
        except Exception as e:
            print(f"Error in sync callback wrapper: {e}")
    
    def get_sync_callback(self):
        """Get a synchronous callback function that wraps the async broadcast_progress."""
        return self._sync_callback_wrapper
    
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
        serializable_message = make_json_serializable(message)
        await websocket.send_json(serializable_message)
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        """Send a message to a specific session."""
        if session_id in self.active_connections:
            # Make the message JSON-serializable before sending
            serializable_message = make_json_serializable(message)
            await self.active_connections[session_id].send_json(serializable_message)
    
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
