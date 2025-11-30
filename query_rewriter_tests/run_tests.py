"""
Query Rewriter Test Runner

Runs the full test suite by:
1. Running Q1 through the real RAG pipeline (demo_central_engine)
2. Capturing the response as conversation history
3. Feeding Q2 + history to the QueryRewriter
4. Evaluating if the rewritten query is standalone and correct

This tests with REAL responses from the actual system, not mocked data.
"""

import sys
import asyncio
import json
import time
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from query_rewriter_tests.test_pairs import (
    ALL_TEST_PAIRS, 
    TESTS_BY_CATEGORY, 
    TESTS_BY_DIFFICULTY,
    TestPair
)


@dataclass
class TestResult:
    """Result of a single test"""
    test_id: str
    category: str
    difficulty: str
    q1: str
    a1: str  # Response from RAG pipeline
    q2: str
    rewritten_q2: str
    expected_keywords: str
    keywords_found: List[str]
    keywords_missing: List[str]
    success: bool
    inference_time_ms: float
    notes: str


def evaluate_rewrite(rewritten: str, expected_keywords: str) -> tuple:
    """
    Evaluate if the rewritten query contains expected keywords.
    
    Returns:
        (keywords_found, keywords_missing, success)
    """
    # Parse expected keywords (space-separated in the test data)
    expected = [k.lower().strip() for k in expected_keywords.split()]
    rewritten_lower = rewritten.lower()
    
    found = []
    missing = []
    
    for keyword in expected:
        if keyword in rewritten_lower:
            found.append(keyword)
        else:
            missing.append(keyword)
    
    # Success if at least 70% of keywords are found
    success_threshold = 0.7
    success = len(found) / len(expected) >= success_threshold if expected else True
    
    return found, missing, success


async def run_rag_query(query: str, demo) -> str:
    """Run a query through the RAG pipeline and get response"""
    try:
        response = await demo.process_single_query(query, show_details=False)
        return response if response else "[No response]"
    except Exception as e:
        return f"[Error: {str(e)}]"


async def run_single_test(test: TestPair, demo, rewriter, verbose: bool = True) -> TestResult:
    """Run a single test pair through the full pipeline"""
    if verbose:
        print(f"\n{'='*60}")
        print(f"Test: {test.id} ({test.category}, {test.difficulty})")
        print(f"{'='*60}")
        print(f"Q1: {test.q1}")
    
    # Step 1: Use mock_a1 if provided (non-empty), otherwise run through RAG pipeline
    if test.mock_a1 and len(test.mock_a1.strip()) > 0:
        a1 = test.mock_a1
        if verbose:
            print(f"[Using mock A1]")
    else:
        a1 = await run_rag_query(test.q1, demo)
    
    if verbose:
        # Truncate for display
        a1_display = a1[:200] + "..." if len(a1) > 200 else a1
        print(f"A1: {a1_display}")
    
    # Step 2: Build conversation history
    conversation_history = [
        {"role": "user", "content": test.q1},
        {"role": "assistant", "content": a1}
    ]
    
    # Step 3: Clear conversation history in demo to avoid interference
    demo.engine.clear_conversation_history()
    
    if verbose:
        print(f"\nQ2 (follow-up): {test.q2}")
    
    # Step 4: Run Q2 through QueryRewriter
    result = rewriter.rewrite(test.q2, conversation_history)
    
    if verbose:
        print(f"Rewritten Q2: {result.rewritten_query}")
        print(f"Inference time: {result.inference_time_ms:.1f}ms")
    
    # Step 5: Evaluate the rewrite
    found, missing, success = evaluate_rewrite(result.rewritten_query, test.expected_rewrite)
    
    if verbose:
        print(f"\nExpected keywords: {test.expected_rewrite}")
        print(f"Keywords found: {found}")
        print(f"Keywords missing: {missing}")
        print(f"Result: {'✅ PASS' if success else '❌ FAIL'}")
    
    return TestResult(
        test_id=test.id,
        category=test.category,
        difficulty=test.difficulty,
        q1=test.q1,
        a1=a1,
        q2=test.q2,
        rewritten_q2=result.rewritten_query,
        expected_keywords=test.expected_rewrite,
        keywords_found=found,
        keywords_missing=missing,
        success=success,
        inference_time_ms=result.inference_time_ms,
        notes=test.notes
    )


async def run_tests(
    tests: List[TestPair], 
    verbose: bool = True,
    save_results: bool = True
) -> List[TestResult]:
    """Run all specified tests"""
    
    print("\n" + "=" * 70)
    print("QUERY REWRITER TEST SUITE")
    print("=" * 70)
    print(f"Running {len(tests)} tests...")
    print("Loading models and pipeline...")
    
    # Import and initialize the demo engine
    from demo_central_engine import InteractiveCentralEngineDemo
    
    demo = InteractiveCentralEngineDemo(
        verbose=False,
        routing_mode="llm"  # Use llm routing
    )
    
    # Initialize the QueryRewriter
    from query_rewriter_tests.query_rewriter import QueryRewriter
    rewriter = QueryRewriter()
    
    print("Models loaded. Starting tests...\n")
    
    results = []
    start_time = time.time()
    
    for i, test in enumerate(tests):
        print(f"\n[{i+1}/{len(tests)}] Running test {test.id}...")
        
        try:
            result = await run_single_test(test, demo, rewriter, verbose=verbose)
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.id} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            # Create a failed result
            results.append(TestResult(
                test_id=test.id,
                category=test.category,
                difficulty=test.difficulty,
                q1=test.q1,
                a1="[Exception]",
                q2=test.q2,
                rewritten_q2="[Exception]",
                expected_keywords=test.expected_rewrite,
                keywords_found=[],
                keywords_missing=test.expected_rewrite.split(),
                success=False,
                inference_time_ms=0,
                notes=f"Exception: {str(e)}"
            ))
    
    total_time = time.time() - start_time
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed} ({100*passed/len(results):.1f}%)")
    print(f"Failed: {failed} ({100*failed/len(results):.1f}%)")
    print(f"Total time: {total_time:.1f}s")
    print(f"Avg inference time: {sum(r.inference_time_ms for r in results)/len(results):.1f}ms")
    
    # Breakdown by category
    print("\nBy Category:")
    categories = set(r.category for r in results)
    for cat in sorted(categories):
        cat_results = [r for r in results if r.category == cat]
        cat_passed = sum(1 for r in cat_results if r.success)
        print(f"  {cat}: {cat_passed}/{len(cat_results)} passed")
    
    # Breakdown by difficulty
    print("\nBy Difficulty:")
    for diff in ["easy", "medium", "hard"]:
        diff_results = [r for r in results if r.difficulty == diff]
        if diff_results:
            diff_passed = sum(1 for r in diff_results if r.success)
            print(f"  {diff}: {diff_passed}/{len(diff_results)} passed")
    
    # Show failed tests
    if failed > 0:
        print("\n❌ Failed Tests:")
        for r in results:
            if not r.success:
                print(f"\n  {r.test_id}:")
                print(f"    Q2: {r.q2}")
                print(f"    Rewritten: {r.rewritten_q2}")
                print(f"    Missing keywords: {r.keywords_missing}")
                print(f"    Notes: {r.notes}")
    
    # Save results
    if save_results:
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"test_results_{timestamp}.json"
        
        # Get model name from rewriter
        model_name = rewriter.MODEL_NAME
        
        # Convert to JSON-serializable format
        results_data = {
            "timestamp": timestamp,
            "model": model_name,
            "total_tests": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{100*passed/len(results):.1f}%",
            "total_time_s": total_time,
            "avg_inference_ms": sum(r.inference_time_ms for r in results)/len(results),
            "results": [asdict(r) for r in results]
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n📄 Results saved to: {results_file}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Run Query Rewriter tests")
    parser.add_argument(
        "--category", "-c",
        type=str,
        help="Run only tests from this category",
        choices=list(TESTS_BY_CATEGORY.keys())
    )
    parser.add_argument(
        "--difficulty", "-d",
        type=str,
        help="Run only tests of this difficulty",
        choices=["easy", "medium", "hard"]
    )
    parser.add_argument(
        "--test", "-t",
        type=str,
        help="Run a specific test by ID"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick mode: run only easy tests"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=True,
        help="Verbose output (default: True)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Quiet mode: minimal output"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to file"
    )
    
    args = parser.parse_args()
    
    # Select tests based on arguments
    if args.test:
        tests = [t for t in ALL_TEST_PAIRS if t.id == args.test]
        if not tests:
            print(f"Error: Test '{args.test}' not found")
            print(f"Available tests: {[t.id for t in ALL_TEST_PAIRS]}")
            sys.exit(1)
    elif args.category:
        tests = TESTS_BY_CATEGORY[args.category]
    elif args.difficulty:
        tests = TESTS_BY_DIFFICULTY[args.difficulty]
    elif args.quick:
        tests = TESTS_BY_DIFFICULTY["easy"]
    else:
        tests = ALL_TEST_PAIRS
    
    verbose = not args.quiet and args.verbose
    save = not args.no_save
    
    # Run tests
    asyncio.run(run_tests(tests, verbose=verbose, save_results=save))


if __name__ == "__main__":
    main()
