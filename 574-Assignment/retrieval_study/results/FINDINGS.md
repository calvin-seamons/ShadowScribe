# Sentence Transformer RAG Evaluation: Core Findings

**Date**: November 30, 2025  
**Study**: Comparing embedding strategies for D&D 5e rulebook QA retrieval

---

## Executive Summary

We evaluated **5 retrieval approaches** on **24 annotated test questions** from the D&D 5e rulebook domain.

### Key Finding: Sentence Transformers Match OpenAI Quality

| System | MRR | R@5 | Latency | Cost |
|--------|-----|-----|---------|------|
| OpenAI baseline (current) | 0.744 | 64.9% | 569ms | ~$0.0001/query |
| **ST mpnet (recommended)** | 0.722 | **67.4%** | 298ms | **$0** |
| ST minilm (fastest) | 0.661 | 67.0% | **73ms** | **$0** |

**Verdict**: `all-mpnet-base-v2` is **only 3% lower MRR than OpenAI** but:
- **2x faster** (298ms vs 569ms)
- **Free** (no API cost)
- **Higher Recall@5** (67.4% vs 64.9%)

---

## Results Summary

| Retriever | MRR | R@1 | R@3 | R@5 | Latency | Cost |
|-----------|-----|-----|-----|-----|---------|------|
| **OpenAI baseline** | **0.744** | **40.3%** | **61.5%** | 64.9% | 569ms | ~$0.0001/q |
| st_section_mpnet | 0.722 | 38.9% | 61.5% | **67.4%** | 298ms | $0 |
| st_section_minilm | 0.661 | 32.6% | 59.0% | 67.0% | **73ms** | $0 |
| st_sentence_mpnet | 0.610 | 33.7% | 54.9% | 62.5% | 84ms | $0 |
| hybrid_bm25_mpnet | 0.581 | 28.1% | 41.3% | 54.5% | 86ms | $0 |

**Key Metrics:**
- **MRR (Mean Reciprocal Rank)**: How high does the first relevant result appear? (1.0 = always first)
- **Recall@k**: What fraction of relevant sections appear in top-k results?
- **Latency**: End-to-end query time (includes embedding generation)

---

## Detailed Findings

### Finding 1: Section-Level Embeddings Outperform Sentence-Level

**Contrary to our hypothesis**, chunking content into smaller sentence-level pieces (2 sentences per chunk) **decreased retrieval quality**.

| Approach | MRR | R@5 |
|----------|-----|-----|
| Section-level (mpnet) | 0.722 | 67.4% |
| Sentence-level (mpnet) | 0.610 | 62.5% |

**Why?** The D&D rulebook has relatively short, well-structured sections. Breaking them into smaller chunks:
- Loses important context (e.g., section titles that provide strong signals)
- Creates more candidates to rank (10,151 chunks vs 1,516 sections)
- The 2-sentence chunks often match semantically similar but irrelevant content

**Recommendation**: For well-structured knowledge bases with clear hierarchical sections, prefer section-level embeddings.

---

### Finding 2: Hybrid BM25+Dense Underperformed

**Surprisingly**, adding BM25 keyword matching to dense retrieval **hurt performance**.

| Approach | MRR | R@5 |
|----------|-----|-----|
| Dense only (mpnet) | 0.722 | 67.4% |
| Hybrid BM25+Dense | 0.581 | 54.5% |

**Analysis of failures:**
- `entity_005` ("Explain what a longsword is"): Hybrid returned `sun-blade`, `section-weapons` but missed `longsword`
- `calc_004` ("longsword damage"): Same issue - BM25 matched "sword" in irrelevant sections

**Why?** BM25's keyword matching:
- Over-weighted exact keyword matches in long sections (weapons list, spell lists)
- D&D entity names are often compound words that BM25 doesn't handle well
- RRF fusion diluted the strong dense signal

**Recommendation**: For domain-specific QA where concepts matter more than exact keywords, pure dense retrieval may be better.

---

### Finding 3: Model Size vs Speed Tradeoff

| Model | Dimensions | MRR | Latency | Memory |
|-------|-----------|-----|---------|--------|
| all-mpnet-base-v2 | 768 | 0.722 | 298ms | ~420MB |
| all-MiniLM-L6-v2 | 384 | 0.661 | 73ms | ~90MB |

**Tradeoff**: MiniLM is **4x faster** with only **8% lower MRR**.

For production use cases:
- **Quality-critical**: Use mpnet (0.722 MRR)
- **Latency-sensitive**: Use MiniLM (73ms, 0.661 MRR)

---

### Finding 4: Performance by Question Category

| Category | Best Retriever | Avg MRR | Notes |
|----------|---------------|---------|-------|
| RULE_MECHANICS | mpnet-section | 0.74 | Strong on conceptual questions |
| DESCRIBE_ENTITY | mpnet-section | 0.67 | Good for single-entity lookups |
| COMPARE_ENTITIES | mpnet-section | 0.75 | Comparison queries work well |
| CALCULATE_VALUES | All struggled | 0.10-0.20 | **Major weakness** |
| COMBINED | mpnet-section | 0.67 | Multi-part questions OK |

**Critical Weakness**: All retrievers performed poorly on **calculation questions**:
- "How do I calculate my attack bonus?" → retrieved weapon proficiency, not attack rules
- "What's my AC with chain mail?" → retrieved magic armor, not AC calculation rules
- "How much HP does a fighter have?" → completely irrelevant results

**Root Cause**: Calculation questions require procedural knowledge spread across multiple sections. The semantic similarity doesn't capture the "how to calculate" intent.

---

## Hypotheses: Validated vs Refuted

| Hypothesis | Result | Notes |
|------------|--------|-------|
| H1: Sentence-level has higher recall for specific questions | **REFUTED** | Section-level was better across all categories |
| H2: BM25+dense hybrid outperforms pure dense for entity names | **REFUTED** | Hybrid was worst performer |
| H3: Local sentence transformers are 10-100x cheaper than OpenAI | **VALIDATED** | $0 API cost vs ~$0.0001/query for OpenAI |

---

## Recommendations

### For This Project (ShadowScribe)
1. **Replace OpenAI `text-embedding-3-small`** with `all-mpnet-base-v2` for rulebook retrieval
   - Near-identical quality (0.722 vs 0.744 MRR)
   - Higher recall (67.4% vs 64.9% R@5)
   - Zero API cost (saves ~$0.0001/query)
   - 2x faster (298ms vs 569ms)

2. **Keep section-level chunking** - no need for finer granularity

3. **Add special handling for calculation questions**:
   - Detect "calculate", "how much", "what's my X" patterns
   - Retrieve from dedicated "formulas" section
   - Consider rule-based retrieval for known calculation types

### For Similar RAG Projects
1. **Start with section-level dense retrieval** - it's often sufficient
2. **Test before adding complexity** - hybrid approaches may not help
3. **Profile by question category** - identify systematic weaknesses early
4. **Consider query type detection** - route different query types to different strategies

---

## Technical Details

### Test Set Composition
- **24 questions** from `docs/rulebook-testqs.md`
- **5 categories**: RULE_MECHANICS, DESCRIBE_ENTITY, COMPARE_ENTITIES, CALCULATE_VALUES, COMBINED
- **Ground truth**: Manually annotated relevant section IDs

### Embedding Configuration
```python
# Section-level: 1,516 sections
# Sentence-level: 10,151 chunks (2 sentences each)
# Models: all-mpnet-base-v2 (768d), all-MiniLM-L6-v2 (384d)
# Similarity: Cosine (normalized embeddings)
```

### BM25 Configuration
```python
k1 = 1.5  # Term frequency saturation
b = 0.75  # Document length normalization
# Fusion: Reciprocal Rank Fusion (k=60)
```

---

## Files Generated

```
574-Assignment/retrieval_study/
├── results/
│   ├── comparison_results.json    # Full per-question results
│   └── FINDINGS.md                # This document
├── embeddings_cache/
│   ├── section_embeddings_all-mpnet-base-v2.pkl
│   ├── section_embeddings_all-MiniLM-L6-v2.pkl
│   ├── sentence_embeddings_all-mpnet-base-v2_chunk2.pkl
│   └── hybrid_embeddings_all-mpnet-base-v2.pkl
└── ground_truth/
    └── test_questions.json        # 24 annotated questions
```

---

## Conclusion

**Current system** (OpenAI `text-embedding-3-small`): **MRR 0.744, R@5 64.9%, 569ms, ~$0.0001/query**

**Recommended replacement** (`all-mpnet-base-v2`): **MRR 0.722, R@5 67.4%, 298ms, $0**

The sentence transformer approach is:
- **97% the quality** of OpenAI (3% lower MRR)
- **Better recall** (67.4% vs 64.9% at k=5)
- **2x faster** (no network roundtrip)
- **Free** (no API costs)

**Bottom line**: Switch to `all-mpnet-base-v2` for essentially equivalent quality at zero cost.

The main improvement opportunity is **handling calculation questions**, which require a different retrieval strategy than semantic similarity.
