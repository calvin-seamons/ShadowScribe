"""
Evaluation Harness for Context Dependency Detection

Tests both zero-shot and fine-tuned approaches against the test dataset.
Generates comprehensive metrics and comparison reports.
"""

import json
import time
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from context_detector.zero_shot import ZeroShotDetector, get_model_info
from query_rewriter_tests.test_pairs import ALL_TEST_PAIRS, TESTS_BY_CATEGORY


@dataclass
class TestCase:
    """A single test case for evaluation"""
    id: str
    category: str
    difficulty: str
    q1: str
    q2: str
    is_context_dependent: bool  # Ground truth label
    mock_a1: Optional[str] = None


@dataclass
class EvaluationResult:
    """Results from evaluating a single test case"""
    test_id: str
    category: str
    difficulty: str
    q1: str
    q2: str
    ground_truth: bool
    predicted: bool
    correct: bool
    similarity_score: float
    threshold: float
    inference_time_ms: float


@dataclass
class EvaluationSummary:
    """Summary statistics for an evaluation run"""
    model_name: str
    approach: str  # "zero_shot" or "fine_tuned"
    threshold: float
    total_tests: int
    correct: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int
    tn: int
    avg_inference_ms: float
    total_time_s: float
    by_category: Dict[str, Dict]
    by_difficulty: Dict[str, Dict]


def load_test_cases() -> List[TestCase]:
    """
    Load test cases from the existing test_pairs.py

    Labels:
    - "already_standalone" category = standalone (is_context_dependent=False)
    - All other categories = context-dependent (is_context_dependent=True)
    """
    test_cases = []

    for pair in ALL_TEST_PAIRS:
        # Determine if context-dependent based on category
        is_context_dependent = pair.category != "already_standalone"

        test_cases.append(TestCase(
            id=pair.id,
            category=pair.category,
            difficulty=pair.difficulty,
            q1=pair.q1,
            q2=pair.q2,
            is_context_dependent=is_context_dependent,
            mock_a1=pair.mock_a1 if pair.mock_a1 else None
        ))

    return test_cases


def evaluate_zero_shot(
    model_name: str,
    test_cases: List[TestCase],
    threshold: float = 0.4,
    mock_responses: Optional[Dict[str, str]] = None
) -> Tuple[List[EvaluationResult], EvaluationSummary]:
    """
    Evaluate zero-shot approach on test cases.

    Args:
        model_name: Sentence transformer model to use
        test_cases: List of test cases
        threshold: Similarity threshold for classification
        mock_responses: Optional dict of test_id -> mock A1 responses

    Returns:
        Tuple of (individual results, summary)
    """
    print(f"\n{'='*60}")
    print(f"Evaluating Zero-Shot: {model_name}")
    print(f"Threshold: {threshold}")
    print(f"Test cases: {len(test_cases)}")
    print(f"{'='*60}\n")

    detector = ZeroShotDetector(model_name, threshold=threshold)

    results = []
    total_inference_time = 0
    start_time = time.time()

    for i, tc in enumerate(test_cases):
        # Build conversation history
        # Use mock A1 if available, otherwise use a generic response
        a1 = tc.mock_a1 or f"Information about: {tc.q1}"

        history = [
            {"role": "user", "content": tc.q1},
            {"role": "assistant", "content": a1}
        ]

        # Run detection
        detection = detector.detect(tc.q2, history)

        total_inference_time += detection.inference_time_ms

        result = EvaluationResult(
            test_id=tc.id,
            category=tc.category,
            difficulty=tc.difficulty,
            q1=tc.q1,
            q2=tc.q2,
            ground_truth=tc.is_context_dependent,
            predicted=detection.is_context_dependent,
            correct=detection.is_context_dependent == tc.is_context_dependent,
            similarity_score=detection.similarity_score,
            threshold=threshold,
            inference_time_ms=detection.inference_time_ms
        )
        results.append(result)

        # Progress indicator
        status = "✓" if result.correct else "✗"
        print(f"  [{i+1}/{len(test_cases)}] {status} {tc.id}: sim={detection.similarity_score:.3f} "
              f"pred={detection.is_context_dependent} actual={tc.is_context_dependent}")

    total_time = time.time() - start_time

    # Calculate summary statistics
    summary = calculate_summary(
        results=results,
        model_name=model_name,
        approach="zero_shot",
        threshold=threshold,
        total_time_s=total_time
    )

    return results, summary


def calculate_summary(
    results: List[EvaluationResult],
    model_name: str,
    approach: str,
    threshold: float,
    total_time_s: float
) -> EvaluationSummary:
    """Calculate summary statistics from results"""

    # Overall metrics
    tp = sum(1 for r in results if r.predicted and r.ground_truth)
    fp = sum(1 for r in results if r.predicted and not r.ground_truth)
    fn = sum(1 for r in results if not r.predicted and r.ground_truth)
    tn = sum(1 for r in results if not r.predicted and not r.ground_truth)

    total = len(results)
    correct = tp + tn
    accuracy = correct / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    avg_inference = sum(r.inference_time_ms for r in results) / total if total > 0 else 0

    # By category
    by_category = {}
    categories = set(r.category for r in results)
    for cat in categories:
        cat_results = [r for r in results if r.category == cat]
        cat_correct = sum(1 for r in cat_results if r.correct)
        by_category[cat] = {
            "total": len(cat_results),
            "correct": cat_correct,
            "accuracy": cat_correct / len(cat_results) if cat_results else 0
        }

    # By difficulty
    by_difficulty = {}
    for diff in ["easy", "medium", "hard"]:
        diff_results = [r for r in results if r.difficulty == diff]
        if diff_results:
            diff_correct = sum(1 for r in diff_results if r.correct)
            by_difficulty[diff] = {
                "total": len(diff_results),
                "correct": diff_correct,
                "accuracy": diff_correct / len(diff_results)
            }

    return EvaluationSummary(
        model_name=model_name,
        approach=approach,
        threshold=threshold,
        total_tests=total,
        correct=correct,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        tp=tp,
        fp=fp,
        fn=fn,
        tn=tn,
        avg_inference_ms=avg_inference,
        total_time_s=total_time_s,
        by_category=by_category,
        by_difficulty=by_difficulty
    )


def find_best_threshold(
    model_name: str,
    test_cases: List[TestCase],
    thresholds: Optional[List[float]] = None
) -> Tuple[float, Dict]:
    """
    Find the best threshold for a model by testing multiple values.

    Returns:
        Tuple of (best_threshold, all_threshold_results)
    """
    if thresholds is None:
        thresholds = [round(t, 2) for t in [0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6]]

    print(f"\n{'='*60}")
    print(f"Finding optimal threshold for {model_name}")
    print(f"Testing thresholds: {thresholds}")
    print(f"{'='*60}\n")

    detector = ZeroShotDetector(model_name, threshold=0.5)

    # Get all similarity scores once
    queries = [tc.q2 for tc in test_cases]
    histories = []
    labels = [tc.is_context_dependent for tc in test_cases]

    for tc in test_cases:
        a1 = tc.mock_a1 or f"Information about: {tc.q1}"
        histories.append([
            {"role": "user", "content": tc.q1},
            {"role": "assistant", "content": a1}
        ])

    best_threshold, results = detector.find_optimal_threshold(
        queries=queries,
        histories=histories,
        labels=labels,
        thresholds=thresholds
    )

    print(f"\nThreshold Analysis:")
    print(f"{'Threshold':<10} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1':<10}")
    print("-" * 50)
    for thresh, metrics in sorted(results.items()):
        print(f"{thresh:<10.2f} {metrics['accuracy']:<10.3f} {metrics['precision']:<10.3f} "
              f"{metrics['recall']:<10.3f} {metrics['f1']:<10.3f}")

    print(f"\nBest threshold: {best_threshold} (F1: {results[best_threshold]['f1']:.3f})")

    return best_threshold, results


def run_full_evaluation(output_dir: Optional[str] = None) -> Dict:
    """
    Run complete evaluation across all models and approaches.

    Returns:
        Dict with all results
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "results"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(exist_ok=True)

    # Load test cases
    test_cases = load_test_cases()
    print(f"Loaded {len(test_cases)} test cases")

    # Count by label
    dependent_count = sum(1 for tc in test_cases if tc.is_context_dependent)
    standalone_count = len(test_cases) - dependent_count
    print(f"  - Context-dependent: {dependent_count}")
    print(f"  - Standalone: {standalone_count}")

    models = list(get_model_info().keys())
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "test_cases_count": len(test_cases),
        "models": {}
    }

    for model_name in models:
        print(f"\n{'#'*60}")
        print(f"# Model: {model_name}")
        print(f"{'#'*60}")

        model_info = get_model_info()[model_name]

        # Find best threshold
        best_threshold, threshold_results = find_best_threshold(model_name, test_cases)

        # Run evaluation with best threshold
        results, summary = evaluate_zero_shot(
            model_name=model_name,
            test_cases=test_cases,
            threshold=best_threshold
        )

        # Store results
        all_results["models"][model_name] = {
            "model_info": model_info,
            "best_threshold": best_threshold,
            "threshold_search": threshold_results,
            "summary": asdict(summary),
            "results": [asdict(r) for r in results]
        }

        # Print summary
        print(f"\n{'='*40}")
        print(f"Summary for {model_name}")
        print(f"{'='*40}")
        print(f"Accuracy: {summary.accuracy:.1%}")
        print(f"Precision: {summary.precision:.1%}")
        print(f"Recall: {summary.recall:.1%}")
        print(f"F1 Score: {summary.f1:.3f}")
        print(f"Avg Inference: {summary.avg_inference_ms:.1f}ms")
        print(f"\nConfusion Matrix:")
        print(f"  TP: {summary.tp}  FP: {summary.fp}")
        print(f"  FN: {summary.fn}  TN: {summary.tn}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"zero_shot_eval_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n\nResults saved to: {output_file}")

    return all_results


def print_comparison_table(results: Dict):
    """Print a comparison table of all models"""
    print(f"\n{'='*80}")
    print("MODEL COMPARISON - ZERO-SHOT CONTEXT DEPENDENCY DETECTION")
    print(f"{'='*80}\n")

    headers = ["Model", "Params", "Threshold", "Accuracy", "Precision", "Recall", "F1", "Avg ms"]
    print(f"{headers[0]:<28} {headers[1]:<8} {headers[2]:<10} {headers[3]:<10} "
          f"{headers[4]:<10} {headers[5]:<8} {headers[6]:<6} {headers[7]:<8}")
    print("-" * 90)

    for model_name, data in results["models"].items():
        summary = data["summary"]
        info = data["model_info"]
        print(f"{model_name:<28} {info['params']:<8} {data['best_threshold']:<10.2f} "
              f"{summary['accuracy']:<10.1%} {summary['precision']:<10.1%} "
              f"{summary['recall']:<8.1%} {summary['f1']:<6.3f} {summary['avg_inference_ms']:<8.1f}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate context dependency detection")
    parser.add_argument("--model", type=str, help="Specific model to evaluate")
    parser.add_argument("--threshold", type=float, default=0.4, help="Similarity threshold")
    parser.add_argument("--find-threshold", action="store_true", help="Find optimal threshold")
    parser.add_argument("--output", type=str, help="Output directory for results")

    args = parser.parse_args()

    if args.model:
        test_cases = load_test_cases()
        if args.find_threshold:
            best_thresh, _ = find_best_threshold(args.model, test_cases)
            results, summary = evaluate_zero_shot(args.model, test_cases, threshold=best_thresh)
        else:
            results, summary = evaluate_zero_shot(args.model, test_cases, threshold=args.threshold)
    else:
        # Run full evaluation
        all_results = run_full_evaluation(args.output)
        print_comparison_table(all_results)
