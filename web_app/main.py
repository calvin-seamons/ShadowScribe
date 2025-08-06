from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from typing import List
import uuid
import os
import sys
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.engine.shadowscribe_engine import ShadowScribeEngine
from websocket_handler import WebSocketManager
from api_routes import router as api_router
from session_manager import SessionManager

# Initialize FastAPI app
app = FastAPI(title="ShadowScribe API", version="1.0.0")

# Configure CORS
frontend_port = os.getenv("FRONTEND_PORT", "3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{frontend_port}",  # Frontend dev server
        "http://localhost:3000",  # Default React port
        "http://localhost:3001",  # Alternate port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
websocket_manager = WebSocketManager()
session_manager = SessionManager()

# Initialize ShadowScribe engine
engine = ShadowScribeEngine(
    knowledge_base_path="../knowledge_base",
    model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
)

# Set dependencies for API routes
from api_routes import set_dependencies
set_dependencies(engine, session_manager)

# Include API routes
app.include_router(api_router, prefix="/api")

# Serve static files in production
if os.path.exists("../frontend/build"):
    app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    print("🌙 ShadowScribe Web Server Starting...")
    # Set up debug callback for engine
    engine.set_debug_callback(websocket_manager.get_sync_callback())
    print("✅ Debug callback configured")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    print("🌙 ShadowScribe Web Server Shutting Down...")
    await websocket_manager.shutdown()
    print("✅ WebSocket manager shut down")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    await websocket_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data["type"] == "query":
                # Process the query
                query = data["data"]["query"]
                
                # Send immediate acknowledgment
                await websocket_manager.send_personal_message({
                    "type": "acknowledgment",
                    "sessionId": session_id,
                    "data": {
                        "status": "processing",
                        "timestamp": time.time()
                    }
                }, websocket)
                
                # Set the active websocket for progress updates
                websocket_manager.set_active_session(session_id)
                
                # Process query with engine in a separate task to avoid blocking
                try:
                    # Create a task for processing the query
                    process_task = asyncio.create_task(engine.process_query(query))
                    
                    # Wait for the result
                    response = await process_task
                    
                    # Send the final response
                    await websocket_manager.send_personal_message({
                        "type": "response",
                        "sessionId": session_id,
                        "data": {
                            "response": response,
                            "timestamp": time.time()
                        }
                    }, websocket)
                    
                    # Save to session history (non-blocking)
                    asyncio.create_task(
                        asyncio.to_thread(
                            session_manager.add_to_history, 
                            session_id, 
                            query, 
                            response
                        )
                    )
                    
                except Exception as e:
                    # Send error message
                    error_msg = str(e)
                    print(f"Error processing query: {error_msg}")
                    
                    await websocket_manager.send_personal_message({
                        "type": "error",
                        "sessionId": session_id,
                        "data": {
                            "error": error_msg,
                            "timestamp": time.time()
                        }
                    }, websocket)
                    
            elif data["type"] == "ping":
                # Handle ping/pong for connection keepalive
                await websocket_manager.send_personal_message({
                    "type": "pong",
                    "sessionId": session_id,
                    "data": {"timestamp": time.time()}
                }, websocket)
                    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, session_id)
    except Exception as e:
        print(f"WebSocket error for session {session_id}: {e}")
        websocket_manager.disconnect(websocket, session_id)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "active_sessions": len(websocket_manager.active_connections)
    }

# Export app and managers for use in other modules
app.engine = engine
app.session_manager = session_manager
app.websocket_manager = websocket_manager

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment variables
    host = os.getenv("BACKEND_HOST", "localhost")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    
    print(f"🚀 Starting ShadowScribe backend on {host}:{port}")
    print(f"📁 Knowledge base path: {engine.knowledge_base.base_path}")
    
    # Check if OpenAI API key is loaded
    from src.config.settings import Config
    config = Config()
    if config.openai_api_key:
        print("✅ OpenAI API key loaded from environment")
    else:
        print("⚠️  No OpenAI API key found in .env file")
    
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        reload=True,
        log_level="info"
    )