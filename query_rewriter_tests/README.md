# Query Rewriter Testing Environment

This folder tests the Query Rewriter concept - using a small local LLM (SmolLM2) to synthesize conversation history + a context-dependent user query into a standalone question.

## Goal

Validate that SmolLM2-1.7B-Instruct can accurately rewrite follow-up questions so they're self-contained without losing meaning.

## Test Structure

1. **Question Pairs**: Each test has:
   - `Q1`: Initial question (standalone) - run through full RAG pipeline
   - `Q2`: Follow-up question (context-dependent) - needs rewriting
   
2. **Process**:
   - Run Q1 through `demo_central_engine.py`, capture response
   - Build conversation history: [Q1, A1]
   - Feed Q2 + history to SmolLM2 query rewriter
   - Evaluate if rewritten Q2 is standalone and preserves meaning

## Test Categories

- **Pronoun Resolution**: "What about its damage?" → "What is Fireball's damage?"
- **Entity Continuation**: "When did I meet her?" → "When did I meet [NPC name]?"
- **Topic Switching with Reference**: "Now tell me about his abilities" → "Tell me about [character]'s abilities"
- **Complex Multi-turn**: Questions that reference multiple prior turns
- **Implicit Context**: Where the entity isn't directly stated but implied

## Running Tests

```bash
# Install SmolLM2 (first time only)
uv run python query_rewriter_tests/setup_model.py

# Run all tests
uv run python query_rewriter_tests/run_tests.py

# Run specific test
uv run python query_rewriter_tests/run_tests.py --test pronoun_resolution
```

## Files

- `test_pairs.py`: Comprehensive test question pairs
- `query_rewriter.py`: SmolLM2 wrapper for rewriting
- `run_tests.py`: Test runner that uses real RAG pipeline
- `results/`: Test results and logs
