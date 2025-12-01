from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, AsyncGenerator
from dataclasses import dataclass
import json
import asyncio

# OpenAI + Anthropic async SDKs
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from ..config import get_config


@dataclass
class LLMResponse:
    content: str
    success: bool = True
    error: Optional[str] = None
    model_used: Optional[str] = None


class LLMClient(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse: ...
    @abstractmethod
    async def generate_json_response(self, prompt: str, **kwargs) -> Dict[str, Any]: ...
    @abstractmethod
    async def generate_response_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]: ...


class OpenAILLMClient(LLMClient):
    """
    OpenAI client (async).
    - Uses Chat Completions for compatibility (Responses API also available).
    - Supports JSON mode via response_format={"type": "json_object"}.
    - Fully controlled by config.py settings
    """
    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None, use_router_model: bool = False):
        cfg = get_config()
        self.api_key = api_key or cfg.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Use config models unless explicitly overridden
        if default_model:
            self.default_model = default_model
        elif use_router_model:
            self.default_model = cfg.openai_router_model
        else:
            self.default_model = cfg.openai_final_model
            
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        try:
            model = kwargs.get("model", self.default_model)
            cfg = get_config()
            
            # Base parameters
            base_params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            # Add parameters based on model type
            if cfg.is_reasoning_model(model):
                # Reasoning models (o1, gpt-5 family) - no temperature/max_tokens
                max_completion_tokens = kwargs.get("max_completion_tokens", 2000)
                if max_completion_tokens:
                    base_params["max_completion_tokens"] = max_completion_tokens
                    
                # Add stop sequences if provided
                stop = kwargs.get("stop")
                if stop:
                    base_params["stop"] = stop
            else:
                # Standard models - support temperature and max_tokens
                base_params["temperature"] = kwargs.get("temperature", 0.3)
                base_params["max_tokens"] = kwargs.get("max_tokens", 2000)
                
                stop = kwargs.get("stop")
                if stop:
                    base_params["stop"] = stop

            resp = await self.client.chat.completions.create(**base_params)
            content = resp.choices[0].message.content or ""
            return LLMResponse(content=content, model_used=model)
        except Exception as e:
            return LLMResponse(content="", success=False, error=str(e), model_used=kwargs.get("model", self.default_model))

    async def generate_response_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream response chunks from OpenAI.
        Yields text chunks as they arrive.
        
        Args:
            prompt: The user prompt (current message)
            conversation_history: Optional list of previous conversation turns
            **kwargs: Additional parameters
        """
        try:
            model = kwargs.get("model", self.default_model)
            cfg = get_config()
            conversation_history = kwargs.get("conversation_history", [])
            
            # Build messages array with conversation history
            messages = []
            
            # Add previous conversation turns (excluding the current prompt)
            for turn in conversation_history:
                messages.append({
                    "role": turn["role"],
                    "content": turn["content"]
                })
            
            # Add current user prompt
            messages.append({"role": "user", "content": prompt})
            
            # Base parameters
            base_params = {
                "model": model,
                "messages": messages,
                "stream": True
            }
            
            # Add parameters based on model type
            if cfg.is_reasoning_model(model):
                # Reasoning models - no temperature/max_tokens
                max_completion_tokens = kwargs.get("max_completion_tokens", 2000)
                if max_completion_tokens:
                    base_params["max_completion_tokens"] = max_completion_tokens
                    
                stop = kwargs.get("stop")
                if stop:
                    base_params["stop"] = stop
            else:
                # Standard models - support temperature and max_tokens
                base_params["temperature"] = kwargs.get("temperature", 0.3)
                base_params["max_tokens"] = kwargs.get("max_tokens", 2000)
                
                stop = kwargs.get("stop")
                if stop:
                    base_params["stop"] = stop

            stream = await self.client.chat.completions.create(**base_params)
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    async def generate_json_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Prefer OpenAI JSON mode for well-formed JSON.
        Falls back to parsing plain text if provider rejects response_format (e.g., non-OpenAI compat hosts).
        Handles reasoning models that don't support temperature/max_tokens.
        """
        model = kwargs.get("model", self.default_model)
        cfg = get_config()
        
        try:
            # Base parameters
            base_params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}  # JSON mode
            }
            
            # Add parameters based on model type
            if cfg.is_reasoning_model(model):
                # Reasoning models - use max_completion_tokens instead
                max_completion_tokens = kwargs.get("max_completion_tokens", kwargs.get("max_tokens", 1000))
                if max_completion_tokens:
                    base_params["max_completion_tokens"] = max_completion_tokens
            else:
                # Standard models - use temperature and max_tokens
                base_params["max_tokens"] = kwargs.get("max_tokens", 1000)
                base_params["temperature"] = kwargs.get("temperature", 0)

            resp = await self.client.chat.completions.create(**base_params)
            raw = resp.choices[0].message.content or "{}"
            return json.loads(raw)
        except Exception:
            # Retry once without response_format and parse best-effort
            try:
                fallback_params = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}]
                }
                
                # Add appropriate parameters for fallback
                if cfg.is_reasoning_model(model):
                    max_completion_tokens = kwargs.get("max_completion_tokens", kwargs.get("max_tokens", 1000))
                    if max_completion_tokens:
                        fallback_params["max_completion_tokens"] = max_completion_tokens
                else:
                    fallback_params["max_tokens"] = kwargs.get("max_tokens", 1000)
                    fallback_params["temperature"] = kwargs.get("temperature", 0)
                
                fallback = await self.client.chat.completions.create(**fallback_params)
                return json.loads(fallback.choices[0].message.content or "{}")
            except Exception as e2:
                return {"error": str(e2)}


class AnthropicLLMClient(LLMClient):
    """
    Anthropic client (async).
    - Uses Messages API.
    - Defaults to tool-based structured output for JSON responses (enforces schema).
    - Fully controlled by config.py settings
    """
    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None, use_router_model: bool = False):
        cfg = get_config()
        self.api_key = api_key or cfg.anthropic_api_key
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        # Use config models unless explicitly overridden
        if default_model:
            self.default_model = default_model
        elif use_router_model:
            self.default_model = cfg.anthropic_router_model
        else:
            self.default_model = cfg.anthropic_final_model
            
        self.client = AsyncAnthropic(api_key=self.api_key)

    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        try:
            model = kwargs.get("model", self.default_model)
            max_tokens = kwargs.get("max_tokens", 2000)
            temperature = kwargs.get("temperature", 0.3)
            stop = kwargs.get("stop")

            msg = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                stop_sequences=stop if isinstance(stop, list) else ([stop] if stop else None),
                messages=[{"role": "user", "content": prompt}]
            )
            # Claude returns a list of content blocks; pick first text block
            text = ""
            for block in msg.content:
                if getattr(block, "type", None) == "text" and hasattr(block, "text"):
                    text = block.text
                    break
            return LLMResponse(content=text, model_used=model)
        except Exception as e:
            return LLMResponse(content="", success=False, error=str(e), model_used=kwargs.get("model", self.default_model))

    async def generate_response_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream response chunks from Anthropic.
        Yields text chunks as they arrive.
        
        Args:
            prompt: The user prompt (current message)
            conversation_history: Optional list of previous conversation turns
            **kwargs: Additional parameters
        """
        try:
            model = kwargs.get("model", self.default_model)
            max_tokens = kwargs.get("max_tokens", 2000)
            temperature = kwargs.get("temperature", 0.3)
            stop = kwargs.get("stop")
            conversation_history = kwargs.get("conversation_history", [])
            
            # Build messages array with conversation history
            messages = []
            
            # Add previous conversation turns (excluding the current prompt)
            for turn in conversation_history:
                messages.append({
                    "role": turn["role"],
                    "content": turn["content"]
                })
            
            # Add current user prompt
            messages.append({"role": "user", "content": prompt})

            async with self.client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                stop_sequences=stop if isinstance(stop, list) else ([stop] if stop else None),
                messages=messages
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    async def generate_json_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Defaults to tool-based structured output for reliable JSON (recommended).
        Pass `use_prompt_only=True` to fallback to prompt-based JSON parsing.
        Pass `json_schema` to enforce a specific schema via tools.
        """
        model = kwargs.get("model", self.default_model)
        json_schema = kwargs.get("json_schema")
        max_tokens = kwargs.get("max_tokens", 2000)
        use_prompt_only = kwargs.get("use_prompt_only", False)

        try:
            if not use_prompt_only:
                # Default to tool-based JSON for reliability
                if not json_schema:
                    # Generic JSON schema if none provided
                    json_schema = {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": True
                    }
                
                # JSON via tools pattern (schema enforcement)
                tools = [{
                    "name": "return_json",
                    "description": "Return the result as JSON matching the provided schema.",
                    "input_schema": json_schema,
                }]
                tool_choice = {"type": "tool", "name": "return_json"}
                msg = await self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    tools=tools,
                    tool_choice=tool_choice,
                    messages=[{"role": "user", "content": prompt}]
                )
                # Extract tool call arguments
                for block in msg.content:
                    if block.type == "tool_use" and block.name == "return_json":
                        return block.input  # already a dict
                # Fallback if tool not used (rare)
                
            # Fallback: prompt-only JSON
            strict_prompt = (
                "Return ONLY valid JSON. Do not include any prose. "
                "Escape all newlines and quotes within string values if needed."
            )
            msg = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0,
                messages=[{"role": "user", "content": f"{prompt}\n\n{strict_prompt}"}]
            )
            raw = ""
            for block in msg.content:
                if getattr(block, "type", None) == "text":
                    raw = block.text
                    break
            return json.loads(raw)
        except Exception as e:
            return {"error": str(e)}


class LLMClientFactory:
    @staticmethod
    def create_client(provider: str = "openai", use_router_model: bool = False, **kwargs) -> LLMClient:
        """
        Create an LLM client with config-driven model selection.
        
        Args:
            provider: "openai" or "anthropic"
            use_router_model: If True, use router model from config, otherwise use final model
            **kwargs: Additional arguments to pass to client constructor
        """
        p = provider.lower()
        if p == "openai":
            return OpenAILLMClient(use_router_model=use_router_model, **kwargs)
        if p == "anthropic":
            return AnthropicLLMClient(use_router_model=use_router_model, **kwargs)
        raise ValueError(f"Unsupported LLM provider: {provider}")

    @staticmethod
    def create_router_client(provider: Optional[str] = None) -> LLMClient:
        """Create a client optimized for routing decisions (fast, cheaper models)"""
        cfg = get_config()
        provider = provider or cfg.router_llm_provider
        return LLMClientFactory.create_client(provider, use_router_model=True)
    
    @staticmethod
    def create_final_response_client(provider: Optional[str] = None) -> LLMClient:
        """Create a client optimized for final responses (higher quality models)"""
        cfg = get_config()
        provider = provider or cfg.final_response_llm_provider
        return LLMClientFactory.create_client(provider, use_router_model=False)

    @staticmethod
    def create_default_clients() -> Dict[str, LLMClient]:
        """Create all available clients based on config"""
        cfg = get_config()
        out: Dict[str, LLMClient] = {}
        
        if cfg.openai_api_key:
            out["openai"] = OpenAILLMClient(use_router_model=False)  # Final model
            out["openai_router"] = OpenAILLMClient(use_router_model=True)  # Router model
            
        if cfg.anthropic_api_key:
            out["anthropic"] = AnthropicLLMClient(use_router_model=False)  # Final model
            out["anthropic_router"] = AnthropicLLMClient(use_router_model=True)  # Router model
            
        return out
