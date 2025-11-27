from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from models.citation import Citation


class Variant(BaseModel):
    """
    Represents one grounded marketing message variant.
    Produced by ContentCreatorAgent using async RAG grounding.
    Consumed by ComplianceOfficerAgent and ExperimentRunnerAgent.
    """

    variant_id: str = Field(
        ...,
        description="Unique identifier for the variant (A, B, C, etc.)"
    )

    subject: Optional[str] = Field(
        None,
        description="Subject line or title for email/push content"
    )

    body: str = Field(
        ...,
        description="The generated marketing message body text, with inline citations"
    )

    mode: str = Field(
        ...,
        description="Creative mode used: precision, brand_voice, adaptive_creative, high_variance, divergent_ideation"
    )

    citations: List[Citation] = Field(
        default_factory=list,
        description="Structured citation objects derived from grounded content"
    )

    embeddings: Optional[List[float]] = Field(
        None,
        description="Optional embedding vector for semantic similarity or clustering"
    )

    score: Optional[float] = Field(
        None,
        description="Optional ranking score assigned by experiment analysis or variant selection"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the variant was generated"
    )
