"""
Audience segment data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Segment:
    """Audience segment data model."""
    
    id: str
    name: str
    description: str
    
    # Criteria
    criteria: Dict = field(default_factory=dict)
    sql_query: Optional[str] = None
    
    # Size and characteristics
    size: int = 0
    estimated: bool = True
    
    # Source
    source: str = "cdp"  # cdp, sql, manual
    source_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_refreshed: Optional[datetime] = None
    
    # User attributes (aggregated, no PII)
    attributes: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "criteria": self.criteria,
            "sql_query": self.sql_query,
            "size": self.size,
            "estimated": self.estimated,
            "source": self.source,
            "source_id": self.source_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_refreshed": self.last_refreshed.isoformat() if self.last_refreshed else None,
            "attributes": self.attributes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Segment':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            criteria=data.get("criteria", {}),
            sql_query=data.get("sql_query"),
            size=data.get("size", 0),
            estimated=data.get("estimated", True),
            source=data.get("source", "cdp"),
            source_id=data.get("source_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            last_refreshed=datetime.fromisoformat(data["last_refreshed"]) if data.get("last_refreshed") else None,
            attributes=data.get("attributes", {})
        )
