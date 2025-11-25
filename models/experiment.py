"""
A/B/n experiment data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class ExperimentStatus(Enum):
    """Experiment status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class VariantResult:
    """Results for a single variant."""
    
    variant_name: str
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    
    def get_conversion_rate(self) -> float:
        """Calculate conversion rate."""
        if self.impressions == 0:
            return 0.0
        return self.conversions / self.impressions
    
    def get_click_rate(self) -> float:
        """Calculate click-through rate."""
        if self.impressions == 0:
            return 0.0
        return self.clicks / self.impressions


@dataclass
class StatisticalResult:
    """Statistical analysis result."""
    
    variant_a_name: str
    variant_b_name: str
    uplift_percentage: float
    p_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    is_significant: bool
    recommendation: str


@dataclass
class Experiment:
    """A/B/n experiment data model."""
    
    id: str
    name: str
    campaign_id: str
    
    # Configuration
    variants: List[str] = field(default_factory=list)
    traffic_allocation: List[int] = field(default_factory=list)  # Percentages
    
    # Metrics
    primary_metric: str = "conversion_rate"
    guardrail_metrics: List[str] = field(default_factory=list)
    
    # Status
    status: ExperimentStatus = ExperimentStatus.DRAFT
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Feature flag
    feature_flag_id: Optional[str] = None
    
    # Results
    variant_results: Dict[str, VariantResult] = field(default_factory=dict)
    statistical_analysis: Optional[StatisticalResult] = None
    winner: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    
    def get_winning_variant(self) -> Optional[str]:
        """Determine winning variant based on conversion rate."""
        if not self.variant_results:
            return None
        
        best_variant = None
        best_rate = 0.0
        
        for variant_name, result in self.variant_results.items():
            rate = result.get_conversion_rate()
            if rate > best_rate:
                best_rate = rate
                best_variant = variant_name
        
        return best_variant
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "campaign_id": self.campaign_id,
            "variants": self.variants,
            "traffic_allocation": self.traffic_allocation,
            "primary_metric": self.primary_metric,
            "guardrail_metrics": self.guardrail_metrics,
            "status": self.status.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "feature_flag_id": self.feature_flag_id,
            "variant_results": {
                k: {
                    "variant_name": v.variant_name,
                    "impressions": v.impressions,
                    "clicks": v.clicks,
                    "conversions": v.conversions
                }
                for k, v in self.variant_results.items()
            },
            "winner": self.winner,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by
        }
