"""
Audit log data model for compliance tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class AuditLog:
    """Audit log entry for tracking agent actions."""
    
    id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Actor
    agent_name: str = ""
    user_id: Optional[str] = None
    
    # Action
    action_type: str = ""  # query_cdp, generate_content, approve_campaign, etc.
    action_details: Dict = field(default_factory=dict)
    
    # Context
    campaign_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Result
    success: bool = True
    error_message: Optional[str] = None
    
    # Compliance
    pii_detected: bool = False
    safety_violations: list = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "agent_name": self.agent_name,
            "user_id": self.user_id,
            "action_type": self.action_type,
            "action_details": self.action_details,
            "campaign_id": self.campaign_id,
            "session_id": self.session_id,
            "success": self.success,
            "error_message": self.error_message,
            "pii_detected": self.pii_detected,
            "safety_violations": self.safety_violations
        }