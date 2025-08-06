#!/usr/bin/env python3
"""
Test the fully converted QueryRouter to ensure it works with direct JSON only.
"""

import asyncio
import sys
import os

sys.path.insert(0, '/Users/calvinseamons/ShadowScribe')

from src.engine.query_router import QueryRouter

async def test_converted_router():
    """Test the router with various queries."""
    
    router = QueryRouter()
    
    # Test queries
    test_queries = [
        "What spells can I cast?",
        "Tell me about my backstory and family",
        "What happened in the last session with the party?",
        "How does concentration work in D&D?",
        "Who else is in my party and what are their abilities?"
    ]
    
    print("Testing Converted QueryRouter (Direct JSON Only)")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: {query}")
        print("-" * 40)
        
        try:
            # Test source selection
            sources = await router.select_sources(query)
            print(f"Sources: {[s.value for s in sources.sources_needed]}")
            print(f"Confidence: {sources.confidence}")
            print(f"Reasoning: {sources.reasoning}")
            
            # Test content targeting
            targets = await router.target_content(query, sources)
            print(f"Targets: {len(targets)} content targets")
            
            for target in targets:
                print(f"  - {target.source_type.value}: {target.reasoning[:100]}...")
                
        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_converted_router())
