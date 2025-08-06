"""
Simplified LLM Client - Streamlined communication with language models
"""

from typing import Dict, Any, Optional, Type, TypeVar, Union
import json
import asyncio
from openai import AsyncOpenAI
import os
from pydantic import BaseModel, ValidationError
import time

T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """
    Simplified LLM client with improved structured output handling.
    """
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        """Initialize LLM client with model and API configuration."""
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.debug_callback = None
        
        # Optimized parameters for structured responses
        self.default_params = {
            "temperature": 0.1,  # Very low for consistent structured output
            "max_tokens": 2000,
            "top_p": 1.0,
        }
    
    def set_debug_callback(self, callback):
        """Set a callback function for debug logging."""
        self.debug_callback = callback
    
    async def _log_debug(self, event_type: str, message: str, data: dict = None):
        """Helper to log debug messages if callback is set."""
        if self.debug_callback:
            try:
                self.debug_callback(event_type, message, data or {})
            except Exception as e:
                print(f"Debug callback error: {e}")
    
    async def generate_structured_response(
        self, 
        prompt: str, 
        response_model: Type[T],
        max_retries: int = 2,
        use_fallback: bool = True
    ) -> T:
        """
        Generate a structured response using function calling.
        Primary method for getting structured data from the LLM.
        
        Args:
            prompt: The prompt to send
            response_model: Pydantic model for response validation
            max_retries: Number of retries before fallback
            use_fallback: Whether to use intelligent fallback on failure
        """
        function_schema = self._create_function_schema(response_model)
        
        await self._log_debug("LLM_FUNCTION_CALL_START", f"Requesting {response_model.__name__}", {
            "model": self.model,
            "prompt_length": len(prompt),
            "retries": max_retries
        })
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # Enhance prompt on retries
                retry_prompt = prompt
                if attempt > 0 and last_error:
                    retry_prompt += f"\n\nIMPORTANT: Previous attempt failed with: {last_error}\nPlease ensure all required fields are included."
                
                # Make the API call with function calling
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{
                        "role": "system",
                        "content": "You are a D&D assistant that provides accurate, complete JSON responses for game queries."
                    }, {
                        "role": "user",
                        "content": retry_prompt
                    }],
                    tools=[{
                        "type": "function",
                        "function": function_schema
                    }],
                    tool_choice={"type": "function", "function": {"name": function_schema["name"]}},
                    temperature=0.1,  # Low for consistency
                    max_tokens=2000
                )
                
                # Extract and validate the response
                if not response.choices[0].message.tool_calls:
                    raise ValueError("No function call in response")
                
                tool_call = response.choices[0].message.tool_calls[0]
                arguments = json.loads(tool_call.function.arguments)
                
                # Validate required fields are present
                self._validate_arguments(arguments, response_model)
                
                # Create and validate the model
                result = response_model(**arguments)
                
                elapsed = time.time() - start_time
                await self._log_debug("LLM_FUNCTION_CALL_SUCCESS", f"Got valid {response_model.__name__}", {
                    "attempt": attempt + 1,
                    "elapsed_seconds": round(elapsed, 2),
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
                })
                
                return result
                
            except (json.JSONDecodeError, ValidationError, ValueError) as e:
                last_error = str(e)
                
                if attempt < max_retries - 1:
                    await self._log_debug("LLM_FUNCTION_CALL_RETRY", f"Retrying due to: {str(e)}", {
                        "attempt": attempt + 1,
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
                    await asyncio.sleep(0.3 * (attempt + 1))  # Exponential backoff
                else:
                    await self._log_debug("LLM_FUNCTION_CALL_FAILED", f"Failed after {max_retries} attempts", {
                        "error": str(e),
                        "model": response_model.__name__
                    })
                    
                    if use_fallback:
                        # Use intelligent fallback
                        return self._create_fallback_response(response_model, prompt)
                    else:
                        raise
            
            except Exception as e:
                # Unexpected errors
                await self._log_debug("LLM_FUNCTION_CALL_ERROR", f"Unexpected error: {str(e)}", {
                    "error_type": type(e).__name__
                })
                
                if use_fallback:
                    return self._create_fallback_response(response_model, prompt)
                else:
                    raise
    
    def _validate_arguments(self, arguments: Dict[str, Any], model: Type[BaseModel]) -> None:
        """Validate that required fields are present in arguments."""
        schema = model.model_json_schema()
        required_fields = schema.get("required", [])
        
        missing = [field for field in required_fields if field not in arguments]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
    
    def _create_function_schema(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """Create a simplified function schema for OpenAI."""
        schema = model.model_json_schema()
        
        # Simplified schema focusing on essential fields
        return {
            "name": model.__name__.lower().replace("response", ""),
            "description": f"Extract {model.__name__} information",
            "parameters": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", [])
            }
        }
    
    def _create_fallback_response(self, model: Type[BaseModel], prompt: str) -> BaseModel:
        """Create a sensible fallback response when LLM fails."""
        from ..utils.response_models import (
            SourceSelectionResponse, 
            RulebookTargetResponse,
            CharacterTargetResponse,
            SessionTargetResponse,
            SourceTypeEnum
        )
        
        # Analyze the prompt to make intelligent fallbacks
        prompt_lower = prompt.lower()
        
        if model == SourceSelectionResponse:
            # Default to character data for most queries
            sources = [SourceTypeEnum.CHARACTER_DATA]
            
            # Add rulebook for rules questions
            if any(word in prompt_lower for word in ["rule", "spell", "how does", "can i", "what is"]):
                sources.append(SourceTypeEnum.DND_RULEBOOK)
            
            # Add sessions for story questions
            if any(word in prompt_lower for word in ["session", "last", "story", "npc", "quest"]):
                sources.append(SourceTypeEnum.SESSION_NOTES)
            
            return SourceSelectionResponse(
                sources_needed=sources,
                reasoning="Fallback: Selected based on keyword analysis"
            )
        
        elif model == CharacterTargetResponse:
            # Smart defaults based on query type
            fields = {"character.json": ["name", "class", "level", "combat_stats"]}
            
            if any(word in prompt_lower for word in ["spell", "cast", "magic"]):
                fields["spell_list.json"] = ["character_spells"]
            
            if any(word in prompt_lower for word in ["item", "weapon", "armor", "equipment"]):
                fields["inventory_list.json"] = ["inventory"]
            
            if any(word in prompt_lower for word in ["action", "attack", "damage"]):
                fields["action_list.json"] = ["character_actions"]
            
            return CharacterTargetResponse(
                file_fields=fields,
                reasoning="Fallback: Selected common fields based on query"
            )
        
        elif model == RulebookTargetResponse:
            # Extract keywords for rulebook search
            keywords = []
            for word in ["spell", "attack", "action", "damage", "save", "check", "condition"]:
                if word in prompt_lower:
                    keywords.append(word)
            
            return RulebookTargetResponse(
                section_ids=[],
                keywords=keywords if keywords else ["rules"],
                reasoning="Fallback: Keyword-based search"
            )
        
        elif model == SessionTargetResponse:
            return SessionTargetResponse(
                session_dates=["latest"],
                keywords=[],
                reasoning="Fallback: Getting most recent session"
            )
        
        # Generic fallback
        required_fields = model.model_json_schema().get("required", [])
        fallback_data = {}
        for field in required_fields:
            fallback_data[field] = [] if "list" in str(model.model_fields[field].annotation) else ""
        
        return model(**fallback_data)
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a standard text response.
        Simplified version with better error handling.
        """
        params = {**self.default_params, **kwargs}
        
        await self._log_debug("LLM_TEXT_REQUEST", "Generating text response", {
            "prompt_length": len(prompt)
        })
        
        try:
            start_time = time.time()
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **params
            )
            
            result = response.choices[0].message.content
            
            elapsed = time.time() - start_time
            await self._log_debug("LLM_TEXT_SUCCESS", "Generated response", {
                "response_length": len(result),
                "elapsed_seconds": round(elapsed, 2)
            })
            
            return result
            
        except Exception as e:
            await self._log_debug("LLM_TEXT_ERROR", f"Error: {str(e)}", {})
            return "I encountered an error generating a response. Please try again."
    
    async def generate_with_context(
        self,
        system_prompt: str,
        user_prompt: str,
        context_data: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        Generate response with structured context data.
        Formats JSON data clearly for the LLM.
        """
        # Build a clear, structured prompt
        formatted_prompt = f"{user_prompt}\n\n"
        
        # Add context data in a clear format
        if context_data:
            formatted_prompt += "=== AVAILABLE DATA ===\n"
            for key, value in context_data.items():
                if value:
                    formatted_prompt += f"\n{key.upper()}:\n"
                    if isinstance(value, (dict, list)):
                        formatted_prompt += json.dumps(value, indent=2)
                    else:
                        formatted_prompt += str(value)
                    formatted_prompt += "\n"
        
        return await self.generate_response(formatted_prompt, **kwargs)