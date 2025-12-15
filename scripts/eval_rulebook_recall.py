#!/usr/bin/env python
"""
Evaluate rulebook retrieval recall using the production RulebookQueryRouter.

Tests the complete pipeline including:
- Intent-based category filtering
- Hybrid search (BM25 + semantic)
- Cross-encoder reranking (if enabled)
- Contextual embeddings (if present)

Usage:
    uv run python -m scripts.eval_rulebook_recall
    uv run python -m scripts.eval_rulebook_recall --verbose
    uv run python -m scripts.eval_rulebook_recall --top-k 10
"""
import argparse
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Standard project root setup
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.rulebook.rulebook_query_router import RulebookQueryRouter
from src.rag.rulebook.rulebook_storage import RulebookStorage
from src.rag.rulebook.rulebook_types import RulebookQueryIntent


# Simple intent mapping based on question category
CATEGORY_TO_INTENT = {
    "RULE_MECHANICS": RulebookQueryIntent.RULE_MECHANICS,
    "DESCRIBE_ENTITY": RulebookQueryIntent.DESCRIBE_ENTITY,
    "COMPARE_ENTITIES": RulebookQueryIntent.COMPARE_ENTITIES,
    "CALCULATE_VALUES": RulebookQueryIntent.CALCULATE_VALUES,
    "COMBINED": RulebookQueryIntent.RULE_MECHANICS,  # General fallback
    "CLASS_FEATURES": RulebookQueryIntent.SUBCLASS_FEATURES,
    "SPELLCASTING": RulebookQueryIntent.SPELL_DETAILS,
    "COMBAT": RulebookQueryIntent.ACTION_OPTIONS,
    "EQUIPMENT": RulebookQueryIntent.EQUIPMENT_PROPERTIES,
    "EXPLORATION": RulebookQueryIntent.ENVIRONMENTAL_RULES,
    "CREATURES": RulebookQueryIntent.MONSTER_STATS,
}


@dataclass
class EvalResult:
    """Result for a single question evaluation."""
    question_id: str
    question: str
    category: str
    expected_sections: list[str]
    retrieved_sections: list[str]
    hits: list[str]
    misses: list[str]
    recall: float
    mrr: float  # Mean Reciprocal Rank - rank of first hit
    first_hit_rank: Optional[int]


def load_test_questions() -> list[dict]:
    """Load the ground truth test questions."""
    test_file = project_root / "574-Assignment" / "retrieval_study" / "ground_truth" / "test_questions.json"
    
    with open(test_file) as f:
        data = json.load(f)
    
    return data["questions"]


def evaluate_question(
    router: RulebookQueryRouter,
    question: dict,
    top_k: int = 10
) -> EvalResult:
    """Evaluate a single question against ground truth."""
    query = question["question"]
    expected = set(question["relevant_sections"])
    category = question["category"]
    
    # Map category to intent
    intent = CATEGORY_TO_INTENT.get(category, RulebookQueryIntent.RULE_MECHANICS)
    
    # Get retrieval results using the router's query method
    # We pass empty entities/hints to test pure retrieval
    results, _metrics = router.query(
        intention=intent,
        user_query=query,
        entities=[],  # No pre-extracted entities
        context_hints=[],
        k=top_k
    )
    
    # Extract section IDs from results
    retrieved_ids = [r.section.id for r in results]
    retrieved_set = set(retrieved_ids)
    
    # Calculate metrics
    hits = list(expected & retrieved_set)
    misses = list(expected - retrieved_set)
    
    # Recall = fraction of expected sections that were retrieved
    recall = len(hits) / len(expected) if expected else 0.0
    
    # MRR = 1/rank of first relevant result (0 if none found)
    first_hit_rank = None
    mrr = 0.0
    for i, section_id in enumerate(retrieved_ids, 1):
        if section_id in expected:
            first_hit_rank = i
            mrr = 1.0 / i
            break
    
    return EvalResult(
        question_id=question["id"],
        question=query,
        category=question["category"],
        expected_sections=list(expected),
        retrieved_sections=retrieved_ids,
        hits=hits,
        misses=misses,
        recall=recall,
        mrr=mrr,
        first_hit_rank=first_hit_rank
    )


def run_evaluation(
    top_k: int = 10,
    verbose: bool = False
) -> dict:
    """Run full evaluation and return metrics."""
    print("=" * 70)
    print("RULEBOOK RETRIEVAL EVALUATION")
    print("=" * 70)
    
    # Initialize router
    print("\nInitializing RulebookStorage and Router...")
    storage = RulebookStorage()
    if not storage.load_from_disk("rulebook_storage.pkl"):
        print("ERROR: Could not load rulebook storage. Run 'uv run python -m scripts.build_rulebook_storage' first.")
        return {}
    router = RulebookQueryRouter(storage)
    
    # Check config
    from src.config import get_config
    config = get_config()
    print(f"  Reranking enabled: {config.rulebook_rerank_enabled}")
    print(f"  Candidate pool size: {config.rulebook_candidate_pool_size}")
    print(f"  BM25 weight: {config.rulebook_bm25_weight}")
    print(f"  Semantic weight: {config.rulebook_semantic_weight}")
    
    # Check for contextual embeddings
    contextual_path = project_root / "knowledge_base" / "processed_rulebook" / "contextual_prefixes.json"
    print(f"  Contextual prefixes: {'✓ found' if contextual_path.exists() else '✗ not found'}")
    
    # Load test questions
    print("\nLoading test questions...")
    questions = load_test_questions()
    print(f"  {len(questions)} questions loaded")
    
    # Run evaluation
    print(f"\nEvaluating with top_k={top_k}...")
    results: list[EvalResult] = []
    
    for i, q in enumerate(questions, 1):
        result = evaluate_question(router, q, top_k=top_k)
        results.append(result)
        
        if verbose:
            status = "✓" if result.recall == 1.0 else "○" if result.recall > 0 else "✗"
            print(f"  [{i:3d}/{len(questions)}] {status} R={result.recall:.2f} MRR={result.mrr:.2f} | {q['id']}")
            if result.misses and verbose:
                print(f"           Missed: {result.misses}")
        else:
            # Progress indicator
            if i % 10 == 0:
                print(f"  {i}/{len(questions)} questions processed...")
    
    # Calculate aggregate metrics
    total_recall = sum(r.recall for r in results) / len(results)
    total_mrr = sum(r.mrr for r in results) / len(results)
    perfect_recall = sum(1 for r in results if r.recall == 1.0)
    partial_recall = sum(1 for r in results if 0 < r.recall < 1.0)
    zero_recall = sum(1 for r in results if r.recall == 0)
    
    # Calculate by category
    categories = {}
    for r in results:
        if r.category not in categories:
            categories[r.category] = {"count": 0, "recall_sum": 0, "mrr_sum": 0}
        categories[r.category]["count"] += 1
        categories[r.category]["recall_sum"] += r.recall
        categories[r.category]["mrr_sum"] += r.mrr
    
    # Print results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    print(f"\nOverall Metrics (top_k={top_k}):")
    print(f"  Mean Recall:    {total_recall:.3f} ({total_recall*100:.1f}%)")
    print(f"  Mean MRR:       {total_mrr:.3f}")
    print(f"  Perfect recall: {perfect_recall}/{len(results)} ({perfect_recall/len(results)*100:.1f}%)")
    print(f"  Partial recall: {partial_recall}/{len(results)} ({partial_recall/len(results)*100:.1f}%)")
    print(f"  Zero recall:    {zero_recall}/{len(results)} ({zero_recall/len(results)*100:.1f}%)")
    
    print(f"\nRecall by Category:")
    for cat, stats in sorted(categories.items()):
        avg_recall = stats["recall_sum"] / stats["count"]
        avg_mrr = stats["mrr_sum"] / stats["count"]
        print(f"  {cat:20s}: R={avg_recall:.3f} MRR={avg_mrr:.3f} (n={stats['count']})")
    
    # Find worst failures
    failures = [r for r in results if r.recall < 1.0]
    failures.sort(key=lambda r: r.recall)
    
    if failures:
        print(f"\nWorst Failures (lowest recall):")
        for r in failures[:10]:
            print(f"  {r.question_id}: R={r.recall:.2f} | {r.question[:50]}...")
            print(f"    Expected: {r.expected_sections}")
            print(f"    Missed:   {r.misses}")
    
    # Calculate recall@k for different k values
    print(f"\nRecall@K Analysis:")
    for k in [1, 3, 5, 10]:
        if k <= top_k:
            # Re-evaluate with smaller k
            k_results = [evaluate_question(router, q, top_k=k) for q in questions]
            k_recall = sum(r.recall for r in k_results) / len(k_results)
            k_mrr = sum(r.mrr for r in k_results) / len(k_results)
            print(f"  R@{k}: {k_recall:.3f} | MRR@{k}: {k_mrr:.3f}")
    
    # Save detailed results
    output_path = project_root / "574-Assignment" / "retrieval_study" / "results" / "production_eval_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "config": {
            "top_k": top_k,
            "rerank_enabled": config.rulebook_rerank_enabled,
            "candidate_pool_size": config.rulebook_candidate_pool_size,
            "bm25_weight": config.rulebook_bm25_weight,
            "semantic_weight": config.rulebook_semantic_weight,
            "contextual_prefixes": contextual_path.exists()
        },
        "metrics": {
            "mean_recall": total_recall,
            "mean_mrr": total_mrr,
            "perfect_recall_count": perfect_recall,
            "partial_recall_count": partial_recall,
            "zero_recall_count": zero_recall,
            "total_questions": len(results)
        },
        "by_category": {
            cat: {
                "count": stats["count"],
                "avg_recall": stats["recall_sum"] / stats["count"],
                "avg_mrr": stats["mrr_sum"] / stats["count"]
            }
            for cat, stats in categories.items()
        },
        "per_question": [
            {
                "id": r.question_id,
                "question": r.question,
                "category": r.category,
                "expected": r.expected_sections,
                "retrieved": r.retrieved_sections,
                "hits": r.hits,
                "misses": r.misses,
                "recall": r.recall,
                "mrr": r.mrr,
                "first_hit_rank": r.first_hit_rank
            }
            for r in results
        ]
    }
    
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nDetailed results saved to: {output_path}")
    
    return output_data


def main():
    parser = argparse.ArgumentParser(description="Evaluate rulebook retrieval recall")
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=10,
        help="Number of results to retrieve per query (default: 10)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print per-question results"
    )
    
    args = parser.parse_args()
    run_evaluation(top_k=args.top_k, verbose=args.verbose)


if __name__ == "__main__":
    main()
