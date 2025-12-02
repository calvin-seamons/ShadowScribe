"""FastAPI main application entry point."""
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.database.connection import init_db, close_db
from api.routers import websocket, characters, feedback


def warmup_local_classifier():
    """Preload the local classifier model to avoid cold start delays.
    
    Uses the singleton pattern from central_engine to ensure the model
    is loaded once and shared across all engine instances.
    """
    try:
        print("[Warmup] Loading local classifier model...")
        start = time.time()
        
        # Import and trigger singleton initialization
        from src.central_engine import get_local_classifier
        
        classifier = get_local_classifier()
        
        if classifier:
            # Run a warmup inference to fully initialize CUDA/MPS kernels
            _ = classifier.classify_single("What is my AC?")
            elapsed = time.time() - start
            print(f"[Warmup] Local classifier ready in {elapsed:.2f}s")
        else:
            print("[Warmup] Local classifier not available")
    except Exception as e:
        print(f"[Warmup] Failed to preload local classifier: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    
    # Warmup: preload local classifier to avoid cold start on first query
    warmup_local_classifier()
    
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="ShadowScribe 2.0 API",
    description="D&D Character Management and RAG Query System",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(characters.router, prefix="/api", tags=["Characters"])
app.include_router(feedback.router, prefix="/api", tags=["Feedback"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ShadowScribe 2.0 API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
