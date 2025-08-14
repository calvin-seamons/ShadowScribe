from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
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

# Initialize managers
websocket_manager = WebSocketManager()
session_manager = SessionManager()

# Get the knowledge base path - use absolute path
base_dir = os.getenv("SHADOWSCRIBE_BASE_DIR", os.path.join(os.path.dirname(__file__), '..'))
knowledge_base_path = os.path.join(base_dir, "knowledge_base")

# Initialize ShadowScribe engine
engine = ShadowScribeEngine(
    knowledge_base_path=knowledge_base_path,
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    print("[*] ShadowScribe Web Server Starting...")
    # Set up debug callback for engine
    engine.set_debug_callback(websocket_manager.get_sync_callback())
    print("[+] Debug callback configured")
    
    yield
    
    # Shutdown
    print("[*] ShadowScribe Web Server Shutting Down...")
    await websocket_manager.shutdown()
    print("[+] WebSocket manager shut down")

# Initialize FastAPI app with lifespan
app = FastAPI(title="ShadowScribe API", version="1.0.0", lifespan=lifespan)

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

# Set dependencies for API routes
from api_routes import set_dependencies
set_dependencies(engine, session_manager)

# Initialize knowledge base file manager and set dependencies
from knowledge_base_service import KnowledgeBaseFileManager
from knowledge_base_routes import router as knowledge_base_router, set_file_manager

knowledge_base_file_manager = KnowledgeBaseFileManager(knowledge_base_path)
set_file_manager(knowledge_base_file_manager)

# Initialize PDF import services and set dependencies
from vision_character_parser import VisionCharacterParser
from pdf_image_converter import PDFImageConverter
from pdf_import_routes import router as pdf_import_router, set_pdf_import_dependencies

vision_parser = VisionCharacterParser()
pdf_converter = PDFImageConverter()
set_pdf_import_dependencies(vision_parser, pdf_converter, knowledge_base_file_manager)

# Include API routes
app.include_router(api_router, prefix="/api")
app.include_router(knowledge_base_router, prefix="/api")
app.include_router(pdf_import_router, prefix="/api/character/import-pdf")

# Serve static files in production
if os.path.exists("../frontend/build"):
    app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="static")

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
                    result = await process_task
                    
                    # Extract response and source usage from structured result
                    if isinstance(result, dict) and "response" in result:
                        response = result["response"]
                        source_usage = result.get("sourceUsage")
                        print(f"[DEBUG] Got structured result - response length: {len(response) if response else 0}")
                        # Safe Unicode printing for Windows console
                        try:
                            print(f"[DEBUG] Response preview: {response[:100] if response else 'None'}...")
                        except UnicodeEncodeError:
                            print(f"[DEBUG] Response preview: [Unicode content - {len(response)} chars]")
                        print(f"[DEBUG] Source usage available: {source_usage is not None}")
                    else:
                        # Fallback for string responses (backwards compatibility)
                        response = str(result)
                        source_usage = None
                        print(f"[DEBUG] Got string result - length: {len(response)}")
                    
                    # Small delay to ensure PASS_4_COMPLETE message is sent first
                    await asyncio.sleep(0.05)
                    
                    # Send the final response with source usage through the queue system
                    response_data = {
                        "response": response,
                        "timestamp": time.time()
                    }
                    
                    if source_usage:
                        response_data["sourceUsage"] = source_usage
                    
                    print(f"[DEBUG] Sending response message with {len(response_data)} fields")
                    
                    # Use the queue system to ensure proper ordering
                    await websocket_manager.broadcast_to_session(session_id, {
                        "type": "response",
                        "sessionId": session_id,
                        "data": response_data
                    })
                    print(f"[DEBUG] Response message queued successfully")
                    
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
    
    print(f"[*] Starting ShadowScribe backend on {host}:{port}")
    print(f"[*] Knowledge base path: {engine.knowledge_base.base_path}")
    
    # Check if OpenAI API key is loaded
    from src.config.settings import Config
    config = Config()
    if config.openai_api_key:
        print("[+] OpenAI API key loaded from environment")
    else:
        print("[!] No OpenAI API key found in .env file")
    
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        reload=True,
        log_level="info"
    )