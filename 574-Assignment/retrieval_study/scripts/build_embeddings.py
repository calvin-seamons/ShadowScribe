#!/usr/bin/env python
"""
Pre-build embeddings for all retrievers to speed up evaluation.

Usage:
    python -m retrieval_study.scripts.build_embeddings [--model MODEL]
    
Examples:
    # Build with default model (all-mpnet-base-v2)
    python -m retrieval_study.scripts.build_embeddings
    
    # Build with specific model
    python -m retrieval_study.scripts.build_embeddings --model all-MiniLM-L6-v2
"""
import argparse
import pickle
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from retrieval_study.config import (
    RULEBOOK_STORAGE_PATH, 
    DEFAULT_ST_MODEL, 
    SENTENCE_TRANSFORMER_MODELS
)
from retrieval_study.retrievers import STSectionRetriever, STSentenceRetriever


def load_sections():
    """Load sections from rulebook storage"""
    print(f"Loading sections from {RULEBOOK_STORAGE_PATH}...")
    with open(RULEBOOK_STORAGE_PATH, 'rb') as f:
        data = pickle.load(f)
    sections = data['sections']
    print(f"Loaded {len(sections)} sections")
    return sections


def main():
    parser = argparse.ArgumentParser(description="Pre-build embeddings")
    parser.add_argument(
        '--model',
        type=str,
        default=DEFAULT_ST_MODEL,
        help=f'Sentence transformer model (default: {DEFAULT_ST_MODEL})'
    )
    parser.add_argument(
        '--all-models',
        action='store_true',
        help='Build embeddings for all configured models'
    )
    
    args = parser.parse_args()
    
    # Load sections
    sections = load_sections()
    
    # Determine which models to build
    if args.all_models:
        models = list(SENTENCE_TRANSFORMER_MODELS.values())
    else:
        models = [args.model]
    
    for model_name in models:
        print(f"\n{'='*60}")
        print(f"Building embeddings with {model_name}")
        print('='*60)
        
        # Section-level embeddings
        print("\n1. Building section-level embeddings...")
        st_section = STSectionRetriever(model_name=model_name)
        st_section.build_index(sections)
        
        # Sentence-level embeddings
        print("\n2. Building sentence-level embeddings...")
        st_sentence = STSentenceRetriever(model_name=model_name, chunk_size=2)
        st_sentence.build_index(sections)
        
        print(f"\nDone with {model_name}!")
    
    print("\n" + "="*60)
    print("All embeddings built successfully!")
    print("="*60)


if __name__ == "__main__":
    main()
