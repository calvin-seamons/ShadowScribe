"""
Simplified LLM Client - Fixed to handle gpt-4o-mini responses better
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
    FIXED: Better handling of gpt-4o-mini function calling responses.
    """
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        """Initialize LLM client with model and API configuration."""
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.debug_callback = None
        
        # Optimized parameters for structured responses (will be model-aware)
        self.default_params = {
            "top_p": 1.0,
        }
    
    def _get_token_params(self, max_tokens: int) -> Dict[str, int]:
        """Get the appropriate token parameter name and value based on model."""
        # GPT-5 models use max_completion_tokens
        if (self.model.startswith("gpt-5") or 
            self.model.startswith("o1") or 
            self.model.startswith("o3")):
            return {"max_completion_tokens": max_tokens}
        else:
            # Older models (GPT-4, GPT-4o, etc.) use max_tokens
            return {"max_tokens": max_tokens}
    
    def _get_temperature_params(self, desired_temperature: float = 0.1) -> Dict[str, float]:
        """Get the appropriate temperature parameter based on model support."""
        # GPT-5 models only support temperature = 1.0 (default), so don't include the parameter
        if (self.model.startswith("gpt-5") or 
            self.model.startswith("o1") or 
            self.model.startswith("o3")):
            return {}  # Don't include temperature parameter, let it use default (1.0)
        else:
            # Older models support custom temperature
            return {"temperature": desired_temperature}
    
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
        FIXED: Better parsing and error recovery for gpt-4o-mini.
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
                
                # Enhance prompt on retries with more specific instructions
                retry_prompt = prompt
                if attempt > 0 and last_error:
                    # More explicit instructions for gpt-4o-mini
                    if "file_fields" in str(last_error):
                        retry_prompt += """

CRITICAL: You MUST return a JSON object with EXACTLY these two fields:
1. "file_fields": A dictionary mapping filenames to lists of field names
2. "reasoning": A string explaining your choices (at least 10 characters)

Example format:
{
  "file_fields": {
    "character_background.json": ["backstory", "backstory.family_backstory"],
    "character.json": ["character_base"]
  },
  "reasoning": "Selected background file for backstory information"
}"""
                    else:
                        retry_prompt += f"\n\nIMPORTANT: Previous attempt failed with: {last_error}\nPlease ensure all required fields are included."
                
                # Make the API call with function calling
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{
                        "role": "system",
                        "content": "You are a D&D assistant that provides accurate, complete JSON responses. Always include all required fields in your response."
                    }, {
                        "role": "user",
                        "content": retry_prompt
                    }],
                    tools=[{
                        "type": "function",
                        "function": function_schema
                    }],
                    tool_choice={"type": "function", "function": {"name": function_schema["name"]}},
                    **self._get_temperature_params(0.1),  # Low for consistency
                    **self._get_token_params(2000)
                )
                
                # Extract and validate the response
                if not response.choices[0].message.tool_calls:
                    raise ValueError("No function call in response")
                
                tool_call = response.choices[0].message.tool_calls[0]
                arguments_str = tool_call.function.arguments
                
                # Log raw arguments for debugging
                await self._log_debug("LLM_RAW_ARGS", "Raw function arguments", {
                    "arguments": arguments_str[:500]  # First 500 chars
                })
                
                # Parse JSON with error recovery
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError as je:
                    # Try to fix common JSON issues
                    fixed_str = self._fix_json_string(arguments_str)
                    arguments = json.loads(fixed_str)
                
                # FIX: Handle common response format issues from gpt-4o-mini
                arguments = self._normalize_arguments(arguments, response_model)
                
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
                
                await self._log_debug("LLM_FUNCTION_CALL_RETRY", f"Attempt {attempt + 1} failed", {
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.3 * (attempt + 1))  # Exponential backoff
                else:
                    await self._log_debug("LLM_FUNCTION_CALL_FAILED", f"All attempts failed", {
                        "final_error": str(e)
                    })
                    
                    if use_fallback:
                        return self._create_enhanced_fallback_response(response_model, prompt)
                    else:
                        raise
            
            except Exception as e:
                # Unexpected errors
                await self._log_debug("LLM_FUNCTION_CALL_ERROR", f"Unexpected error: {str(e)}", {
                    "error_type": type(e).__name__
                })
                
                if use_fallback:
                    return self._create_enhanced_fallback_response(response_model, prompt)
                else:
                    raise
    
    def _normalize_arguments(self, arguments: Dict[str, Any], model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Normalize arguments to handle common formatting issues from gpt-4o-mini.
        """
        from ..utils.response_models import CharacterTargetResponse
        
        # Special handling for CharacterTargetResponse
        if model == CharacterTargetResponse:
            # Sometimes the LLM nests the response
            if "file_fields" not in arguments and len(arguments) == 1:
                # Check if there's a nested structure
                first_key = list(arguments.keys())[0]
                if isinstance(arguments[first_key], dict) and "file_fields" in arguments[first_key]:
                    arguments = arguments[first_key]
            
            # Ensure file_fields exists and is a dict
            if "file_fields" not in arguments:
                # Try to find anything that looks like file fields
                for key, value in arguments.items():
                    if isinstance(value, dict) and any(".json" in k for k in value.keys()):
                        arguments["file_fields"] = value
                        if "reasoning" not in arguments:
                            arguments["reasoning"] = "Extracted file fields from response"
                        break
            
            # Ensure reasoning exists
            if "reasoning" not in arguments:
                arguments["reasoning"] = "Selected files based on query requirements"
        
        return arguments
    
    def _fix_json_string(self, json_str: str) -> str:
        """
        Attempt to fix common JSON formatting issues.
        """
        # Remove any markdown code blocks
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        
        # Fix trailing commas
        import re
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        return json_str.strip()
    
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
    
    def _create_enhanced_fallback_response(self, model: Type[BaseModel], prompt: str) -> BaseModel:
        """
        Create a sensible fallback response when LLM fails.
        ENHANCED: Now includes ALL character files for backstory queries.
        """
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
            # ENHANCED: Include ALL 7 character files in fallback
            fields = {
                "character.json": ["character_base", "combat_stats", "ability_scores"],
                "spell_list.json": ["character_spells"],
                "inventory_list.json": ["inventory"],
                "action_list.json": ["character_actions"],
                # ADD THE MISSING FILES
                "feats_and_traits.json": ["features_and_traits"],
                "character_background.json": ["background", "characteristics", "backstory", "backstory.family_backstory"],
                "objectives_and_contracts.json": ["objectives_and_contracts"]
            }
            
            # Emphasize specific files based on query keywords
            if any(word in prompt_lower for word in ["backstory", "background", "family", "parents", "history", "past", "thaldrin", "brenna"]):
                # Expand background fields for family queries
                fields["character_background.json"] = [
                    "background",
                    "characteristics", 
                    "backstory",
                    "backstory.family_backstory",
                    "backstory.family_backstory.parents",
                    "organizations",
                    "allies",
                    "enemies",
                    "notes"
                ]
            
            if any(word in prompt_lower for word in ["spell", "cast", "magic", "warlock", "paladin"]):
                fields["spell_list.json"] = ["character_spells", "character_spells.paladin_spells", "character_spells.warlock_spells"]
            
            if any(word in prompt_lower for word in ["item", "weapon", "armor", "equipment", "eldaryth"]):
                fields["inventory_list.json"] = ["inventory.equipped_items", "inventory.weapons", "inventory.armor"]
            
            if any(word in prompt_lower for word in ["action", "attack", "damage", "combat", "smite"]):
                fields["action_list.json"] = ["character_actions.action_economy", "character_actions.attacks_per_action"]
            
            if any(word in prompt_lower for word in ["objective", "contract", "quest", "covenant", "ghul"]):
                fields["objectives_and_contracts.json"] = [
                    "objectives_and_contracts.active_contracts",
                    "objectives_and_contracts.current_objectives",
                    "objectives_and_contracts.completed_objectives"
                ]
            
            return CharacterTargetResponse(
                file_fields=fields,
                reasoning="Fallback: Selected all character files to ensure comprehensive data access"
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
    
    def _create_fallback_response(self, model: Type[BaseModel], prompt: str) -> BaseModel:
        """Deprecated: Use _create_enhanced_fallback_response instead."""
        return self._create_enhanced_fallback_response(model, prompt)
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a standard text response.
        Simplified version with better error handling.
        """
        # Build params with model-aware defaults
        params = {**self.default_params}
        
        # Add model-aware temperature and token parameters if not overridden
        if 'temperature' not in kwargs and 'max_completion_tokens' not in kwargs and 'max_tokens' not in kwargs:
            params.update(self._get_temperature_params(0.7))  # Higher temp for creative text
            params.update(self._get_token_params(2000))
        
        # Override with any user-provided kwargs
        params.update(kwargs)
        
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