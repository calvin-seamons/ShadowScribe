#!/usr/bin/env python
"""
Main script to run retrieval evaluation comparing different approaches.

Usage:
    python -m retrieval_study.scripts.run_evaluation [--retrievers NAMES] [--verbose]
    
Examples:
    # Run all retrievers
    python -m retrieval_study.scripts.run_evaluation
    
    # Run specific retrievers
    python -m retrieval_study.scripts.run_evaluation --retrievers st_section hybrid
    
    # Skip hybrid (requires rank-bm25)
    python -m retrieval_study.scripts.run_evaluation --skip-hybrid
"""
import argparse
import pickle
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from retrieval_study.config import RULEBOOK_STORAGE_PATH, DEFAULT_ST_MODEL, SENTENCE_TRANSFORMER_MODELS
from retrieval_study.retrievers import (
    STSectionRetriever,
    STSentenceRetriever,
    HybridRetriever,
)
from retrieval_study.evaluation import RetrievalEvaluator


def load_sections():
    """Load sections from rulebook storage"""
    print(f"Loading sections from {RULEBOOK_STORAGE_PATH}...")
    with open(RULEBOOK_STORAGE_PATH, 'rb') as f:
        data = pickle.load(f)
    sections = data['sections']
    print(f"Loaded {len(sections)} sections")
    return sections


def create_retrievers(sections, args):
    """Create retriever instances based on args"""
    retrievers = []
    
    # Sentence Transformer - Section level (mpnet)
    if 'st_section' in args.retrievers or 'all' in args.retrievers:
        print("Creating ST Section retriever (mpnet)...")
        st_section = STSectionRetriever(model_name=DEFAULT_ST_MODEL)
        st_section.build_index(sections)
        retrievers.append(st_section)
    
    # Sentence Transformer - Section level (minilm - faster)
    if 'st_section_mini' in args.retrievers or 'all' in args.retrievers:
        print("Creating ST Section retriever (minilm)...")
        st_section_mini = STSectionRetriever(model_name=SENTENCE_TRANSFORMER_MODELS['minilm'])
        st_section_mini.build_index(sections)
        retrievers.append(st_section_mini)
    
    # Sentence Transformer - Sentence level
    if 'st_sentence' in args.retrievers or 'all' in args.retrievers:
        print("Creating ST Sentence retriever...")
        st_sentence = STSentenceRetriever(model_name=DEFAULT_ST_MODEL, chunk_size=2)
        st_sentence.build_index(sections)
        retrievers.append(st_sentence)
    
    # Hybrid BM25 + Dense
    if ('hybrid' in args.retrievers or 'all' in args.retrievers) and not args.skip_hybrid:
        try:
            print("Creating Hybrid retriever...")
            hybrid = HybridRetriever(model_name=DEFAULT_ST_MODEL)
            hybrid.build_index(sections)
            retrievers.append(hybrid)
        except ImportError as e:
            print(f"Skipping hybrid retriever: {e}")
    
    return retrievers


def main():
    parser = argparse.ArgumentParser(description="Run retrieval evaluation")
    parser.add_argument(
        '--retrievers', 
        nargs='+', 
        default=['all'],
        choices=['all', 'st_section', 'st_section_mini', 'st_sentence', 'hybrid'],
        help='Which retrievers to evaluate'
    )
    parser.add_argument(
        '--skip-hybrid',
        action='store_true',
        help='Skip hybrid retriever (useful if rank-bm25 not installed)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print per-question results'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path for results JSON'
    )
    
    args = parser.parse_args()
    
    # Load sections
    sections = load_sections()
    
    # Create retrievers
    retrievers = create_retrievers(sections, args)
    
    if not retrievers:
        print("No retrievers to evaluate!")
        return
    
    print(f"\nEvaluating {len(retrievers)} retrievers...")
    
    # Run evaluation
    evaluator = RetrievalEvaluator()
    results = evaluator.evaluate_all(retrievers, verbose=args.verbose)
    
    # Print comparison table
    evaluator.print_comparison_table(results)
    
    # Save results
    evaluator.save_results(results, args.output)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
