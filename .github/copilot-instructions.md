# ShadowScribe - AI Coding Agent Instructions

## Project Overview
ShadowScribe is a D&D character management system with RAG (Retrieval-Augmented Generation) capabilities. It combines character data, rulebook embeddings, and session notes with AI chat.

**Tech Stack:**
- **Frontend**: Next.js 14, Tailwind CSS, Zustand, Firebase Auth
- **Backend**: FastAPI (Python 3.12), WebSocket streaming
- **Database**: Google Cloud Firestore (NoSQL)
- **Deployment**: Vercel (frontend), Google Cloud Run (API)
- **AI**: Claude (Anthropic) for chat, local DeBERTa classifier for routing

**Core Architecture:**
- **`src/central_engine.py`**: Main RAG query orchestrator with streaming
- **`src/rag/character/character_types.py`**: 20+ dataclasses for D&D characters
- **`src/rag/session_notes/`**: Session notes storage and query routing (Firestore-backed)
- **`api/`**: FastAPI backend with WebSocket and REST endpoints
- **`frontend/`**: Next.js frontend with Firebase Auth

## Environment Setup

### Google Cloud & Firebase
- **GCP Project**: `shadowscribe-prod`
- **Firebase Project**: `shadowscribe-prod-3405b`
- **Credentials**: `credentials/firebase-service-account.json`
- **Region**: `us-central1`
- **Cloud Run URL**: `https://shadowscribe-api-768657256070.us-central1.run.app`

### API Keys Configuration
Keys in `.env` (local) or Cloud Run secrets (production):
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_APPLICATION_CREDENTIALS=./credentials/firebase-service-account.json
```

### Firestore Database Collections
```text
users/{firebase_uid}
  - email, display_name, created_at

characters/{character_id}
  - user_id, campaign_id (required), name, data (nested JSON)

campaigns/{campaign_id}
  - name, description, created_at

campaigns/{campaign_id}/sessions/{session_id}  (unified SessionDocument)
  - session_number, session_name, title, summary
  - player_characters, npcs, locations, items (List[dict] - per-session)
  - key_events, combat_encounters, character_decisions
  - All 30+ structured RAG fields
```

## Critical Development Patterns

### Running Python Scripts (ESSENTIAL)
**ALWAYS use `uv run` to execute Python scripts**:
```bash
# Interactive RAG testing - THE BEST WAY TO TEST THE BACKEND
uv run python scripts/interactive_test.py
uv run python scripts/interactive_test.py --character "Duskryn Nightwarden"
uv run python scripts/interactive_test.py --character "Duskryn" --query "What happened last session?"

# Local API server
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Other scripts
uv run python -m scripts.run_inspector --list
uv run python scripts/deploy_cloudrun.py
```

### Frontend Development
```bash
cd frontend
npm run dev      # Development server (port 3000)
npm run build    # Production build
npm run lint     # ESLint
```

### Deployment
```bash
# Fast deploy - build locally and push (uses Docker cache, ~70% faster)
uv run python scripts/deploy_cloudrun.py --local

# Standard deploy - build with Cloud Build
uv run python scripts/deploy_cloudrun.py

# With version bump
uv run python scripts/deploy_cloudrun.py --local --patch

# Frontend auto-deploys from main branch via Vercel
```

**Deployment files:**
- `Dockerfile` - Optimized with single pip install layer
- `requirements-cloudrun.txt` - All dependencies consolidated
- `.gcloudignore` - Excludes frontend/tests/scripts from upload

### Import System
**Use absolute imports in all files:**
```python
# Correct imports
from src.rag.character.character_types import Character
from api.database.firestore_client import get_firestore_client
from api.database.firestore_models import SessionDocument

# NOT: from .character_manager import CharacterManager
```

### Firestore Async Pattern
```python
from api.database.firestore_client import get_firestore_client

db = get_firestore_client()  # Singleton AsyncClient
doc_ref = db.collection('characters').document(char_id)
doc = await doc_ref.get()
if doc.exists:
    data = doc.to_dict()
```

### Character Type Access
```python
# Required fields (always present)
character.character_base.name
character.ability_scores.strength
character.combat_stats.armor_class

# Optional fields (check for None)
if character.inventory:
    items = character.inventory.backpack
if character.spell_list:
    spells = character.spell_list.spells
```

## Key Files & Their Roles

| File | Purpose |
|------|---------|
| `src/central_engine.py` | Main RAG query orchestrator with streaming |
| `src/rag/character/character_types.py` | 20+ dataclasses for D&D characters |
| `src/rag/session_notes/session_notes_storage.py` | Async Firestore session loading with caching |
| `src/rag/session_notes/session_notes_query_router.py` | Session notes RAG query routing |
| `api/main.py` | FastAPI entry point |
| `api/auth.py` | Firebase token verification |
| `api/database/firestore_client.py` | Firestore async client singleton |
| `api/database/firestore_models.py` | Document dataclasses (SessionDocument is unified model) |
| `api/routers/websocket.py` | WebSocket `/ws/chat` endpoint |
| `frontend/lib/stores/wizardStore.ts` | 8-step character creation wizard |
| `scripts/interactive_test.py` | **THE BEST way to test backend** - Interactive RAG testing CLI |
| `scripts/deploy_cloudrun.py` | Automated Cloud Run deployment |

## Testing & Debugging

### Interactive Test - THE BEST WAY TO TEST THE BACKEND
**`scripts/interactive_test.py` is THE BEST way to test changes to the RAG system.** It provides a complete end-to-end testing environment with real LLM calls, Firestore data, and full conversation history.

```bash
# Interactive mode - best for exploratory testing
uv run python scripts/interactive_test.py

# With specific character
uv run python scripts/interactive_test.py --character "Duskryn Nightwarden"

# Single query test
uv run python scripts/interactive_test.py --character "Duskryn" --query "What happened last session?"
```

**Interactive commands:**
- `/sessions` - Show loaded sessions from Firestore
- `/reload` - Reload session notes from Firestore
- `/debug` - Toggle debug output
- `/quit` - Exit

**Why use interactive_test.py:**
- ✅ Full RAG pipeline: Tests routing, entity extraction, context assembly, and final response
- ✅ Real Firestore data: Loads characters and sessions from actual database
- ✅ Conversation history: Maintains context across multiple queries
- ✅ Real LLM calls: Uses actual API keys and models from config
- ✅ Streaming responses: Tests async streaming behavior
- ✅ Session notes verification: Test the new per-session entity architecture

### Other Testing Commands
```bash
# Run pytest tests
uv run pytest tests/ -v
uv run pytest tests/ -v -k "test_name"

# List characters from Firestore
uv run python -m scripts.run_inspector --list
```

## Session Notes Architecture

The `SessionDocument` model (`api/database/firestore_models.py`) is the **single source of truth** for session data - used for both Firestore persistence AND in-memory RAG queries (no serialization layer).

```text
Firestore: campaigns/{id}/sessions/{id}
    └── SessionDocument (30+ fields)
              │
              ▼ (SessionNotesStorage.get_campaign)
CampaignSessionNotesStorage
    └── sessions: Dict[str, SessionDocument]
              │
              ▼ (SessionNotesQueryRouter.query)
RAG Context: SessionNotesContext
```

**Per-Session Entities**: Each session stores its own entity lists (npcs, locations, items) rather than a campaign-wide index. This preserves chronological context for queries like "When did we first meet Ghul'Vor?"

## Query Logs System (Training Data Collection)

Every chat query is automatically saved to Firestore for training data collection.

### Quick Stats Check
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
- `response_time_ms` - Query-to-response time in ms
- `model_used` - LLM model (e.g., "claude-sonnet-4-20250514")
- `context_sources` - `{character_fields, rulebook_sections, session_notes}`
- `is_correct` - `null`=pending, `true`=confirmed, `false`=corrected

### Code Locations
- Collection: `api/routers/websocket.py`
- Repository: `api/database/repositories/feedback_repo.py` → `QueryLogRepository`
- Model: `api/database/firestore_models.py` → `QueryLogDocument`

## Code Philosophy

1. **Delete obsolete code** - no commented-out code or legacy cruft
2. **No fallback measures** - don't hide bugs with silent fallbacks
3. **Let things fail loudly** - crash immediately so we can fix root causes
4. **Config is the source of truth** - settings belong in `src/config.py`
5. **Always use `uv run`** for Python - it manages the virtual environment
6. **Write tests** - new parsing/utility code should have tests in `tests/`

## Common Pitfalls to Avoid

1. **Always use `uv run`** - never run Python directly without it
2. **Don't use relative imports** - always use `from src.module import Class`
3. **Check for None on optional Character fields** before accessing nested attributes
4. **Use `character.character_base.total_level`** not `.level` for character level access
5. **Firestore patterns** - avoid `where()` + `order_by()` combinations (requires composite indexes). Sort in Python instead.
6. **Session notes are per-session** - entities are stored in each SessionDocument, not aggregated campaign-wide
7. **Delete legacy code** - never leave commented-out code or obsolete implementations
8. **No fallback measures** - don't hide bugs with silent fallbacks or defensive `try/except` blocks
9. **Let things fail loudly** - if something is broken, crash immediately so we can fix the root cause
10. **Config is the source of truth** - settings belong in `src/config.py`, don't hardcode or override
