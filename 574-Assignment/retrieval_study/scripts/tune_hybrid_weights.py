#!/usr/bin/env python
"""
Tune the BM25 vs Semantic weight balance for hybrid search.

Tests different weight combinations to find optimal MRR.
"""
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field

# Add paths
script_dir = Path(__file__).parent
study_root = script_dir.parent
assignment_root = study_root.parent
project_root = assignment_root.parent

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(assignment_root))

from src.rag.rulebook.rulebook_storage import RulebookStorage
from src.rag.rulebook.rulebook_query_router import RulebookQueryRouter
from src.rag.rulebook.rulebook_types import RulebookQueryIntent

from retrieval_study.config import GROUND_TRUTH_PATH, EVAL_K_VALUES
from retrieval_study.evaluation.metrics import compute_recall_at_k, compute_mrr


def load_ground_truth() -> List[Dict]:
    with open(GROUND_TRUTH_PATH, 'r') as f:
        data = json.load(f)
    return data['questions']


def category_to_intention(category: str) -> RulebookQueryIntent:
    mapping = {
        "RULE_MECHANICS": RulebookQueryIntent.RULE_MECHANICS,
        "DESCRIBE_ENTITY": RulebookQueryIntent.DESCRIBE_ENTITY,
        "COMPARE_ENTITIES": RulebookQueryIntent.COMPARE_ENTITIES,
        "CALCULATE_VALUES": RulebookQueryIntent.CALCULATE_VALUES,
        "COMBINED": RulebookQueryIntent.RULE_MECHANICS,
    }
    return mapping.get(category, RulebookQueryIntent.DESCRIBE_ENTITY)


def evaluate_with_weights(router: RulebookQueryRouter, test_questions: List[Dict], 
                          bm25_weight: float) -> Dict[str, float]:
    """Evaluate with specific BM25 weight (semantic weight = 1 - bm25_weight)"""
    
    # Temporarily modify the router's RRF weights
    original_query = router._hybrid_search
    
    def patched_hybrid_search(query, candidate_sections, candidate_ids, performance):
        """Patched hybrid search with custom weights"""
        if not candidate_sections:
            return []
        
        import numpy as np
        
        performance.sections_with_embeddings = sum(1 for s in candidate_sections if s.vector is not None)
        n_candidates = min(len(candidate_sections), 50)
        
        # BM25 search
        bm25_results = router._bm25_search(query, candidate_ids)[:n_candidates]
        
        # Semantic search
        query_embedding = router._get_embedding(query, performance)
        semantic_results = []
        for section in candidate_sections:
            if section.vector is None:
                continue
            similarity = router._cosine_similarity(query_embedding, section.vector)
            semantic_results.append((section.id, similarity))
        semantic_results.sort(key=lambda x: x[1], reverse=True)
        semantic_results = semantic_results[:n_candidates]
        
        # RRF fusion with custom weights
        fused_scores = {}
        semantic_weight = 1.0 - bm25_weight
        
        for rank, (section_id, _) in enumerate(bm25_results):
            rrf_score = bm25_weight / (router.RRF_K + rank + 1)
            fused_scores[section_id] = fused_scores.get(section_id, 0) + rrf_score
        
        for rank, (section_id, _) in enumerate(semantic_results):
            rrf_score = semantic_weight / (router.RRF_K + rank + 1)
            fused_scores[section_id] = fused_scores.get(section_id, 0) + rrf_score
        
        section_lookup = {s.id: s for s in candidate_sections}
        results = [(section_lookup[sid], score) for sid, score in fused_scores.items() if sid in section_lookup]
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    # Patch the method
    router._hybrid_search = patched_hybrid_search
    
    # Run evaluation
    mrr_sum = 0.0
    recall_at_5_sum = 0.0
    
    for question in test_questions:
        query = question['question']
        category = question['category']
        relevant_ids = set(question['relevant_sections'])
        intention = category_to_intention(category)
        
        search_results, _ = router.query(
            intention=intention,
            user_query=query,
            entities=[],
            context_hints=[],
            k=10
        )
        
        retrieved_ids = [r.section.id for r in search_results]
        mrr_sum += compute_mrr(retrieved_ids, relevant_ids)
        recall_at_5_sum += compute_recall_at_k(retrieved_ids, relevant_ids, 5)
    
    # Restore original method
    router._hybrid_search = original_query
    
    n = len(test_questions)
    return {
        'mrr': mrr_sum / n,
        'recall@5': recall_at_5_sum / n
    }


def main():
    print("=" * 70)
    print("TUNING BM25 vs SEMANTIC WEIGHT BALANCE")
    print("=" * 70)
    
    # Load storage and router
    print("\nLoading rulebook storage...")
    storage = RulebookStorage()
    storage.load_from_disk()
    
    print("Initializing RulebookQueryRouter...")
    router = RulebookQueryRouter(storage)
    
    test_questions = load_ground_truth()
    print(f"Loaded {len(test_questions)} test questions\n")
    
    # Test different weight combinations
    weights_to_test = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    print(f"{'BM25 Weight':<15} {'Semantic Weight':<17} {'MRR':>8} {'R@5':>8}")
    print("-" * 55)
    
    results = []
    for bm25_weight in weights_to_test:
        semantic_weight = 1.0 - bm25_weight
        metrics = evaluate_with_weights(router, test_questions, bm25_weight)
        results.append((bm25_weight, metrics))
        print(f"{bm25_weight:<15.1f} {semantic_weight:<17.1f} {metrics['mrr']:>8.3f} {metrics['recall@5']:>8.3f}")
    
    # Find best
    best_mrr = max(results, key=lambda x: x[1]['mrr'])
    best_recall = max(results, key=lambda x: x[1]['recall@5'])
    
    print("-" * 55)
    print(f"\nBest MRR:     BM25={best_mrr[0]:.1f}, Semantic={1-best_mrr[0]:.1f} → MRR={best_mrr[1]['mrr']:.3f}")
    print(f"Best R@5:     BM25={best_recall[0]:.1f}, Semantic={1-best_recall[0]:.1f} → R@5={best_recall[1]['recall@5']:.3f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
