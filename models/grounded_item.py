from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List


class GroundedItem(BaseModel):
    """
    Represents a retrieved content chunk from a vector store (Azure AI Search,
    Cosmos DB Vector Index, or in-memory fallback). Used to ground the
    ContentCreatorAgent's marketing variant generation.

    This model directly reflects the structure returned by the async RAGService.
    """

    text: str = Field(
        ...,
        description="The relevant text chunk retrieved from product documentation or knowledge base."
    )

    source: str = Field(
        ...,
        description="Document, dataset, or source identifier from which the chunk was retrieved."
    )

    score: float = Field(
        ...,
        description="Similarity score from vector search (0–1 range). Higher = more relevant."
    )

    chunk_id: Optional[str] = Field(
        None,
        description="Unique chunk identifier assigned during vectorization (optional)."
    )

    page: Optional[int] = Field(
        None,
        description="Page number or positional index within the source document (optional)."
    )

    embedding: Optional[List[float]] = Field(
        None,
        description="Optional embedding vector stored for debugging, reranking, or clustering."
    )
