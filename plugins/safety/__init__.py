"""
Safety and compliance plugins.
Each plugin must inherit from BasePlugin and implement .register(agent).
"""

from .content_safety_plugin import ContentSafetyPlugin
from .brand_compliance_plugin import BrandCompliancePlugin

__all__ = [
    "ContentSafetyPlugin",
    "BrandCompliancePlugin"
]
