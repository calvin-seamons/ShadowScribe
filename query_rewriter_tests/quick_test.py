"""
Quick standalone test of the QueryRewriter without the full RAG pipeline.

This uses mocked conversation history to test the rewriter in isolation.
Useful for quick iteration on the prompt or model settings.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_quick_tests():
    """Run a few quick tests with mocked responses"""
    
    print("=" * 60)
    print("Quick Query Rewriter Test (Mocked History)")
    print("=" * 60)
    
    from query_rewriter_tests.query_rewriter import QueryRewriter
    
    print("\nLoading QueryRewriter...")
    rewriter = QueryRewriter()
    print("Model loaded!\n")
    
    # Test cases with mocked responses
    test_cases = [
        # Test 1: Simple pronoun - "its"
        {
            "name": "Pronoun 'its' → Fireball",
            "history": [
                {"role": "user", "content": "What is Fireball?"},
                {"role": "assistant", "content": "Fireball is a 3rd-level evocation spell that creates a 20-foot radius explosion dealing 8d6 fire damage. Creatures in the area make a Dexterity saving throw for half damage. It's one of the most iconic and powerful AOE spells in D&D 5e."}
            ],
            "q2": "What's its damage at higher levels?",
            "expected_contains": ["fireball", "damage", "higher"]
        },
        
        # Test 2: Entity continuation - "her"
        {
            "name": "Pronoun 'her' → Elara (NPC)",
            "history": [
                {"role": "user", "content": "Who is Elara?"},
                {"role": "assistant", "content": "Elara is an elven ranger NPC you encountered in session 3. She was the one who guided your party through the Mistwood Forest and warned you about the vampire Lord Strahd's presence in the region. She seemed knowledgeable about the local area."}
            ],
            "q2": "When did I first meet her and what did she want?",
            "expected_contains": ["elara", "meet", "want"]
        },
        
        # Test 3: "there" referring to location
        {
            "name": "Pronoun 'there' → Shadowfell",
            "history": [
                {"role": "user", "content": "Tell me about the Shadowfell"},
                {"role": "assistant", "content": "The Shadowfell is a dark, twisted mirror of the Material Plane. It's a realm of darkness, despair, and undeath. Creatures like shadows, wraiths, and the Raven Queen make their home there. Colors are muted and emotions tend toward melancholy."}
            ],
            "q2": "What creatures live there?",
            "expected_contains": ["shadowfell", "creature"]
        },
        
        # Test 4: "the weapon" referring to named item
        {
            "name": "Reference 'the weapon' → Eldaryth of Regret",
            "history": [
                {"role": "user", "content": "What's special about Eldaryth of Regret?"},
                {"role": "assistant", "content": "Eldaryth of Regret is your sentient longsword. It was forged by a grief-stricken elven smith and contains the echo of lost souls. It grants +2 to attack and damage rolls, and once per day can cast Speak with Dead. The sword occasionally whispers melancholic thoughts."}
            ],
            "q2": "How did I get the weapon?",
            "expected_contains": ["eldaryth", "regret", "get", "obtain"]
        },
        
        # Test 5: Already standalone (should not change much)
        {
            "name": "Already standalone → minimal change",
            "history": [
                {"role": "user", "content": "What's my AC?"},
                {"role": "assistant", "content": "Your AC is 18 with your plate armor equipped."}
            ],
            "q2": "How does flanking work in 5e?",
            "expected_contains": ["flanking", "5e"]
        },
        
        # Test 6: Complex multi-reference
        {
            "name": "Multiple references in one question",
            "history": [
                {"role": "user", "content": "Compare my longsword to my dagger"},
                {"role": "assistant", "content": "Your longsword deals 1d8 slashing damage (or 1d10 two-handed) and has the versatile property. Your dagger deals 1d4 piercing damage but has the finesse, light, and thrown properties. The longsword does more damage but the dagger is more versatile for different situations."}
            ],
            "q2": "Which one is better for a sneak attack?",
            "expected_contains": ["longsword", "dagger", "sneak attack"]
        },
        
        # Test 7: Implicit reference
        {
            "name": "Implicit reference - 'the save DC'",
            "history": [
                {"role": "user", "content": "How do I calculate my spell attack bonus?"},
                {"role": "assistant", "content": "Your spell attack bonus is calculated as your proficiency bonus + your spellcasting ability modifier. As a Warlock, you use Charisma, so it's +3 proficiency + +4 Charisma = +7 spell attack bonus."}
            ],
            "q2": "And the save DC?",
            "expected_contains": ["spell", "save", "dc"]
        },
        
        # Test 8: Topic switch with reference
        {
            "name": "Topic switch - 'Speaking of vampires'",
            "history": [
                {"role": "user", "content": "Tell me about the combat in session 5 where we fought the vampire"},
                {"role": "assistant", "content": "In session 5, your party fought Count Vasili, a vampire lord. The battle was intense - he nearly killed the cleric with his bite attack. You eventually drove him off using radiant damage from your paladin's smites and the cleric's Spirit Guardians."}
            ],
            "q2": "Speaking of vampires, what are their weaknesses according to the rules?",
            "expected_contains": ["vampire", "weakness"]
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test['name']}")
        print(f"{'='*60}")
        
        # Show condensed history
        for turn in test["history"]:
            role = turn["role"].upper()
            content = turn["content"][:100] + "..." if len(turn["content"]) > 100 else turn["content"]
            print(f"{role}: {content}")
        
        print(f"\nQ2 (follow-up): {test['q2']}")
        
        # Run rewriter
        result = rewriter.rewrite(test["q2"], test["history"])
        
        print(f"Rewritten: {result.rewritten_query}")
        print(f"Time: {result.inference_time_ms:.1f}ms")
        
        # Check if expected keywords are present
        rewritten_lower = result.rewritten_query.lower()
        found = []
        missing = []
        for keyword in test["expected_contains"]:
            if keyword.lower() in rewritten_lower:
                found.append(keyword)
            else:
                missing.append(keyword)
        
        # Need at least 60% of keywords for a pass
        success = len(found) / len(test["expected_contains"]) >= 0.6
        
        print(f"Expected keywords: {test['expected_contains']}")
        print(f"Found: {found}")
        if missing:
            print(f"Missing: {missing}")
        
        if success:
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    print(f"Success rate: {100*passed/len(test_cases):.1f}%")
    
    return passed == len(test_cases)


if __name__ == "__main__":
    success = run_quick_tests()
    sys.exit(0 if success else 1)
