"""
Base protocol and types for classifier backends.

Defines the interface that both LLM and local model classifiers must implement.
"""

from typing import Protocol, Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ClassificationResult:
    """Unified output from any classifier backend."""
    
    # Tool selection
    tools_needed: List[Dict[str, Any]] = field(default_factory=list)
    # Format: [{"tool": "character_data", "intention": "combat_info", "confidence": 0.95}]
    
    tool_confidences: Dict[str, float] = field(default_factory=dict)
    # Format: {"character_data": 0.95, "rulebook": 0.3, "session_notes": 0.1}
    
    # Entity extraction
    entities: List[Dict[str, Any]] = field(default_factory=list)
    # Format: [{"name": "Fireball", "type": "SPELL", "canonical": "Fireball", "confidence": 1.0}]
    
    # Metadata
    backend: str = "unknown"  # "llm" or "local"
    inference_time_ms: float = 0.0


class ClassifierBackend(Protocol):
    """Protocol for classifier backends (LLM or local model)."""
    
    async def classify(
        self,
        query: str,
        character_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> ClassificationResult:
        """
        Classify a query to determine tools, intents, and entities.
        
        Args:
            query: The user's query text
            character_name: Optional character name for context
            conversation_history: Optional list of prior conversation turns
            
        Returns:
            ClassificationResult with tools, intents, and entities
        """
        ...
