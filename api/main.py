"""FastAPI main application entry point."""
import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from api.config import config
from api.routers import websocket, characters, feedback, campaigns


# Global warmup state
_warmup_complete = False
_warmup_started_at: float | None = None


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

    try:
        # 3. Load cross-encoder reranker (used for rulebook RAG reranking)
        from src.config import get_config
        rag_config = get_config()

        if rag_config.rulebook_rerank_enabled:
            print(f"[Warmup] Loading cross-encoder reranker: {rag_config.rulebook_reranker_model}...")
            start = time.time()

            from src.rag.rulebook.rulebook_query_router import get_reranker
            reranker = get_reranker()

            if reranker:
                # Run a warmup prediction to fully initialize
                _ = reranker.predict([["warmup query", "warmup document"]], show_progress_bar=False)
                elapsed = time.time() - start
                print(f"[Warmup] Cross-encoder reranker ready in {elapsed:.2f}s")
        else:
            print("[Warmup] Cross-encoder reranking disabled, skipping")
    except Exception as e:
        print(f"[Warmup] Failed to preload cross-encoder reranker: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    import asyncio

    global _warmup_complete, _warmup_started_at

    print("[Startup] Initializing Firestore client...")
    _warmup_started_at = time.time()

    # WARMUP_BLOCKING=true (default): Block startup until models loaded
    # WARMUP_BLOCKING=false: Load models in background (for local dev)
    blocking = os.getenv("WARMUP_BLOCKING", "true").lower() == "true"

    if blocking:
        print("[Startup] Running blocking warmup (WARMUP_BLOCKING=true)...")
        warmup_models()
        _warmup_complete = True
        elapsed = time.time() - _warmup_started_at
        print(f"[Startup] Blocking warmup complete in {elapsed:.2f}s, accepting requests")
    else:
        print("[Startup] Running background warmup (WARMUP_BLOCKING=false)...")
        asyncio.create_task(asyncio.to_thread(_warmup_models_and_mark_complete))

    yield

    print("[Shutdown] Application shutting down...")


def _warmup_models_and_mark_complete():
    """Wrapper to run warmup and set completion flag (for background mode)."""
    global _warmup_complete
    warmup_models()
    _warmup_complete = True
    print("[Warmup] Background warmup complete")


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
    """Health check endpoint (liveness probe)."""
    return {"status": "healthy"}


@app.get("/ready")
async def readiness_check():
    """Readiness endpoint - returns 503 until all models are loaded.

    Used by:
    - Cloud Run startup probe to know when instance is ready
    - Frontend to poll until backend is ready for queries
    """
    if not _warmup_complete:
        elapsed = time.time() - _warmup_started_at if _warmup_started_at else 0
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "status": "warming_up",
                "elapsed_seconds": round(elapsed, 1),
            },
        )
    return {"ready": True, "status": "ready"}


@app.post("/warmup")
async def trigger_warmup():
    """Explicit warmup trigger endpoint.

    Called by frontend on page load to trigger Cloud Run instance startup.
    Idempotent - safe to call multiple times.
    """
    if _warmup_complete:
        return {"status": "ready"}
    return {"status": "warming_up"}