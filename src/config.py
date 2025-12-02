"""
RAG System Configuration
Centralized configuration for embedding models, API keys, and system settings
"""
from typing import Literal, Optional
from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables at module level - find .env in project root
project_root = Path(__file__).parent.parent  # Go up from src/config.py to project root
env_path = project_root / '.env'
load_dotenv(env_path)


EmbeddingModel = Literal[
    # OpenAI models (API-based)
    "text-embedding-3-small",  # Fast, good quality (1536 dim)
    "text-embedding-3-large",  # Slower, best quality (3072 dim) 
    "text-embedding-ada-002",  # Legacy, fast (1536 dim)
    # Local models (no API calls)
    "local-minilm-l6",         # Local, very fast (384 dim)
    "local-mpnet-base",        # Local, fast, good quality (768 dim)
    "local-bge-small",         # Local, high quality (384 dim)
    "local-bge-base",          # Local, very high quality (768 dim)
    "local-gte-small",         # Local, excellent quality (384 dim)
    "local-gte-base"           # Local, excellent quality (768 dim)
]

# OpenAI Model Categories - Different models require different parameters
OpenAIStandardModel = Literal[
    # Standard models - support temperature, max_tokens
    "gpt-4o",                  # High quality, multimodal
    "gpt-4o-mini",            # Fast, cost-effective
    "gpt-4-turbo",            # High quality, large context
    "gpt-4",                  # High quality, standard
    "gpt-3.5-turbo",          # Legacy, fast
    "gpt-3.5-turbo-16k"       # Legacy, large context
]

OpenAIReasoningModel = Literal[
    # Reasoning models - no temperature/max_tokens, use max_completion_tokens
    "o1",                     # Advanced reasoning
    "o1-mini",                # Fast reasoning
    "gpt-5",                  # Latest flagship reasoning
    "gpt-5-mini",             # Fast flagship reasoning  
    "gpt-5-nano"              # Ultra-fast reasoning
]

AnthropicModel = Literal[
    # Claude 4 models - Latest generation
    "claude-opus-4-1",            # Claude 4 Opus
    "claude-haiku-4-5",           # Claude 4.5 Haiku - Fast, cost-effective
    "claude-sonnet-4-5",          # Claude 4.5 Sonnet - Balanced quality/speed
    "claude-sonnet-4-0",          # Claude 4 Sonnet
    
    # Claude 3.7 models - Advanced reasoning
    "claude-3-7-sonnet-latest",   # Claude 3.7 Sonnet
    
    # Claude 3.5 models
    "claude-3-5-haiku-latest",    # Claude 3.5 Haiku - Fast, cost-effective
    "claude-3-5-sonnet-latest",   # Claude 3.5 Sonnet - Balanced quality/speed
    
    # Claude 3 models
    "claude-3-opus-latest",       # Claude 3 Opus
    "claude-3-haiku-20240307"     # Claude 3 Haiku
]


@dataclass
class RAGConfig:
    """Configuration for the RAG system"""
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # LLM Client Settings
    primary_llm_provider: str = "anthropic"  # "openai" or "anthropic"
    router_llm_provider: str = "anthropic"   # Provider for router decisions
    final_response_llm_provider: str = "anthropic"  # Provider for final response

    # Model Settings - Updated with latest available models (as of Sept 2025)
    # OpenAI Models
    openai_router_model: str = "gpt-4o-mini"  # Fast, cost-effective for routing
    openai_final_model: str = "gpt-4o"        # High quality for final responses
    
    # Anthropic Models  
    anthropic_router_model: str = "claude-haiku-4-5"   # Latest Claude 4.5 Haiku - Fast, cost-effective for routing
    anthropic_final_model: str = "claude-sonnet-4-5"    # Latest Claude 4.5 Sonnet - Default response model
    
    # Embedding Model Settings
    # Use local model by default (no API calls, fast, good quality)
    embedding_model: EmbeddingModel = "local-bge-base"
    
    # LLM Generation Settings
    # Router LLM Settings (fast, cheaper models for routing decisions)
    router_temperature: float = 0.3
    router_max_tokens: int = 2000
    router_max_completion_tokens: int = 2000  # For reasoning models
    
    # Final Response LLM Settings (higher quality models for final responses)
    final_temperature: float = 0.7
    final_max_tokens: int = 2000
    final_max_completion_tokens: int = 2000  # For reasoning models
    
    # Query Engine Settings
    max_results: int = 10
    entity_boost_weight: float = 0.25
    context_hint_weight: float = 0.15
    
    # Caching Settings
    embedding_cache_size: int = 1000
    
    # Local Model Settings (if using local models)
    local_model_device: str = "cpu"  # or "cuda" if GPU available
    
    # Local Classifier Settings (Joint Classifier Model)
    local_classifier_model_path: str = "574-Assignment/models/joint_classifier"
    local_classifier_srd_cache: str = "src/classifiers/data/srd_cache"
    local_classifier_device: str = "auto"  # auto, cuda, mps, cpu
    local_classifier_tool_threshold: float = 0.5  # Confidence threshold for tool selection
    gazetteer_min_similarity: float = 0.70  # Minimum similarity for gazetteer NER matching (lower = more permissive)

    # Routing Mode - Controls which classifier is used for tool/intention routing
    # Options:
    #   "haiku"      - Use Claude Haiku 4.5 API for routing (saves to DB for training data)
    #   "local"      - Use local DeBERTa classifier for routing (fast, no API calls)
    #   "comparison" - Run BOTH classifiers, Haiku is primary, local shown in UI for comparison
    routing_mode: str = "comparison"  # Run both for UI comparison
    
    def __post_init__(self):
        """Validate API keys after initialization"""
        # Only require the API key for the providers you're actually using
        providers_needed = {self.router_llm_provider, self.final_response_llm_provider, self.primary_llm_provider}
        
        if "openai" in providers_needed and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required but not found in environment variables")
        
        if "anthropic" in providers_needed and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required but not found in environment variables")
        
        # Warn about unused API keys
        if "openai" not in providers_needed and self.openai_api_key:
            print("ℹ️  OpenAI API key found but not needed with current provider settings")
        
        if "anthropic" not in providers_needed and self.anthropic_api_key:
            print("ℹ️  Anthropic API key found but not needed with current provider settings")
    
    @classmethod
    def from_env(cls) -> 'RAGConfig':
        """Create config from environment variables, using class defaults as fallbacks.
        
        Environment variables can override any setting, but class defaults are
        the source of truth. If you need to change a default, change it in the
        class definition above, not here.
        """
        # Get class defaults for fallback values
        defaults = cls.__dataclass_fields__
        
        def get_default(field_name: str):
            """Get the default value for a field."""
            field = defaults[field_name]
            return field.default if field.default is not field.default_factory else field.default_factory()
        
        def env_or_default(env_var: str, field_name: str, cast=str):
            """Get env var or fall back to class default."""
            val = os.getenv(env_var)
            if val is None:
                return get_default(field_name)
            if cast == bool:
                return val.lower() == 'true'
            return cast(val)
        
        return cls(
            # API Keys (no defaults - must come from environment)
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            
            # LLM Provider Settings
            primary_llm_provider=env_or_default('RAG_PRIMARY_LLM_PROVIDER', 'primary_llm_provider'),
            router_llm_provider=env_or_default('RAG_ROUTER_LLM_PROVIDER', 'router_llm_provider'),
            final_response_llm_provider=env_or_default('RAG_FINAL_LLM_PROVIDER', 'final_response_llm_provider'),
            
            # Model Settings
            openai_router_model=env_or_default('RAG_OPENAI_ROUTER_MODEL', 'openai_router_model'),
            openai_final_model=env_or_default('RAG_OPENAI_FINAL_MODEL', 'openai_final_model'),
            anthropic_router_model=env_or_default('RAG_ANTHROPIC_ROUTER_MODEL', 'anthropic_router_model'),
            anthropic_final_model=env_or_default('RAG_ANTHROPIC_FINAL_MODEL', 'anthropic_final_model'),
            
            # Embedding and Query Settings
            embedding_model=env_or_default('RAG_EMBEDDING_MODEL', 'embedding_model'),
            
            # LLM Generation Settings
            router_temperature=env_or_default('RAG_ROUTER_TEMPERATURE', 'router_temperature', float),
            router_max_tokens=env_or_default('RAG_ROUTER_MAX_TOKENS', 'router_max_tokens', int),
            router_max_completion_tokens=env_or_default('RAG_ROUTER_MAX_COMPLETION_TOKENS', 'router_max_completion_tokens', int),
            final_temperature=env_or_default('RAG_FINAL_TEMPERATURE', 'final_temperature', float),
            final_max_tokens=env_or_default('RAG_FINAL_MAX_TOKENS', 'final_max_tokens', int),
            final_max_completion_tokens=env_or_default('RAG_FINAL_MAX_COMPLETION_TOKENS', 'final_max_completion_tokens', int),
            
            max_results=env_or_default('RAG_MAX_RESULTS', 'max_results', int),
            entity_boost_weight=env_or_default('RAG_ENTITY_BOOST_WEIGHT', 'entity_boost_weight', float),
            context_hint_weight=env_or_default('RAG_CONTEXT_HINT_WEIGHT', 'context_hint_weight', float),
            embedding_cache_size=env_or_default('RAG_CACHE_SIZE', 'embedding_cache_size', int),
            local_model_device=env_or_default('RAG_LOCAL_DEVICE', 'local_model_device'),
            
            # Local Classifier Settings
            local_classifier_model_path=env_or_default('RAG_LOCAL_CLASSIFIER_MODEL_PATH', 'local_classifier_model_path'),
            local_classifier_srd_cache=env_or_default('RAG_LOCAL_CLASSIFIER_SRD_CACHE', 'local_classifier_srd_cache'),
            local_classifier_device=env_or_default('RAG_LOCAL_CLASSIFIER_DEVICE', 'local_classifier_device'),
            local_classifier_tool_threshold=env_or_default('RAG_LOCAL_CLASSIFIER_TOOL_THRESHOLD', 'local_classifier_tool_threshold', float),
            gazetteer_min_similarity=env_or_default('RAG_GAZETTEER_MIN_SIMILARITY', 'gazetteer_min_similarity', float),

            # Routing Mode
            routing_mode=env_or_default('RAG_ROUTING_MODE', 'routing_mode')
        )
    
    @classmethod
    def from_defaults(cls) -> 'RAGConfig':
        """Create config using class defaults - config is the source of truth.
        
        Only injects API keys from environment since they shouldn't be in code.
        All other settings come from the class defaults defined above.
        """
        return cls(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY')
        )
    
    def get_embedding_dimensions(self) -> int:
        """Get the expected embedding dimensions for the current model"""
        dimensions = {
            # OpenAI models
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
            # Local models
            "local-minilm-l6": 384,
            "local-mpnet-base": 768,
            "local-bge-small": 384,
            "local-bge-base": 768,
            "local-gte-small": 384,
            "local-gte-base": 768
        }
        return dimensions.get(self.embedding_model, 768)
    
    def is_local_model(self) -> bool:
        """Check if the current model is a local model"""
        return self.embedding_model.startswith("local-")
    
    def validate_openai_key(self) -> bool:
        """Validate that OpenAI API key is present and appears valid"""
        if not self.openai_api_key:
            return False
        return self.openai_api_key.startswith('sk-') and len(self.openai_api_key) > 20
    
    def validate_anthropic_key(self) -> bool:
        """Validate that Anthropic API key is present and appears valid"""
        if not self.anthropic_api_key:
            return False
        return self.anthropic_api_key.startswith('sk-ant-') and len(self.anthropic_api_key) > 20

    def is_reasoning_model(self, model: str) -> bool:
        """Check if a model is a reasoning model that requires special parameters"""
        reasoning_models = {"o1", "o1-mini", "gpt-5", "gpt-5-mini", "gpt-5-nano"}
        return model in reasoning_models
    
    def is_standard_model(self, model: str) -> bool:
        """Check if a model supports standard parameters (temperature, max_tokens)"""
        return not self.is_reasoning_model(model)
    
    def get_available_openai_models(self) -> dict:
        """Get all available OpenAI models categorized by type"""
        return {
            "standard": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
            "reasoning": ["o1", "o1-mini", "gpt-5", "gpt-5-mini", "gpt-5-nano"]
        }
    
    def get_available_anthropic_models(self) -> dict:
        """Get all available Anthropic models categorized by generation"""
        return {
            "claude_4": [
                "claude-opus-4-1",
                "claude-haiku-4-5",
                "claude-sonnet-4-5",
                "claude-sonnet-4-0"
            ],
            "claude_3_7": [
                "claude-3-7-sonnet-latest"
            ],
            "claude_3_5": [
                "claude-3-5-haiku-latest",
                "claude-3-5-sonnet-latest"
            ],
            "claude_3": [
                "claude-3-opus-latest",
                "claude-3-haiku-20240307"
            ]
        }
    
    def get_router_llm_params(self, model: Optional[str] = None) -> dict:
        """Get LLM parameters for router calls (fast, cheaper models)"""
        model = model or (
            self.openai_router_model if self.router_llm_provider == "openai" 
            else self.anthropic_router_model
        )
        
        if self.is_reasoning_model(model):
            # Reasoning models don't support temperature
            return {
                "max_completion_tokens": self.router_max_completion_tokens
            }
        else:
            # Standard models
            return {
                "temperature": self.router_temperature,
                "max_tokens": self.router_max_tokens
            }
    
    def get_final_llm_params(self, model: Optional[str] = None) -> dict:
        """Get LLM parameters for final response calls (higher quality models)"""
        model = model or (
            self.openai_final_model if self.final_response_llm_provider == "openai" 
            else self.anthropic_final_model
        )
        
        if self.is_reasoning_model(model):
            # Reasoning models don't support temperature
            return {
                "max_completion_tokens": self.final_max_completion_tokens
            }
        else:
            # Standard models
            return {
                "temperature": self.final_temperature,
                "max_tokens": self.final_max_tokens
            }


# Global config instance
_config: Optional[RAGConfig] = None


def get_config() -> RAGConfig:
    """Get the global RAG configuration instance"""
    global _config
    if _config is None:
        _config = RAGConfig.from_defaults()  # Use class defaults instead of env defaults
    return _config


def set_config(config: RAGConfig) -> None:
    """Set the global RAG configuration instance"""
    global _config
    _config = config


def get_embedding_model() -> EmbeddingModel:
    """Quick helper to get just the embedding model"""
    return get_config().embedding_model
