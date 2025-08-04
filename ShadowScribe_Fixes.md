# ShadowScribe Issues & Improvements Guide

## 🔴 Critical Issues Found

### 1. **Import Statements Missing**
Many files are missing crucial imports, which will cause immediate runtime errors:

- [`llm_client.py`](src/utils/llm_client.py): Missing `import os`, `import json`
- [`character_handler.py`](src/knowledge/character_handler.py): Missing `import os`, `import json`
- [`rulebook_handler.py`](src/knowledge/rulebook_handler.py): Missing `import os`, `import json`
- [`session_handler.py`](src/knowledge/session_handler.py): Missing `import os`, `import re`, `from datetime import datetime`
- [`validation.py`](src/utils/validation.py): Missing `import os`, `import json`

### 2. **Incomplete Method Implementations**
Several methods have incomplete implementations:

- [`character_handler.py`](src/knowledge/character_handler.py): Methods like `get_spell_save_dc()`, `get_spell_attack_bonus()`, `validate()` are incomplete
- [`validation.py`](src/utils/validation.py): Most validation methods have incomplete logic
- [`session_handler.py`](src/knowledge/session_handler.py): Several parsing methods are incomplete

### 3. **Path Configuration Issues**
The [`Config`](src/config/settings.py) class uses hardcoded Unix-style paths that won't work on Windows:
```python
'base_dir': '/Users/calvinseamons/ShadowScribe',  # This won't work on Windows!
```

## 🎯 Better LLM Output Structure Guarantees

### Current Approach Issues:
1. **Pydantic Validation**: Good start, but relies on LLM following instructions
2. **Retry Logic**: Helps, but still not 100% reliable
3. **JSON Parsing**: Fragile when LLM adds markdown formatting

### Recommended Improvements:

#### 1. **Use OpenAI Function Calling**
Instead of prompt engineering, use OpenAI's function calling feature for guaranteed structure:

```python
# filepath: c:\Users\calvi\Repositories\ShadowScribe\src\utils\llm_client_v2.py
import os
import json
from typing import Dict, Any, Optional, Type, TypeVar
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

T = TypeVar('T', bound=BaseModel)

class LLMClientV2:
    """Enhanced LLM client using OpenAI function calling for guaranteed structure."""
    
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def generate_structured_response(
        self, 
        prompt: str, 
        response_model: Type[T]
    ) -> T:
        """
        Generate response with guaranteed structure using function calling.
        
        This approach forces the LLM to return data in the exact format needed.
        """
        # Convert Pydantic model to OpenAI function schema
        function_schema = self._pydantic_to_function_schema(response_model)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                tools=[{
                    "type": "function",
                    "function": function_schema
                }],
                tool_choice={"type": "function", "function": {"name": function_schema["name"]}}
            )
            
            # Extract the function call arguments
            tool_call = response.choices[0].message.tool_calls[0]
            arguments = json.loads(tool_call.function.arguments)
            
            # Validate with Pydantic
            return response_model(**arguments)
            
        except Exception as e:
            raise Exception(f"Error generating structured response: {str(e)}")
    
    def _pydantic_to_function_schema(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """Convert Pydantic model to OpenAI function schema."""
        schema = model.schema()
        
        return {
            "name": model.__name__.lower(),
            "description": f"Extract {model.__name__} data",
            "parameters": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", [])
            }
        }
```

#### 2. **Implement Output Parsers**
Add fallback parsers that can handle common LLM output mistakes:

```python
# filepath: c:\Users\calvi\Repositories\ShadowScribe\src\utils\output_parsers.py
import re
import json
from typing import Dict, Any, Optional

class RobustJSONParser:
    """Robust JSON parser that handles common LLM formatting issues."""
    
    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        """Parse JSON from LLM output with multiple fallback strategies."""
        
        # Strategy 1: Direct JSON parsing
        try:
            return json.loads(text)
        except:
            pass
        
        # Strategy 2: Extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Strategy 3: Find JSON object boundaries
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except:
                pass
        
        # Strategy 4: Fix common issues
        cleaned = text
        # Remove trailing commas
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        # Convert single quotes to double quotes
        cleaned = re.sub(r"'([^']*)'", r'"\1"', cleaned)
        
        try:
            return json.loads(cleaned)
        except:
            raise ValueError(f"Could not parse JSON from text: {text[:200]}...")
```

## 🔧 Workflow Improvements

### 1. **Configuration Management**
Fix the path issues with dynamic path resolution:

```python
# filepath: c:\Users\calvi\Repositories\ShadowScribe\src\config\settings_v2.py
import os
import platform
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

class ConfigV2:
    """Enhanced configuration with cross-platform support."""
    
    def __init__(self, config_file: str = "config.ini"):
        load_dotenv()
        
        # Dynamic base directory detection
        self.base_dir = self._get_base_dir()
        
        # Load config file if exists
        self.config_file = Path(config_file)
        if self.config_file.exists():
            self._load_config()
        else:
            self._set_defaults()
    
    def _get_base_dir(self) -> Path:
        """Get base directory dynamically."""
        # Try environment variable first
        if os.getenv('SHADOWSCRIBE_BASE_DIR'):
            return Path(os.getenv('SHADOWSCRIBE_BASE_DIR'))
        
        # Otherwise use current working directory
        return Path.cwd()
    
    def _set_defaults(self):
        """Set default configuration values with cross-platform paths."""
        self.knowledge_base_dir = self.base_dir / "knowledge_base"
        self.rulebook_file = self.knowledge_base_dir / "dnd5rulebook.md"
        self.session_notes_dir = self.knowledge_base_dir / "session_notes"
        self.output_dir = self.base_dir / "vector_store"
        self.chunks_output_file = self.base_dir / "chunks_output.json"
```

### 2. **Error Handling & Validation**
Implement comprehensive error handling:

```python
# filepath: c:\Users\calvi\Repositories\ShadowScribe\src\utils\error_handling.py
from typing import Optional, Callable, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class ShadowScribeError(Exception):
    """Base exception for ShadowScribe errors."""
    pass

class DataLoadError(ShadowScribeError):
    """Error loading data from knowledge base."""
    pass

class LLMError(ShadowScribeError):
    """Error communicating with LLM."""
    pass

def with_fallback(fallback_value: Any, log_errors: bool = True):
    """Decorator to provide fallback values on error."""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                return fallback_value
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                return fallback_value
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
```

### 3. **Complete the Validation System**
Implement the missing validation logic:

```python
# filepath: c:\Users\calvi\Repositories\ShadowScribe\src\utils\validation_complete.py
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

class ValidationHelper:
    """Complete validation utilities for the ShadowScribe engine."""
    
    @staticmethod
    def validate_json_file(file_path: str) -> Dict[str, Any]:
        """Validate a JSON file for syntax and basic structure."""
        result = {
            "file_path": file_path,
            "exists": False,
            "valid_json": False,
            "readable": False,
            "size_mb": 0,
            "error": None
        }
        
        try:
            path = Path(file_path)
            result["exists"] = path.exists()
            
            if not result["exists"]:
                result["error"] = "File not found"
                return result
            
            result["size_mb"] = path.stat().st_size / (1024 * 1024)
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result["valid_json"] = True
                result["readable"] = True
                
        except json.JSONDecodeError as e:
            result["error"] = f"Invalid JSON: {str(e)}"
        except UnicodeDecodeError as e:
            result["error"] = f"Encoding error: {str(e)}"
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        return result
```

## 📊 Architecture Improvements

### 1. **Implement Caching Layer**
Add a proper caching system with TTL:

```python
# filepath: c:\Users\calvi\Repositories\ShadowScribe\src\utils\caching.py
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class CacheEntry:
    value: Any
    timestamp: datetime
    ttl: timedelta

class TTLCache:
    """Time-based cache for expensive operations."""
    
    def __init__(self, default_ttl: timedelta = timedelta(minutes=5)):
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if datetime.now() - entry.timestamp > entry.ttl:
            del self._cache[key]
            return None
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        """Set value in cache with TTL."""
        self._cache[key] = CacheEntry(
            value=value,
            timestamp=datetime.now(),
            ttl=ttl or self.default_ttl
        )
```

### 2. **Add Monitoring & Metrics**
Track system performance:

```python
# filepath: c:\Users\calvi\Repositories\ShadowScribe\src\utils\metrics.py
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime
import statistics

@dataclass
class QueryMetrics:
    """Track metrics for query processing."""
    query: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    tokens_used: int = 0
    sources_accessed: List[str] = field(default_factory=list)
    cache_hits: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def duration_ms(self) -> float:
        """Get query duration in milliseconds."""
        if not self.end_time:
            return 0
        return (self.end_time - self.start_time).total_seconds() * 1000

class MetricsCollector:
    """Collect and analyze system metrics."""
    
    def __init__(self):
        self.queries: List[QueryMetrics] = []
    
    def start_query(self, query: str) -> QueryMetrics:
        """Start tracking a new query."""
        metric = QueryMetrics(query=query)
        self.queries.append(metric)
        return metric
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.queries:
            return {}
        
        durations = [q.duration_ms for q in self.queries if q.end_time]
        tokens = [q.tokens_used for q in self.queries]
        
        return {
            "total_queries": len(self.queries),
            "avg_duration_ms": statistics.mean(durations) if durations else 0,
            "avg_tokens": statistics.mean(tokens) if tokens else 0,
            "error_rate": sum(1 for q in self.queries if q.errors) / len(self.queries),
            "cache_hit_rate": sum(q.cache_hits for q in self.queries) / len(self.queries)
        }
```

## 🚀 Quick Fixes to Implement Now

1. **Add all missing imports** to get the system running
2. **Fix the path configuration** to use dynamic paths
3. **Complete the incomplete method implementations** with basic functionality
4. **Switch to OpenAI function calling** for reliable structured output
5. **Add proper error handling** throughout the system
6. **Implement the caching layer** to improve performance

## 💡 Long-term Improvements

1. **Add unit tests** for all components
2. **Implement proper logging** with structured logs
3. **Add API versioning** for the LLM interactions
4. **Create a web interface** for easier testing
5. **Add support for other LLMs** (Claude, local models)
6. **Implement conversation memory** for multi-turn interactions

This system has great potential, but needs these fixes to be production-ready!