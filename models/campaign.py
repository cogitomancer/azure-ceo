from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
import uuid


class CampaignStatus(Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class Campaign(BaseModel):
    """
    Campaign data model for the marketing agent system.
    Fully Pydantic for validation, serialization, and API compatibility.
    """

    # Identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    objective: str
    status: CampaignStatus = CampaignStatus.DRAFT

    # Targeting
    segment_id: Optional[str] = None
    segment_size: int = 0

    # Content
    message_variants: List[str] = Field(default_factory=list)

    # Experiment
    experiment_id: Optional[str] = None
    experiment_config: Optional[Dict] = None

    # Approval & compliance
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    compliance_check_passed: bool = False
    safety_violations: List[str] = Field(default_factory=list)

    # Metadata
    created_by: str = "system"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Results
    metrics: Dict = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

    def to_dict(self) -> Dict:
        """Return clean dict with ISO timestamps."""
        data = self.model_dump()
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.approval_timestamp:
            data["approval_timestamp"] = self.approval_timestamp.isoformat()
        return data
