"""
LLM Client - Handles communication with language models (OpenAI, etc.)
"""

from typing import Dict, Any, Optional, Type, TypeVar
import json
import asyncio
from openai import AsyncOpenAI
import os
from pydantic import BaseModel, ValidationError

T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """
    Handles communication with language models for the ShadowScribe engine.
    Supports structured responses with Pydantic validation.
    """
    
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        """Initialize LLM client with model and API configuration."""
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Default parameters
        self.default_params = {
            "temperature": 0.3,  # Lower for more consistent structured responses
            "max_tokens": 2000,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
    
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
        
        for attempt in range(max_retries):
            try:
                # Generate response
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": schema_prompt}],
                    **self.default_params
                )
                
                content = response.choices[0].message.content.strip()
                
                # Clean up response (remove markdown code blocks if present)
                content = self._clean_json_response(content)
                
                # Parse JSON
                try:
                    json_data = json.loads(content)
                except json.JSONDecodeError as e:
                    if attempt < max_retries - 1:
                        # Retry with clearer instructions
                        schema_prompt = self._enhance_prompt_with_schema(
                            prompt, response_model, include_error_instruction=True
                        )
                        continue
                    else:
                        raise ValidationError(f"Invalid JSON after {max_retries} attempts: {e}")
                
                # Validate against Pydantic model
                validated_response = response_model(**json_data)
                return validated_response
                
            except ValidationError as e:
                if attempt < max_retries - 1:
                    # Add validation error to prompt for next attempt
                    error_prompt = f"{schema_prompt}\n\nPREVIOUS ATTEMPT FAILED WITH ERROR: {str(e)}\nPlease fix the format and try again."
                    schema_prompt = error_prompt
                    continue
                else:
                    # Final attempt failed
                    raise ValidationError(f"Response validation failed after {max_retries} attempts: {e}")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    continue
                else:
                    raise Exception(f"LLM generation failed after {max_retries} attempts: {e}")
        
        # This should never be reached
        raise Exception("Unexpected error in generate_validated_response")
    
    def _enhance_prompt_with_schema(self, prompt: str, response_model: Type[BaseModel], 
                                  include_error_instruction: bool = False) -> str:
        """Add schema information to the prompt."""
        schema = response_model.schema()
        
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
    
    def _clean_json_response(self, content: str) -> str:
        """Clean up LLM response to extract valid JSON."""
        # Remove markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        # Remove any leading/trailing whitespace
        content = content.strip()
        
        # Find JSON object boundaries
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and start_idx <= end_idx:
            content = content[start_idx:end_idx + 1]
        
        return content
    
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
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **params
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Error generating LLM response: {str(e)}")
    
    async def generate_structured_response(self, prompt: str, response_format: str = "json", **kwargs) -> str:
        """
        Generate a structured response (JSON, etc.).
        
        Args:
            prompt: The prompt to send to the LLM
            response_format: Expected response format ("json", "yaml", etc.)
            **kwargs: Additional parameters to override defaults
            
        Returns:
            Generated response in the specified format
        """
        # Add format instruction to prompt
        if response_format == "json":
            format_instruction = "\n\nPlease respond with valid JSON only, no additional text."
            enhanced_prompt = prompt + format_instruction
        else:
            enhanced_prompt = prompt
        
        params = {**self.default_params, **kwargs}
        
        # Lower temperature for structured responses to improve consistency
        params["temperature"] = 0.3
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": enhanced_prompt}],
                **params
            )
            
            content = response.choices[0].message.content
            
            # Validate JSON if requested
            if response_format == "json":
                try:
                    json.loads(content)  # Validate JSON
                except json.JSONDecodeError as e:
                    raise Exception(f"LLM returned invalid JSON: {str(e)}")
            
            return content
            
        except Exception as e:
            raise Exception(f"Error generating structured LLM response: {str(e)}")
    
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
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt}
                ],
                **params
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Error generating LLM response with system message: {str(e)}")
    
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