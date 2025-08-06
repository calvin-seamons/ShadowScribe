# ShadowScribe - Intelligent D&D Assistant

ShadowScribe is an advanced AI-powered assistant designed specifically for Dungeons & Dragons 5th Edition gameplay. It combines deep rule knowledge, character data management, and campaign history to provide intelligent, context-aware responses to player and DM queries.

## Overview

ShadowScribe uses a sophisticated **4-pass query processing system** that intelligently routes questions through multiple knowledge sources to provide accurate, comprehensive answers. Whether you need rules clarification, character information, or campaign history, ShadowScribe delivers contextually relevant responses by understanding what information is needed and where to find it.

### Key Features

- 🎯 **Intelligent Query Routing**: 4-pass system for optimal information retrieval
- 📚 **Comprehensive D&D 5e Knowledge**: Complete SRD integration with smart search
- 🧙‍♂️ **Character Data Management**: Stats, inventory, spells, abilities, and background
- 📝 **Campaign History Tracking**: Session notes and story continuity
- ⚡ **Real-time Web Interface**: Modern chat-based interface with live progress updates
- 🔄 **Async Architecture**: Non-blocking operations for responsive performance
- 🛡️ **Structured Validation**: Pydantic models ensure reliable LLM responses

## Architecture Overview

ShadowScribe is built around a modular, async-first architecture that separates concerns into distinct, testable components:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ShadowScribe Engine                         │
├─────────────────────────────────────────────────────────────────┤
│  Query Processing Pipeline (4-Pass System)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │
│  │   Pass 1    │ │   Pass 2    │ │   Pass 3    │ │  Pass 4   │  │
│  │   Source    │ │   Content   │ │   Content   │ │ Response  │  │
│  │ Selection   │ │ Targeting   │ │ Retrieval   │ │Generation │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Knowledge Base Layer                                           │
│  ┌───────────────┐ ┌─────────────────┐ ┌─────────────────────┐  │
│  │ Rulebook      │ │ Character       │ │ Session             │  │
│  │ Handler       │ │ Handler         │ │ Handler             │  │
│  │ (D&D SRD)     │ │ (Stats/Items)   │ │ (Campaign History)  │  │
│  └───────────────┘ └─────────────────┘ └─────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Core Infrastructure                                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │
│  │ LLM Client  │ │ Response    │ │ Validation  │ │ File I/O  │  │
│  │ (OpenAI)    │ │ Models      │ │ Helpers     │ │ Utilities │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components Deep Dive

### 1. The 4-Pass Query Processing System

ShadowScribe's intelligence comes from its multi-pass approach to understanding and answering queries:

#### Pass 1: Source Selection (`query_router.py`)
**Purpose**: Determine which knowledge sources are needed to answer the query.

```python
# Example: "What's the damage for my Hex spell?"
# Result: [CHARACTER_DATA, DND_RULEBOOK]
# Reasoning: Need character's spell list AND spell rules
```

**Process**:
- Analyzes user query using LLM with structured output
- Returns `SourceSelectionResponse` with needed sources and reasoning
- Uses keyword hints for optimization but relies on LLM judgment
- Validates against available source types: `dnd_rulebook`, `character_data`, `session_notes`

#### Pass 2: Content Targeting (`query_router.py`)
**Purpose**: Identify specific content within each selected source.

```python
# For CHARACTER_DATA: {"file_fields": {"spell_list.json": ["hex", "warlock_spells"]}}
# For DND_RULEBOOK: {"keywords": ["hex", "spell", "damage"], "section_ids": ["spells"]}
```

**Process**:
- Takes sources from Pass 1 and creates specific retrieval targets
- Different targeting strategies per source type:
  - **Rulebook**: Section IDs and/or keyword search
  - **Character**: Specific files and field paths
  - **Sessions**: Date ranges and topic keywords
- Returns structured response models (`RulebookTargetResponse`, `CharacterTargetResponse`, etc.)

#### Pass 3: Content Retrieval (`content_retriever.py`)
**Purpose**: Fetch the exact data needed from knowledge sources.

**Process**:
- Takes targeting information and retrieves actual content
- Implements caching for frequently accessed data
- Optimizes data transfer by fetching only needed fields
- Returns `RetrievedContent` objects with structured data and metadata

#### Pass 4: Response Generation (`response_generator.py`)
**Purpose**: Synthesize retrieved content into a natural, helpful response.

**Process**:
- Organizes all retrieved content by type and relevance
- Creates clear, structured prompts for the LLM
- Generates natural language responses with proper context
- Maintains conversation flow and user-friendly tone

### 2. Knowledge Base Architecture

#### Central Knowledge Hub (`knowledge_base.py`)
The `KnowledgeBase` class serves as the central coordinator for all data sources:

```python
class KnowledgeBase:
    def __init__(self, knowledge_base_path: str = "./knowledge_base"):
        self.rulebook = RulebookHandler(knowledge_base_path)    # D&D SRD
        self.character = CharacterHandler(knowledge_base_path)  # Character data
        self.sessions = SessionHandler(knowledge_base_path)     # Campaign history
```

#### Rulebook Handler (`rulebook_handler.py`)
Manages the complete D&D 5e System Reference Document:

**Data Structure**:
- `dnd5e_srd_full.json`: Complete rule content with sections
- `dnd5e_srd_query_helper.json`: Optimized structure for LLM navigation

**Key Features**:
- Hierarchical section organization
- Keyword-based search across all content
- Section ID-based retrieval for precise targeting
- Category-based browsing (spells, combat, equipment, etc.)

#### Character Handler (`character_handler.py`)
Manages all character-related data across multiple JSON files:

**File Structure**:
- `character.json`: Basic stats, class, race, level
- `inventory_list.json`: Equipment, weapons, armor, items
- `spell_list.json`: Available spells by class/level
- `action_list.json`: Combat actions and abilities
- `feats_and_traits.json`: Character features and traits
- `character_background.json`: Backstory and roleplay information
- `objectives_and_contracts.json`: Quests, goals, divine covenants

**Features**:
- Nested field access with dot notation
- Class-specific spell filtering
- Combat information aggregation
- Equipment status tracking

#### Session Handler (`session_handler.py`)
Manages campaign history and session notes:

**Features**:
- Markdown-based session notes
- Date-based organization
- Topic and keyword search
- Session summary generation
- Story continuity tracking

### 3. Core Infrastructure

#### LLM Client (`llm_client.py`)
Streamlined interface to OpenAI's API with advanced features:

**Key Features**:
- Async-first design for non-blocking operations
- Structured output validation using Pydantic models
- Automatic retry logic with exponential backoff
- Debug logging and monitoring hooks
- Temperature and parameter optimization for different use cases

```python
# Example usage
response = await llm_client.generate_structured_response(
    prompt, 
    SourceSelectionResponse,  # Pydantic model for validation
    temperature=0.1  # Low temperature for consistent structured output
)
```

#### Response Models (`response_models.py`)
Pydantic models that enforce LLM response structure:

```python
class SourceSelectionResponse(BaseModel):
    sources_needed: List[SourceTypeEnum] = Field(min_items=1, max_items=3)
    reasoning: str = Field(min_length=10, max_length=500)
    
    @validator('sources_needed')
    def validate_sources(cls, v):
        # Custom validation logic
        return v
```

**Benefits**:
- Guarantees consistent LLM output format
- Prevents malformed responses from breaking the system
- Provides clear error messages for debugging
- Enables reliable parsing of complex nested responses

#### Validation Helpers (`validation.py`)
Comprehensive validation utilities for data integrity:

- JSON syntax validation
- File existence and format checking
- LLM response structure validation
- Character data completeness checks

## Web Application Architecture

ShadowScribe includes a modern web interface built with FastAPI and React:

### Backend (`web_app/`)

#### FastAPI Server (`main.py`)
- **WebSocket Support**: Real-time chat interface with live progress updates
- **CORS Configuration**: Secure cross-origin requests for frontend
- **Session Management**: Persistent chat history and user sessions
- **API Endpoints**: RESTful API for system status and data access

#### WebSocket Handler (`websocket_handler.py`)
- **Connection Management**: Handle multiple concurrent users
- **Progress Streaming**: Real-time updates during 4-pass processing
- **Message Routing**: Distribute messages to connected clients
- **Error Handling**: Graceful connection failure recovery

#### Session Manager (`session_manager.py`)
- **Chat History**: Persistent conversation storage
- **User Sessions**: Multiple character support per user
- **State Management**: Maintain context across queries

### Frontend (`frontend-src/`)

#### React Components
- **Chat Interface**: Modern, responsive chat UI
- **Progress Indicators**: Visual feedback during query processing
- **Source Panels**: Display which knowledge sources are being used
- **Character Quick Reference**: Sidebar with key character information

#### Real-time Features
- **Live Progress Updates**: See each pass of the 4-pass system in real-time
- **Response Streaming**: Partial responses displayed as they generate
- **Connection Status**: Visual indicators for WebSocket connection health

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for web interface)
- OpenAI API key

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/calvin-seamons/ShadowScribe.git
   cd ShadowScribe
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. **Prepare knowledge base**:
   - Place your character JSON files in `knowledge_base/`
   - Add session notes to `knowledge_base/session_notes/`
   - The D&D SRD files should already be included

### Running the Application

#### Web Interface (Recommended)
```bash
npm run dev
```
This starts both the FastAPI backend (port 8000) and React frontend (port 3000).

#### Terminal Interface
```bash
python interactive_shadowscribe.py
```

#### Testing the System
```bash
python -m src.tests.test_suite
```

### Example Usage

**Rules Query**:
```
User: "How does counterspell work?"
Pass 1: Identifies need for DND_RULEBOOK
Pass 2: Targets spell sections and counterspell keywords
Pass 3: Retrieves counterspell rules and related mechanics
Pass 4: Generates comprehensive explanation with examples
```

**Character Query**:
```
User: "What's my AC and can I cast Shield?"
Pass 1: Identifies need for CHARACTER_DATA
Pass 2: Targets character.json (AC) and spell_list.json (Shield)
Pass 3: Retrieves armor class calculation and spell availability
Pass 4: Provides current AC and Shield spell details
```

**Complex Query**:
```
User: "Given my paladin abilities, how much damage would Divine Smite do against the undead from last session?"
Pass 1: Identifies need for CHARACTER_DATA, DND_RULEBOOK, SESSION_NOTES
Pass 2: Targets paladin abilities, Divine Smite rules, and recent session notes
Pass 3: Retrieves spell slots, smite mechanics, and enemy information
Pass 4: Calculates damage with bonuses and provides tactical advice
```

## Development and Testing

### Running Tests
```bash
# Full comprehensive test suite
python -m src.tests.test_suite

# Individual component tests
python -m unittest src.tests.test_suite.TestShadowScribeEngine
```

### Development Mode
```bash
# Backend only with hot reload
cd web_app && python main.py

# Frontend only
npm run frontend

# Both with concurrent execution
npm run dev
```

### Adding New Knowledge Sources

1. **Create Handler Class**:
   ```python
   class NewHandler:
       def __init__(self, knowledge_base_path: str):
           # Initialize handler
       
       def load_data(self):
           # Load data files
       
       def get_data(self, targets: Dict[str, Any]) -> Dict[str, Any]:
           # Retrieve specific data based on targets
   ```

2. **Update Response Models**:
   ```python
   class NewTargetResponse(BaseModel):
       # Define structure for targeting this source
   ```

3. **Integrate with Knowledge Base**:
   ```python
   # Add to KnowledgeBase.__init__()
   self.new_source = NewHandler(knowledge_base_path)
   ```

4. **Update Query Router**:
   - Add to `SourceTypeEnum`
   - Update targeting logic in `target_content()`
   - Add new response model handling

## Performance and Scaling

### Optimization Features

- **Async Architecture**: All operations are non-blocking
- **Content Caching**: Frequently accessed data cached in memory
- **Targeted Retrieval**: Only fetch data that's actually needed
- **Streaming Responses**: Start delivering results before complete processing
- **Connection Pooling**: Efficient API request management

### Scaling Considerations

- **Horizontal Scaling**: Stateless design allows multiple instances
- **Database Migration**: Current JSON files can migrate to database for larger datasets
- **CDN Integration**: Static assets can be served from CDN
- **Caching Layer**: Redis integration for shared caching across instances

## Contributing

### Code Organization
- `src/engine/`: Core processing pipeline
- `src/knowledge/`: Data source handlers
- `src/utils/`: Shared utilities and infrastructure
- `web_app/`: FastAPI backend
- `frontend-src/`: React frontend components

### Testing Requirements
- All new features must include unit tests
- Integration tests for new knowledge sources
- End-to-end tests for complete query flows

### Code Quality
- Type hints required for all Python code
- Pydantic models for all structured data
- Comprehensive error handling
- Async-first design patterns

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **D&D 5e SRD**: Wizards of the Coast for the System Reference Document
- **OpenAI**: For providing the language model capabilities
- **FastAPI & React**: For the excellent web framework foundations