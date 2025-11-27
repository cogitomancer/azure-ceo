"""
Predefined workflows for common agent tasks.

These workflows orchestrate multi-agent sequences such as:
- full campaign creation
- segmentation → content → compliance → experiment setup
- automated approvals and <APPROVED> flows
"""

from .campaign_creation import CampaignCreationWorkflow

__all__ = [
    "CampaignCreationWorkflow",
]
