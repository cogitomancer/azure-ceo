"""
Campaign data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum


class CampaignStatus(Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Campaign:
    """Campaign data model."""
    
    id: str
    name: str
    objective: str
    status: CampaignStatus = CampaignStatus.DRAFT
    
    # Targeting
    segment_id: Optional[str] = None
    segment_size: int = 0
    
    # Content
    message_variants: List[str] = field(default_factory=list)
    
    # Experiment
    experiment_id: Optional[str] = None
    experiment_config: Optional[Dict] = None
    
    # Approval & compliance
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    compliance_check_passed: bool = False
    safety_violations: List[str] = field(default_factory=list)
    
    # Metadata
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Results
    metrics: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "objective": self.objective,
            "status": self.status.value,
            "segment_id": self.segment_id,
            "segment_size": self.segment_size,
            "message_variants": self.message_variants,
            "experiment_id": self.experiment_id,
            "experiment_config": self.experiment_config,
            "approved_by": self.approved_by,
            "approval_timestamp": self.approval_timestamp.isoformat() if self.approval_timestamp else None,
            "compliance_check_passed": self.compliance_check_passed,
            "safety_violations": self.safety_violations,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metrics": self.metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Campaign':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            objective=data["objective"],
            status=CampaignStatus(data["status"]),
            segment_id=data.get("segment_id"),
            segment_size=data.get("segment_size", 0),
            message_variants=data.get("message_variants", []),
            experiment_id=data.get("experiment_id"),
            experiment_config=data.get("experiment_config"),
            approved_by=data.get("approved_by"),
            approval_timestamp=datetime.fromisoformat(data["approval_timestamp"]) if data.get("approval_timestamp") else None,
            compliance_check_passed=data.get("compliance_check_passed", False),
            safety_violations=data.get("safety_violations", []),
            created_by=data.get("created_by", "system"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metrics=data.get("metrics", {})
        )