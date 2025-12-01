#!/usr/bin/env python
"""Check categories for missing sections"""
from src.rag.rulebook.rulebook_storage import RulebookStorage

s = RulebookStorage()
s.load_from_disk()

sections = [
    'armor-class', 'shield', 'heavy-armor', 
    'hit-points', 'hit-points-and-hit-dice', 
    'section-fighter', 'section-barbarian', 
    'attack-rolls-and-damage', 'section-damage-and-healing',
    'section-making-an-attack', 'extra-attack'
]

print("SECTION CATEGORY ANALYSIS")
print("=" * 60)
for sid in sections:
    if sid in s.sections:
        sec = s.sections[sid]
        cats = [c.name for c in sec.categories]
        print(f"{sid:30} → {cats}")
    else:
        print(f"{sid:30} → NOT FOUND")
