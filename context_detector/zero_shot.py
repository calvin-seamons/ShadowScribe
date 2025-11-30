"""
Zero-Shot Context Dependency Detection using Sentence Transformers

Uses cosine similarity between the follow-up query and conversation history
to determine if a query is context-dependent.

Hypothesis: If Q2 has high semantic similarity to Q1+A1, it likely depends on that context.
"""

import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class ZeroShotResult:
    """Result from zero-shot context dependency detection"""
    query: str
    history_text: str
    similarity_score: float
    is_context_dependent: bool
    threshold: float
    inference_time_ms: float
    model_name: str


class ZeroShotDetector:
    """
    Detects context dependency using cosine similarity between embeddings.

    Approach: Embed Q2 and (Q1 + A1), compute cosine similarity.
    If similarity > threshold, classify as context-dependent.
    """

    # Available models to compare (smallest to largest)
    MODELS = {
        "paraphrase-MiniLM-L3-v2": {
            "params": "17M",
            "size_mb": 61,
            "layers": 3
        },
        "all-MiniLM-L6-v2": {
            "params": "22M",
            "size_mb": 80,
            "layers": 6
        },
        "all-MiniLM-L12-v2": {
            "params": "33M",
            "size_mb": 120,
            "layers": 12
        }
    }

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", threshold: float = 0.5):
        """
        Initialize the detector with a specific model.

        Args:
            model_name: Name of the sentence transformer model
            threshold: Similarity threshold for context dependency (0-1)
        """
        if model_name not in self.MODELS:
            raise ValueError(f"Model {model_name} not in supported models: {list(self.MODELS.keys())}")

        self.model_name = model_name
        self.threshold = threshold

        print(f"[ZeroShotDetector] Loading {model_name}...")
        start = time.time()
        self.model = SentenceTransformer(model_name)
        load_time = time.time() - start
        print(f"[ZeroShotDetector] Model loaded in {load_time:.2f}s")

    def _format_history(self, conversation_history: List[Dict[str, str]]) -> str:
        """Format conversation history into a single string for embedding"""
        parts = []
        for turn in conversation_history:
            role = turn.get("role", "unknown")
            content = turn.get("content", "")
            # Truncate long responses
            if len(content) > 500:
                content = content[:500] + "..."
            parts.append(f"{role}: {content}")
        return " ".join(parts)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def detect(
        self,
        query: str,
        conversation_history: List[Dict[str, str]]
    ) -> ZeroShotResult:
        """
        Detect if a query is context-dependent.

        Args:
            query: The follow-up query (Q2)
            conversation_history: Prior turns [{"role": "user/assistant", "content": "..."}]

        Returns:
            ZeroShotResult with similarity score and classification
        """
        # If no history, can't be context-dependent
        if not conversation_history:
            return ZeroShotResult(
                query=query,
                history_text="",
                similarity_score=0.0,
                is_context_dependent=False,
                threshold=self.threshold,
                inference_time_ms=0.0,
                model_name=self.model_name
            )

        start_time = time.time()

        # Format history
        history_text = self._format_history(conversation_history)

        # Embed both texts
        embeddings = self.model.encode([query, history_text])
        query_embedding = embeddings[0]
        history_embedding = embeddings[1]

        # Compute similarity
        similarity = self._cosine_similarity(query_embedding, history_embedding)

        inference_time_ms = (time.time() - start_time) * 1000

        return ZeroShotResult(
            query=query,
            history_text=history_text,
            similarity_score=similarity,
            is_context_dependent=similarity > self.threshold,
            threshold=self.threshold,
            inference_time_ms=inference_time_ms,
            model_name=self.model_name
        )

    def detect_batch(
        self,
        queries: List[str],
        histories: List[List[Dict[str, str]]]
    ) -> List[ZeroShotResult]:
        """
        Batch detection for efficiency.

        Args:
            queries: List of follow-up queries
            histories: List of conversation histories (one per query)

        Returns:
            List of ZeroShotResults
        """
        if len(queries) != len(histories):
            raise ValueError("queries and histories must have same length")

        results = []

        # Prepare all texts for batch embedding
        all_texts = []
        history_texts = []

        for query, history in zip(queries, histories):
            all_texts.append(query)
            if history:
                h_text = self._format_history(history)
                all_texts.append(h_text)
                history_texts.append(h_text)
            else:
                all_texts.append("")
                history_texts.append("")

        start_time = time.time()

        # Batch encode
        all_embeddings = self.model.encode(all_texts)

        total_time_ms = (time.time() - start_time) * 1000
        per_query_time = total_time_ms / len(queries)

        # Process results
        for i, (query, history, h_text) in enumerate(zip(queries, histories, history_texts)):
            query_idx = i * 2
            history_idx = i * 2 + 1

            if history:
                similarity = self._cosine_similarity(
                    all_embeddings[query_idx],
                    all_embeddings[history_idx]
                )
            else:
                similarity = 0.0

            results.append(ZeroShotResult(
                query=query,
                history_text=h_text,
                similarity_score=similarity,
                is_context_dependent=similarity > self.threshold,
                threshold=self.threshold,
                inference_time_ms=per_query_time,
                model_name=self.model_name
            ))

        return results

    def find_optimal_threshold(
        self,
        queries: List[str],
        histories: List[List[Dict[str, str]]],
        labels: List[bool],
        thresholds: Optional[List[float]] = None
    ) -> Tuple[float, Dict]:
        """
        Find the optimal threshold by testing multiple values.

        Args:
            queries: List of test queries
            histories: List of conversation histories
            labels: True labels (True = context-dependent)
            thresholds: Thresholds to test (default: 0.1 to 0.9 in 0.05 steps)

        Returns:
            Tuple of (best_threshold, results_dict)
        """
        if thresholds is None:
            thresholds = [round(t, 2) for t in np.arange(0.1, 0.95, 0.05)]

        # Get similarity scores once
        all_texts = []
        for query, history in zip(queries, histories):
            all_texts.append(query)
            all_texts.append(self._format_history(history) if history else "")

        embeddings = self.model.encode(all_texts)

        similarities = []
        for i in range(len(queries)):
            query_emb = embeddings[i * 2]
            history_emb = embeddings[i * 2 + 1]
            if histories[i]:
                sim = self._cosine_similarity(query_emb, history_emb)
            else:
                sim = 0.0
            similarities.append(sim)

        # Test each threshold
        results = {}
        best_f1 = 0
        best_threshold = 0.5

        for threshold in thresholds:
            predictions = [sim > threshold for sim in similarities]

            # Calculate metrics
            tp = sum(1 for p, l in zip(predictions, labels) if p and l)
            fp = sum(1 for p, l in zip(predictions, labels) if p and not l)
            fn = sum(1 for p, l in zip(predictions, labels) if not p and l)
            tn = sum(1 for p, l in zip(predictions, labels) if not p and not l)

            accuracy = (tp + tn) / len(labels) if labels else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

            results[threshold] = {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn
            }

            if f1 > best_f1:
                best_f1 = f1
                best_threshold = threshold

        return best_threshold, results


def get_model_info() -> Dict:
    """Return information about available models"""
    return ZeroShotDetector.MODELS.copy()


# Quick test
if __name__ == "__main__":
    print("Testing ZeroShotDetector...")

    detector = ZeroShotDetector("all-MiniLM-L6-v2", threshold=0.4)

    # Test 1: Context-dependent query
    history1 = [
        {"role": "user", "content": "What is Fireball?"},
        {"role": "assistant", "content": "Fireball is a 3rd-level evocation spell..."}
    ]
    result1 = detector.detect("What's its damage?", history1)
    print(f"\nTest 1 - Context Dependent:")
    print(f"  Query: {result1.query}")
    print(f"  Similarity: {result1.similarity_score:.3f}")
    print(f"  Classified as dependent: {result1.is_context_dependent}")
    print(f"  Time: {result1.inference_time_ms:.1f}ms")

    # Test 2: Standalone query
    history2 = [
        {"role": "user", "content": "What is Fireball?"},
        {"role": "assistant", "content": "Fireball is a 3rd-level evocation spell..."}
    ]
    result2 = detector.detect("How does grappling work in 5e?", history2)
    print(f"\nTest 2 - Standalone:")
    print(f"  Query: {result2.query}")
    print(f"  Similarity: {result2.similarity_score:.3f}")
    print(f"  Classified as dependent: {result2.is_context_dependent}")
    print(f"  Time: {result2.inference_time_ms:.1f}ms")

    print("\n✅ ZeroShotDetector tests complete!")
