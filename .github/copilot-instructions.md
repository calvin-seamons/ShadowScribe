# ShadowScribe AI Coding Agent Instructions

## Architecture Overview

ShadowScribe is a D&D AI assistant built around a **4-pass async query processing pipeline**:
1. **Source Selection** (`src/engine/query_router.py`) - Determine which knowledge sources are needed
2. **Content Targeting** - Identify specific content within each source  
3. **Content Retrieval** (`src/engine/content_retriever.py`) - Fetch exact data needed
4. **Response Generation** (`src/engine/response_generator.py`) - Synthesize natural language response

All components are **async-first** and communicate through structured Pydantic models in `src/utils/response_models.py`.

## Critical Development Patterns

### Pydantic Response Models Are Required
Every LLM interaction uses validated Pydantic models. Never use raw string responses:
```python
# Always use structured responses
response = await self.llm_client.generate_structured_response(
    prompt, SourceSelectionResponse  # Pydantic model enforces structure
)
```

### Async Patterns & Debug Callbacks
All engine components support debug callbacks for real-time progress streaming:
```python
class NewComponent:
    def set_debug_callback(self, callback):
        self.debug_callback = callback
        
    async def process(self):
        await self._call_debug_callback("STAGE_NAME", "Message", {"data": "value"})
```

### Knowledge Source Handler Pattern
Each knowledge source follows this pattern (`src/knowledge/`):
- `load_data()` - Initialize from JSON files in `knowledge_base/`
- `is_loaded()` - Check if data is available  
- `get_*()` methods - Retrieve specific data with optional field filtering

## Key Development Workflows

### Running the Full System
```bash
# Web interface (FastAPI + React)
npm run dev

# Terminal interface  
python interactive_shadowscribe.py

# Comprehensive test suite
python -m src.tests.test_suite
```

### Adding New Knowledge Sources
1. Create handler in `src/knowledge/` following `*_handler.py` pattern
2. Add to `SourceTypeEnum` in `src/utils/response_models.py`
3. Create `*TargetResponse` Pydantic model
4. Update `KnowledgeBase.__init__()` to initialize handler
5. Add targeting logic in `QueryRouter.target_content()`

### Web App Architecture
- **Backend**: FastAPI in `web_app/main.py` with WebSocket support
- **Frontend**: React TypeScript in `frontend-src/`
- **Real-time**: WebSocket handlers stream 4-pass progress updates
- **API**: RESTful endpoints in `web_app/api_routes.py`

## Project-Specific Conventions

### File Organization
- `src/engine/` - Core 4-pass processing pipeline
- `src/knowledge/` - Data source handlers (D&D rules, character data, sessions)
- `src/utils/` - LLM client, Pydantic models, validation
- `knowledge_base/` - JSON data files (character.json, dnd5e_srd_full.json, etc.)
- `web_app/` - FastAPI backend with WebSocket support

### Error Handling Philosophy
- **Graceful degradation**: If one knowledge source fails, continue with others
- **Debug callbacks**: Always provide progress updates via callbacks
- **Structured validation**: Pydantic models prevent malformed LLM responses

### Testing Approach
- Comprehensive test suite in `src/tests/test_suite.py` tests all components
- Mock LLM responses for deterministic testing
- Test both individual components and full integration

## Integration Points

### LLM Client (`src/utils/llm_client.py`)
Central OpenAI client with:
- Structured response validation via Pydantic
- Debug callback support for progress streaming
- Retry logic with exponential backoff
- Temperature optimization (0.1 for structured, 0.7 for natural responses)

### WebSocket Communication
Progress updates flow: `Engine → Debug Callback → WebSocket → Frontend`
```python
# Engine calls debug callback during each pass
await self._call_debug_callback("PASS_1_START", "Starting source selection", {"query": user_query})
```

### Knowledge Base Data Format
Character data spread across multiple JSON files:
- `character.json` - Basic stats, class, race, level
- `spell_list.json` - Available spells by class
- `inventory_list.json` - Equipment and items
- Session notes in `session_notes/*.md` (markdown format)

When modifying data structures, ensure handlers support nested field access with dot notation and graceful missing field handling.
