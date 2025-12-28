"""
D&D 5e RAG System - Character, Rulebook, and Session Notes
"""

from .character import Character, CharacterManager, CharacterQueryRouter
from .rulebook import RulebookCategory, RulebookQueryIntent, RulebookStorage
from .session_notes import SessionNotesStorage, SessionNotesQueryRouter, CampaignSessionNotesStorage
from .context_assembler import ContextAssembler

__all__ = [
    # Character module
    'Character',
    'CharacterManager',
    'CharacterQueryRouter',

    # Rulebook module
    'RulebookCategory',
    'RulebookQueryIntent',
    'RulebookStorage',

    # Session notes module
    'SessionNotesStorage',
    'SessionNotesQueryRouter',
    'CampaignSessionNotesStorage',

    # Context assembly
    'ContextAssembler',
]
