from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
import uuid


class Citation(BaseModel):
    """
    Represents a structured citation extracted from grounded content.
    Used by ContentCreatorAgent for inline grounding and by
    ComplianceOfficerAgent for factual verification.
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for traceability in logs and pipelines."
    )

    source: str = Field(
        ...,
        description="Document or dataset identifier from which the citation was derived."
    )

    source_type: str = Field(
        default="content_item",
        description="Classification (content_item, product_manual, knowledge_base, etc.)."
    )

    excerpt: Optional[str] = Field(
        None,
        description="Exact snippet of text used as factual support."
    )

    url: Optional[str] = Field(
        None,
        description="Optional public URL for transparency and external review."
    )

    relevance: Optional[float] = Field(
        None,
        description="Similarity relevance score (0–1) assigned by vector search."
    )

    chunk_id: Optional[str] = Field(
        None,
        description="Chunk identifier linking back to the exact vectorized segment."
    )

    page: Optional[int] = Field(
        None,
        description="Optional page number or positional index within the source."
    )

    model_config = {
        "json_encoders": {
            # keep clean serialization for future datetime fields if added
        }
    }
