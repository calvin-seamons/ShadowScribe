"""
Classifier backends for query routing, tool selection, and entity extraction.

This module provides both LLM-based and local model-based classifiers
that can be used interchangeably via the ClassifierBackend protocol.

LocalClassifier requires torch and is imported lazily to avoid import
errors in environments where torch is not installed (e.g., Docker API container).
"""

from .base import ClassifierBackend, ClassificationResult

# Lazy import for LocalClassifier to avoid torch dependency at module level
def get_local_classifier():
    """Get LocalClassifier class (requires torch to be installed)."""
    from .local_classifier import LocalClassifier
    return LocalClassifier

__all__ = [
    'ClassifierBackend',
    'ClassificationResult', 
    'get_local_classifier',
]
