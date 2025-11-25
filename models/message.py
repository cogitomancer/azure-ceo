"""
Message variant data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class Citation:
    """Citation for a claim in the message."""
    
    source_file: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    quote: Optional[str] = None
    url: Optional[str] = None
    
    def to_string(self) -> str:
        """Format citation as string."""
        parts = [f"Source: {self.source_file}"]
        if self.page_number:
            parts.append(f"Page {self.page_number}")
        if self.section:
            parts.append(f"Section: {self.section}")
        return ", ".join(parts)


@dataclass
class MessageVariant:
    """Message variant data model."""
    
    id: str
    variant_name: str  # A, B, C, etc.
    campaign_id: str
    
    # Content
    subject: Optional[str] = None
    body: str = ""
    channel: str = "email"  # email, sms, push
    
    # Citations and grounding
    citations: List[Citation] = field(default_factory=list)
    grounding_sources: List[str] = field(default_factory=list)
    
    # Compliance
    safety_check_passed: bool = False
    safety_analysis: Dict = field(default_factory=dict)
    brand_check_passed: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    
    # Performance (when active)
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    
    def get_conversion_rate(self) -> float:
        """Calculate conversion rate."""
        if self.impressions == 0:
            return 0.0
        return self.conversions / self.impressions
    
    def format_with_citations(self) -> str:
        """Format message body with citation footnotes."""
        content = self.body
        if self.citations:
            content += "\n\n---\nSources:\n"
            for i, citation in enumerate(self.citations, 1):
                content += f"{i}. {citation.to_string()}\n"
        return content
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "variant_name": self.variant_name,
            "campaign_id": self.campaign_id,
            "subject": self.subject,
            "body": self.body,
            "channel": self.channel,
            "citations": [
                {
                    "source_file": c.source_file,
                    "page_number": c.page_number,
                    "section": c.section,
                    "quote": c.quote,
                    "url": c.url
                }
                for c in self.citations
            ],
            "grounding_sources": self.grounding_sources,
            "safety_check_passed": self.safety_check_passed,
            "safety_analysis": self.safety_analysis,
            "brand_check_passed": self.brand_check_passed,
            "created_at": self.created_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "impressions": self.impressions,
            "clicks": self.clicks,
            "conversions": self.conversions
        }
