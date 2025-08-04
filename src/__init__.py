"""
ShadowScribe - Intelligent D&D 5e Assistant with Multi-Pass LLM Engine
"""

from .engine import ShadowScribeEngine
from .knowledge import KnowledgeBase
from .utils import LLMClient, ValidationHelper

__version__ = "1.0.0"
__all__ = [
    'ShadowScribeEngine',
    'KnowledgeBase', 
    'LLMClient',
    'ValidationHelper'
]
