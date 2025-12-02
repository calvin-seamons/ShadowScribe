"""
Query Normalization Utilities

Applies entity placeholders to user queries for training data generalization.
Used by both CentralEngine for routing and WebSocket for feedback recording.
"""

import re
from typing import List, Optional


def apply_entity_placeholders(
    query: str,
    character_name: str,
    entities: Optional[List[dict]]
) -> str:
    """
    Replace entity names with placeholder tokens for training generalization.

    Replaces:
    - {CHARACTER}: The player character name
    - {PARTY_MEMBER}: Other party members
    - {NPC}: Non-player characters
    - {ITEM}: Items, weapons, armor
    - {SPELL}: Spell names
    - {LOCATION}: Location names

    Uses case-insensitive matching and replaces longer names first.

    Args:
        query: The original user query
        character_name: The player character's name
        entities: List of extracted entities from gazetteer NER
                  Each entity should have 'text'/'name' and 'type' fields

    Returns:
        Query with entity names replaced by placeholders
    """
    replacements = []

    # Always add character_name as {CHARACTER}
    if character_name:
        replacements.append((character_name, '{CHARACTER}'))
        # Add first name and 4-char nickname
        parts = character_name.split()
        if len(parts) > 0:
            first_name = parts[0]
            if first_name != character_name:
                replacements.append((first_name, '{CHARACTER}'))
            if len(first_name) > 4:
                replacements.append((first_name[:4], '{CHARACTER}'))

    # Add entities from extraction
    if entities:
        for entity in entities:
            entity_type = entity.get('type', '')
            entity_text = entity.get('text', '') or entity.get('name', '')

            if not entity_text:
                continue

            # Map entity types to placeholder tokens
            placeholder = None
            if entity_type == 'CHARACTER':
                placeholder = '{CHARACTER}'
            elif entity_type == 'PARTY_MEMBER':
                placeholder = '{PARTY_MEMBER}'
            elif entity_type == 'NPC':
                placeholder = '{NPC}'
            elif entity_type == 'ITEM':
                placeholder = '{ITEM}'
            elif entity_type == 'SPELL':
                placeholder = '{SPELL}'
            elif entity_type == 'LOCATION':
                placeholder = '{LOCATION}'
            elif entity_type == 'MONSTER':
                placeholder = '{MONSTER}'
            elif entity_type == 'CONDITION':
                placeholder = '{CONDITION}'
            elif entity_type == 'CLASS':
                placeholder = '{CLASS}'
            elif entity_type == 'RACE':
                placeholder = '{RACE}'
            elif entity_type == 'FEATURE':
                placeholder = '{FEATURE}'

            if placeholder:
                replacements.append((entity_text, placeholder))

    # Sort by length descending (replace longer names first)
    replacements.sort(key=lambda x: len(x[0]), reverse=True)

    # Apply case-insensitive replacements
    result = query
    for original_text, placeholder in replacements:
        pattern = re.compile(re.escape(original_text), re.IGNORECASE)
        result = pattern.sub(placeholder, result)

    return result
