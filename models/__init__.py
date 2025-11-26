"""
Data models for the marketing agent system.
"""

from .campaign import Campaign, CampaignStatus
from .segment import Segment
from .message import MessageVariant, Citation
from .experiment import Experiment, ExperimentStatus, VariantResult, StatisticalResult
from .audit_log import AuditLog

__all__ = [
    "Campaign",
    "CampaignStatus",
    "Segment",
    "MessageVariant",
    "Citation",
    "Experiment",
    "ExperimentStatus",
    "VariantResult",
    "StatisticalResult",
    "AuditLog"
]