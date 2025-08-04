"""
Prompt Templates module - Contains all prompt templates for the LLM engine.
"""

from .router_prompts import RouterPrompts
from .response_prompts import ResponsePrompts

__all__ = [
    'RouterPrompts',
    'ResponsePrompts'
]