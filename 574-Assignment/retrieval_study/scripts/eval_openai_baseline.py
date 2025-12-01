#!/usr/bin/env python
"""
Evaluate the production OpenAI-based rulebook retrieval system.

This script tests the current RulebookQueryRouter (OpenAI text-embedding-3-large)
against the ground truth test questions to establish baseline performance.

Usage:
    cd ShadowScribe2.0
    uv run python 574-Assignment/retrieval_study/scripts/eval_openai_baseline.py
"""
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field

# Add project root and study root to path
script_dir = Path(__file__).parent
study_root = script_dir.parent
assignment_root = study_root.parent
project_root = assignment_root.parent

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(assignment_root))

from src.rag.rulebook.rulebook_storage import RulebookStorage
from src.rag.rulebook.rulebook_query_router import RulebookQueryRouter
from src.rag.rulebook.rulebook_types import RulebookQueryIntent

# Import evaluation framework (relative to 574-Assignment)
from retrieval_study.config import GROUND_TRUTH_PATH, RESULTS_PATH, EVAL_K_VALUES
from retrieval_study.evaluation.metrics import compute_recall_at_k, compute_mrr, compute_hit_at_k


@dataclass
class OpenAIEvaluationResult:
    """Results from OpenAI baseline evaluation"""
    retriever_name: str = "OpenAI text-embedding-3-large"
    recall_at_k: Dict[int, float] = field(default_factory=dict)
    mrr: float = 0.0
    avg_latency_ms: float = 0.0
    total_api_calls: int = 0
    cache_hit_rate: float = 0.0
    per_question_results: List[Dict] = field(default_factory=list)


def load_ground_truth() -> List[Dict]:
    """Load test questions"""
    with open(GROUND_TRUTH_PATH, 'r') as f:
        data = json.load(f)
    return data['questions']


def category_to_intention(category: str) -> RulebookQueryIntent:
    """Map test question category to RulebookQueryIntent"""
    mapping = {
        "RULE_MECHANICS": RulebookQueryIntent.RULE_MECHANICS,
        "DESCRIBE_ENTITY": RulebookQueryIntent.DESCRIBE_ENTITY,
        "COMPARE_ENTITIES": RulebookQueryIntent.COMPARE_ENTITIES,
        "CALCULATE_VALUES": RulebookQueryIntent.CALCULATE_VALUES,
        "COMBINED": RulebookQueryIntent.RULE_MECHANICS,  # Default for combined
        # New category mappings for expanded tests
        "CLASS_FEATURES": RulebookQueryIntent.DESCRIBE_ENTITY,  # Class features are entities
        "SPELLCASTING": RulebookQueryIntent.DESCRIBE_ENTITY,  # Spell descriptions
        "COMBAT": RulebookQueryIntent.RULE_MECHANICS,  # Combat rules/mechanics
        "EQUIPMENT": RulebookQueryIntent.DESCRIBE_ENTITY,  # Equipment descriptions
        "EXPLORATION": RulebookQueryIntent.RULE_MECHANICS,  # Exploration rules
        "CREATURES": RulebookQueryIntent.DESCRIBE_ENTITY,  # Creature descriptions
    }
    return mapping.get(category, RulebookQueryIntent.DESCRIBE_ENTITY)


def extract_entities_from_query(query: str) -> List[str]:
    """Simple entity extraction for testing (just use the query as-is)"""
    # In production, this would come from the entity extractor
    # For now, we pass an empty list and rely on semantic search
    return []


def evaluate_openai_system(verbose: bool = True) -> OpenAIEvaluationResult:
    """
    Evaluate the production OpenAI-based rulebook system.
    
    Returns:
        OpenAIEvaluationResult with all metrics
    """
    print("=" * 70)
    print("EVALUATING OPENAI BASELINE (text-embedding-3-large)")
    print("=" * 70)
    
    # Load the production rulebook storage
    print("\nLoading rulebook storage...")
    storage = RulebookStorage()
    if not storage.load_from_disk():
        raise RuntimeError("Failed to load rulebook storage. Run build_rulebook_storage.py first.")
    
    print(f"Loaded {len(storage.sections)} sections")
    
    # Initialize the query router
    print("Initializing RulebookQueryRouter...")
    router = RulebookQueryRouter(storage)
    
    # Load test questions
    test_questions = load_ground_truth()
    print(f"Loaded {len(test_questions)} test questions\n")
    
    # Initialize result tracking
    result = OpenAIEvaluationResult()
    k_values = EVAL_K_VALUES
    
    recall_sums = {k: 0.0 for k in k_values}
    hit_sums = {k: 0.0 for k in k_values}
    mrr_sum = 0.0
    latency_sum = 0.0
    total_cache_hits = 0
    total_cache_misses = 0
    total_api_calls = 0
    
    print("-" * 70)
    if verbose:
        print(f"{'ID':<15} {'MRR':>6} {'R@1':>5} {'R@3':>5} {'R@5':>5} {'ms':>7} {'Retrieved IDs'}")
        print("-" * 70)
    
    for question in test_questions:
        question_id = question['id']
        query = question['question']
        category = question['category']
        relevant_ids = set(question['relevant_sections'])
        
        # Get intention from category
        intention = category_to_intention(category)
        entities = extract_entities_from_query(query)
        
        # Run the query
        start = time.perf_counter()
        search_results, performance = router.query(
            intention=intention,
            user_query=query,
            entities=entities,
            context_hints=[],
            k=10  # Get top 10 for evaluation
        )
        latency = (time.perf_counter() - start) * 1000
        
        # Extract section IDs from results
        retrieved_ids = [r.section.id for r in search_results]
        
        # Compute metrics
        question_metrics = {
            'question_id': question_id,
            'query': query,
            'category': category,
            'intention': intention.value,
            'relevant_sections': list(relevant_ids),
            'retrieved_sections': retrieved_ids[:5],
            'latency_ms': latency,
            'embedding_cache_hits': performance.embedding_cache_hits,
            'embedding_cache_misses': performance.embedding_cache_misses,
            'embedding_api_calls': performance.embedding_api_calls,
        }
        
        # Track cache stats
        total_cache_hits += performance.embedding_cache_hits
        total_cache_misses += performance.embedding_cache_misses
        total_api_calls += performance.embedding_api_calls
        
        # Recall@k for each k
        for k in k_values:
            recall = compute_recall_at_k(retrieved_ids, relevant_ids, k)
            hit = compute_hit_at_k(retrieved_ids, relevant_ids, k)
            recall_sums[k] += recall
            hit_sums[k] += hit
            question_metrics[f'recall@{k}'] = recall
            question_metrics[f'hit@{k}'] = hit
        
        # MRR
        mrr = compute_mrr(retrieved_ids, relevant_ids)
        mrr_sum += mrr
        question_metrics['mrr'] = mrr
        
        latency_sum += latency
        result.per_question_results.append(question_metrics)
        
        if verbose:
            r1 = question_metrics.get('recall@1', 0)
            r3 = question_metrics.get('recall@3', 0)
            r5 = question_metrics.get('recall@5', 0)
            top3_ids = retrieved_ids[:3]
            print(f"{question_id:<15} {mrr:>6.3f} {r1:>5.2f} {r3:>5.2f} {r5:>5.2f} {latency:>6.0f}ms {top3_ids}")
    
    # Compute averages
    n = len(test_questions)
    for k in k_values:
        result.recall_at_k[k] = recall_sums[k] / n
    result.mrr = mrr_sum / n
    result.avg_latency_ms = latency_sum / n
    result.total_api_calls = total_api_calls
    
    if total_cache_hits + total_cache_misses > 0:
        result.cache_hit_rate = total_cache_hits / (total_cache_hits + total_cache_misses)
    
    # Print summary
    print("-" * 70)
    print("\nSUMMARY")
    print("=" * 70)
    print(f"Retriever:     {result.retriever_name}")
    print(f"MRR:           {result.mrr:.3f}")
    print(f"Recall@1:      {result.recall_at_k.get(1, 0):.3f}")
    print(f"Recall@3:      {result.recall_at_k.get(3, 0):.3f}")
    print(f"Recall@5:      {result.recall_at_k.get(5, 0):.3f}")
    print(f"Recall@10:     {result.recall_at_k.get(10, 0):.3f}")
    print(f"Avg Latency:   {result.avg_latency_ms:.1f}ms")
    print(f"API Calls:     {result.total_api_calls}")
    print(f"Cache Hit %:   {result.cache_hit_rate:.1%}")
    print("=" * 70)
    
    return result


def analyze_failures(result: OpenAIEvaluationResult) -> None:
    """Analyze questions where retrieval failed"""
    print("\n" + "=" * 70)
    print("FAILURE ANALYSIS (Questions with MRR = 0)")
    print("=" * 70)
    
    failures = [q for q in result.per_question_results if q['mrr'] == 0]
    
    if not failures:
        print("No complete failures (all questions had at least one relevant result in top 10)")
        return
    
    print(f"Found {len(failures)} questions with MRR=0:\n")
    
    for q in failures:
        print(f"  {q['question_id']}: {q['query']}")
        print(f"    Expected: {q['relevant_sections']}")
        print(f"    Got:      {q['retrieved_sections']}")
        print()


def save_results(result: OpenAIEvaluationResult) -> None:
    """Save results to JSON"""
    output_path = RESULTS_PATH / "openai_baseline_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        'retriever_name': result.retriever_name,
        'summary': {
            'mrr': result.mrr,
            'recall_at_k': result.recall_at_k,
            'avg_latency_ms': result.avg_latency_ms,
            'total_api_calls': result.total_api_calls,
            'cache_hit_rate': result.cache_hit_rate,
        },
        'per_question_results': result.per_question_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nResults saved to {output_path}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate OpenAI baseline retrieval")
    parser.add_argument('--verbose', '-v', action='store_true', help='Print per-question results')
    parser.add_argument('--analyze', '-a', action='store_true', help='Analyze failure cases')
    parser.add_argument('--save', '-s', action='store_true', help='Save results to JSON')
    
    args = parser.parse_args()
    
    # Default to verbose
    verbose = args.verbose if args.verbose else True
    
    result = evaluate_openai_system(verbose=verbose)
    
    if args.analyze:
        analyze_failures(result)
    
    if args.save:
        save_results(result)
    
    return result


if __name__ == "__main__":
    main()
