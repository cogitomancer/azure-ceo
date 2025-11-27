from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ContentItem(BaseModel):
    """
    Represents a stored marketing or product content unit.
    This object is what gets chunked, embedded, and indexed in
    Azure AI Search / Cosmos DB vector stores.

    GroundedItem references these via chunk_id + source + page.
    """

    content_id: str = Field(
        ...,
        description="Unique ID of the content item (document, product entry, KB article)."
    )

    title: Optional[str] = Field(
        None,
        description="Optional title of the content/document."
    )

    body: str = Field(
        ...,
        description="Full text content body before chunking or preprocessing."
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Tags or categories associated with the content item."
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (product type, doc version, department, etc.)."
    )

    # Chunk-level info
    chunk_id: Optional[str] = Field(
        None,
        description="Chunk identifier if this entry represents a vectorized segment."
    )

    source: Optional[str] = Field(
        None,
        description="Canonical source name (e.g., 'Product Manual v2')."
    )

    page: Optional[int] = Field(
        None,
        description="Page or positional index within the source document."
    )

    # Embedding vector for semantic search
    embedding: Optional[List[float]] = Field(
        None,
        description="Embedding vector stored for vector search / RAG."
    )
