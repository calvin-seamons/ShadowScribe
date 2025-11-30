"""
Context Dependency Detection Module

Provides tools for detecting whether a conversational query depends on
prior context or is standalone.

Two approaches:
1. Zero-shot: Uses cosine similarity between query and history embeddings
2. Fine-tuned: Trained classifier on labeled examples
"""

from context_detector.zero_shot import ZeroShotDetector, ZeroShotResult, get_model_info

__all__ = [
    "ZeroShotDetector",
    "ZeroShotResult",
    "get_model_info"
]
