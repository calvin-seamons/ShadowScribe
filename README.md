# 🎲 ShadowScribe

A D&D character management system with RAG (Retrieval-Augmented Generation) capabilities. Combines character data, rulebook embeddings, and session notes with AI chat.

## Tech Stack

- **Frontend**: Next.js 14, Tailwind CSS, Zustand, Firebase Auth
- **Backend**: FastAPI (Python 3.12), WebSocket streaming
- **Database**: Google Cloud Firestore (NoSQL)
- **Deployment**: Vercel (frontend), Google Cloud Run (API)
- **AI**: Claude (Anthropic) for chat, local DeBERTa classifier for routing

## Architecture

```text
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   Next.js Frontend  │     │   FastAPI Backend   │     │                     │
│   (Vercel)          │────▶│   (Cloud Run)       │────▶│   CentralEngine     │
│                     │     │                     │     │   - Query routing   │
│   - React/Zustand   │     │   - REST API        │     │   - Streaming LLM   │
│   - Firebase Auth   │     │   - WebSocket       │     │   - Entity extract  │
│   - Tailwind CSS    │     │   - Firestore       │     │                     │
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

## Quick Start

### Prerequisites

1. **Python 3.12** with [uv](https://docs.astral.sh/uv/) package manager
2. **Node.js 18+** for frontend
3. **Google Cloud credentials** for Firestore access
4. **API Keys** in `.env`:

   ```bash
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   GOOGLE_APPLICATION_CREDENTIALS=./credentials/firebase-service-account.json
   ```

### Local Development

**Backend:**

```bash
# Start API server
uv run uvicorn api.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### Access Points

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Production Frontend**: https://shadow-scribe-six.vercel.app
- **Production API**: https://shadowscribe-api-768657256070.us-central1.run.app

## Project Structure

```
ShadowScribe/
├── api/                        # FastAPI Backend
│   ├── main.py                # App entry point
│   ├── auth.py                # Firebase token verification
│   ├── database/              # Firestore client & models
│   │   ├── firestore_client.py   # Async client singleton
│   │   └── firestore_models.py   # Document dataclasses
│   ├── routers/               # REST & WebSocket endpoints
│   └── services/              # Business logic
├── frontend/                   # Next.js Frontend
│   ├── app/                   # Pages & layouts
│   ├── components/            # React components
│   └── lib/                   # Stores, services, types
│       ├── firebase.ts        # Firebase client init
│       ├── auth-context.tsx   # Auth context
│       └── stores/            # Zustand stores
├── src/                       # Core Python RAG System
│   ├── central_engine.py      # Main orchestration
│   ├── config.py              # LLM configuration
│   └── rag/                   # Query routers
│       ├── character/         # Character data system
│       ├── rulebook/          # D&D rules system
│       └── session_notes/     # Campaign history
├── scripts/                   # Utility scripts
│   ├── interactive_test.py   # Backend testing CLI
│   ├── deploy_cloudrun.py    # Cloud Run deployment
│   └── migrate_session_notes.py
├── tests/                     # Pytest test suite
├── Dockerfile                 # Cloud Run image
└── pyproject.toml             # Python dependencies (uv)
```

## Testing

### Interactive Backend Testing (Recommended)

The best way to test the backend RAG pipeline locally:

```bash
# Interactive mode - select character, ask questions
uv run python scripts/interactive_test.py

# Specify character directly
uv run python scripts/interactive_test.py --character "Duskryn Nightwarden"
```

This tests the full pipeline: Firestore loading → RAG routing → LLM streaming.

### Unit Tests

```bash
uv run pytest tests/ -v                           # Run all tests
uv run pytest tests/ -v -k "test_name"            # Run specific test
uv run pytest tests/src/character_creation/ -v    # Run module tests
```

## API Endpoints

### REST

- `GET /api/characters` - List user's characters (requires auth)
- `GET /api/characters/{id}` - Character details
- `POST /api/characters` - Create character
- `PUT /api/characters/{id}` - Update character
- `DELETE /api/characters/{id}` - Delete character
- `POST /api/characters/fetch` - Fetch from D&D Beyond URL
- `GET /api/feedback/stats` - Routing feedback statistics

### WebSocket

- `ws://localhost:8000/ws/chat` - Streaming chat with RAG
- `ws://localhost:8000/ws/character/create` - Character creation with progress

## Deployment

### Frontend (Vercel)

Auto-deploys from `main` branch. Environment variables configured in Vercel dashboard.

### Backend (Cloud Run)

```bash
# Using deployment script
uv run python scripts/deploy_cloudrun.py

# Or manually
gcloud run deploy shadowscribe-api \
  --region=us-central1 \
  --source=. \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2
```

## Environment Variables

### Backend (`.env`)

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_APPLICATION_CREDENTIALS=./credentials/firebase-service-account.json
CORS_ORIGINS=https://shadow-scribe-six.vercel.app,http://localhost:3000
```

### Frontend (`frontend/.env.local`)

```bash
NEXT_PUBLIC_FIREBASE_API_KEY=AIza...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=shadowscribe-prod.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=shadowscribe-prod
NEXT_PUBLIC_API_URL=https://shadowscribe-api-768657256070.us-central1.run.app
```

## Session Notes Architecture

Session notes use a unified `SessionDocument` model that serves both Firestore storage AND in-memory RAG queries.

### Firestore Structure

```text
campaigns/{campaign_id}/sessions/{session_id}
├── session_number, session_name, title, summary
├── raw_content (original transcript)
├── processed_markdown (LLM-structured text)
├── npcs, locations, items (entity lists)
├── key_events, combat_encounters, character_decisions
├── quotes, funny_moments, mysteries_revealed
└── created_at, updated_at
```

Entities are stored per-session to preserve chronological context, enabling queries like "When did we first meet Ghul'Vor?"

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

### Character Access

```python
# Required fields (always present)
character.character_base.name
character.ability_scores.strength
character.combat_stats.armor_class

# Optional fields (check for None)
if character.inventory:
    items = character.inventory.backpack
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

Frontend Firebase env vars are missing. Check `frontend/.env.local`.

### 401 Unauthorized on API calls

1. Check Firebase is configured (not demo mode)
2. Verify token in `Authorization: Bearer <token>` header
3. Check Cloud Run logs for verification errors

### CORS errors

Update `CORS_ORIGINS` in Cloud Run env vars, then redeploy.

### Frontend not using new API URL

`NEXT_PUBLIC_*` vars are embedded at build time. Trigger a new Vercel deployment.

---

**Built with:** Python 3.12, FastAPI, Next.js 14, Firestore, Claude Sonnet 4
