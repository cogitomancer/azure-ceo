"""
Custom brand compliance validation plugin.
"""

from semantic_kernel.functions import kernel_function
from typing import Annotated
import yaml
import re
import logging


class BrandCompliancePlugin:
    """Plugin for validating brand guidelines and compliance rules."""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Load brand guidelines
        with open("config/brand_guidelines.yaml", "r") as f:
            self.guidelines = yaml.safe_load(f)
    
    @kernel_function(
        name="validate_brand_compliance",
        description="Validate content against brand guidelines"
    )
    async def validate_brand_compliance(
        self,
        content: Annotated[str, "Content to validate"]
    ) -> Annotated[str, "Compliance validation result"]:
        """
        Validate content against brand guidelines.
        """
        
        violations = []
        
        # Check for prohibited competitor mentions
        if self.guidelines["brand"]["prohibited"]["competitor_mentions"]:
            # In production, load actual competitor list
            competitors = ["competitor1", "competitor2"]
            for comp in competitors:
                if comp.lower() in content.lower():
                    violations.append(f"Competitor mention: {comp}")
        
        # Check for required elements
        if self.guidelines["brand"]["required"]["citations"]:
            if "[Source:" not in content and "Citation:" not in content:
                violations.append("Missing required citations")
        
        # Check tone and style
        avoid_terms = self.guidelines["brand"]["messaging"]["avoid"]
        for term in avoid_terms:
            # Simplified check
            pass
        
        # Format result
        if violations:
            result = "REJECTED\n\nBrand compliance violations:\n"
            for v in violations:
                result += f"- {v}\n"
            return result
        else:
            return "APPROVED - Brand compliance validated"
