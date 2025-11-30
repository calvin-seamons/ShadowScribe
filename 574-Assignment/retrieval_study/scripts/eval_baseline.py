#!/usr/bin/env python
"""Evaluate baseline OpenAI embeddings against test questions"""
import pickle
import numpy as np
import json
import time
import sys
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

import openai

def main():
    # Load sections with OpenAI embeddings
    storage_path = Path(__file__).parent.parent.parent.parent / 'knowledge_base/processed_rulebook/rulebook_storage.pkl'
    with open(storage_path, 'rb') as f:
        data = pickle.load(f)

    sections = data['sections']
    section_ids = []
    embeddings = []

    for sid, sec in sections.items():
        if sec.get('vector'):
            section_ids.append(sid)
            embeddings.append(sec['vector'])

    embeddings = np.array(embeddings)
    print(f'Loaded {len(section_ids)} sections with OpenAI embeddings')
    print(f'Embedding dim: {embeddings.shape[1]}')

    # Load test questions
    gt_path = Path(__file__).parent.parent / 'ground_truth/test_questions.json'
    with open(gt_path, 'r') as f:
        test_data = json.load(f)

    questions = test_data['questions']

    # Run evaluation
    client = openai.OpenAI()
    total_mrr = 0
    total_recall_1 = 0
    total_recall_3 = 0
    total_recall_5 = 0
    total_latency = 0

    for q in questions:
        query = q['question']
        relevant = set(q['relevant_sections'])
        
        # Get query embedding from OpenAI
        start = time.perf_counter()
        resp = client.embeddings.create(model='text-embedding-3-small', input=query)
        query_emb = np.array(resp.data[0].embedding)
        
        # Normalize
        query_emb = query_emb / np.linalg.norm(query_emb)
        
        # Compute similarities
        sims = np.dot(embeddings, query_emb)
        top_idx = np.argsort(sims)[::-1][:10]
        latency = (time.perf_counter() - start) * 1000
        
        retrieved = [section_ids[i] for i in top_idx]
        
        # MRR
        mrr = 0
        for rank, sid in enumerate(retrieved, 1):
            if sid in relevant:
                mrr = 1/rank
                break
        
        # Recall@k
        r1 = len(set(retrieved[:1]) & relevant) / len(relevant) if relevant else 0
        r3 = len(set(retrieved[:3]) & relevant) / len(relevant) if relevant else 0
        r5 = len(set(retrieved[:5]) & relevant) / len(relevant) if relevant else 0
        
        total_mrr += mrr
        total_recall_1 += r1
        total_recall_3 += r3
        total_recall_5 += r5
        total_latency += latency
        
        print(f"  {q['id']}: MRR={mrr:.3f}, R@5={r5:.3f}, latency={latency:.0f}ms")

    n = len(questions)
    print(f'\n{"="*60}')
    print(f'BASELINE: OpenAI text-embedding-3-large')
    print(f'{"="*60}')
    print(f'MRR:      {total_mrr/n:.3f}')
    print(f'Recall@1: {total_recall_1/n:.3f}')
    print(f'Recall@3: {total_recall_3/n:.3f}')
    print(f'Recall@5: {total_recall_5/n:.3f}')
    print(f'Avg latency: {total_latency/n:.0f}ms (includes API call)')


if __name__ == "__main__":
    main()
