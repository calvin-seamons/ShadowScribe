"""
ShadowScribe 2.0 - RPG Character Management System

A comprehensive tool for managing RPG characters with support for
character creation, inspection, and data management.
"""

__version__ = "2.0.0"
__author__ = "Calvin Seamons"

# Import main classes for easy access
from .rag.character.character_types import Character
from .rag.character.character_manager import CharacterManager
from .utils.character_inspector import CharacterInspector

__all__ = ["Character", "CharacterManager", "CharacterInspector"]
