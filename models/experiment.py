from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class ExperimentStatus(str, Enum):
    """Experiment lifecycle state."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class VariantResult(BaseModel):
    """Tracking metrics for a single variant."""
    
    variant_name: str
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0

    @property
    def conversion_rate(self) -> float:
        if self.impressions == 0:
            return 0.0
        return self.conversions / self.impressions

    @property
    def click_rate(self) -> float:
        if self.impressions == 0:
            return 0.0
        return self.clicks / self.impressions


class StatisticalResult(BaseModel):
    """Result of significance testing between variants."""
    
    variant_a_name: str
    variant_b_name: str
    uplift_percentage: float
    p_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    is_significant: bool
    recommendation: str


class Experiment(BaseModel):
    """A/B/n experiment configuration + live metrics + analysis."""

    id: str
    name: str
    campaign_id: str

    # Configuration
    variants: List[str] = Field(default_factory=list)
    traffic_allocation: Dict[str, float] = Field(
        default_factory=dict,
        description="Traffic split per variant in percentage"
    )

    primary_metric: str = "conversion_rate"
    guardrail_metrics: List[str] = Field(default_factory=list)

    # Status
    status: ExperimentStatus = ExperimentStatus.DRAFT
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Integration with Azure AppConfig
    feature_flag_id: Optional[str] = None

    # Results
    variant_results: Dict[str, VariantResult] = Field(default_factory=dict)
    statistical_analysis: Optional[StatisticalResult] = None
    winner: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "system"

    def get_winning_variant(self) -> Optional[str]:
        if not self.variant_results:
            return None

        best_variant = None
        best_rate = 0.0

        for variant_name, result in self.variant_results.items():
            rate = result.conversion_rate
            if rate > best_rate:
                best_rate = rate
                best_variant = variant_name

        return best_variant

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
