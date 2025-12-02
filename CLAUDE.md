# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ShadowScribe 2.0 is a D&D character management system with RAG (Retrieval-Augmented Generation) capabilities. It combines character data, rulebook embeddings, and session notes with AI chat through a Next.js frontend and FastAPI backend.

## Architecture

```
Frontend (Next.js 14)     →  WebSocket/HTTP  →  API (FastAPI)  →  CentralEngine (Python)
    ↓                                              ↓                     ↓
Zustand stores                              MySQL 8.0            RAG Routers (Character,
React components                            Characters              Rulebook, Session Notes)
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
uv run python demo_central_engine.py                  # Interactive RAG testing (PRIMARY)
uv run python demo_central_engine.py -q "What is my AC?"  # Single query test
uv run python -m scripts.run_inspector --list         # List characters
uv run python -m scripts.run_inspector "Name" --format text  # Inspect character
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

### API Keys
Use real API integrations - never mock. Keys in `.env`:
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Key Files

| File | Purpose |
|------|---------|
| `src/central_engine.py` | Main query orchestrator with streaming |
| `src/rag/character/character_types.py` | 20+ dataclasses for D&D characters |
| `src/config.py` | RAG configuration (models, temperatures) |
| `api/main.py` | FastAPI entry point |
| `api/routers/websocket.py` | WebSocket `/ws/chat` endpoint |
| `demo_central_engine.py` | Primary testing tool for RAG system |

## API Endpoints

- `GET /api/characters` - List characters
- `GET /api/characters/{id}` - Character details
- `ws://localhost:8000/ws/chat` - Streaming chat (WebSocket)

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

## Frontend Architecture

- **State**: Zustand stores (`chatStore`, `characterStore`, `metadataStore`)
- **Streaming**: WebSocket connection for real-time responses
- **Styling**: Tailwind CSS with dark mode support
- **Path alias**: `@/*` maps to `frontend/*`
