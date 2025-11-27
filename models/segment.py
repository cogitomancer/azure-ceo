from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List, Optional


class Segment(BaseModel):
    """
    Audience segment model used by the DataSegmenterAgent
    and orchestration pipeline.
    """

    id: str
    name: str
    description: str

    # Criteria
    criteria: Dict = Field(default_factory=dict)
    sql_query: Optional[str] = None

    # Size and characteristics
    size: int = 0
    estimated: bool = True

    # Source (cdp, sql, manual)
    source: str = "cdp"
    source_id: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_refreshed: Optional[datetime] = None

    # Aggregated, non-PII attributes
    attributes: Dict = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
