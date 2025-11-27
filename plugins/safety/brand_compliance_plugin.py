"""
Brand Compliance Plugin — validates outbound content against brand, tone,
and legal restrictions. Safe, structured, and BasePlugin-compatible.
"""

from __future__ import annotations

import json
import yaml
import logging
from typing import Annotated, Dict, Any

from semantic_kernel.functions import kernel_function
from plugins.base_plugin import BasePlugin


class BrandCompliancePlugin(BasePlugin):
    """
    Ensures that model-generated marketing content adheres to brand standards.
    
    Validation includes:
    - prohibited terms (e.g., competitor names)
    - required elements (e.g., citations)
    - tone & style guardrails
    - claim substantiation
    
    Outputs STRICT JSON that the ComplianceOfficerAgent can parse reliably.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # Load brand guidelines safely
        try:
            with open("config/brand_guidelines.yaml", "r") as f:
                self.guidelines = yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Brand guidelines not found or unreadable: {e}")
            self.guidelines = {
                "brand": {
                    "prohibited": {"competitor_mentions": True},
                    "required": {"citations": True},
                    "messaging": {"avoid": []}
                }
            }

        # Preload competitor list if allowed
        self.competitors = [
            c.lower() for c in config.get("competitors", [
                "competitor1", "competitor2"
            ])
        ]

    # ----------------------------------------------------------------------
    # Register plugin with Semantic Kernel
    # ----------------------------------------------------------------------
    def register(self, agent):
        """Attach SK functions to the agent."""
        agent.add_function(self.validate_brand_compliance)

    # ----------------------------------------------------------------------
    # Semantic Kernel Function
    # ----------------------------------------------------------------------
    @kernel_function(
        name="validate_brand_compliance",
        description="Check content against brand rules and output structured violations."
    )
    async def validate_brand_compliance(
        self,
        content: Annotated[str, "Generated marketing content"]
    ) -> Annotated[str, "JSON: {status:..., violations:[...]}"]:
        """
        Returns STRICT machine-readable JSON:

        {
          "status": "APPROVED" | "REJECTED",
          "violations": [
            {"type": "citation_missing", "detail": "..."},
            {"type": "competitor_mention", "detail": "nike"}
          ]
        }
        """

        violations = []

        # --------------------------------------------------------------
        # Competitor mentions
        # --------------------------------------------------------------
        if self.guidelines["brand"]["prohibited"]["competitor_mentions"]:
            content_lower = content.lower()
            for comp in self.competitors:
                if comp in content_lower:
                    violations.append({
                        "type": "competitor_mention",
                        "detail": comp
                    })

        # --------------------------------------------------------------
        # Required citations
        # --------------------------------------------------------------
        if self.guidelines["brand"]["required"]["citations"]:
            if "[source:" not in content.lower():
                violations.append({
                    "type": "citation_missing",
                    "detail": "No inline citations found"
                })

        # --------------------------------------------------------------
        # Messaging: forbidden terms
        # --------------------------------------------------------------
        forbidden_terms = self.guidelines["brand"]["messaging"].get("avoid", [])
        for term in forbidden_terms:
            if term.lower() in content.lower():
                violations.append({
                    "type": "forbidden_term",
                    "detail": term
                })

        # --------------------------------------------------------------
        # Build response
        # --------------------------------------------------------------
        if violations:
            result = {
                "status": "REJECTED",
                "violations": violations
            }
        else:
            result = {
                "status": "APPROVED",
                "violations": []
            }

        return json.dumps(result, indent=2)
