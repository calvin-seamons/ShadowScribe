# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- **Full Development Mode**: `npm run dev` - Starts both FastAPI backend (port 8001) and React frontend (port 3000) concurrently
- **Frontend Only**: `npm run frontend` - Runs Vite dev server for React frontend
- **Backend Only**: `npm run backend` - Starts FastAPI backend via Node.js script that manages Python virtual environment
- **Direct Backend**: `npm run backend:direct` - Directly runs backend assuming virtual environment is already activated

### Building and Testing
- **Build Frontend**: `npm run build` - TypeScript compilation and Vite build
- **Type Check**: `npm run type-check` - TypeScript type checking without emission
- **Frontend Tests**: `npm test` - Run Vitest test suite
- **Frontend Tests with UI**: `npm run test:ui` - Run Vitest with visual UI
- **Frontend Tests (CI)**: `npm run test:run` - Run tests once without watch mode
- **Backend Tests**: `python final_system_test.py` - Comprehensive system tests for the query processing pipeline

### Environment Setup
- **Backend Dependencies**: `npm run install:backend` - Install Python requirements via pip
- Virtual environment should be at `.venv` in project root

## Architecture Overview

ShadowScribe is a D&D 5e AI assistant with a **4-pass query processing system**:

### Core Processing Pipeline (`src/engine/`)
1. **Source Selection** (`query_router.py`) - Determines which knowledge sources are needed
2. **Content Targeting** (`query_router.py`) - Identifies specific content within sources  
3. **Content Retrieval** (`content_retriever.py`) - Fetches exact data needed
4. **Response Generation** (`response_generator.py`) - Synthesizes retrieved content into natural responses

### Knowledge Sources (`src/knowledge/`)
- **Rulebook Handler** (`rulebook_handler.py`) - D&D 5e SRD data from `knowledge_base/dnd5e_srd_*.json`
- **Character Handler** (`character_handler.py`) - Character data from `knowledge_base/characters/*/` JSON files:
  - `character.json` - Stats, class, race, level
  - `spell_list.json` - Available spells
  - `inventory_list.json` - Equipment and items
  - `action_list.json` - Combat actions
  - `feats_and_traits.json` - Character features
  - `character_background.json` - Backstory and roleplay info
  - `objectives_and_contracts.json` - Quests and goals
- **Session Handler** (`session_handler.py`) - Campaign history from `knowledge_base/session_notes/*.md`

### Web Application Architecture
- **Backend** (`web_app/`) - FastAPI with WebSocket support for real-time chat
- **Frontend** (`frontend-src/`) - React with TypeScript, organized by feature:
  - `components/Chat/` - Chat interface components
  - `components/KnowledgeBase/` - Character data editors with validation system
  - `components/Sidebar/` - Character sheet, model selector, navigation
  - `stores/` - Zustand state management
  - `services/` - API clients and WebSocket handling

### Key Infrastructure (`src/utils/`)
- **LLM Client** (`direct_llm_client.py`) - Async OpenAI API interface with structured output validation
- **Response Models** (`response_models.py`) - Pydantic models ensuring consistent LLM responses
- **Validation** (`validation.py`) - Data integrity and format checking

## Development Patterns

### Frontend Development
- React functional components with TypeScript
- Zustand for state management
- Tailwind CSS for styling
- Vitest + Testing Library for tests
- Component structure follows feature-based organization

### Backend Development  
- Async-first Python design with FastAPI
- Pydantic models for all structured data
- WebSocket for real-time communication
- JSON-based knowledge storage with hierarchical file structure

### Testing Approach
- Frontend: Component tests with Vitest in `__tests__/` directories
- Backend: Integration tests focusing on the complete query processing pipeline
- System tests: `final_system_test.py` validates entire 4-pass system functionality

## Key Entry Points
- **Main Backend**: `web_app/main.py` - FastAPI application with WebSocket endpoints
- **Query Processing**: `src/engine/shadowscribe_engine.py` - Main engine orchestrating 4-pass system
- **Frontend App**: `frontend-src/main.tsx` - React application root
- **System Testing**: `final_system_test.py` - Comprehensive end-to-end tests

## Configuration
- **Vite Config**: Frontend proxies `/api` and `/ws` to `localhost:8001`
- **TypeScript**: Strict mode enabled, includes only `frontend-src/`
- **Python Path**: Virtual environment managed via `scripts/start-backend.js`