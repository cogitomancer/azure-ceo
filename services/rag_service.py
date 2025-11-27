from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from models.customer_event import CustomerEvent
from models.grounded_item import GroundedItem
from models.citation import Citation


class GroundedContent(BaseModel):
    """
    Full RAG grounding bundle passed through the orchestrator.
    Contains:
    - The originating customer event
    - Embeddings for semantic search
    - Retrieved items from vector search
    - Structured citations for factual grounding
    """

    event: Optional[CustomerEvent] = Field(
        None,
        description="Origination event. May be null if call is initiated manually or by batch workflow."
    )

    embedding: Optional[List[float]] = Field(
        None,
        description="Dense embedding representation of the event text/query."
    )

    grounded_items: List[GroundedItem] = Field(
        ...,
        description="Top-K retrieved items from vector search, ranked by relevance."
    )

    citations: List[Citation] = Field(
        default_factory=list,
        description="Citations derived from grounded items for inline factual grounding."
    )

    # Optional: reranker scores (Azure Search re-ranker, Cohere ReRank, etc.)
    rerank_scores: Optional[List[float]] = Field(
        None,
        description="Optional reranker scores aligned with grounded_items."
    )

    top_k: int = Field(
        5,
        description="Number of retrieved items used for grounding."
    )

    model_config = {
        "json_encoders": {
            # reserved for future conversion (numpy, datetime, etc.)
        }
    }
