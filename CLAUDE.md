# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ShadowScribe is a D&D character management system with RAG (Retrieval-Augmented Generation) capabilities. It combines character data, rulebook embeddings, and session notes with AI chat through a Next.js frontend and FastAPI backend.

## Architecture

```
Frontend (Next.js 14)     →  WebSocket/HTTP  →  API (FastAPI)  →  CentralEngine (Python)
    ↓                                              ↓                     ↓
Zustand stores                              Firestore           RAG Routers (Character,
React components                            (NoSQL)                Rulebook, Session Notes)
Firebase Auth                                  ↓
                                         Collections:
                                         - users
                                         - characters
                                         - campaigns
                                         - routing_feedback
                                         - metadata/stats
```

**Core RAG Engine**: `src/central_engine.py` pipeline:
1. Gazetteer NER extracts entities from user query
2. Placeholders applied to normalize query (e.g., "Tell me about {CHARACTER}")
3. Router selects tools/intentions (configurable via `routing_mode`)
4. RAG routers execute with entity context
5. Sonnet generates streaming response

**Routing Mode** (`src/config.py` → `routing_mode`):
- `"haiku"` (default): Claude Haiku 4.5 API for routing, saves to DB for training data
- `"local"`: Local DeBERTa classifier, fast, no API calls
- `"comparison"`: Both run in parallel, Haiku primary, local shown in UI

## Build, Test & Run Commands

### Management Script (Recommended - Cross-Platform)
```bash
uv run python manage.py start      # Start all services
uv run python manage.py stop       # Stop all services
uv run python manage.py status     # Show service status
uv run python manage.py logs       # View all logs
uv run python manage.py logs -f api   # Follow API logs
uv run python manage.py health     # Check service health
uv run python manage.py demo -q "What is my AC?"  # Quick demo test
```

### Docker (Alternative)
```bash
docker-compose up -d              # Start all services
docker-compose logs -f api        # View API logs
docker-compose down               # Stop services
```

### Frontend (Next.js)
```bash
cd frontend
npm run dev                       # Development server (port 3000)
npm run build                     # Production build
npm run lint                      # ESLint
```

### Backend (Python) - Always use `uv run`
```bash
# Interactive RAG testing (tests full backend pipeline locally)
uv run python scripts/interactive_test.py
uv run python scripts/interactive_test.py --character "Duskryn Nightwarden"
uv run python scripts/interactive_test.py --character "Duskryn" --query "What happened last session?"

uv run python -m scripts.run_inspector --list         # List characters
uv run python -m scripts.run_inspector "Name" --format text  # Inspect character

# Testing
uv run pytest tests/ -v                               # Run all tests
uv run pytest tests/ -v -k "clean_html"               # Run specific tests
```

### Local API Development
```bash
# Start API server locally (requires environment variables)
DATABASE_URL="..." GOOGLE_APPLICATION_CREDENTIALS="./credentials/firebase-service-account.json" \
  uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Google Cloud & Firebase

### Project Info
- **GCP Project**: `shadowscribe-prod`
- **Firebase Project**: `shadowscribe-prod-3405b`
- **Credentials File**: `credentials/firebase-service-account.json` (for project `shadowscribe-prod-3405b`)
- **Region**: `us-central1`
- **Cloud Run URL**: `https://shadowscribe-api-768657256070.us-central1.run.app`

### Authentication
- **Frontend**: Firebase Auth (Google Sign-In) via `frontend/lib/firebase.ts`
- **Backend**: Firebase Admin SDK verifies ID tokens in `api/auth.py`
- **Credentials**: Service account JSON at `credentials/firebase-service-account.json`

### Firestore Database
The app uses Firestore (NoSQL) instead of SQL. Collections:

```
users/{firebase_uid}
  - email, display_name, created_at

characters/{character_id}
  - user_id, campaign_id (required), name, race, character_class, level, data (nested JSON)

campaigns/{campaign_id}
  - user_id, name, description, created_at

campaigns/{campaign_id}/sessions/{session_id}  (unified SessionDocument model)
  - session_number, session_name, title, summary
  - raw_content (original transcript), processed_markdown (LLM-structured)
  - player_characters, npcs, locations, items (List[dict] - per-session entities)
  - key_events, combat_encounters, character_decisions (List[dict])
  - character_statuses (dict), memories_visions, quest_updates (List[dict])
  - loot_obtained, puzzles_encountered (dict)
  - unresolved_questions, divine_interventions, cliffhanger, etc.
  - date, created_at, updated_at

routing_feedback/{feedback_id}
  - user_query, predicted_tools, is_correct, corrected_tools, etc.

metadata/stats
  - Counter document for efficient stats (avoids expensive COUNT queries)
```

**Important Firestore Patterns:**
- Avoid `order_by()` on queries with `where()` - requires composite indexes. Sort in Python instead.
- Use counter documents for aggregations (metadata/stats pattern)
- Nested JSON is fine in documents - Firestore handles it natively

### Deployment Commands
```bash
# Fast deploy - build locally and push (uses Docker cache, ~70% faster)
uv run python scripts/deploy_cloudrun.py --local

# Standard deploy - build with Cloud Build (default)
uv run python scripts/deploy_cloudrun.py

# With version bump
uv run python scripts/deploy_cloudrun.py --local --patch   # 1.0.0 -> 1.0.1
uv run python scripts/deploy_cloudrun.py --local --minor   # 1.0.0 -> 1.1.0

# Check Cloud Run service status
gcloud run services describe shadowscribe-api --region us-central1 --project shadowscribe-prod

# View Cloud Run logs
gcloud run services logs read shadowscribe-api --region us-central1 --limit 100
```

**Deployment files:**
- `Dockerfile` - Optimized with single pip install layer
- `requirements-cloudrun.txt` - All Cloud Run dependencies consolidated
- `.gcloudignore` - Excludes frontend, tests, scripts from upload

### GCloud CLI Essentials
```bash
gcloud auth list                           # Check authenticated accounts
gcloud config set project shadowscribe-prod   # Set active project (Cloud Run)
gcloud run services describe shadowscribe-api --region us-central1  # Check service
gcloud secrets list                        # List secrets
```

## Critical Development Patterns

### Python Execution
**Always use `uv run`** - it manages the virtual environment automatically:
```bash
# Correct
uv run python -m scripts.run_inspector --list
uv run python demo_central_engine.py

# Wrong - don't run directly
python scripts/run_inspector.py
```

### Import System
Always use absolute imports and run from project root:
```python
# Correct
from src.rag.character.character_manager import CharacterManager
from src.rag.character.character_types import Character

# Wrong
from .character_manager import CharacterManager
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

### Firestore Async Pattern
```python
from api.database.firestore_client import get_firestore_client

db = get_firestore_client()  # Singleton, returns AsyncClient
doc_ref = db.collection('characters').document(char_id)
doc = await doc_ref.get()
if doc.exists:
    data = doc.to_dict()
```

### API Keys & Environment Variables
Keys in `.env` (local) or Cloud Run secrets (production):
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_APPLICATION_CREDENTIALS=./credentials/firebase-service-account.json
```

## Key Files

| File | Purpose |
|------|---------|
| `src/central_engine.py` | Main query orchestrator with streaming |
| `src/rag/character/character_types.py` | 20+ dataclasses for D&D characters |
| `src/rag/session_notes/session_notes_storage.py` | Async Firestore session loading with caching |
| `src/rag/session_notes/session_notes_query_router.py` | Session notes RAG query routing |
| `src/config.py` | RAG configuration (models, temperatures) |
| `api/main.py` | FastAPI entry point |
| `api/auth.py` | Firebase token verification |
| `api/database/firestore_client.py` | Firestore async client singleton |
| `api/database/firestore_models.py` | Document dataclasses (SessionDocument is unified model) |
| `api/routers/websocket.py` | WebSocket `/ws/chat` endpoint |
| `frontend/lib/stores/wizardStore.ts` | 8-step character creation wizard |
| `scripts/interactive_test.py` | Interactive backend/RAG testing CLI |
| `scripts/migrate_session_notes.py` | One-time migration: notes/ → sessions/ |
| `tests/` | Pytest test suite |
| `Dockerfile` | Production Docker image for Cloud Run |

## API Endpoints

### REST
- `GET /api/characters` - List user's characters (requires auth)
- `GET /api/characters/{id}` - Character details
- `POST /api/characters` - Create character
- `PUT /api/characters/{id}` - Update character
- `DELETE /api/characters/{id}` - Delete character
- `GET /api/feedback/stats` - Routing feedback statistics
- `POST /api/feedback/{id}` - Submit feedback correction

### WebSocket
- `ws://localhost:8000/ws/chat` - Streaming chat
- `ws://localhost:8000/ws/character/create` - Character creation with progress

## Code Philosophy

1. **Delete obsolete code** - no commented-out code or legacy cruft
2. **No backward compatibility** unless required for data persistence
3. **Name code as fundamental** - no `_new`, `_v2` suffixes
4. **No fallback measures** - don't hide bugs with silent fallbacks or defensive error handling
5. **Let things fail loudly** - if something is broken, crash immediately so we can fix the root cause:
   - Never use bare `except:` or `except Exception:` to swallow errors
   - Don't provide default values for things that should exist
   - Only catch specific, expected exceptions you can handle meaningfully
   - Prefer crashes during development over silent bugs
6. **Clean up test files** - delete temporary scripts after use
7. **Proactively delete legacy code** - when you encounter outdated code, remove it:
   - Orphaned test files from old experiments
   - Unused modules and dead code paths
   - Files with `DEPRECATED`, `OLD`, `LEGACY`, or `TODO: remove` markers
   - Code that doesn't fit the current architecture
   - Don't ask permission, don't comment out - just delete cleanly
8. **Config is the source of truth** - never hardcode or override config values:
   - All settings belong in `src/config.py` class defaults
   - Functions/classes should read from `get_config()`, not accept override parameters
   - Environment variables can override config, but class defaults are authoritative
   - Never duplicate default values in multiple places
9. **Write tests** - new parsing/utility code should have tests in `tests/`

## Frontend Architecture

- **State**: Zustand stores (`chatStore`, `characterStore`, `wizardStore`)
- **Auth**: Firebase Auth with React context (`lib/auth-context.tsx`)
- **Streaming**: WebSocket connection for real-time responses
- **Styling**: Tailwind CSS with dark mode support
- **Path alias**: `@/*` maps to `frontend/*`
- **Character Wizard**: 8-step creation flow with campaign selection (mandatory)

## Testing

Tests are in `tests/` directory, mirroring source structure:
```
tests/
├── src/character_creation/parsing/test_parse_inventory.py
├── api/routers/
├── api/database/
└── api/services/
```

Run tests:
```bash
uv run pytest tests/ -v                    # All tests
uv run pytest tests/ -v -k "test_name"     # Specific test
```

## Current Project Status

**Database**: Firestore (migrated from Cloud SQL in Dec 2024 to save ~$10/month)

**Session Notes**: Migrated to unified `SessionDocument` model in Firestore (Dec 2024):
- Old: `campaigns/{id}/notes/{id}` with unstructured `processed_content` blob
- New: `campaigns/{id}/sessions/{id}` with full structured RAG fields
- Per-session entities (npcs, locations, items) preserve chronological context
- No more pickle files or local storage - everything in Firestore

**Conversation History**: Currently in-memory only (per-session). Not persisted to database.

**Known Limitations**:
- Firestore composite indexes: Avoid `where()` + `order_by()` combinations. Sort in Python instead.
- Cold starts: Local classifier model takes ~2-3 seconds to load on first query

## Session Notes Architecture

The `SessionDocument` model (`api/database/firestore_models.py`) is the **single source of truth** for session data - used for both Firestore persistence AND in-memory RAG queries (no serialization/hydration layer).

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

**Interactive Testing**:
```bash
uv run python scripts/interactive_test.py --character "Duskryn Nightwarden"
# Commands: /sessions, /reload, /debug, /quit
```
