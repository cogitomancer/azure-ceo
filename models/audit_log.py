from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid


class AuditLog(BaseModel):
    """
    Audit log entry for tracking agent actions, compliance validation,
    safety flags, and operational observability.
    """

    # Core identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Actor
    agent_name: str = Field(..., description="Name of the agent performing the action")
    agent_version: Optional[str] = Field(
        None, description="Agent version or model identifier"
    )
    user_id: Optional[str] = None

    # Action
    action_type: str = Field(..., description="Action performed by the agent")
    action_details: Dict[str, Any] = Field(default_factory=dict)

    # Context
    campaign_id: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None  # Distributed tracing support
    ip_address: Optional[str] = None  # Useful if actions originate from API clients

    # Result
    success: bool = True
    error_message: Optional[str] = None
    latency_ms: Optional[float] = None
    token_usage: Optional[int] = None

    # Compliance flags
    pii_detected: bool = False
    safety_violations: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with timestamp serialized to string."""
        data = self.dict()
        data["timestamp"] = self.timestamp.isoformat()
        return data
