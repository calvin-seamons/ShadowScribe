"""FastAPI main application entry point."""
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.config import config
from api.routers import websocket, characters, feedback, campaigns


def warmup_models():
    """
    Preloads ML models to reduce cold-start latency.

    Loads the local classifier and embedding model at startup to avoid
    slow first-request latency on Cloud Run.
    """
    try:
        # 1. Load local classifier
        print("[Warmup] Loading local classifier model...")
        start = time.time()

        from src.central_engine import get_local_classifier
        classifier = get_local_classifier()

        if classifier:
            _ = classifier.classify_single("What is my AC?")
            elapsed = time.time() - start
            print(f"[Warmup] Local classifier ready in {elapsed:.2f}s")
        else:
            print("[Warmup] Local classifier not available")
    except Exception as e:
        print(f"[Warmup] Failed to preload local classifier: {e}")

    try:
        # 2. Load embedding model (used for rulebook RAG)
        print("[Warmup] Loading embedding model...")
        start = time.time()

        from src.embeddings import get_embedding_provider
        provider = get_embedding_provider()

        # Run a warmup embedding to fully initialize
        _ = provider.embed("warmup query")
        elapsed = time.time() - start
        print(f"[Warmup] Embedding model ready in {elapsed:.2f}s")
    except Exception as e:
        print(f"[Warmup] Failed to preload embedding model: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    import asyncio

    # Startup - Firestore client is initialized on first use (singleton)
    print("[Startup] Initializing Firestore client...")

    # Warmup: preload ML models in background
    # Note: Models should be pre-downloaded in Docker image for fast cold starts
    asyncio.create_task(asyncio.to_thread(warmup_models))

    yield

    # Shutdown - Firestore client handles cleanup automatically
    print("[Shutdown] Application shutting down...")


app = FastAPI(
    title="ShadowScribe API",
    description="D&D Character Management and RAG Query System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(characters.router, prefix="/api", tags=["Characters"])
app.include_router(feedback.router, prefix="/api", tags=["Feedback"])
app.include_router(campaigns.router, prefix="/api", tags=["Campaigns"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ShadowScribe API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}