"""
Evaluation metrics for retrieval quality
"""
from dataclasses import dataclass, field
from typing import List, Dict, Set
import numpy as np


@dataclass
class EvaluationResult:
    """Container for evaluation results"""
    retriever_name: str
    recall_at_k: Dict[int, float] = field(default_factory=dict)  # k -> recall
    mrr: float = 0.0
    avg_latency_ms: float = 0.0
    per_question_results: List[Dict] = field(default_factory=list)


def compute_recall_at_k(
    retrieved_ids: List[str], 
    relevant_ids: Set[str], 
    k: int
) -> float:
    """
    Compute Recall@k: what fraction of relevant documents are in top-k results.
    
    Args:
        retrieved_ids: List of retrieved section IDs (in order)
        relevant_ids: Set of ground truth relevant section IDs
        k: Number of top results to consider
        
    Returns:
        Recall@k score (0-1)
    """
    if not relevant_ids:
        return 0.0
    
    top_k_ids = set(retrieved_ids[:k])
    hits = len(top_k_ids & relevant_ids)
    return hits / len(relevant_ids)


def compute_mrr(
    retrieved_ids: List[str],
    relevant_ids: Set[str]
) -> float:
    """
    Compute Mean Reciprocal Rank: 1/rank of first relevant document.
    
    Args:
        retrieved_ids: List of retrieved section IDs (in order)
        relevant_ids: Set of ground truth relevant section IDs
        
    Returns:
        Reciprocal rank (0-1), 0 if no relevant doc found
    """
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def compute_precision_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int
) -> float:
    """
    Compute Precision@k: what fraction of top-k results are relevant.
    
    Args:
        retrieved_ids: List of retrieved section IDs (in order)
        relevant_ids: Set of ground truth relevant section IDs
        k: Number of top results to consider
        
    Returns:
        Precision@k score (0-1)
    """
    top_k_ids = retrieved_ids[:k]
    if not top_k_ids:
        return 0.0
    
    hits = sum(1 for doc_id in top_k_ids if doc_id in relevant_ids)
    return hits / len(top_k_ids)


def compute_hit_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int
) -> float:
    """
    Compute Hit@k: 1 if any relevant document is in top-k, else 0.
    
    Args:
        retrieved_ids: List of retrieved section IDs (in order)
        relevant_ids: Set of ground truth relevant section IDs
        k: Number of top results to consider
        
    Returns:
        1.0 if hit, 0.0 otherwise
    """
    top_k_ids = set(retrieved_ids[:k])
    return 1.0 if (top_k_ids & relevant_ids) else 0.0


def aggregate_results(results: List[EvaluationResult]) -> Dict:
    """
    Aggregate evaluation results across multiple retrievers for comparison.
    
    Args:
        results: List of EvaluationResult objects
        
    Returns:
        Dictionary with aggregated metrics
    """
    summary = {}
    
    for result in results:
        summary[result.retriever_name] = {
            'recall@1': result.recall_at_k.get(1, 0),
            'recall@3': result.recall_at_k.get(3, 0),
            'recall@5': result.recall_at_k.get(5, 0),
            'recall@10': result.recall_at_k.get(10, 0),
            'mrr': result.mrr,
            'avg_latency_ms': result.avg_latency_ms
        }
    
    return summary
