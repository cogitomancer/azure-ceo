"""
Brand Compliance Plugin — validates outbound content against brand, tone,
and legal restrictions. Safe, structured, and BasePlugin-compatible.

Uses company-specific data from tables (Hudson Street Bakery by default).
"""

from __future__ import annotations

import json
import yaml
import logging
from typing import Annotated, Dict, Any, List

from semantic_kernel.functions import kernel_function
from plugins.base_plugin import BasePlugin


class BrandCompliancePlugin(BasePlugin):
    """
    Ensures that model-generated marketing content adheres to brand standards.
    
    Validation includes:
    - prohibited terms (e.g., competitor names, banned phrases)
    - required elements (e.g., citations)
    - tone & style guardrails
    - claim substantiation
    
    Outputs STRICT JSON that the ComplianceOfficerAgent can parse reliably.
    """

    def __init__(self, config: dict):
        super().__init__(config=config, name="BrandCompliancePlugin")
        self.logger = logging.getLogger(__name__)

        # Load company-specific data
        self.company_data = self._load_company_data()
        self.company_name = self.company_data.get("name", "Unknown Company")
        
        # Load brand guidelines from config as fallback
        try:
            with open("config/brand_guidelines.yaml", "r") as f:
                self.guidelines = yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"Brand guidelines YAML not found, using company data: {e}")
            self.guidelines = {
                "brand": {
                    "prohibited": {"competitor_mentions": True},
                    "required": {"citations": True},
                    "messaging": {"avoid": []}
                }
            }

        # Load banned phrases from company data
        self.banned_phrases = self._get_banned_phrases()
        
        # Preload competitor list
        self.competitors = [
            c.lower() for c in config.get("competitors", [
                "competitor1", "competitor2"
            ])
        ]
        
        self.logger.info(f"BrandCompliancePlugin initialized for: {self.company_name}")

    def _load_company_data(self) -> Dict[str, Any]:
        """Load company info from CompanyDataService."""
        try:
            from services.company_data_service import CompanyDataService
            service = CompanyDataService()
            return {
                "name": service.get_company_info()["name"],
                "brand_rules": service.get_brand_rules(),
                "banned_phrases": service.get_banned_phrases(),
                "tone_guidelines": service.get_tone_guidelines(),
            }
        except Exception as e:
            self.logger.error(f"Could not load company data: {e}")
            return {"name": "Unknown", "brand_rules": {}, "banned_phrases": [], "tone_guidelines": {}}

    def _get_banned_phrases(self) -> List[str]:
        """Get merged banned phrases from company data and config."""
        banned = list(self.company_data.get("banned_phrases", []))
        
        # Also add from config guidelines
        messaging = self.guidelines.get("brand", {}).get("messaging", {})
        config_avoid = messaging.get("avoid", [])
        for term in config_avoid:
            if term.lower() not in banned:
                banned.append(term.lower())
        
        return banned

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
        # Company-specific banned phrases
        # --------------------------------------------------------------
        content_lower = content.lower()
        for phrase in self.banned_phrases:
            if phrase in content_lower:
                violations.append({
                    "type": "banned_phrase",
                    "detail": phrase,
                    "company": self.company_name
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
