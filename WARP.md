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
- **Firebase Project**: `shadowscribe-prod` (same project)
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
├── campaign_id: string (FK to campaigns)
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
└── notes/{note_id}  (subcollection)
    ├── user_id: string
    ├── content: string
    ├── processed_content: object
    └── created_at: timestamp

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
Deploy using the script:
```bash
python scripts/deploy_cloudrun.py
```

Or manually:
```bash
gcloud run deploy shadowscribe-api \
  --region=us-central1 \
  --source=. \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --set-secrets="OPENAI_API_KEY=openai-api-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest" \
  --set-env-vars="CORS_ORIGINS=..."
```

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
| `api/main.py` | FastAPI entry point |
| `api/auth.py` | Firebase token verification |
| `api/database/firestore_client.py` | Firestore async client singleton |
| `api/database/firestore_models.py` | Document dataclasses (UserDocument, CharacterDocument, etc.) |
| `api/routers/websocket.py` | WebSocket `/ws/chat` endpoint |
| `api/routers/characters.py` | Character CRUD REST endpoints |
| `frontend/lib/firebase.ts` | Firebase client initialization |
| `frontend/lib/auth-context.tsx` | React auth context with sign in/out |
| `frontend/lib/services/api.ts` | API client with auth headers |
| `scripts/deploy_cloudrun.py` | Automated Cloud Run deployment |
| `Dockerfile` | Production Docker image for Cloud Run |

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
uv run python demo_central_engine.py   # Test RAG system
uv run uvicorn api.main:app --reload   # Local API server
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

## Code Philosophy

1. **Delete obsolete code** - no commented-out code or legacy cruft
2. **No fallback measures** - don't hide bugs with silent fallbacks
3. **Let things fail loudly** - crash immediately so we can fix root causes
4. **Config is the source of truth** - settings belong in `src/config.py`
5. **Always use `uv run`** for Python - it manages the virtual environment

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
