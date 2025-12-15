#!/usr/bin/env python
"""
Full Pipeline Rulebook Retrieval Evaluation

Tests the COMPLETE production pipeline including:
- LLM-based tool selection and intent classification  
- Gazetteer entity extraction
- RulebookQueryRouter with hybrid search
- Cross-encoder reranking (if enabled)
- Contextual embeddings (if present)

This evaluates what users actually experience - the full end-to-end system.

Usage:
    uv run python -m scripts.eval_full_pipeline_recall
    uv run python -m scripts.eval_full_pipeline_recall --verbose
    uv run python -m scripts.eval_full_pipeline_recall --top-k 10
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple

# Standard project root setup
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.central_engine import CentralEngine
from src.llm.central_prompt_manager import CentralPromptManager
from src.rag.context_assembler import ContextAssembler
from src.config import get_config
from src.rag.character.character_manager import CharacterManager
from src.rag.rulebook.rulebook_storage import RulebookStorage
from src.rag.session_notes.session_notes_storage import SessionNotesStorage
from src.rag.rulebook.rulebook_types import SearchResult


@dataclass
class EvalResult:
    """Result for a single question evaluation."""
    question_id: str
    question: str
    category: str
    expected_sections: List[str]
    retrieved_sections: List[str]
    hits: List[str]
    misses: List[str]
    recall: float
    mrr: float
    first_hit_rank: Optional[int]
    detected_intent: Optional[str]
    extracted_entities: List[str]
    tool_selected: bool  # Did the LLM select the rulebook tool?


def load_test_questions() -> List[dict]:
    """Load the ground truth test questions."""
    test_file = project_root / "574-Assignment" / "retrieval_study" / "ground_truth" / "test_questions.json"
    
    with open(test_file) as f:
        data = json.load(f)
    
    return data["questions"]


class PipelineEvaluator:
    """Evaluator that hooks into the CentralEngine to capture retrieval results."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.config = get_config()
        
        print("=" * 70)
        print("FULL PIPELINE RULEBOOK EVALUATION")
        print("=" * 70)
        
        # Load storage components
        print("\nInitializing components...")
        
        # Load character (needed for pipeline but not used in rulebook queries)
        character_manager = CharacterManager()
        try:
            self.character = character_manager.load_character("Duskryn Nightwarden")
            print(f"  ✓ Character loaded: {self.character.character_base.name}")
        except Exception as e:
            print(f"  ⚠ Character load failed: {e}")
            self.character = None
        
        # Load rulebook storage
        self.rulebook_storage = RulebookStorage()
        if self.rulebook_storage.load_from_disk("rulebook_storage.pkl"):
            print(f"  ✓ Rulebook storage loaded ({len(self.rulebook_storage.sections)} sections)")
        else:
            raise RuntimeError("Could not load rulebook storage!")
        
        # Load session notes (needed for pipeline)
        try:
            session_notes_storage = SessionNotesStorage()
            self.campaign_session_notes = session_notes_storage.get_campaign("main_campaign")
            if self.campaign_session_notes:
                print(f"  ✓ Session notes loaded")
            else:
                self.campaign_session_notes = None
        except Exception:
            self.campaign_session_notes = None
        
        # Create CentralEngine
        context_assembler = ContextAssembler()
        prompt_manager = CentralPromptManager(context_assembler)
        
        self.engine = CentralEngine.create_from_config(
            prompt_manager,
            character=self.character,
            rulebook_storage=self.rulebook_storage,
            campaign_session_notes=self.campaign_session_notes
        )
        
        # Check config
        print(f"\nConfiguration:")
        print(f"  Reranking enabled: {self.config.rulebook_rerank_enabled}")
        print(f"  Candidate pool: {self.config.rulebook_candidate_pool_size}")
        print(f"  BM25 weight: {self.config.rulebook_bm25_weight}")
        print(f"  Semantic weight: {self.config.rulebook_semantic_weight}")
        
        contextual_path = project_root / "knowledge_base" / "processed_rulebook" / "contextual_prefixes.json"
        print(f"  Contextual prefixes: {'✓ found' if contextual_path.exists() else '✗ not found'}")
        
        print("\n✓ Pipeline ready!")
    
    async def evaluate_question(
        self,
        question: dict,
        top_k: int = 10
    ) -> EvalResult:
        """Evaluate a single question through the full pipeline."""
        query = question["question"]
        expected = set(question["relevant_sections"])
        
        # Use character name for pipeline (required by tool selector)
        character_name = self.character.character_base.name if self.character else "Test Character"
        
        # Step 1: Run tool selection (LLM call)
        tool_selector_output = await self.engine._call_tool_selector(query, character_name)
        
        # Check if rulebook was selected
        tools_needed = tool_selector_output.tools_needed
        rulebook_tool = next(
            (t for t in tools_needed if t.get("tool") == "rulebook"),
            None
        )
        
        tool_selected = rulebook_tool is not None
        detected_intent = rulebook_tool.get("intention") if rulebook_tool else None
        
        # Step 2: Extract entities using Gazetteer
        entity_output = self.engine._extract_entities_gazetteer(query)
        extracted_entities = [e.get("name", e.get("text", "")) for e in entity_output.entities]
        
        # Step 3: Execute retrieval if rulebook was selected
        retrieved_ids = []
        if tool_selected and self.engine.rulebook_router:
            from src.rag.rulebook.rulebook_types import RulebookQueryIntent
            try:
                intention_enum = RulebookQueryIntent(detected_intent.lower())
                results, _metrics = self.engine.rulebook_router.query(
                    intention=intention_enum,
                    user_query=query,
                    entities=extracted_entities,
                    context_hints=[],
                    k=top_k
                )
                retrieved_ids = [r.section.id for r in results]
            except (ValueError, AttributeError) as e:
                if self.verbose:
                    print(f"    Warning: {e}")
        
        # Calculate metrics
        retrieved_set = set(retrieved_ids)
        hits = list(expected & retrieved_set)
        misses = list(expected - retrieved_set)
        
        recall = len(hits) / len(expected) if expected else 0.0
        
        # MRR calculation
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
            first_hit_rank=first_hit_rank,
            detected_intent=detected_intent,
            extracted_entities=extracted_entities,
            tool_selected=tool_selected
        )
    
    async def run_evaluation(self, top_k: int = 10) -> dict:
        """Run full evaluation on test set."""
        questions = load_test_questions()
        print(f"\nEvaluating {len(questions)} questions with top_k={top_k}...")
        print("(This involves LLM calls for each question)\n")
        
        results: List[EvalResult] = []
        
        for i, q in enumerate(questions, 1):
            result = await self.evaluate_question(q, top_k=top_k)
            results.append(result)
            
            # Progress indicator
            status = "✓" if result.recall == 1.0 else "○" if result.recall > 0 else "✗"
            tool_status = "📚" if result.tool_selected else "⊘"
            
            if self.verbose:
                print(f"  [{i:3d}/{len(questions)}] {status} {tool_status} R={result.recall:.2f} MRR={result.mrr:.2f} | {q['id']}")
                if result.detected_intent:
                    print(f"           Intent: {result.detected_intent}, Entities: {result.extracted_entities}")
                if result.misses:
                    print(f"           Missed: {result.misses}")
            else:
                print(f"  [{i:3d}/{len(questions)}] {status} {tool_status} R={result.recall:.2f} | {q['id'][:15]}...")
        
        # Aggregate metrics
        total_recall = sum(r.recall for r in results) / len(results)
        total_mrr = sum(r.mrr for r in results) / len(results)
        perfect_recall = sum(1 for r in results if r.recall == 1.0)
        partial_recall = sum(1 for r in results if 0 < r.recall < 1.0)
        zero_recall = sum(1 for r in results if r.recall == 0)
        tool_selected_count = sum(1 for r in results if r.tool_selected)
        
        # By category
        categories = {}
        for r in results:
            if r.category not in categories:
                categories[r.category] = {"count": 0, "recall_sum": 0, "mrr_sum": 0, "tool_selected": 0}
            categories[r.category]["count"] += 1
            categories[r.category]["recall_sum"] += r.recall
            categories[r.category]["mrr_sum"] += r.mrr
            if r.tool_selected:
                categories[r.category]["tool_selected"] += 1
        
        # Print results
        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)
        
        print(f"\nOverall Metrics (top_k={top_k}):")
        print(f"  Mean Recall:      {total_recall:.3f} ({total_recall*100:.1f}%)")
        print(f"  Mean MRR:         {total_mrr:.3f}")
        print(f"  Perfect recall:   {perfect_recall}/{len(results)} ({perfect_recall/len(results)*100:.1f}%)")
        print(f"  Partial recall:   {partial_recall}/{len(results)} ({partial_recall/len(results)*100:.1f}%)")
        print(f"  Zero recall:      {zero_recall}/{len(results)} ({zero_recall/len(results)*100:.1f}%)")
        print(f"  Rulebook selected:{tool_selected_count}/{len(results)} ({tool_selected_count/len(results)*100:.1f}%)")
        
        print(f"\nRecall by Category:")
        for cat, stats in sorted(categories.items()):
            avg_recall = stats["recall_sum"] / stats["count"]
            avg_mrr = stats["mrr_sum"] / stats["count"]
            tool_pct = stats["tool_selected"] / stats["count"] * 100
            print(f"  {cat:20s}: R={avg_recall:.3f} MRR={avg_mrr:.3f} Tool={tool_pct:.0f}% (n={stats['count']})")
        
        # Worst failures
        failures = [r for r in results if r.recall < 1.0]
        failures.sort(key=lambda r: r.recall)
        
        if failures:
            print(f"\nWorst Failures (lowest recall):")
            for r in failures[:10]:
                tool_status = f"intent={r.detected_intent}" if r.tool_selected else "NOT SELECTED"
                print(f"  {r.question_id}: R={r.recall:.2f} | {tool_status}")
                print(f"    Q: {r.question[:60]}...")
                print(f"    Missed: {r.misses}")
        
        # Save results
        output_path = project_root / "574-Assignment" / "retrieval_study" / "results" / "full_pipeline_eval.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            "config": {
                "top_k": top_k,
                "rerank_enabled": self.config.rulebook_rerank_enabled,
                "candidate_pool_size": self.config.rulebook_candidate_pool_size,
                "bm25_weight": self.config.rulebook_bm25_weight,
                "semantic_weight": self.config.rulebook_semantic_weight,
            },
            "metrics": {
                "mean_recall": total_recall,
                "mean_mrr": total_mrr,
                "perfect_recall_count": perfect_recall,
                "partial_recall_count": partial_recall,
                "zero_recall_count": zero_recall,
                "tool_selected_count": tool_selected_count,
                "total_questions": len(results)
            },
            "by_category": {
                cat: {
                    "count": stats["count"],
                    "avg_recall": stats["recall_sum"] / stats["count"],
                    "avg_mrr": stats["mrr_sum"] / stats["count"],
                    "tool_selected_pct": stats["tool_selected"] / stats["count"]
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
                    "detected_intent": r.detected_intent,
                    "extracted_entities": r.extracted_entities,
                    "tool_selected": r.tool_selected
                }
                for r in results
            ]
        }
        
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"\nDetailed results saved to: {output_path}")
        
        return output_data


async def main():
    parser = argparse.ArgumentParser(description="Full pipeline rulebook recall evaluation")
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=10,
        help="Number of results to retrieve per query (default: 10)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed per-question results"
    )
    
    args = parser.parse_args()
    
    evaluator = PipelineEvaluator(verbose=args.verbose)
    await evaluator.run_evaluation(top_k=args.top_k)


if __name__ == "__main__":
    asyncio.run(main())
