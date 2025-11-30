"""
Query Rewriter using Qwen2.5-3B via Ollama

This module provides a local LLM-based query rewriter that synthesizes
conversation history + context-dependent user queries into standalone questions.

Uses Qwen2.5:3b via Ollama for fast, optimized inference on Apple Silicon.
"""

import time
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class RewriteResult:
    """Result from query rewriting"""
    original_query: str
    rewritten_query: str
    was_changed: bool
    inference_time_ms: float
    model_name: str


class QueryRewriter:
    """
    Rewrites context-dependent queries into standalone queries using Qwen2.5 via Ollama.
    
    Uses Ollama's REST API for optimized inference on Apple Silicon.
    """
    
    _instance = None
    _initialized = False
    
    # Model configuration
    MODEL_NAME = "qwen2.5:3b"
    OLLAMA_URL = "http://localhost:11434/api/generate"
    TEMPERATURE = 0.1  # Low temperature for deterministic rewrites
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not QueryRewriter._initialized:
            self._verify_ollama()
            QueryRewriter._initialized = True
    
    def _verify_ollama(self):
        """Verify Ollama is running and model is available"""
        print(f"[QueryRewriter] Verifying Ollama connection...")
        
        try:
            # Check if Ollama is running
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            response.raise_for_status()
            
            # Check if our model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            if not any(self.MODEL_NAME in name for name in model_names):
                raise RuntimeError(
                    f"Model {self.MODEL_NAME} not found in Ollama. "
                    f"Run: ollama pull {self.MODEL_NAME}"
                )
            
            print(f"[QueryRewriter] ✅ Ollama ready with {self.MODEL_NAME}")
            
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Ollama is not running. Start it with: ollama serve"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to verify Ollama: {e}")
    
    def _build_prompt(self, user_query: str, conversation_history: List[Dict[str, str]]) -> str:
        """
        Build the prompt for query rewriting.
        """
        # Format conversation history
        history_text = ""
        if conversation_history:
            for i, turn in enumerate(conversation_history[-5:]):  # Last 5 turns
                role = turn.get('role', 'unknown').upper()
                content = turn.get('content', '')
                # Truncate long responses to save context
                if role == "ASSISTANT" and len(content) > 500:
                    content = content[:500] + "..."
                history_text += f"{role}: {content}\n\n"
        
        prompt = f"""You are a query rewriter. Rewrite the follow-up question to be completely standalone.

RULES:
1. Replace ALL pronouns (it, its, he, she, they, them, this, that, these, those) with the EXACT entity names
2. For comparisons ("which one"), include ALL item names being compared
3. For contrasts ("What about X?", "Now the Y ones", "And the Z?"), expand to full questions:
   - "What about enemies?" after discussing family → "What are my character's enemies?"
   - "Now the hostile ones" after discussing friendly NPCs → "Tell me about the hostile NPCs in the campaign"
   - "And the save DC?" after discussing spell attack → "What is my spell save DC?"
4. NEVER pass through incomplete fragments - always make a complete question
5. Keep abbreviations as-is ("5e" stays "5e")
6. If already standalone, return it unchanged
7. Return ONLY the rewritten question, nothing else

EXAMPLES:
- History: "Fireball is a spell...", Q: "What's its damage?" → "What is Fireball's damage?"
- History: "longsword vs dagger", Q: "Which one is better?" → "Which is better: longsword or dagger?"
- History: "friendly NPCs...", Q: "Now the hostile ones" → "Tell me about the hostile NPCs"
- History: "spell attack bonus is +5", Q: "And the save DC?" → "What is my spell save DC?"
- History: "family relationships...", Q: "What about enemies?" → "What are my character's enemies?"
- Q: "How does flanking work?" (standalone) → "How does flanking work?"

CONVERSATION HISTORY:
{history_text}

CURRENT QUESTION: {user_query}

Rewritten standalone question:"""

        return prompt
    
    def rewrite(
        self, 
        user_query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> RewriteResult:
        """
        Rewrite a context-dependent query into a standalone query.
        
        Args:
            user_query: The follow-up question that may depend on context
            conversation_history: List of prior conversation turns 
                                  [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            RewriteResult with original and rewritten queries
        """
        # If no history, no rewriting needed
        if not conversation_history or len(conversation_history) < 1:
            return RewriteResult(
                original_query=user_query,
                rewritten_query=user_query,
                was_changed=False,
                inference_time_ms=0.0,
                model_name=self.MODEL_NAME
            )
        
        start_time = time.time()
        
        # Build the prompt
        prompt = self._build_prompt(user_query, conversation_history)
        
        # Call Ollama API
        try:
            response = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": self.MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.TEMPERATURE,
                        "num_predict": 150,  # Max tokens
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            rewritten = result.get("response", "").strip()
            
        except Exception as e:
            print(f"[QueryRewriter] Ollama error: {e}")
            rewritten = user_query
        
        # Clean up the response
        rewritten = self._clean_response(rewritten, user_query)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return RewriteResult(
            original_query=user_query,
            rewritten_query=rewritten,
            was_changed=(rewritten.lower() != user_query.lower()),
            inference_time_ms=elapsed_ms,
            model_name=self.MODEL_NAME
        )
    
    def _clean_response(self, response: str, original: str) -> str:
        """Clean up the model's response to extract just the rewritten query"""
        # Remove common prefixes the model might add
        prefixes_to_remove = [
            "Rewritten question:",
            "Rewritten:",
            "Standalone question:",
            "Here is the rewritten question:",
            "The rewritten question is:",
            "CURRENT QUESTION:",
            "Current question:",
        ]
        
        cleaned = response
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        # Also check if the response echoes part of the prompt
        if "CONVERSATION HISTORY:" in cleaned:
            # Model echoed the prompt, extract just the last part
            parts = cleaned.split("Rewrite this question to be completely standalone:")
            if len(parts) > 1:
                cleaned = parts[-1].strip()
        
        # Remove quotes if present
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        if cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]
        
        # If the model failed badly, return original
        if len(cleaned) < 3 or len(cleaned) > 500:
            return original
        
        return cleaned


def get_rewriter() -> QueryRewriter:
    """Get the singleton QueryRewriter instance"""
    return QueryRewriter()


# Testing
if __name__ == "__main__":
    print("Testing QueryRewriter...")
    
    rewriter = get_rewriter()
    
    # Test case 1: Simple pronoun resolution
    history1 = [
        {"role": "user", "content": "What is Fireball?"},
        {"role": "assistant", "content": "Fireball is a 3rd-level evocation spell that creates a 20-foot radius explosion of fire. It deals 8d6 fire damage to all creatures in the area (Dexterity save for half). It's one of the most iconic damage spells in D&D."}
    ]
    result1 = rewriter.rewrite("What's its damage?", history1)
    print(f"\nTest 1 - Pronoun Resolution:")
    print(f"  Original: {result1.original_query}")
    print(f"  Rewritten: {result1.rewritten_query}")
    print(f"  Changed: {result1.was_changed}")
    print(f"  Time: {result1.inference_time_ms:.1f}ms")
    
    # Test case 2: Entity continuation
    history2 = [
        {"role": "user", "content": "Who is Elara?"},
        {"role": "assistant", "content": "Elara is an elven ranger you met in session 3. She helped guide your party through the Mistwood Forest and warned you about the vampire's lair."}
    ]
    result2 = rewriter.rewrite("When did I first meet her?", history2)
    print(f"\nTest 2 - Entity Continuation:")
    print(f"  Original: {result2.original_query}")
    print(f"  Rewritten: {result2.rewritten_query}")
    print(f"  Changed: {result2.was_changed}")
    print(f"  Time: {result2.inference_time_ms:.1f}ms")
    
    # Test case 3: Already standalone
    history3 = [
        {"role": "user", "content": "What's my AC?"},
        {"role": "assistant", "content": "Your AC is 18 with your plate armor."}
    ]
    result3 = rewriter.rewrite("How does flanking work in 5e?", history3)
    print(f"\nTest 3 - Already Standalone:")
    print(f"  Original: {result3.original_query}")
    print(f"  Rewritten: {result3.rewritten_query}")
    print(f"  Changed: {result3.was_changed}")
    print(f"  Time: {result3.inference_time_ms:.1f}ms")
    
    print("\n✅ QueryRewriter tests complete!")
