"""
Configuration for the retrieval study
"""
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent  # ShadowScribe2.0
STUDY_ROOT = Path(__file__).parent  # retrieval_study

# Data paths
RULEBOOK_STORAGE_PATH = PROJECT_ROOT / "knowledge_base" / "processed_rulebook" / "rulebook_storage.pkl"
GROUND_TRUTH_PATH = STUDY_ROOT / "ground_truth" / "test_questions.json"
RESULTS_PATH = STUDY_ROOT / "results"

# Embedding cache paths
EMBEDDINGS_CACHE_DIR = STUDY_ROOT / "embeddings_cache"

# Sentence transformer models to evaluate
SENTENCE_TRANSFORMER_MODELS = {
    "mpnet": "all-mpnet-base-v2",      # Best quality, 768 dims
    "minilm": "all-MiniLM-L6-v2",      # Fast, 384 dims
}

# Default model for experiments
DEFAULT_ST_MODEL = "all-mpnet-base-v2"

# Evaluation settings
EVAL_K_VALUES = [1, 3, 5, 10]  # k values for Recall@k
DEFAULT_TOP_K = 5

# BM25 settings (for hybrid retriever)
BM25_K1 = 1.5
BM25_B = 0.75

# Hybrid fusion settings
RRF_K = 60  # Reciprocal Rank Fusion constant
