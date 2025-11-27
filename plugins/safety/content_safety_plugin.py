"""
Azure AI Content Safety plugin — detects harmful content before it reaches users.
Stable, structured JSON output, BasePlugin-compatible, and safe for multi-agent use.
"""

from __future__ import annotations

import json
from typing import Annotated, Dict, Any

from azure.ai.contentsafety.aio import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.identity.aio import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential

from semantic_kernel.functions import kernel_function
from plugins.base_plugin import BasePlugin


class ContentSafetyPlugin(BasePlugin):
    """
    Wraps Azure AI Content Safety and exposes:
    - analyze_content_safety (LLM safety, violence/offense detection)
    - check_groundedness (ensures citations appear)
    
    Returns STRICT JSON with the schema:
    {
      "status": "APPROVED" | "REJECTED",
      "violations": [
        {"type": "...", "detail": "..."}
      ]
    }
    """

    # Azure returns categories under names like:
    # - hate_result
    # - sexual_result
    # - selfharm_result
    # - violence_result
    CATEGORY_MAP = {
        "Hate": "hate_result",
        "Violence": "violence_result",
        "Sexual": "sexual_result",
        "SelfHarm": "selfharm_result"
    }

    # Default severity thresholds (0–6 scale)
    DEFAULT_THRESHOLDS = {
        "Hate": 0,
        "Sexual": 0,
        "SelfHarm": 0,
        "Violence": 2
    }

    def __init__(self, config: dict):
        super().__init__(config)

        # Load thresholds or use defaults
        self.thresholds = config.get("content_safety", {}).get(
            "thresholds",
            self.DEFAULT_THRESHOLDS
        )

        # Setup credentials
        safety_cfg = config["content_safety"]
        key = safety_cfg.get("key")
        endpoint = safety_cfg["endpoint"]

        if key:
            self.client = ContentSafetyClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key)
            )
        else:
            self.client = ContentSafetyClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential()
            )

    # ----------------------------------------------------------------------
    # Register plugin with the agent
    # ----------------------------------------------------------------------
    def register(self, agent):
        agent.add_function(self.analyze_content_safety)
        agent.add_function(self.check_groundedness)

    # ----------------------------------------------------------------------
    # Safety Validation
    # ----------------------------------------------------------------------
    @kernel_function(
        name="analyze_content_safety",
        description="Check for harmful content (hate, violence, sexual, self-harm). Returns machine-readable JSON."
    )
    async def analyze_content_safety(
        self,
        content: Annotated[str, "Generated content to check"]
    ) -> Annotated[str, "JSON string of violations or approval"]:
        """
        Runs Azure Content Safety and returns structured JSON:
        {
          "status": "...",
          "violations": [{ "type": "...", "detail": "..." }]
        }
        """
        violations = []

        try:
            response = await self.client.analyze_text(
                AnalyzeTextOptions(text=content)
            )

            analysis = response.categories_analysis

            # Check each category
            for category_name, attr_name in self.CATEGORY_MAP.items():
                result = getattr(analysis, attr_name, None)
                if not result:
                    continue  # Category may be missing in preview versions

                severity = result.severity
                threshold = self.thresholds.get(category_name, 0)

                if severity > threshold:
                    violations.append({
                        "type": f"{category_name.lower()}_violation",
                        "detail": f"Severity {severity} exceeds threshold {threshold}"
                    })

            # Check for jailbreaks if present
            if hasattr(response, "jailbreak_analysis"):
                if response.jailbreak_analysis.detected:
                    violations.append({
                        "type": "prompt_injection",
                        "detail": "Jailbreak or prompt manipulation detected"
                    })

        except Exception as e:
            return json.dumps({
                "status": "ERROR",
                "violations": [{"type": "api_error", "detail": str(e)}]
            })

        # Build final response
        if violations:
            return json.dumps({
                "status": "REJECTED",
                "violations": violations
            }, indent=2)

        return json.dumps({
            "status": "APPROVED",
            "violations": []
        }, indent=2)

    # ----------------------------------------------------------------------
    # Groundedness Check
    # ----------------------------------------------------------------------
    @kernel_function(
        name="check_groundedness",
        description="Verify claims are grounded in source docs via citations."
    )
    async def check_groundedness(
        self,
        content: Annotated[str, "Generated content"],
        sources: Annotated[str, "Source documents used"]
    ) -> Annotated[str, "JSON result with groundedness status"]:
        """
        Minimal groundedness validator:
        Ensures presence of citation markers like `[Source: ...]`
        """

        violations = []

        if "[source:" not in content.lower():
            violations.append({
                "type": "citation_missing",
                "detail": "No inline citations found."
            })

        if violations:
            return json.dumps({
                "status": "REJECTED",
                "violations": violations
            }, indent=2)

        return json.dumps({
            "status": "APPROVED",
            "violations": []
        }, indent=2)
