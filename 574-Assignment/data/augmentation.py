"""
Data Augmentation Module

Provides text augmentation utilities for training data generation:
- Typo injection (realistic keyboard errors)
- Case and contraction variations
- Preserves placeholder tokens like {CHARACTER}, {PARTY_MEMBER}, {NPC}

Usage:
    from data.augmentation import augment_query, AugmentationConfig
    
    config = AugmentationConfig(typo_probability=0.15, num_variants=5)
    variants = augment_query("What spells does {CHARACTER} know?", config)
"""

import random
import re
from dataclasses import dataclass, field
from typing import Optional


# Adjacent keys on QWERTY keyboard for realistic typo simulation
ADJACENT_KEYS = {
    'a': 'qwsz', 'b': 'vghn', 'c': 'xdfv', 'd': 'erfcxs', 'e': 'rdsw',
    'f': 'rtgvcd', 'g': 'tyhbvf', 'h': 'yujnbg', 'i': 'uojk', 'j': 'uiknmh',
    'k': 'ioljm', 'l': 'opk', 'm': 'njk', 'n': 'bhjm', 'o': 'iplk',
    'p': 'ol', 'q': 'wa', 'r': 'etdf', 's': 'wedxza', 't': 'ryfg',
    'u': 'yihj', 'v': 'cfgb', 'w': 'qeas', 'x': 'zsdc', 'y': 'tugh',
    'z': 'asx'
}

# Common contractions and their expansions
CONTRACTIONS = {
    "what is": "what's",
    "what are": "what're",
    "what has": "what's",
    "what have": "what've",
    "what would": "what'd",
    "what will": "what'll",
    "who is": "who's",
    "who are": "who're",
    "who has": "who's",
    "who would": "who'd",
    "who will": "who'll",
    "where is": "where's",
    "where are": "where're",
    "where has": "where's",
    "where would": "where'd",
    "when is": "when's",
    "when has": "when's",
    "when would": "when'd",
    "why is": "why's",
    "why are": "why're",
    "why has": "why's",
    "why would": "why'd",
    "how is": "how's",
    "how are": "how're",
    "how has": "how's",
    "how would": "how'd",
    "how will": "how'll",
    "that is": "that's",
    "that has": "that's",
    "that would": "that'd",
    "that will": "that'll",
    "there is": "there's",
    "there are": "there're",
    "there has": "there's",
    "there would": "there'd",
    "there will": "there'll",
    "here is": "here's",
    "here are": "here're",
    "it is": "it's",
    "it has": "it's",
    "it would": "it'd",
    "it will": "it'll",
    "i am": "i'm",
    "i have": "i've",
    "i had": "i'd",
    "i would": "i'd",
    "i will": "i'll",
    "you are": "you're",
    "you have": "you've",
    "you had": "you'd",
    "you would": "you'd",
    "you will": "you'll",
    "we are": "we're",
    "we have": "we've",
    "we had": "we'd",
    "we would": "we'd",
    "we will": "we'll",
    "they are": "they're",
    "they have": "they've",
    "they had": "they'd",
    "they would": "they'd",
    "they will": "they'll",
    "he is": "he's",
    "he has": "he's",
    "he would": "he'd",
    "he will": "he'll",
    "she is": "she's",
    "she has": "she's",
    "she would": "she'd",
    "she will": "she'll",
    "is not": "isn't",
    "are not": "aren't",
    "was not": "wasn't",
    "were not": "weren't",
    "has not": "hasn't",
    "have not": "haven't",
    "had not": "hadn't",
    "do not": "don't",
    "does not": "doesn't",
    "did not": "didn't",
    "will not": "won't",
    "would not": "wouldn't",
    "could not": "couldn't",
    "should not": "shouldn't",
    "can not": "can't",
    "cannot": "can't",
    "let us": "let's",
}

# Build reverse mapping for expansion
EXPANSIONS = {v: k for k, v in CONTRACTIONS.items()}

# Placeholder pattern to preserve during augmentation
PLACEHOLDER_PATTERN = re.compile(r'\{[A-Z_]+\}')


@dataclass
class AugmentationConfig:
    """Configuration for text augmentation."""
    
    # Typo settings
    typo_probability: float = 0.12  # Probability of introducing typo per word
    typo_types: list = field(default_factory=lambda: ['swap', 'delete', 'duplicate', 'adjacent'])
    
    # Case variation settings
    case_variation_probability: float = 0.3  # Probability of applying case variation
    case_types: list = field(default_factory=lambda: ['lower', 'upper', 'title', 'random'])
    
    # Contraction settings
    contraction_probability: float = 0.5  # Probability of contracting/expanding
    
    # Generation settings
    num_variants: int = 3  # Number of augmented variants to generate
    include_original: bool = True  # Include the original in output
    
    # Random seed for reproducibility
    seed: Optional[int] = None


def _extract_placeholders(text: str) -> list[tuple[str, int, int]]:
    """Extract placeholder tokens and their positions."""
    return [(m.group(), m.start(), m.end()) for m in PLACEHOLDER_PATTERN.finditer(text)]


def _inject_typo_word(word: str, typo_type: str) -> str:
    """Inject a single typo into a word."""
    if len(word) < 2:
        return word
    
    if typo_type == 'swap' and len(word) >= 2:
        # Swap two adjacent characters
        idx = random.randint(0, len(word) - 2)
        chars = list(word)
        chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
        return ''.join(chars)
    
    elif typo_type == 'delete':
        # Delete a random character
        idx = random.randint(0, len(word) - 1)
        return word[:idx] + word[idx + 1:]
    
    elif typo_type == 'duplicate':
        # Duplicate a random character
        idx = random.randint(0, len(word) - 1)
        return word[:idx] + word[idx] + word[idx:]
    
    elif typo_type == 'adjacent':
        # Replace with adjacent key
        idx = random.randint(0, len(word) - 1)
        char = word[idx].lower()
        if char in ADJACENT_KEYS:
            replacement = random.choice(ADJACENT_KEYS[char])
            if word[idx].isupper():
                replacement = replacement.upper()
            return word[:idx] + replacement + word[idx + 1:]
    
    return word


def inject_typos(text: str, probability: float = 0.12, 
                 typo_types: list = None, rng: random.Random = None) -> str:
    """
    Inject realistic typos into text while preserving placeholders.
    
    Args:
        text: Input text
        probability: Probability of typo per word
        typo_types: List of typo types to use
        rng: Random number generator for reproducibility
    
    Returns:
        Text with typos injected
    """
    if rng is None:
        rng = random.Random()
    
    if typo_types is None:
        typo_types = ['swap', 'delete', 'duplicate', 'adjacent']
    
    # Extract and protect placeholders
    placeholders = _extract_placeholders(text)
    placeholder_tokens = {p[0] for p in placeholders}
    
    # Split into words while preserving whitespace and punctuation
    tokens = re.findall(r'\S+|\s+', text)
    
    result = []
    for token in tokens:
        # Skip whitespace
        if token.isspace():
            result.append(token)
            continue
        
        # Skip placeholders
        if token in placeholder_tokens or PLACEHOLDER_PATTERN.match(token):
            result.append(token)
            continue
        
        # Skip very short words
        if len(token) < 3:
            result.append(token)
            continue
        
        # Separate word from trailing punctuation
        word = token.rstrip('.,!?;:')
        punctuation = token[len(word):]
        
        # Maybe inject typo
        if rng.random() < probability:
            typo_type = rng.choice(typo_types)
            word = _inject_typo_word(word, typo_type)
        
        result.append(word + punctuation)
    
    return ''.join(result)


def apply_case_variation(text: str, case_type: str = None, 
                         rng: random.Random = None) -> str:
    """
    Apply case variation while preserving placeholders.
    
    Args:
        text: Input text
        case_type: One of 'lower', 'upper', 'title', 'random', or None for random choice
        rng: Random number generator
    
    Returns:
        Text with case variation applied
    """
    if rng is None:
        rng = random.Random()
    
    if case_type is None:
        case_type = rng.choice(['lower', 'upper', 'title', 'random'])
    
    # Find all placeholders and their positions
    placeholders = list(PLACEHOLDER_PATTERN.finditer(text))
    
    if not placeholders:
        # No placeholders, simple case
        if case_type == 'lower':
            return text.lower()
        elif case_type == 'upper':
            return text.upper()
        elif case_type == 'title':
            return text.title()
        elif case_type == 'random':
            return ''.join(
                c.upper() if c.isalpha() and rng.random() < 0.5 else c.lower() if c.isalpha() else c
                for c in text
            )
        return text
    
    # Build result by processing segments between placeholders
    result = []
    last_end = 0
    
    for match in placeholders:
        # Get text before this placeholder
        before = text[last_end:match.start()]
        
        # Apply case to the segment
        if case_type == 'lower':
            before = before.lower()
        elif case_type == 'upper':
            before = before.upper()
        elif case_type == 'title':
            before = before.title()
        elif case_type == 'random':
            before = ''.join(
                c.upper() if c.isalpha() and rng.random() < 0.5 else c.lower() if c.isalpha() else c
                for c in before
            )
        
        result.append(before)
        # Add placeholder unchanged
        result.append(match.group())
        last_end = match.end()
    
    # Handle text after last placeholder
    after = text[last_end:]
    if case_type == 'lower':
        after = after.lower()
    elif case_type == 'upper':
        after = after.upper()
    elif case_type == 'title':
        after = after.title()
    elif case_type == 'random':
        after = ''.join(
            c.upper() if c.isalpha() and rng.random() < 0.5 else c.lower() if c.isalpha() else c
            for c in after
        )
    result.append(after)
    
    return ''.join(result)


def apply_contraction_variation(text: str, expand: bool = None,
                                 rng: random.Random = None) -> str:
    """
    Apply contraction or expansion to text.
    
    Args:
        text: Input text
        expand: True to expand contractions, False to contract, None for random
        rng: Random number generator
    
    Returns:
        Text with contractions modified
    """
    if rng is None:
        rng = random.Random()
    
    if expand is None:
        expand = rng.random() < 0.5
    
    # Extract and protect placeholders
    placeholders = _extract_placeholders(text)
    marker_map = {}
    modified = text
    for i, (placeholder, start, end) in enumerate(placeholders):
        marker = f"__PH{i}__"
        marker_map[marker] = placeholder
        modified = modified.replace(placeholder, marker, 1)
    
    if expand:
        # Expand contractions
        lower_text = modified.lower()
        for contraction, expansion in EXPANSIONS.items():
            if contraction in lower_text:
                # Case-insensitive replacement
                pattern = re.compile(re.escape(contraction), re.IGNORECASE)
                modified = pattern.sub(expansion, modified)
    else:
        # Contract phrases
        lower_text = modified.lower()
        for phrase, contraction in CONTRACTIONS.items():
            if phrase in lower_text:
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                modified = pattern.sub(contraction, modified)
    
    # Restore placeholders
    for marker, placeholder in marker_map.items():
        modified = modified.replace(marker, placeholder)
    
    return modified


def augment_query(text: str, config: AugmentationConfig = None,
                  rng: random.Random = None) -> list[str]:
    """
    Generate augmented variants of a query.
    
    Args:
        text: Input query text
        config: Augmentation configuration
        rng: Random number generator
    
    Returns:
        List of augmented variants
    """
    if config is None:
        config = AugmentationConfig()
    
    if rng is None:
        rng = random.Random(config.seed) if config.seed else random.Random()
    
    variants = []
    
    if config.include_original:
        variants.append(text)
    
    seen = {text}
    attempts = 0
    max_attempts = config.num_variants * 10  # Prevent infinite loops
    
    while len(variants) < (config.num_variants + (1 if config.include_original else 0)):
        if attempts >= max_attempts:
            break
        attempts += 1
        
        variant = text
        
        # Maybe apply case variation
        if rng.random() < config.case_variation_probability:
            case_type = rng.choice(config.case_types)
            variant = apply_case_variation(variant, case_type, rng)
        
        # Maybe apply contraction variation
        if rng.random() < config.contraction_probability:
            variant = apply_contraction_variation(variant, rng=rng)
        
        # Maybe inject typos
        if rng.random() < config.typo_probability * 3:  # Scale up to ensure some typos
            variant = inject_typos(variant, config.typo_probability, 
                                   config.typo_types, rng)
        
        # Only add if unique
        if variant not in seen:
            seen.add(variant)
            variants.append(variant)
    
    return variants


def augment_batch(texts: list[str], config: AugmentationConfig = None,
                  rng: random.Random = None) -> list[tuple[str, list[str]]]:
    """
    Augment a batch of texts.
    
    Args:
        texts: List of input texts
        config: Augmentation configuration
        rng: Random number generator
    
    Returns:
        List of (original, variants) tuples
    """
    if config is None:
        config = AugmentationConfig()
    
    if rng is None:
        rng = random.Random(config.seed) if config.seed else random.Random()
    
    results = []
    for text in texts:
        variants = augment_query(text, config, rng)
        results.append((text, variants))
    
    return results


# Quick test
if __name__ == "__main__":
    # Test with placeholder preservation
    test_queries = [
        "What spells does {CHARACTER} know?",
        "Tell me about {PARTY_MEMBER}'s backstory",
        "Did {NPC} give us any quests?",
        "What is my AC?",
        "How does Fireball work?",
    ]
    
    config = AugmentationConfig(
        typo_probability=0.15,
        case_variation_probability=0.4,
        contraction_probability=0.5,
        num_variants=3,
        include_original=True,
        seed=42
    )
    
    print("=" * 60)
    print("Augmentation Module Test")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nOriginal: {query}")
        variants = augment_query(query, config)
        for i, v in enumerate(variants):
            print(f"  [{i}] {v}")
