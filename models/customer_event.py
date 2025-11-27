from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class CustomerEvent(BaseModel):
    """
    Core event object representing a customer-triggered action.
    This serves as the root input into the orchestrator and connects
    to async workflows such as:
    - RAG grounding
    - Variant generation
    - Segmentation
    - Experiment orchestration
    """

    # Auto-generated event identifier for full traceability
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Event classification
    event_type: str  # e.g., "signup", "purchase", "page_view", "churn_warning"

    # Timestamp for event creation
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Customer identifier (anonymized or hashed upstream if required)
    customer_id: str

    # Additional contextual metadata:
    # location, device, session, product purchased, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Optional embedding for:
    # - semantic routing
    # - personalization
    # - similarity-based retrieval
    embedding: Optional[List[float]] = None
