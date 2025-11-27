# services/vector_store/in_memory.py

from typing import Dict, List, Any, Tuple
import math


class InMemoryVectorStore:
    """
    Lightweight in-memory vector store for local dev, testing RAG,
    and running the pipeline without provisioning Azure Cognitive Search.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}

    def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        """
        Store or update an item in the in-memory vector index.
        """
        self._store[id] = {
            "vector": vector,
            "metadata": metadata
        }

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0

        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, Dict[str, Any], float]]:
        """
        Return top_k vector matches as (id, metadata, similarity_score).
        """
        results: List[Tuple[str, Dict[str, Any], float]] = []

        for doc_id, payload in self._store.items():
            score = self._cosine_similarity(query_vector, payload["vector"])
            results.append((doc_id, payload["metadata"], score))

        # Sort by score descending
        results.sort(key=lambda x: x[2], reverse=True)

        return results[:top_k]
