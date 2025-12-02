"""
Abstract base class for retrievers
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time


@dataclass
class RetrievalResult:
    """Result from a retrieval operation"""
    section_id: str
    score: float
    title: str = ""
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalMetrics:
    """Metrics from a single retrieval operation"""
    latency_ms: float = 0.0
    num_candidates: int = 0
    num_results: int = 0


class BaseRetriever(ABC):
    """Abstract base class for retrievers"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the retriever name/identifier"""
        pass
    
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve relevant sections for a query.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            List of RetrievalResult objects, sorted by score descending
        """
        pass
    
    def retrieve_with_metrics(self, query: str, top_k: int = 5) -> tuple[List[RetrievalResult], RetrievalMetrics]:
        """
        Retrieve relevant sections and return timing metrics.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            Tuple of (results, metrics)
        """
        start = time.perf_counter()
        results = self.retrieve(query, top_k)
        end = time.perf_counter()
        
        metrics = RetrievalMetrics(
            latency_ms=(end - start) * 1000,
            num_results=len(results)
        )
        return results, metrics
    
    @abstractmethod
    def build_index(self, sections: Dict[str, Any]) -> None:
        """
        Build the retrieval index from rulebook sections.
        
        Args:
            sections: Dictionary of section_id -> section data
        """
        pass
