#!/usr/bin/env python
"""Analyze recall failures in detail"""
import json
from pathlib import Path

results_path = Path('574-Assignment/retrieval_study/results/openai_baseline_results.json')
with open(results_path) as f:
    data = json.load(f)

print('DETAILED FAILURE ANALYSIS - Questions with R@5 < 0.5')
print('=' * 80)

for q in data['per_question_results']:
    r5 = q.get('recall@5', 0)
    if r5 < 0.5:
        print(f"\n{q['question_id']}: {q['query']}")
        print(f"  Category:  {q['category']}")
        print(f"  Expected:  {q['relevant_sections']}")
        print(f"  Got:       {q['retrieved_sections']}")
        print(f"  MRR={q['mrr']:.2f}, R@5={r5:.2f}")
        
        expected = set(q['relevant_sections'])
        got = set(q['retrieved_sections'])
        missing = expected - got
        print(f"  MISSING:   {list(missing)}")
