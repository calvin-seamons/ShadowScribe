"""
Comprehensive Test Pairs for Query Rewriter

Each test pair consists of:
- q1: The initial question (standalone, run through RAG)
- q2: The follow-up question (context-dependent, needs rewriting)
- expected_rewrite: What we expect the model to produce (for evaluation)
- difficulty: easy, medium, hard
- category: Type of context dependency

The tests are designed to be HARD and comprehensive, testing edge cases
and complex conversational patterns that would trip up naive approaches.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TestPair:
    """A single test case for query rewriting"""
    id: str
    category: str
    difficulty: str  # easy, medium, hard
    q1: str  # Initial question (standalone)
    q2: str  # Follow-up question (context-dependent)
    expected_rewrite: str  # What we expect the rewritten q2 to contain (key concepts)
    notes: str = ""  # Why this test is tricky
    mock_a1: str = ""  # Optional: Use this instead of real RAG response for testing


# =============================================================================
# CATEGORY 1: PRONOUN RESOLUTION
# Tests: it, its, this, that, these, those, they, them
# =============================================================================

PRONOUN_TESTS = [
    TestPair(
        id="pronoun_001",
        category="pronoun_resolution",
        difficulty="easy",
        q1="What is Fireball?",
        q2="What's its damage?",
        expected_rewrite="Fireball damage",
        notes="Basic 'its' resolution to spell name"
    ),
    TestPair(
        id="pronoun_002",
        category="pronoun_resolution",
        difficulty="easy",
        q1="Tell me about my armor",
        q2="How much AC does it give me?",
        expected_rewrite="armor AC",
        notes="'it' refers to armor"
    ),
    TestPair(
        id="pronoun_003",
        category="pronoun_resolution",
        difficulty="medium",
        q1="What spells do I know?",
        q2="Which of them require concentration?",
        expected_rewrite="spells concentration",
        notes="'them' refers to the list of spells from Q1"
    ),
    TestPair(
        id="pronoun_004",
        category="pronoun_resolution",
        difficulty="medium",
        q1="Tell me about the grappling rules",
        q2="Can I do that while holding a weapon?",
        expected_rewrite="grapple holding weapon",
        notes="'that' refers to grappling action"
    ),
    TestPair(
        id="pronoun_005",
        category="pronoun_resolution",
        difficulty="hard",
        q1="What's the difference between a long rest and a short rest?",
        q2="How long does each take?",
        expected_rewrite="rest duration",
        notes="'each' refers to both rest types - 'rest' with duration/time context is sufficient"
    ),
    TestPair(
        id="pronoun_006",
        category="pronoun_resolution",
        difficulty="hard",
        q1="Compare my longsword to my dagger",
        q2="Which one deals more damage on a critical hit?",
        expected_rewrite="longsword dagger critical hit damage",
        notes="'which one' requires resolving both items from comparison"
    ),
]

# =============================================================================
# CATEGORY 2: NPC/ENTITY CONTINUATION
# Tests: References to NPCs, locations, items from prior context
# =============================================================================

ENTITY_TESTS = [
    TestPair(
        id="entity_001",
        category="entity_continuation",
        difficulty="easy",
        q1="Who is Elara?",
        q2="When did I first meet her?",
        expected_rewrite="Elara first meet",
        notes="'her' refers to Elara"
    ),
    TestPair(
        id="entity_002",
        category="entity_continuation",
        difficulty="easy",
        q1="Tell me about Shadowfell",
        q2="What creatures live there?",
        expected_rewrite="Shadowfell creatures",
        notes="'there' refers to Shadowfell location"
    ),
    TestPair(
        id="entity_003",
        category="entity_continuation",
        difficulty="medium",
        q1="What's special about Eldaryth of Regret?",
        q2="How did I get the weapon?",
        expected_rewrite="Eldaryth of Regret get",
        notes="'the weapon' refers to named item, must carry full name"
    ),
    TestPair(
        id="entity_004",
        category="entity_continuation",
        difficulty="medium",
        q1="Who is Lord Blackwood and what does he want?",
        q2="Has he betrayed us before?",
        expected_rewrite="Lord Blackwood betray",
        notes="'he' refers to Lord Blackwood from compound question"
    ),
    TestPair(
        id="entity_005",
        category="entity_continuation",
        difficulty="hard",
        q1="Tell me about the Dragon's Hoard tavern in Neverwinter",
        q2="Who did we meet there and what did they want?",
        expected_rewrite="Dragon's Hoard meet",
        notes="'there' refers to compound location - Dragon's Hoard is sufficient for RAG lookup"
    ),
    TestPair(
        id="entity_006",
        category="entity_continuation",
        difficulty="hard",
        q1="Compare the Cloak of Elvenkind and the Ring of Invisibility",
        q2="Which one should I attune to first given my build?",
        expected_rewrite="Cloak of Elvenkind Ring of Invisibility attune",
        notes="'which one' references two magic items, must include both"
    ),
]

# =============================================================================
# CATEGORY 3: TOPIC SWITCHING WITH REFERENCE
# Tests: Changing topic but referencing something from prior context
# =============================================================================

TOPIC_SWITCH_TESTS = [
    TestPair(
        id="topic_001",
        category="topic_switch",
        difficulty="medium",
        q1="What are my class features as a Warlock?",
        q2="Now tell me about my spell slots",
        expected_rewrite="Warlock spell slots",
        notes="Topic switch from features to slots, but 'my' implies Warlock context"
    ),
    TestPair(
        id="topic_002",
        category="topic_switch",
        difficulty="medium",
        q1="How does the Shield spell work?",
        q2="What about Counterspell?",
        expected_rewrite="Counterspell",
        notes="'What about' implies comparison/relation but new spell is independent"
    ),
    TestPair(
        id="topic_003",
        category="topic_switch",
        difficulty="hard",
        q1="Tell me about the combat in session 5 where we fought the vampire",
        q2="Speaking of vampires, what are their weaknesses according to the rules?",
        expected_rewrite="vampire weaknesses rules",
        notes="Topic switch from session notes to rulebook, entity carries over"
    ),
    TestPair(
        id="topic_004",
        category="topic_switch",
        difficulty="hard",
        q1="What happened in our last session?",
        q2="Based on that, what should I prepare for next time?",
        expected_rewrite="prepare next",
        notes="Tricky: 'that' is vague - this is borderline an advice question that may pass through unchanged"
    ),
]

# =============================================================================
# CATEGORY 4: MULTI-TURN CONVERSATIONS
# Tests: References spanning multiple turns, not just the immediate prior turn
# =============================================================================

MULTI_TURN_TESTS = [
    TestPair(
        id="multi_001",
        category="multi_turn",
        difficulty="hard",
        q1="What's my character's backstory?",
        q2="Tell me more about the village",
        expected_rewrite="village Thornhaven",
        notes="'the village' requires understanding backstory context - should resolve to Thornhaven",
        mock_a1="Your character Duskryn grew up in the small village of Thornhaven with his parents. He left home at age 16 to train as a paladin after the village was attacked by shadow creatures."
    ),
    TestPair(
        id="multi_002",
        category="multi_turn",
        difficulty="hard",
        q1="List all the NPCs we've encountered",
        q2="What did the merchant sell us?",
        expected_rewrite="Grimshaw",
        notes="'the merchant' requires picking out specific NPC from list - resolving to Grimshaw is ideal",
        mock_a1="You've encountered several NPCs: **Elara** the elven ranger who guided you through Mistwood, **Grimshaw** the traveling merchant who sold you healing potions, **Lord Vance** the noble who hired you, and **Sister Mariel** the priestess at the temple."
    ),
    TestPair(
        id="multi_003",
        category="multi_turn",
        difficulty="hard",
        q1="What quests are we currently working on?",
        q2="Where was the artifact last seen?",
        expected_rewrite="artifact last",
        notes="'the artifact' needs quest context - should resolve to Moonstone Amulet or include 'artifact'",
        mock_a1="You have two active quests: 1) **Retrieve the Stolen Artifact** - The Moonstone Amulet was stolen from the temple and last seen being carried into the Shadowfell. 2) **Clear the Goblin Cave** - The village elder asked you to deal with goblins raiding nearby farms."
    ),
]

# =============================================================================
# CATEGORY 5: IMPLICIT CONTEXT
# Tests: Entity isn't directly stated but implied by context/domain
# =============================================================================

IMPLICIT_TESTS = [
    TestPair(
        id="implicit_001",
        category="implicit_context",
        difficulty="hard",
        q1="How do I calculate my spell attack bonus?",
        q2="And the save DC?",
        expected_rewrite="save DC",
        notes="'the' implies spell save DC from spell attack context - 'spell' is implicit in 'save DC'"
    ),
    TestPair(
        id="implicit_002",
        category="implicit_context",
        difficulty="hard",
        q1="What's my proficiency bonus at level 5?",
        q2="When does it increase?",
        expected_rewrite="proficiency bonus increase level",
        notes="'it' is proficiency bonus, needs to maintain that context"
    ),
    TestPair(
        id="implicit_003",
        category="implicit_context",
        difficulty="hard",
        q1="Tell me about my Hexblade patron",
        q2="What abilities do I get from the pact?",
        expected_rewrite="Hexblade patron pact abilities",
        notes="'the pact' implies Hexblade Warlock pact"
    ),
    TestPair(
        id="implicit_004",
        category="implicit_context",
        difficulty="hard",
        q1="What languages does my character speak?",
        q2="Can I learn more?",
        expected_rewrite="character learn new languages",
        notes="'more' implies more languages, context is implicit"
    ),
]

# =============================================================================
# CATEGORY 6: NEGATION AND CONTRAST
# Tests: Questions about what something ISN'T or comparing to prior answer
# =============================================================================

NEGATION_TESTS = [
    TestPair(
        id="negation_001",
        category="negation_contrast",
        difficulty="medium",
        q1="What damage types is my character resistant to?",
        q2="What about vulnerabilities?",
        expected_rewrite="character vulnerabilities",
        notes="Contrast to resistances, same domain - 'damage' is implicit in vulnerabilities context"
    ),
    TestPair(
        id="negation_002",
        category="negation_contrast",
        difficulty="hard",
        q1="What spells can I cast at 3rd level?",
        q2="Which of those can't be upcasted?",
        expected_rewrite="spells upcast",
        notes="Negation 'can't' + reference to prior spell list - key is preserving spell context and upcast concept"
    ),
    TestPair(
        id="negation_003",
        category="negation_contrast",
        difficulty="hard",
        q1="Tell me about the friendly NPCs in the campaign",
        q2="Now the hostile ones",
        expected_rewrite="hostile NPCs",
        notes="Contrast switch from friendly to hostile - must expand fragment to full question"
    ),
]

# =============================================================================
# CATEGORY 7: QUANTIFIERS AND SPECIFICITY
# Tests: "the first", "the last", "all of them", "the strongest"
# =============================================================================

QUANTIFIER_TESTS = [
    TestPair(
        id="quant_001",
        category="quantifiers",
        difficulty="medium",
        q1="What sessions have we played?",
        q2="Tell me about the first one",
        expected_rewrite="first session",
        notes="'the first one' needs session context"
    ),
    TestPair(
        id="quant_002",
        category="quantifiers",
        difficulty="medium",
        q1="List my known cantrips",
        q2="Which is the strongest for combat?",
        expected_rewrite="strongest combat",
        notes="Superlative 'strongest' applied to prior list - naming specific cantrips is also valid"
    ),
    TestPair(
        id="quant_003",
        category="quantifiers",
        difficulty="hard",
        q1="What magic items do I have?",
        q2="Do any of them require attunement?",
        expected_rewrite="magic items attunement require",
        notes="'any of them' references full magic item list"
    ),
    TestPair(
        id="quant_004",
        category="quantifiers",
        difficulty="hard",
        q1="Tell me about the major battles we've had",
        q2="The last one almost killed me, what happened?",
        expected_rewrite="last battle",
        notes="'the last one' requires temporal ordering of battles"
    ),
]

# =============================================================================
# CATEGORY 8: ALREADY STANDALONE (SHOULD NOT CHANGE MUCH)
# Tests: Questions that are already self-contained - rewriter should not break them
# =============================================================================

STANDALONE_TESTS = [
    TestPair(
        id="standalone_001",
        category="already_standalone",
        difficulty="easy",
        q1="What's my character's name?",
        q2="How does flanking work in 5e?",
        expected_rewrite="flanking 5e",
        notes="Q2 is completely independent, should pass through mostly unchanged"
    ),
    TestPair(
        id="standalone_002",
        category="already_standalone",
        difficulty="easy",
        q1="Who is the party's healer?",
        q2="What are the rules for death saving throws?",
        expected_rewrite="death saving throws rules",
        notes="Q2 is independent rule question"
    ),
    TestPair(
        id="standalone_003",
        category="already_standalone",
        difficulty="medium",
        q1="Tell me about session 3",
        q2="What is the casting time for Wish?",
        expected_rewrite="Wish casting time",
        notes="Complete topic change, Q2 is standalone"
    ),
]

# =============================================================================
# CATEGORY 9: AMBIGUOUS OR TRICKY
# Tests: Edge cases that could confuse the model
# =============================================================================

AMBIGUOUS_TESTS = [
    TestPair(
        id="ambig_001",
        category="ambiguous",
        difficulty="hard",
        q1="Compare my Intelligence and Wisdom scores",
        q2="Which one affects my spell attacks?",
        expected_rewrite="Intelligence Wisdom spell attacks",
        notes="Model needs to understand D&D mechanics to not drop context"
    ),
    TestPair(
        id="ambig_002",
        category="ambiguous",
        difficulty="hard",
        q1="What did Lord Vance tell us about the curse?",
        q2="Is he lying?",
        expected_rewrite="Lord Vance lying curse",
        notes="'he' is Lord Vance, but question is about trustworthiness"
    ),
    TestPair(
        id="ambig_003",
        category="ambiguous",
        difficulty="hard",
        q1="Tell me about my character's relationship with their family",
        q2="What about enemies?",
        expected_rewrite="character enemies",
        notes="'What about' could mean family enemies OR character's own enemies - must expand to full question"
    ),
    TestPair(
        id="ambig_004",
        category="ambiguous",
        difficulty="hard",
        q1="Explain how bonus actions work",
        q2="Can I use one with Healing Word?",
        expected_rewrite="Healing Word bonus action",
        notes="'one' refers to bonus action, domain-specific knowledge"
    ),
]


# =============================================================================
# ALL TEST PAIRS COMBINED
# =============================================================================

ALL_TEST_PAIRS: List[TestPair] = (
    PRONOUN_TESTS +
    ENTITY_TESTS +
    TOPIC_SWITCH_TESTS +
    MULTI_TURN_TESTS +
    IMPLICIT_TESTS +
    NEGATION_TESTS +
    QUANTIFIER_TESTS +
    STANDALONE_TESTS +
    AMBIGUOUS_TESTS
)

# Organize by category for selective testing
TESTS_BY_CATEGORY = {
    "pronoun_resolution": PRONOUN_TESTS,
    "entity_continuation": ENTITY_TESTS,
    "topic_switch": TOPIC_SWITCH_TESTS,
    "multi_turn": MULTI_TURN_TESTS,
    "implicit_context": IMPLICIT_TESTS,
    "negation_contrast": NEGATION_TESTS,
    "quantifiers": QUANTIFIER_TESTS,
    "already_standalone": STANDALONE_TESTS,
    "ambiguous": AMBIGUOUS_TESTS,
}

# Organize by difficulty
TESTS_BY_DIFFICULTY = {
    "easy": [t for t in ALL_TEST_PAIRS if t.difficulty == "easy"],
    "medium": [t for t in ALL_TEST_PAIRS if t.difficulty == "medium"],
    "hard": [t for t in ALL_TEST_PAIRS if t.difficulty == "hard"],
}


def get_test_summary():
    """Print summary of all test pairs"""
    print("=" * 60)
    print("QUERY REWRITER TEST SUITE")
    print("=" * 60)
    print(f"\nTotal test pairs: {len(ALL_TEST_PAIRS)}")
    print(f"\nBy Category:")
    for cat, tests in TESTS_BY_CATEGORY.items():
        print(f"  - {cat}: {len(tests)} tests")
    print(f"\nBy Difficulty:")
    for diff, tests in TESTS_BY_DIFFICULTY.items():
        print(f"  - {diff}: {len(tests)} tests")
    print("=" * 60)


if __name__ == "__main__":
    get_test_summary()
