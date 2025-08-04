"""
LLM Client - Handles communication with language models (OpenAI, etc.)
"""

from typing import Dict, Any, Optional, Type, TypeVar
import json
import asyncio
from openai import AsyncOpenAI
import os
from pydantic import BaseModel, ValidationError

from .output_parsers import RobustJSONParser
from .error_handling import retry_on_failure, LLMError

T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """
    Handles communication with language models for the ShadowScribe engine.
    Supports structured responses with Pydantic validation and OpenAI function calling.
    """
    
    def __init__(self, model: str = "gpt-4.1-nano", api_key: Optional[str] = None):
        """Initialize LLM client with model and API configuration."""
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.debug_callback = None  # Optional debug callback
        
        # Default parameters optimized for gpt-4o-mini
        self.default_params = {
            "temperature": 0.3,  # Lower for more consistent structured responses
            "max_tokens": 4000,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
    
    def set_debug_callback(self, callback):
        """Set a callback function for debug logging."""
        self.debug_callback = callback
    
    async def generate_structured_response(
        self, 
        prompt: str, 
        response_model: Type[T],
        use_function_calling: bool = True
    ) -> T:
        """Generate response with fallback strategy."""
        if use_function_calling:
            try:
                return await self._generate_with_function_calling(prompt, response_model)
            except Exception as e:
                if self.debug_callback:
                    self.debug_callback("LLM_FUNCTION_CALLING_FALLBACK", f"Function calling failed, trying prompt validation: {str(e)}")
                
                # Fallback to prompt-based validation
                return await self.generate_validated_response(prompt, response_model)
        else:
            return await self.generate_validated_response(prompt, response_model)
    
    async def _generate_with_function_calling(
        self, 
        prompt: str, 
        response_model: Type[T],
        max_retries: int = 3
    ) -> T:
        """Generate response using OpenAI function calling with improved reliability."""
        function_schema = self._pydantic_to_function_schema(response_model)
        
        if self.debug_callback:
            self.debug_callback("LLM_STRUCTURED_PROMPT_SENT", "Sending structured prompt to LLM", {
                "model": self.model,
                "prompt": prompt,
                "response_model": response_model.__name__,
                "function_schema": function_schema
            })
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Enhanced prompt with specific field requirements on retries
                retry_prompt = prompt
                if attempt > 0:
                    required_fields = function_schema["parameters"].get("required", [])
                    retry_prompt += f"\n\nIMPORTANT: Your previous attempt was missing required fields. You MUST include ALL of these fields in your response: {', '.join(required_fields)}. Do not omit any required field."
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": retry_prompt}],
                    tools=[{
                        "type": "function",
                        "function": function_schema
                    }],
                    tool_choice={"type": "function", "function": {"name": function_schema["name"]}},
                    # Add these parameters for more consistent results
                    temperature=0.1,  # Lower temperature for more deterministic output
                    max_tokens=2000   # Ensure enough tokens for complete response
                )
                
                # Check if we have tool calls
                if not response.choices[0].message.tool_calls:
                    raise ValueError("No function call returned by LLM")
                
                tool_call = response.choices[0].message.tool_calls[0]
                arguments = json.loads(tool_call.function.arguments)
                
                # Detailed validation before Pydantic
                required_fields = function_schema["parameters"].get("required", [])
                missing_fields = [field for field in required_fields if field not in arguments]
                
                if missing_fields:
                    error_msg = f"Missing required fields: {missing_fields}. Got: {list(arguments.keys())}"
                    if attempt < max_retries - 1:
                        if self.debug_callback:
                            self.debug_callback("LLM_RETRY_MISSING_FIELDS", error_msg, {
                                "attempt": attempt + 1,
                                "missing": missing_fields,
                                "received": list(arguments.keys())
                            })
                        continue
                    else:
                        raise ValueError(error_msg)
                
                # Additional validation of field contents
                self._validate_function_response(arguments, response_model)
                
                # Validate with Pydantic
                validated_response = response_model(**arguments)
                
                if self.debug_callback:
                    self.debug_callback("LLM_STRUCTURED_RESPONSE_RECEIVED", "Received valid structured response", {
                        "model": self.model,
                        "response_model": response_model.__name__,
                        "attempt": attempt + 1,
                        "arguments": arguments
                    })
                
                return validated_response
                
            except Exception as e:
                last_error = e
                if self.debug_callback:
                    self.debug_callback("LLM_STRUCTURED_ERROR", f"Attempt {attempt + 1} failed: {str(e)}", {
                        "model": self.model,
                        "response_model": response_model.__name__,
                        "error": str(e),
                        "attempt": attempt + 1
                    })
                
                # Don't retry JSON decode errors - usually unfixable
                if isinstance(e, json.JSONDecodeError) and attempt >= 1:
                    break
        
        # All attempts failed
        if self.debug_callback:
            self.debug_callback("LLM_STRUCTURED_FINAL_ERROR", f"All attempts failed for function calling", {
                "model": self.model,
                "response_model": response_model.__name__,
                "final_error": str(last_error)
            })
        
        raise LLMError(f"Function calling failed after {max_retries} attempts: {str(last_error)}")
    
    def _pydantic_to_function_schema(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """Convert Pydantic model to OpenAI function schema with better descriptions."""
        schema = model.model_json_schema()
        
        # Resolve any $ref definitions
        resolved_properties = self._resolve_schema_refs(
            schema.get("properties", {}), 
            schema.get("$defs", {})
        )
        
        # Add detailed descriptions for required fields
        for field_name in schema.get("required", []):
            if field_name in resolved_properties:
                prop = resolved_properties[field_name]
                if "description" not in prop:
                    # Add helpful descriptions for key fields
                    if field_name == "file_fields":
                        prop["description"] = "Dictionary mapping filenames to lists of field names to retrieve"
                    elif field_name == "reasoning":
                        prop["description"] = "Explanation of why these specific files and fields are needed"
        
        return {
            "name": model.__name__.lower(),
            "description": f"Extract {model.__name__} data. ALL required fields must be included.",
            "parameters": {
                "type": "object",
                "properties": resolved_properties,
                "required": schema.get("required", []),
                "additionalProperties": False  # Prevent extra fields
            }
        }
    
    def _resolve_schema_refs(self, properties: Dict[str, Any], defs: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve $ref definitions in schema properties for OpenAI function calling."""
        resolved = {}
        
        for prop_name, prop_schema in properties.items():
            resolved[prop_name] = self._resolve_single_property(prop_schema, defs)
        
        return resolved
    
    def _resolve_single_property(self, prop_schema: Dict[str, Any], defs: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a single property's schema references."""
        if isinstance(prop_schema, dict):
            # Handle direct $ref
            if "$ref" in prop_schema:
                ref_path = prop_schema["$ref"]
                if ref_path.startswith("#/$defs/"):
                    def_name = ref_path.replace("#/$defs/", "")
                    if def_name in defs:
                        return self._resolve_single_property(defs[def_name], defs)
            
            # Handle arrays with $ref items
            elif prop_schema.get("type") == "array" and "items" in prop_schema:
                items_schema = prop_schema["items"]
                resolved_items = self._resolve_single_property(items_schema, defs)
                return {
                    **prop_schema,
                    "items": resolved_items
                }
            
            # Handle objects with $ref properties
            elif "properties" in prop_schema:
                resolved_props = {}
                for nested_name, nested_schema in prop_schema["properties"].items():
                    resolved_props[nested_name] = self._resolve_single_property(nested_schema, defs)
                return {
                    **prop_schema,
                    "properties": resolved_props
                }
        
        return prop_schema

    def _validate_function_response(self, arguments: Dict[str, Any], response_model: Type[T]) -> None:
        """Validate function call arguments against the expected model."""
        schema = response_model.model_json_schema()
        required_fields = schema.get("required", [])
        
        # Check for missing required fields
        missing = [field for field in required_fields if field not in arguments]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        # Check for empty required fields
        empty_fields = []
        for field in required_fields:
            value = arguments.get(field)
            if value is None or (isinstance(value, (str, list, dict)) and not value):
                empty_fields.append(field)
        
        if empty_fields:
            raise ValueError(f"Required fields cannot be empty: {empty_fields}")
        
        # Type validation for critical fields
        properties = schema.get("properties", {})
        for field_name, field_value in arguments.items():
            if field_name in properties:
                expected_type = properties[field_name].get("type")
                if expected_type == "object" and not isinstance(field_value, dict):
                    raise ValueError(f"Field '{field_name}' must be an object/dict, got {type(field_value)}")
                elif expected_type == "array" and not isinstance(field_value, list):
                    raise ValueError(f"Field '{field_name}' must be an array/list, got {type(field_value)}")
                elif expected_type == "string" and not isinstance(field_value, str):
                    raise ValueError(f"Field '{field_name}' must be a string, got {type(field_value)}")

    async def generate_validated_response(self, prompt: str, response_model: Type[T], 
                                        max_retries: int = 3) -> T:
        """
        Generate a response that's validated against a Pydantic model.
        
        Args:
            prompt: The prompt to send to the LLM
            response_model: Pydantic model class to validate against
            max_retries: Number of retries if validation fails
            
        Returns:
            Validated Pydantic model instance
            
        Raises:
            ValidationError: If response doesn't match model after all retries
        """
        # Add schema to prompt
        schema_prompt = self._enhance_prompt_with_schema(prompt, response_model)
        
        # Log the validated prompt if debug callback is available
        if self.debug_callback:
            self.debug_callback("LLM_VALIDATED_PROMPT_SENT", "Sending validated prompt to LLM", {
                "model": self.model,
                "original_prompt": prompt,
                "enhanced_prompt": schema_prompt,
                "response_model": response_model.__name__,
                "max_retries": max_retries
            })
        
        for attempt in range(max_retries):
            try:
                # Generate response
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": schema_prompt}],
                    **self.default_params
                )
                
                content = response.choices[0].message.content.strip()
                
                # Use robust JSON parser instead of basic cleaning
                try:
                    json_data = RobustJSONParser.parse(content)
                except ValueError as e:
                    if attempt < max_retries - 1:
                        # Retry with clearer instructions
                        schema_prompt = self._enhance_prompt_with_schema(
                            prompt, response_model, include_error_instruction=True
                        )
                        if self.debug_callback:
                            self.debug_callback("LLM_VALIDATION_RETRY", f"JSON parsing failed, retrying (attempt {attempt + 1})", {
                                "error": str(e),
                                "raw_response": content,
                                "attempt": attempt + 1
                            })
                        continue
                    else:
                        if self.debug_callback:
                            self.debug_callback("LLM_VALIDATION_ERROR", f"JSON parsing failed after all retries", {
                                "error": str(e),
                                "raw_response": content,
                                "max_retries": max_retries
                            })
                        raise ValidationError(f"Invalid JSON after {max_retries} attempts: {e}")
                
                # Validate against Pydantic model
                validated_response = response_model(**json_data)
                
                # Log successful validation if debug callback is available
                if self.debug_callback:
                    self.debug_callback("LLM_VALIDATED_RESPONSE_RECEIVED", "Received and validated response from LLM", {
                        "model": self.model,
                        "response_model": response_model.__name__,
                        "attempt": attempt + 1,
                        "validated_data": json_data,
                        "usage": getattr(response, 'usage', {})
                    })
                
                return validated_response
                
            except ValidationError as e:
                if attempt < max_retries - 1:
                    # Add validation error to prompt for next attempt
                    error_prompt = f"{schema_prompt}\n\nPREVIOUS ATTEMPT FAILED WITH ERROR: {str(e)}\nPlease fix the format and try again."
                    schema_prompt = error_prompt
                    if self.debug_callback:
                        self.debug_callback("LLM_VALIDATION_RETRY", f"Validation failed, retrying (attempt {attempt + 1})", {
                            "validation_error": str(e),
                            "attempt": attempt + 1
                        })
                    continue
                else:
                    # Final attempt failed
                    if self.debug_callback:
                        self.debug_callback("LLM_VALIDATION_ERROR", f"Validation failed after all retries", {
                            "validation_error": str(e),
                            "max_retries": max_retries
                        })
                    raise ValidationError(f"Response validation failed after {max_retries} attempts: {e}")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    if self.debug_callback:
                        self.debug_callback("LLM_GENERATION_RETRY", f"LLM generation failed, retrying (attempt {attempt + 1})", {
                            "error": str(e),
                            "attempt": attempt + 1
                        })
                    continue
                else:
                    if self.debug_callback:
                        self.debug_callback("LLM_GENERATION_ERROR", f"LLM generation failed after all retries", {
                            "error": str(e),
                            "max_retries": max_retries
                        })
                    raise LLMError(f"LLM generation failed after {max_retries} attempts: {e}")
        
        # This should never be reached
        raise LLMError("Unexpected error in generate_validated_response")
    
    def _enhance_prompt_with_schema(self, prompt: str, response_model: Type[BaseModel], 
                                  include_error_instruction: bool = False) -> str:
        """Add schema information to the prompt."""
        # Use Pydantic v2 method instead of deprecated v1 method
        schema = response_model.model_json_schema()
        
        enhanced_prompt = f"""{prompt}

REQUIRED RESPONSE FORMAT:
You must respond with valid JSON that matches this exact schema:

{json.dumps(schema, indent=2)}

CRITICAL REQUIREMENTS:
- Respond with ONLY valid JSON, no additional text or formatting
- All required fields must be present
- Field types must match exactly (strings, arrays, objects, etc.)
- Follow any validation rules specified in the schema"""

        if include_error_instruction:
            enhanced_prompt += """

IMPORTANT: Your previous response had formatting errors. Please ensure:
- No markdown code blocks (```json)
- No trailing commas
- Proper string escaping
- All quotes are double quotes, not single quotes"""

        return enhanced_prompt
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a standard text response.
        
        Args:
            prompt: The prompt to send to the LLM
            **kwargs: Additional parameters to override defaults
            
        Returns:
            Generated response text
        """
        params = {**self.default_params, **kwargs}
        
        # Log the prompt if debug callback is available
        if self.debug_callback:
            self.debug_callback("LLM_PROMPT_SENT", "Sending prompt to LLM", {
                "model": self.model,
                "prompt": prompt,
                "parameters": params
            })
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **params
            )
            
            response_content = response.choices[0].message.content
            
            # Log the response if debug callback is available
            if self.debug_callback:
                self.debug_callback("LLM_RESPONSE_RECEIVED", "Received response from LLM", {
                    "model": self.model,
                    "response": response_content,
                    "usage": getattr(response, 'usage', {})
                })
            
            return response_content
            
        except Exception as e:
            if self.debug_callback:
                self.debug_callback("LLM_ERROR", f"Error generating LLM response: {str(e)}", {
                    "model": self.model,
                    "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    "error": str(e)
                })
            raise LLMError(f"Error generating LLM response: {str(e)}")
    
    async def generate_with_system_message(self, system_message: str, user_prompt: str, **kwargs) -> str:
        """
        Generate response with a system message to set context/behavior.
        
        Args:
            system_message: System message to set LLM behavior
            user_prompt: The user's prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        params = {**self.default_params, **kwargs}
        
        # Log the system message prompt if debug callback is available
        if self.debug_callback:
            self.debug_callback("LLM_SYSTEM_PROMPT_SENT", "Sending system message prompt to LLM", {
                "model": self.model,
                "system_message": system_message,
                "user_prompt": user_prompt,
                "parameters": params
            })
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt}
                ],
                **params
            )
            
            response_content = response.choices[0].message.content
            
            # Log the response if debug callback is available
            if self.debug_callback:
                self.debug_callback("LLM_SYSTEM_RESPONSE_RECEIVED", "Received response from LLM with system message", {
                    "model": self.model,
                    "response": response_content,
                    "usage": getattr(response, 'usage', {})
                })
            
            return response_content
            
        except Exception as e:
            if self.debug_callback:
                self.debug_callback("LLM_SYSTEM_ERROR", f"Error generating LLM response with system message: {str(e)}", {
                    "model": self.model,
                    "system_message": system_message[:200] + "..." if len(system_message) > 200 else system_message,
                    "user_prompt": user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt,
                    "error": str(e)
                })
            raise LLMError(f"Error generating LLM response with system message: {str(e)}")
    
    async def generate_character_targeting_response(self, prompt: str):
        """Specialized method for character targeting with extra validation."""
        from .response_models import CharacterTargetResponse
        
        # Add extra instructions specific to character targeting
        enhanced_prompt = f"""{prompt}

CRITICAL INSTRUCTIONS FOR RESPONSE:
1. You MUST provide both 'file_fields' and 'reasoning' in your response
2. file_fields must be a dictionary where:
   - Keys are filenames (e.g., "character.json", "inventory_list.json")
   - Values are arrays of field names (e.g., ["combat_stats", "ability_scores"])
3. reasoning must be a detailed explanation of your choices
4. Do not omit either field - both are required

Example format:
{{
  "file_fields": {{
    "character.json": ["combat_stats", "ability_scores"],
    "inventory_list.json": ["inventory.weapons"]
  }},
  "reasoning": "Need combat stats for AC calculation and weapons for damage output"
}}"""

        return await self._generate_with_function_calling(enhanced_prompt, CharacterTargetResponse)
    
    def set_default_params(self, **params):
        """Update default parameters for LLM calls."""
        self.default_params.update(params)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model configuration."""
        return {
            "model": self.model,
            "default_params": self.default_params,
            "api_key_set": bool(self.api_key)
        }