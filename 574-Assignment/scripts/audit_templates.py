"""
Audit script to analyze template coverage and identify gaps.
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.templates.character_templates import CHARACTER_TEMPLATES
from data.templates.session_templates import SESSION_TEMPLATES
from data.templates.rulebook_templates import RULEBOOK_TEMPLATES
from data.templates.multi_tool_templates import (
    CHARACTER_RULEBOOK_TEMPLATES, 
    CHARACTER_SESSION_TEMPLATES, 
    SESSION_RULEBOOK_TEMPLATES, 
    THREE_TOOL_TEMPLATES
)

def main():
    print('=' * 70)
    print('SINGLE-TOOL TEMPLATE COUNTS')
    print('=' * 70)
    
    # Character templates
    print('\n📊 CHARACTER_DATA (10 intents):')
    char_counts = {k: len(v) for k, v in CHARACTER_TEMPLATES.items()}
    for intent, count in sorted(char_counts.items(), key=lambda x: -x[1]):
        status = "✓" if count >= 15 else "⚠️" if count >= 10 else "❌"
        print(f'  {status} {intent}: {count}')
    print(f'  TOTAL: {sum(char_counts.values())} templates')
    print(f'  MIN: {min(char_counts.values())}, MAX: {max(char_counts.values())}')
    
    # Session templates
    print('\n📊 SESSION_NOTES (20 intents):')
    session_counts = {k: len(v) for k, v in SESSION_TEMPLATES.items()}
    for intent, count in sorted(session_counts.items(), key=lambda x: -x[1]):
        status = "✓" if count >= 15 else "⚠️" if count >= 10 else "❌"
        print(f'  {status} {intent}: {count}')
    print(f'  TOTAL: {sum(session_counts.values())} templates')
    print(f'  MIN: {min(session_counts.values())}, MAX: {max(session_counts.values())}')
    
    # Rulebook templates
    print('\n📊 RULEBOOK (30 intents):')
    rule_counts = {k: len(v) for k, v in RULEBOOK_TEMPLATES.items()}
    for intent, count in sorted(rule_counts.items(), key=lambda x: -x[1]):
        status = "✓" if count >= 15 else "⚠️" if count >= 10 else "❌"
        print(f'  {status} {intent}: {count}')
    print(f'  TOTAL: {sum(rule_counts.values())} templates')
    print(f'  MIN: {min(rule_counts.values())}, MAX: {max(rule_counts.values())}')
    
    print('\n' + '=' * 70)
    print('MULTI-TOOL INTENT COVERAGE')
    print('=' * 70)
    
    # Analyze multi-tool templates for intent coverage
    multi_intent_counts = defaultdict(lambda: defaultdict(int))
    
    all_multi = (CHARACTER_RULEBOOK_TEMPLATES + CHARACTER_SESSION_TEMPLATES + 
                 SESSION_RULEBOOK_TEMPLATES + THREE_TOOL_TEMPLATES)
    
    for t in all_multi:
        for tool, intent in t['intents'].items():
            multi_intent_counts[tool][intent] += 1
    
    print('\n📊 INTENT COVERAGE IN MULTI-TOOL TEMPLATES:')
    
    tool_intents = {
        'character_data': set(CHARACTER_TEMPLATES.keys()),
        'session_notes': set(SESSION_TEMPLATES.keys()),
        'rulebook': set(RULEBOOK_TEMPLATES.keys()),
    }
    
    for tool, all_intents in tool_intents.items():
        print(f'\n  {tool.upper()}:')
        
        covered = set(multi_intent_counts[tool].keys())
        missing = all_intents - covered
        
        for intent in sorted(covered, key=lambda x: -multi_intent_counts[tool][x]):
            count = multi_intent_counts[tool][intent]
            status = "✓" if count >= 5 else "⚠️" if count >= 2 else "❌"
            print(f'    {status} {intent}: {count}')
        
        if missing:
            print(f'\n    --- MISSING FROM MULTI-TOOL ({len(missing)}): ---')
            for intent in sorted(missing):
                print(f'    ✗ {intent}: 0')
    
    print('\n' + '=' * 70)
    print('SUMMARY')
    print('=' * 70)
    
    total_single = sum(char_counts.values()) + sum(session_counts.values()) + sum(rule_counts.values())
    total_multi = len(all_multi)
    
    print(f'\nSingle-tool templates: {total_single}')
    print(f'  - character_data: {sum(char_counts.values())}')
    print(f'  - session_notes: {sum(session_counts.values())}')
    print(f'  - rulebook: {sum(rule_counts.values())}')
    
    print(f'\nMulti-tool templates: {total_multi}')
    print(f'  - character+rulebook: {len(CHARACTER_RULEBOOK_TEMPLATES)}')
    print(f'  - character+session: {len(CHARACTER_SESSION_TEMPLATES)}')
    print(f'  - session+rulebook: {len(SESSION_RULEBOOK_TEMPLATES)}')
    print(f'  - 3-tool: {len(THREE_TOOL_TEMPLATES)}')
    
    print(f'\nGRAND TOTAL: {total_single + total_multi} templates')
    
    # Recommendations
    print('\n' + '=' * 70)
    print('RECOMMENDATIONS')
    print('=' * 70)
    
    target_per_intent = 20
    
    print(f'\nTo balance at {target_per_intent} templates per intent:')
    
    print('\n  CHARACTER_DATA needs:')
    for intent, count in char_counts.items():
        if count < target_per_intent:
            print(f'    {intent}: +{target_per_intent - count} templates')
    
    print('\n  SESSION_NOTES needs:')
    for intent, count in session_counts.items():
        if count < target_per_intent:
            print(f'    {intent}: +{target_per_intent - count} templates')
    
    print('\n  RULEBOOK needs:')
    for intent, count in rule_counts.items():
        if count < target_per_intent:
            print(f'    {intent}: +{target_per_intent - count} templates')
    
    # Total new templates needed
    char_needed = sum(max(0, target_per_intent - c) for c in char_counts.values())
    session_needed = sum(max(0, target_per_intent - c) for c in session_counts.values())
    rule_needed = sum(max(0, target_per_intent - c) for c in rule_counts.values())
    
    print(f'\n  TOTAL NEW TEMPLATES NEEDED: {char_needed + session_needed + rule_needed}')
    print(f'    - character_data: {char_needed}')
    print(f'    - session_notes: {session_needed}')
    print(f'    - rulebook: {rule_needed}')


if __name__ == "__main__":
    main()
