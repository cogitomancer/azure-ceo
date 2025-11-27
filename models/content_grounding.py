from __future__ import annotations

from typing import List, Optional, Any
from pydantic import BaseModel, Field

from models.customer_event import CustomerEvent
from models.grounded_item import GroundedItem
from models.citation import Citation


class GroundedContent(BaseModel):
    """
    Represents the full RAG grounding context for a customer event or orchestrator input.
    Passed into ContentCreatorAgent to generate grounded, citation-backed variants.
    """

    # Root cause of the workflow (optional for batch or admin-triggered flows)
    event: Optional[CustomerEvent] = Field(
        None,
        description="Originating customer event. May be null for manual requests."
    )

    # Dense embedding used for vector retrieval
    embedding: Optional[List[float]] = Field(
        None,
        description="Embedding representation of the event or query text."
    )

    # Retrieved structured items
    grounded_items: List[GroundedItem] = Field(
        ...,
        description="Top-K items retrieved from vector search, ranked by relevance."
    )

    # Structured citations derived from grounded_items
    citations: List[Citation] = Field(
        default_factory=list,
        description="Citations for inline grounding."
    )

    # Optional scores from a reranker (Azure semantic ranker, Cohere ReRank, etc.)
    rerank_scores: Optional[List[float]] = Field(
        None,
        description="Optional reranker scores aligned with grounded_items."
    )

    # Additional metadata for debugging or observability
    metadata: Optional[dict] = Field(
        default_factory=dict,
        description="Optional structured metadata (latency, raw results, query text, etc.)."
    )

    top_k: int = Field(
        5,
        description="Number of retrieved items used for grounding."
    )

    model_config = {
        "json_encoders": {
            # clean future serialization (numpy, datetime, etc.)
        }
    }
