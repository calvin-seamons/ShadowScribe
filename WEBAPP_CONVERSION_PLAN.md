# ShadowScribe Web Application Conversion Plan

## Executive Summary

This plan outlines the conversion of ShadowScribe from a terminal-based D&D 5e assistant to a modern web application. ShadowScribe uses a sophisticated 4-pass query processing system with async operations, making it well-suited for a real-time web chat interface.

## Current Architecture Analysis

### Core Components
- **4-Pass Query Processing System**: Source Selection → Content Targeting → Content Retrieval → Response Generation
- **Async Architecture**: Built with `asyncio` for non-blocking operations
- **Structured Data Sources**: D&D rulebook, character data, session notes
- **LLM Integration**: OpenAI API with structured response validation
- **Debug Logging**: Comprehensive logging system for troubleshooting

### Existing Technology Stack
- **Backend**: Python 3.x with async/await patterns
- **AI/ML**: OpenAI API, Pydantic for validation
- **Data**: JSON files, markdown parsing
- **Current Interface**: Terminal-based with `interactive_shadowscribe.py`

## Recommended Web Technology Stack

### Option 1: FastAPI + React (Recommended)
**Best for**: Production-ready, scalable application with real-time features

**Backend**: FastAPI + WebSockets
- Native async support (perfect for existing codebase)
- Built-in WebSocket support for real-time chat
- Automatic API documentation with Swagger/OpenAPI
- Excellent for streaming responses

**Frontend**: React + TypeScript
- Modern, component-based UI
- Real-time updates with WebSocket support
- Rich ecosystem for chat components
- Mobile-responsive design capabilities

### Option 2: Streamlit (Fastest Development)
**Best for**: Rapid prototyping and quick deployment

**Pros**:
- Minimal code changes required
- Built-in chat components (`st.chat_message`, `st.chat_input`)
- Easy deployment to Streamlit Cloud
- Automatic UI generation

**Cons**:
- Limited customization options
- Less suitable for complex user interactions
- May not handle high concurrent users as well

### Option 3: Flask + Socket.IO
**Best for**: Simpler backend with real-time requirements

**Backend**: Flask + Flask-SocketIO
- Lightweight and familiar
- Good WebSocket support
- Easy to integrate with existing code

**Frontend**: Vanilla JS or React
- More control over implementation
- Can use Socket.IO client libraries

## Detailed Implementation Plan

### Phase 1: Core Backend API Development (FastAPI Approach)

#### 1.1 FastAPI Server Setup
```python
# New file: web_app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
from typing import List
import uuid

# Import existing ShadowScribe components
from src.engine.shadowscribe_engine import ShadowScribeEngine
```

#### 1.2 WebSocket Chat Handler
- Create WebSocket endpoint for real-time chat
- Handle connection management (multiple users)
- Stream responses as they're generated (4-pass updates)
- Implement session management

#### 1.3 API Endpoints
```python
# Core API routes
@app.get("/api/sources")  # Get available knowledge sources
@app.post("/api/validate")  # Validate system health
@app.get("/api/character")  # Get character summary
@app.get("/api/session-history")  # Get recent sessions
```

#### 1.4 Integration with Existing Engine
- Wrap `ShadowScribeEngine` in web-friendly interface
- Modify debug callback to send progress updates via WebSocket
- Add session persistence for web users
- Implement query history storage

### Phase 2: Frontend Development

#### 2.1 React Chat Interface Components
```tsx
// Core components
- ChatContainer: Main chat interface
- MessageList: Display conversation history
- MessageInput: User input with send button
- ProgressIndicator: Show 4-pass progress
- SourcesPanel: Display available knowledge sources
- CharacterSheet: Quick character reference
```

#### 2.2 Real-time Features
- WebSocket connection management
- Live progress updates during query processing
- Typing indicators
- Message status (sending, processing, complete)

#### 2.3 Enhanced UI Features
- **Knowledge Source Indicators**: Show which sources are being used
- **Response Streaming**: Display partial responses as they generate
- **Query Suggestions**: Show example queries
- **Character Quick Reference**: Sidebar with key stats
- **Session History**: Previous conversations
- **Dark/Light Theme**: User preference

### Phase 3: Enhanced Features

#### 3.1 User Authentication & Sessions
- Simple session management (no accounts initially)
- Persistent chat history per session
- Multiple character support per user

#### 3.2 Advanced Chat Features
- **Message Reactions**: Thumbs up/down for responses
- **Query Templates**: Pre-built query buttons
  - "What's my AC?"
  - "Show available spells"
  - "What happened last session?"
- **Bulk Operations**: Ask multiple questions at once

#### 3.3 Real-time Collaboration
- Share sessions with DM/other players
- Live session note taking
- Campaign management features

### Phase 4: Deployment & Production

#### 4.1 Containerization
```dockerfile
# Dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "web_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 4.2 Deployment Options
1. **Heroku**: Easiest for small scale
2. **Railway/Render**: Modern alternatives
3. **AWS/GCP**: For production scale
4. **Docker + VPS**: Full control

#### 4.3 Production Considerations
- Environment variable management
- API key security
- Rate limiting for OpenAI calls
- Caching layer for common queries
- CDN for static assets

## Implementation Timeline

### Week 1-2: Backend Foundation
- [ ] Set up FastAPI project structure
- [ ] Create WebSocket chat endpoint
- [ ] Integrate existing ShadowScribe engine
- [ ] Implement progress streaming
- [ ] Basic API endpoints

### Week 3-4: Frontend Development
- [ ] React app setup with TypeScript
- [ ] Chat interface components
- [ ] WebSocket integration
- [ ] Responsive design
- [ ] Basic styling

### Week 5-6: Enhanced Features
- [ ] Session management
- [ ] Query history
- [ ] Character quick reference
- [ ] Progress indicators
- [ ] Error handling

### Week 7-8: Polish & Deployment
- [ ] UI/UX improvements
- [ ] Testing and bug fixes
- [ ] Documentation
- [ ] Deployment setup
- [ ] Performance optimization

## File Structure for Web App

```
ShadowScribe/
├── src/                     # Existing backend code (keep as-is)
├── web_app/
│   ├── main.py             # FastAPI main application
│   ├── websocket_handler.py # WebSocket chat management
│   ├── api_routes.py       # REST API endpoints
│   ├── session_manager.py  # User session handling
│   └── models.py           # Pydantic models for web API
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   │   ├── ChatContainer.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── MessageInput.tsx
│   │   │   │   └── ProgressIndicator.tsx
│   │   │   ├── Sidebar/
│   │   │   │   ├── CharacterSheet.tsx
│   │   │   │   ├── SourcesPanel.tsx
│   │   │   │   └── SessionHistory.tsx
│   │   │   └── Common/
│   │   │       ├── Header.tsx
│   │   │       └── Layout.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   └── useSessionManager.ts
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   └── utils/
│   ├── package.json
│   └── tsconfig.json
├── requirements-web.txt     # Additional web dependencies
├── Dockerfile
└── docker-compose.yml
```

## Required Dependencies (Additional)

### Backend (requirements-web.txt)
```
# Existing dependencies from requirements.txt
# Plus web-specific additions:
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
websockets>=11.0
python-multipart>=0.0.6
redis>=4.5.0  # For session storage
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "@types/react": "^18.2.0",
    "socket.io-client": "^4.7.0",
    "axios": "^1.6.0",
    "tailwindcss": "^3.3.0",
    "lucide-react": "^0.292.0"
  }
}
```

## Key Implementation Details

### 1. WebSocket Message Protocol
```typescript
interface WebSocketMessage {
  type: 'query' | 'progress' | 'response' | 'error';
  sessionId: string;
  data: {
    query?: string;
    progress?: {
      pass: number;
      status: string;
      details: string;
    };
    response?: string;
    error?: string;
  };
}
```

### 2. Streaming Response Integration
Modify the existing debug callback to stream updates:
```python
async def web_debug_callback(stage: str, message: str, data: dict = None):
    await websocket.send_json({
        "type": "progress",
        "data": {
            "pass": get_pass_number(stage),
            "status": stage,
            "details": message
        }
    })
```

### 3. Session Management
- Store chat history in Redis or simple file system
- Generate unique session IDs
- Persist user preferences (character selection, theme)

## Security Considerations

1. **API Key Protection**: Never expose OpenAI keys to frontend
2. **Rate Limiting**: Prevent abuse of expensive LLM calls
3. **Input Validation**: Sanitize user queries
4. **CORS Configuration**: Properly configure for production
5. **Session Security**: Secure session token handling

## Performance Optimizations

1. **Response Caching**: Cache common D&D rule queries
2. **Connection Pooling**: Efficient WebSocket connection management
3. **Lazy Loading**: Load character data and sources on demand
4. **CDN Integration**: Serve static assets efficiently

## Testing Strategy

1. **Backend Tests**: 
   - API endpoint testing
   - WebSocket connection testing
   - Integration tests with existing engine

2. **Frontend Tests**:
   - Component unit tests
   - Chat flow integration tests
   - WebSocket communication tests

3. **End-to-End Tests**:
   - Full query processing workflow
   - Multi-user scenarios
   - Error handling and recovery

## Future Enhancements

1. **Voice Interface**: Add speech-to-text for hands-free querying
2. **Mobile App**: React Native version for mobile D&D sessions
3. **Campaign Management**: Full campaign tracking and management
4. **Multi-Character Support**: Switch between different characters
5. **DM Tools**: Special features for Dungeon Masters
6. **Dice Rolling Integration**: Built-in dice roller with query context
7. **Visual Character Sheet**: Interactive character sheet interface
8. **Battle Map Integration**: Connect with virtual tabletop tools

## Conclusion

The FastAPI + React approach is recommended for this conversion because:

1. **Async Compatibility**: FastAPI's native async support aligns perfectly with ShadowScribe's existing architecture
2. **Real-time Capabilities**: WebSocket support enables live progress updates during the 4-pass query processing
3. **Scalability**: Can handle multiple concurrent users efficiently
4. **Developer Experience**: Excellent tooling and documentation
5. **Flexibility**: Easy to extend with additional features

The existing ShadowScribe engine requires minimal changes - primarily wrapping the debug callback system to work with WebSockets and adding session management. The core query processing logic can remain unchanged, making this a relatively straightforward conversion with significant user experience improvements.
