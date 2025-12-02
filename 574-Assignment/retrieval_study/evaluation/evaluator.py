"""
Main evaluator for running retrieval experiments
"""
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from .metrics import (
    compute_recall_at_k, 
    compute_mrr, 
    compute_hit_at_k,
    EvaluationResult,
    aggregate_results
)
from ..retrievers.base import BaseRetriever
from ..config import GROUND_TRUTH_PATH, EVAL_K_VALUES, RESULTS_PATH


class RetrievalEvaluator:
    """Evaluator for comparing retrieval approaches"""
    
    def __init__(
        self, 
        ground_truth_path: Optional[Path] = None,
        k_values: List[int] = None
    ):
        """
        Initialize the evaluator.
        
        Args:
            ground_truth_path: Path to test questions JSON
            k_values: List of k values for Recall@k evaluation
        """
        self.ground_truth_path = Path(ground_truth_path) if ground_truth_path else GROUND_TRUTH_PATH
        self.k_values = k_values or EVAL_K_VALUES
        self.test_questions = self._load_ground_truth()
    
    def _load_ground_truth(self) -> List[Dict]:
        """Load test questions and ground truth"""
        with open(self.ground_truth_path, 'r') as f:
            data = json.load(f)
        return data['questions']
    
    def evaluate_retriever(
        self, 
        retriever: BaseRetriever,
        max_k: int = None,
        verbose: bool = False
    ) -> EvaluationResult:
        """
        Evaluate a single retriever on all test questions.
        
        Args:
            retriever: The retriever to evaluate
            max_k: Maximum k to retrieve (default: max of k_values)
            verbose: Whether to print per-question results
            
        Returns:
            EvaluationResult with all metrics
        """
        max_k = max_k or max(self.k_values)
        
        result = EvaluationResult(retriever_name=retriever.name)
        
        # Accumulators for aggregate metrics
        recall_sums = {k: 0.0 for k in self.k_values}
        hit_sums = {k: 0.0 for k in self.k_values}
        mrr_sum = 0.0
        latency_sum = 0.0
        
        for question in self.test_questions:
            question_id = question['id']
            query = question['question']
            relevant_ids = set(question['relevant_sections'])
            
            # Run retrieval with timing
            start = time.perf_counter()
            results = retriever.retrieve(query, top_k=max_k)
            latency = (time.perf_counter() - start) * 1000
            
            retrieved_ids = [r.section_id for r in results]
            
            # Compute metrics for this question
            question_metrics = {
                'question_id': question_id,
                'query': query,
                'relevant_sections': list(relevant_ids),
                'retrieved_sections': retrieved_ids[:5],  # Store top-5 for analysis
                'latency_ms': latency
            }
            
            # Recall@k for each k
            for k in self.k_values:
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
                print(f"  {question_id}: MRR={mrr:.3f}, R@5={question_metrics.get('recall@5', 0):.3f}, "
                      f"latency={latency:.1f}ms")
        
        # Compute averages
        n = len(self.test_questions)
        for k in self.k_values:
            result.recall_at_k[k] = recall_sums[k] / n
        result.mrr = mrr_sum / n
        result.avg_latency_ms = latency_sum / n
        
        return result
    
    def evaluate_all(
        self, 
        retrievers: List[BaseRetriever],
        verbose: bool = True
    ) -> List[EvaluationResult]:
        """
        Evaluate all retrievers and return results.
        
        Args:
            retrievers: List of retrievers to evaluate
            verbose: Whether to print progress
            
        Returns:
            List of EvaluationResult objects
        """
        results = []
        
        for retriever in retrievers:
            if verbose:
                print(f"\nEvaluating {retriever.name}...")
            
            result = self.evaluate_retriever(retriever, verbose=verbose)
            results.append(result)
            
            if verbose:
                print(f"  Average MRR: {result.mrr:.3f}")
                print(f"  Recall@1: {result.recall_at_k.get(1, 0):.3f}")
                print(f"  Recall@5: {result.recall_at_k.get(5, 0):.3f}")
                print(f"  Avg latency: {result.avg_latency_ms:.1f}ms")
        
        return results
    
    def save_results(
        self, 
        results: List[EvaluationResult],
        output_path: Optional[Path] = None
    ) -> None:
        """
        Save evaluation results to JSON.
        
        Args:
            results: List of EvaluationResult objects
            output_path: Path to save results (uses default if None)
        """
        output_path = Path(output_path) if output_path else RESULTS_PATH / "comparison_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to serializable format
        output_data = {
            'summary': aggregate_results(results),
            'detailed_results': []
        }
        
        for result in results:
            result_dict = {
                'retriever_name': result.retriever_name,
                'recall_at_k': result.recall_at_k,
                'mrr': result.mrr,
                'avg_latency_ms': result.avg_latency_ms,
                'per_question_results': result.per_question_results
            }
            output_data['detailed_results'].append(result_dict)
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Results saved to {output_path}")
    
    def print_comparison_table(self, results: List[EvaluationResult]) -> None:
        """Print a comparison table of all retrievers"""
        print("\n" + "=" * 80)
        print("RETRIEVAL COMPARISON RESULTS")
        print("=" * 80)
        
        # Header
        header = f"{'Retriever':<35} {'MRR':>8} {'R@1':>8} {'R@3':>8} {'R@5':>8} {'Latency':>10}"
        print(header)
        print("-" * 80)
        
        # Sort by MRR
        sorted_results = sorted(results, key=lambda x: x.mrr, reverse=True)
        
        for result in sorted_results:
            row = (
                f"{result.retriever_name:<35} "
                f"{result.mrr:>8.3f} "
                f"{result.recall_at_k.get(1, 0):>8.3f} "
                f"{result.recall_at_k.get(3, 0):>8.3f} "
                f"{result.recall_at_k.get(5, 0):>8.3f} "
                f"{result.avg_latency_ms:>8.1f}ms"
            )
            print(row)
        
        print("=" * 80)
