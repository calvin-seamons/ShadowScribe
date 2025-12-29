# ShadowScribe - Warp AI Rules

## Project Overview
ShadowScribe is a D&D character management system with RAG capabilities. Next.js frontend + FastAPI backend + Firestore database.

## Essential Commands

### Python (ALWAYS use `uv run`)
```bash
uv run python scripts/interactive_test.py                    # Interactive RAG testing
uv run python scripts/interactive_test.py --character "Duskryn Nightwarden"
uv run python scripts/deploy_cloudrun.py --local             # Fast deploy
uv run pytest tests/ -v                                       # Run tests
```

### Frontend
```bash
cd frontend && npm run dev    # Development server (port 3000)
```

## Key URLs
- **Cloud Run API**: `https://shadowscribe-api-768657256070.us-central1.run.app`
- **GCP Project**: `shadowscribe-prod`
- **Firebase Project**: `shadowscribe-prod-3405b`

## Query Logs System (Training Data)

Every chat query is saved to Firestore for training data collection.

### Check Stats
```bash
curl https://shadowscribe-api-768657256070.us-central1.run.app/api/query-logs/stats
# Returns: {"queries_total": N, "queries_pending_review": N, "queries_confirmed_correct": N, "queries_corrected": N, "queries_exported": N}
```

### Query Logs API Endpoints
- `GET /api/query-logs/stats` - Counts of all logs
- `GET /api/query-logs/recent?limit=50` - Recent logs
- `GET /api/query-logs/pending?limit=50` - Logs awaiting review
- `POST /api/query-logs/{id}/feedback` - Submit correction
- `POST /api/query-logs/export` - Export for training

### What's Stored
Each query saves to `query_logs/{id}`:
- `user_query` - Normalized with placeholders (e.g., "What is {CHARACTER}'s AC?")
- `original_query` - Raw query before normalization
- `predicted_tools` - `[{tool, intention, confidence}]`
- `predicted_entities` - `[{name, text, type, confidence}]`
- `classifier_backend` - "local" or "haiku"
- `assistant_response` - Full LLM response
- `response_time_ms`, `model_used`, `context_sources`
- `is_correct` - `null`=pending, `true`=confirmed, `false`=corrected

### Code Locations
- Collection: `api/routers/websocket.py`
- Repository: `api/database/repositories/feedback_repo.py` → `QueryLogRepository`
- Model: `api/database/firestore_models.py` → `QueryLogDocument`
- Stats counter: `metadata/stats` document in Firestore

## Firestore Collections
```
users/{uid}
characters/{id} - includes campaign_id (required)
campaigns/{id}/sessions/{id} - SessionDocument with 30+ RAG fields
query_logs/{id} - Training data collection (was: routing_feedback)
metadata/stats - Counter document
```

## Code Philosophy
1. Always use `uv run` for Python
2. Use absolute imports: `from src.module import Class`
3. Delete obsolete code - no commented-out cruft
4. Let things fail loudly - no silent fallbacks
5. Config is source of truth: `src/config.py`
