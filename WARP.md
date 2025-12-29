# WARP.md - ShadowScribe Project Guide

This file provides context for AI assistants working with the ShadowScribe codebase.

## Project Overview

ShadowScribe is a D&D character management system with RAG (Retrieval-Augmented Generation) capabilities. It combines character data, rulebook embeddings, and session notes with AI chat.

**Tech Stack:**
- **Frontend**: Next.js 14, Tailwind CSS, Zustand, Firebase Auth
- **Backend**: FastAPI (Python 3.12), WebSocket streaming
- **Database**: Google Cloud Firestore (NoSQL)
- **Deployment**: Vercel (frontend), Google Cloud Run (API)
- **AI**: Claude (Anthropic) for chat, local DeBERTa classifier for routing

## Architecture

```text
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   Next.js Frontend  │
│   (Vercel)          │────▶│    (Cloud Run)      │────▶│                     │
│                     │     │                     │     │   CentralEngine     │
│   - React/Zustand   │     │   - REST API        │     │   - Query routing   │
│   - Firebase Auth   │     │   - WebSocket       │     │   - Streaming LLM   │
│   - Tailwind CSS    │     │   - Firestore       │     │   - Entity extract  │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
         │                           │
         │                           ▼
         │                  ┌─────────────────────┐
         │                  │   Firestore (NoSQL) │
         │                  │                     │
         │                  │   Collections:      │
         │                  │   - users           │
         │                  │   - characters      │
         │                  │   - campaigns       │
         │                  │   - routing_feedback│
         │                  └─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   Firebase Auth     │
│   (Google Sign-In)  │
└─────────────────────┘
```

## Google Cloud Setup

### Project Configuration
- **GCP Project ID**: `shadowscribe-prod`
- **Firebase Project**: `shadowscribe-prod-3405b`
- **Region**: `us-central1`
- **Cloud Run Service**: `shadowscribe-api`
- **Cloud Run URL**: `https://shadowscribe-api-768657256070.us-central1.run.app`

### Secret Manager Secrets
These secrets are configured in Google Secret Manager and mounted to Cloud Run:
- `openai-api-key` - OpenAI API key (env var)
- `anthropic-api-key` - Anthropic API key (env var)
- `firebase-service-account` - Firebase service account JSON (mounted file)

### Firestore Collections

```text
users/{firebase_uid}
├── email: string
├── display_name: string
└── created_at: timestamp

characters/{character_id}
├── user_id: string (FK to users)
├── campaign_id: string (FK to campaigns, required)
├── name: string
├── race: string
├── character_class: string
├── level: number
├── data: object (full Character dataclass)
├── created_at: timestamp
└── updated_at: timestamp

campaigns/{campaign_id}
├── name: string
├── description: string
├── created_at: timestamp
└── sessions/{session_id}  (subcollection - unified SessionDocument)
    ├── user_id: string
    ├── session_number: int
    ├── session_name: string
    ├── raw_content: string (original transcript)
    ├── processed_markdown: string (LLM-structured text)
    ├── title, summary: string
    ├── player_characters, npcs, locations, items: List[dict]
    ├── key_events, combat_encounters, character_decisions: List[dict]
    ├── character_statuses: dict {name: status_dict}
    ├── memories_visions, quest_updates, spells_abilities_used: List[dict]
    ├── loot_obtained, puzzles_encountered: dict
    ├── deaths, revivals, party_conflicts, party_bonds: List
    ├── quotes, funny_moments, mysteries_revealed: List
    ├── unresolved_questions, divine_interventions, religious_elements: List
    ├── rules_clarifications, dice_rolls, dm_notes: List
    ├── cliffhanger, next_session_hook: Optional[str]
    ├── raw_sections: dict {section_name: text}
    ├── date: timestamp (in-game or real session date)
    └── created_at, updated_at: timestamp

routing_feedback/{feedback_id}
├── user_query: string
├── character_name: string
├── predicted_tools: array
├── is_correct: boolean
├── corrected_tools: array
└── created_at: timestamp

metadata/stats
├── feedback_total: number
├── feedback_pending: number
├── feedback_correct: number
└── feedback_corrected: number
```

**Firestore Patterns:**
- Avoid `where()` + `order_by()` combinations (requires composite indexes). Sort in Python instead.
- Use counter documents for aggregations (`metadata/stats` pattern)
- Nested JSON is fine in documents

## Authentication Flow

### Frontend (Firebase Auth)
1. User clicks "Sign In" → `signInWithPopup(auth, googleProvider)`
2. Firebase returns `FirebaseUser` with `uid`, `email`, `displayName`
3. Frontend gets ID token: `await firebaseUser.getIdToken()`
4. Token stored in `localStorage` and sent with API requests via `Authorization: Bearer <token>`
5. Token auto-refreshes every 50 minutes (expires after 1 hour)

### Backend (Firebase Admin SDK)
1. Request arrives with `Authorization: Bearer <token>` header
2. `api/auth.py` extracts token and calls `firebase_auth.verify_id_token(token)`
3. Returns decoded claims with `uid`, `email`, `name`
4. User is created/fetched from Firestore `users` collection
5. `get_current_user` dependency injects `UserDocument` into routes

### Demo Mode
If Firebase env vars are not configured, the frontend uses demo mode:
- Creates mock user with `uid: demo-user-{timestamp}`
- Creates mock JWT-like token (not verified by real Firebase)
- Backend must handle demo tokens separately or reject them

## Environment Variables

### Backend (`.env` or Cloud Run)
```bash
# Required API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Firebase (local development)
GOOGLE_APPLICATION_CREDENTIALS=./credentials/firebase-service-account.json

# CORS (Cloud Run)
CORS_ORIGINS=https://shadow-scribe-six.vercel.app,http://localhost:3000
```

### Frontend (`frontend/.env.local`)
```bash
# Firebase Auth Config
NEXT_PUBLIC_FIREBASE_API_KEY=AIza...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=shadowscribe-prod.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=shadowscribe-prod
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=shadowscribe-prod.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=...
NEXT_PUBLIC_FIREBASE_APP_ID=...

# Backend API URL
NEXT_PUBLIC_API_URL=https://shadowscribe-api-768657256070.us-central1.run.app
```

**Important:** `NEXT_PUBLIC_*` variables are embedded at build time. After changing them, you must rebuild/redeploy the frontend.

## Deployment

### Frontend (Vercel)
- Auto-deploys from `main` branch
- Vercel URLs:
  - Production: `shadow-scribe-six.vercel.app`
  - Preview: `shadow-scribe-git-main-sherman-portfolios.vercel.app`
- Environment variables configured in Vercel dashboard

### Backend (Cloud Run)
Deploy using manage.py:
```bash
# Fast deploy - build locally, push to Artifact Registry (uses Docker cache)
uv run python manage.py deploy --local

# Standard deploy - build with Cloud Build
uv run python manage.py deploy

# With version bump
uv run python manage.py deploy --local --patch   # 1.0.0 -> 1.0.1
uv run python manage.py deploy --local --minor   # 1.0.0 -> 1.1.0
uv run python manage.py deploy --version         # Show current version
```

**Deployment files:**
- `Dockerfile` - Optimized with single pip install layer for better caching
- `requirements-cloudrun.txt` - All Cloud Run dependencies in one file
- `.gcloudignore` - Excludes frontend, tests, scripts from Cloud Build upload

**Artifact Registry** (for `--local` builds):
- Repository: `us-central1-docker.pkg.dev/shadowscribe-prod/shadowscribe/api`
- The script automatically builds for `linux/amd64` platform (required for Cloud Run, works on Apple Silicon)

### Checking Deployment Status
```bash
# Cloud Run service
gcloud run services describe shadowscribe-api --region us-central1

# Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=shadowscribe-api" --limit=50

# Currently authenticated account
gcloud auth list
```

## Key Files

| File | Purpose |
|------|---------|
| `src/central_engine.py` | Main RAG query orchestrator with streaming |
| `src/config.py` | RAG configuration (models, temperatures) |
| `src/rag/character/character_types.py` | 20+ dataclasses for D&D characters |
| `src/rag/session_notes/session_notes_storage.py` | Async Firestore session loading with caching |
| `src/rag/session_notes/session_notes_query_router.py` | Session notes RAG query routing |
| `api/main.py` | FastAPI entry point |
| `api/auth.py` | Firebase token verification |
| `api/database/firestore_client.py` | Firestore async client singleton |
| `api/database/firestore_models.py` | Document dataclasses (SessionDocument is unified Firestore+RAG model) |
| `api/routers/websocket.py` | WebSocket `/ws/chat` endpoint |
| `api/routers/characters.py` | Character CRUD REST endpoints |
| `frontend/lib/firebase.ts` | Firebase client initialization |
| `frontend/lib/auth-context.tsx` | React auth context with sign in/out |
| `frontend/lib/services/api.ts` | API client with auth headers |
| `frontend/lib/stores/wizardStore.ts` | 8-step character creation wizard state |
| `manage.py` | Unified management script (start, stop, deploy, etc.) |
| `scripts/interactive_test.py` | Interactive backend/RAG testing CLI |
| `scripts/migrate_session_notes.py` | One-time migration: notes/ → sessions/ |
| `Dockerfile` | Production Docker image for Cloud Run |
| `tests/` | Pytest test suite |

## API Endpoints

### REST
- `GET /api/characters` - List user's characters (requires auth)
- `GET /api/characters/{id}` - Character details
- `POST /api/characters` - Create character (requires auth)
- `PUT /api/characters/{id}` - Update character
- `DELETE /api/characters/{id}` - Delete character (requires auth)
- `POST /api/characters/fetch` - Fetch from D&D Beyond URL
- `GET /api/feedback/stats` - Routing feedback statistics
- `POST /api/feedback/{id}` - Submit feedback correction

### WebSocket
- `ws://localhost:8000/ws/chat` - Streaming chat with RAG
- `ws://localhost:8000/ws/character/create` - Character creation with progress

## Development Commands

### Backend (Python)
```bash
# Always use uv run for Python
uv run python manage.py start          # Start all services
uv run python manage.py stop           # Stop services
uv run uvicorn api.main:app --reload   # Local API server

# Interactive RAG testing (tests full backend pipeline locally)
uv run python scripts/interactive_test.py
uv run python scripts/interactive_test.py --character "Duskryn Nightwarden"

# Run tests
uv run pytest tests/ -v                # Run all tests
uv run pytest tests/ -v -k "clean_html"  # Run specific tests
```

### Frontend (Next.js)
```bash
cd frontend
npm run dev      # Development server (port 3000)
npm run build    # Production build
npm run lint     # ESLint
```

### Google Cloud CLI
```bash
gcloud auth list                              # Check authenticated accounts
gcloud config set project shadowscribe-prod   # Set active project
gcloud run services list                      # List Cloud Run services
gcloud secrets list                           # List secrets
```

## Code Patterns

### Firestore Async Pattern
```python
from api.database.firestore_client import get_firestore_client

db = get_firestore_client()  # Singleton AsyncClient
doc_ref = db.collection('characters').document(char_id)
doc = await doc_ref.get()
if doc.exists:
    data = doc.to_dict()
```

### Authentication in Routes
```python
from api.auth import get_current_user
from api.database.firestore_models import UserDocument

@router.get("/characters")
async def list_characters(
    current_user: UserDocument = Depends(get_current_user)
):
    # current_user.id is the Firebase UID
    ...
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
```

## Character Creation Wizard

The frontend uses an 8-step wizard for character creation:
1. **Import** - Enter D&D Beyond URL
2. **Parse** - Fetch and parse character data
3. **Stats** - Review/edit ability scores and combat stats
4. **Gear** - Edit inventory and equipment
5. **Abilities** - Review features and traits
6. **Story** - Edit background and personality
7. **Campaign** - Select campaign (required)
8. **Review** - Final review and save

Campaign association is mandatory - characters cannot be saved without selecting a campaign.

## Testing

Tests are located in `tests/` and use pytest:
```bash
uv run pytest tests/ -v                           # Run all tests
uv run pytest tests/ -v -k "test_name"            # Run specific test
uv run pytest tests/src/character_creation/ -v    # Run module tests
```

Test structure mirrors source:
```
tests/
├── src/
│   └── character_creation/
│       └── parsing/
│           └── test_parse_inventory.py
├── api/
│   ├── routers/
│   ├── database/
│   └── services/
└── __init__.py
```

## Code Philosophy

1. **Delete obsolete code** - no commented-out code or legacy cruft
2. **No fallback measures** - don't hide bugs with silent fallbacks
3. **Let things fail loudly** - crash immediately so we can fix root causes
4. **Config is the source of truth** - settings belong in `src/config.py`
5. **Always use `uv run`** for Python - it manages the virtual environment
6. **Write tests** - new parsing/utility code should have tests in `tests/`

## Troubleshooting

### "Firebase not configured, using demo mode"
Frontend Firebase env vars are missing. Check `frontend/.env.local` has all `NEXT_PUBLIC_FIREBASE_*` variables set.

### 401 Unauthorized on API calls
1. Check if Firebase is configured (not demo mode)
2. Verify token is being sent in `Authorization: Bearer <token>` header
3. Check Cloud Run logs for token verification errors

### Cloud Run deployment fails
1. Check build logs: `gcloud builds log <build-id> --region=us-central1`
2. Common issues:
   - Missing secrets in Secret Manager
   - Dockerfile COPY errors (files in .gitignore excluded)
   - Import errors in Python code

### CORS errors
Update `CORS_ORIGINS` in Cloud Run env vars to include the frontend domain, then redeploy.

### Frontend not using new API URL
`NEXT_PUBLIC_*` vars are embedded at build time. Trigger a new Vercel deployment after changing them.

## Session Notes Architecture

Session notes use a unified `SessionDocument` model that serves both Firestore storage AND in-memory RAG queries (no serialization layer).

### Data Flow
```text
Firestore: campaigns/{id}/sessions/{id}
    └── SessionDocument (all 30+ fields)
              │
              ▼ (async load)
RAG Layer: CampaignSessionNotesStorage
    └── sessions: Dict[str, SessionDocument]
              │
              ▼ (query)
SessionNotesQueryRouter
    └── Returns SessionNotesContext with relevant_sections
```

### Per-Session Entities (Chronological Context)
Entities are stored per-session (not campaign-wide) to preserve chronological context:
```python
# Each SessionDocument has its own entity lists:
session.npcs        # [{name, entity_type, aliases, description}]
session.locations   # [{name, entity_type, ...}]
session.items       # [{name, entity_type, ...}]
```

This allows the RAG system to answer "When did we first meet Ghul'Vor?" by finding the earliest session where that NPC appears.

### Key Types
- `SessionDocument` (`api/database/firestore_models.py`) - Unified model for storage + RAG
- `SessionNotesContext` (`src/rag/session_notes/session_types.py`) - Query result context
- `QueryEngineResult` - Aggregated results from query router
