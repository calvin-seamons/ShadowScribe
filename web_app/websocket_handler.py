from typing import Dict, List, Optional
from fastapi import WebSocket
import json
import asyncio
from enum import Enum
import time


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


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        # Store active connections by session ID
        self.active_connections: Dict[str, WebSocket] = {}
        self.active_session_id: Optional[str] = None
        # Queue for messages to be sent
        self.message_queue: Dict[str, asyncio.Queue] = {}
        # Track active sender tasks
        self.sender_tasks: Dict[str, asyncio.Task] = {}
        # Track background progress tasks to prevent them from being destroyed
        self.progress_tasks: List[asyncio.Task] = []
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # Create a message queue for this session
        self.message_queue[session_id] = asyncio.Queue()
        
        # Start a background task to send messages from the queue
        self.sender_tasks[session_id] = asyncio.create_task(
            self._message_sender(session_id)
        )
        
        print(f"[+] WebSocket connected: {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            
        # Cancel the sender task
        if session_id in self.sender_tasks:
            self.sender_tasks[session_id].cancel()
            del self.sender_tasks[session_id]
            
        # Clear the message queue
        if session_id in self.message_queue:
            del self.message_queue[session_id]
            
        # Clean up completed progress tasks
        self._cleanup_progress_tasks()
            
        print(f"[-] WebSocket disconnected: {session_id}")
    
    def _cleanup_progress_tasks(self):
        """Clean up completed or cancelled progress tasks."""
        self.progress_tasks = [task for task in self.progress_tasks if not task.done()]
    
    async def shutdown(self):
        """Clean shutdown of all WebSocket connections and tasks."""
        # Cancel all sender tasks
        for task in self.sender_tasks.values():
            task.cancel()
        
        # Cancel all progress tasks
        for task in self.progress_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete or be cancelled
        all_tasks = list(self.sender_tasks.values()) + self.progress_tasks
        if all_tasks:
            await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # Clear all collections
        self.sender_tasks.clear()
        self.progress_tasks.clear()
        self.message_queue.clear()
        self.active_connections.clear()
    
    async def _message_sender(self, session_id: str):
        """Background task to send messages from the queue."""
        try:
            while session_id in self.active_connections:
                # Get message from queue
                message = await self.message_queue[session_id].get()
                
                # Send the message
                if session_id in self.active_connections:
                    try:
                        websocket = self.active_connections[session_id]
                        serializable_message = make_json_serializable(message)
                        await websocket.send_json(serializable_message)
                        
                        # Small delay to prevent overwhelming the client
                        await asyncio.sleep(0.01)
                    except Exception as e:
                        print(f"Error sending message to {session_id}: {e}")
                        break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Message sender error for {session_id}: {e}")
    
    def set_active_session(self, session_id: str):
        """Set the currently active session for progress updates."""
        self.active_session_id = session_id
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message directly to a specific WebSocket connection."""
        try:
            serializable_message = make_json_serializable(message)
            await websocket.send_json(serializable_message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        """Queue a message to be sent to a specific session."""
        if session_id in self.message_queue:
            await self.message_queue[session_id].put(message)
    
    def _sync_callback_wrapper(self, stage: str, message: str, data: dict = None):
        """
        Synchronous wrapper for the async broadcast_progress method.
        This is called from synchronous contexts and needs to schedule the async work.
        """
        try:
            # Create the coroutine
            coro = self.broadcast_progress(stage, message, data)
            
            # Try to get the current event loop and run the coroutine
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, create a task and track it
                task = loop.create_task(coro)
                self.progress_tasks.append(task)
                
                # Add a callback to clean up when the task completes
                def cleanup_callback(t):
                    try:
                        self._cleanup_progress_tasks()
                    except Exception as e:
                        print(f"Error in cleanup callback: {e}")
                
                task.add_done_callback(cleanup_callback)
                
            except RuntimeError:
                # No running loop - this shouldn't happen in FastAPI but handle gracefully
                # Try to run synchronously as last resort
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(coro)
                    loop.close()
                except Exception as sync_error:
                    print(f"[!] Failed to run sync callback for {stage}: {sync_error}")
                
        except Exception as e:
            print(f"[!] Error in sync callback wrapper for {stage}: {e}")
    
    def get_sync_callback(self):
        """Get a synchronous callback function that wraps the async broadcast_progress."""
        return self._sync_callback_wrapper
    
    async def broadcast_progress(self, stage: str, message: str, data: dict = None):
        """
        Broadcast progress updates to the active session.
        This is used as the debug callback for the ShadowScribe engine.
        """
        if not self.active_session_id or self.active_session_id not in self.active_connections:
            return
        
        # Map stage to pass number and determine if it's a start, complete, or error
        pass_info = {
            "PASS_1_START": (1, "starting", "Analyzing your question..."),
            "PASS_1_COMPLETE": (1, "complete", "Identified relevant sources"),
            "PASS_1_ERROR": (1, "error", "Source selection failed"),
            "PASS_1_SUCCESS": (1, "complete", "Identified relevant sources"),
            "PASS_2_START": (2, "starting", "Targeting specific content..."),
            "PASS_2_COMPLETE": (2, "complete", "Content targets identified"),
            "PASS_2_ERROR": (2, "error", "Content targeting failed"),
            "PASS_3_START": (3, "starting", "Retrieving information..."),
            "PASS_3_COMPLETE": (3, "complete", "Information retrieved"),
            "PASS_3_ERROR": (3, "error", "Content retrieval failed"),
            "PASS_4_START": (4, "starting", "Generating response..."),
            "PASS_4_COMPLETE": (4, "complete", "Response ready"),
            "PASS_4_ERROR": (4, "error", "Response generation failed"),
        }
        
        pass_number, status, friendly_message = pass_info.get(stage, (0, "unknown", message))
        
        # Include data details based on status
        details = {}
        if data:
            if status == "error":
                # For errors, include the error message and any additional context
                details["error"] = data.get("error", message)
                if "reasoning" in data:
                    details["reasoning"] = data["reasoning"]
                if "fallback_used" in data:
                    details["fallback_used"] = data["fallback_used"]
            elif status == "complete":
                # For successful completion, include success data
                if "selected_sources" in data:
                    details["sources"] = data["selected_sources"]
                if "targets" in data:
                    # Restructure targets to be more frontend-friendly
                    targets_data = data["targets"]
                    if isinstance(targets_data, list):
                        # Convert list of target objects to source-keyed dictionary
                        structured_targets = {}
                        for target_info in targets_data:
                            if isinstance(target_info, dict) and "source" in target_info:
                                source = target_info["source"]
                                raw_targets = target_info.get("targets", {})
                                
                                # Transform the targets based on source type
                                if source == "character_data":
                                    # Handle character data - flatten file_fields structure
                                    if isinstance(raw_targets, dict) and "file_fields" in raw_targets:
                                        structured_targets[source] = raw_targets["file_fields"]
                                    else:
                                        structured_targets[source] = raw_targets
                                elif source == "dnd_rulebook":
                                    # Handle rulebook data - keep section_ids and keywords separate
                                    structured_targets[source] = raw_targets
                                else:
                                    # Default handling for other sources
                                    structured_targets[source] = raw_targets
                        details["targets"] = structured_targets
                    else:
                        details["targets"] = targets_data
                if "content_summary" in data:
                    details["content"] = data["content_summary"]
                if "response_preview" in data:
                    details["preview"] = data["response_preview"][:100]
        
        progress_message = {
            "type": "progress",
            "sessionId": self.active_session_id,
            "data": {
                "progress": {
                    "pass": pass_number,
                    "status": status,
                    "stage": stage,
                    "message": friendly_message,
                    "details": message,
                    "metadata": details,
                    "timestamp": time.time()
                }
            }
        }
        
        # Queue the message for sending
        await self.broadcast_to_session(self.active_session_id, progress_message)