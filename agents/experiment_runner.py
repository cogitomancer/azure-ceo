from __future__ import annotations

import json
import logging
from typing import List, Dict, Any

from agents.base_agent import BaseMarketingAgent
from plugins.experiment.app_config_plugin import AppConfigPlugin
from plugins.experiment.metrics_plugin import MetricsPlugin
from models.variant import Variant

logger = logging.getLogger(__name__)


class ExperimentRunnerAgent(BaseMarketingAgent):
    """
    Controls the full experiment lifecycle:
    - Create feature flags in Azure App Config
    - Set / update traffic allocation
    - Enforce guardrails (unsubscribe, complaint, safety)
    - Perform statistical significance analysis
    - Produce final rollout recommendations
    """

    def __init__(self, kernel, config):
        super().__init__(kernel, config, agent_key="ExperimentRunner")

        self.instructions = """
You are the Experiment Engineering Lead for Azure CEO.

MISSION:
Design, deploy, monitor, and evaluate A/B/n experiments across marketing variants.
You must ensure statistical rigor, controlled exposure, and safe rollouts.

TOOLS:
- create_feature_flag
- update_traffic_allocation
- get_experiment_metrics
- calculate_significance

RULES:
- Equal split by default (33/33/33 for A/B/C)
- Minimum: 1,000 conversions per variant
- Significance: p < 0.05
- Runtime: 7 days minimum unless early winner is safe
- MUST include control group
- Max 5% initial exposure unless overridden

GUARDRAILS:
- Unsubscribe Rate > 1.2x control → reduce exposure
- Complaint Rate > 1.1x control → reduce exposure
- Any critical safety signal → <HALT_EXPERIMENT>

OUTPUT TOKENS:
- <APPROVED>
- <NO_DECISION_YET>
- <HALT_EXPERIMENT>
"""

    # ───────────────────────────────────────────────────────────────
    # Plugin wiring
    # ───────────────────────────────────────────────────────────────
    def get_plugins(self) -> List:
        return [
            AppConfigPlugin(self.config),
            MetricsPlugin(self.config),
        ]

    # ───────────────────────────────────────────────────────────────
    # Helper: Parse plugin result safely
    # ───────────────────────────────────────────────────────────────
    def _parse_plugin_response(self, result: Any) -> Dict[str, Any]:
        """
        Normalizes plugin output:
        - supports SK .value
        - supports JSON strings
        - supports dict passthrough
        """

        if hasattr(result, "value"):
            try:
                return json.loads(result.value)
            except Exception:
                pass

        if isinstance(result, str):
            try:
                return json.loads(result)
            except Exception:
                raise ValueError(
                    "ExperimentRunner: Plugin output was not valid JSON."
                )

        if isinstance(result, dict):
            return result

        raise ValueError(
            f"ExperimentRunner: Unexpected plugin output type {type(result)}"
        )

    # ───────────────────────────────────────────────────────────────
    # Experiment Setup
    # ───────────────────────────────────────────────────────────────
    async def configure_experiment(
        self,
        experiment_name: str,
        variants: List[Variant]
    ) -> Dict[str, Any]:
        """
        Creates AppConfig feature flags + initializes traffic allocation.
        """

        # Create feature flag
        create_raw = await self.kernel.run_async(
            plugin_name="AppConfigPlugin",
            function_name="create_feature_flag",
            input_vars={
                "experiment_name": experiment_name,
                "variants": [v.variant_id for v in variants]
            }
        )

        create_parsed = self._parse_plugin_response(create_raw)
        flag_id = create_parsed.get("flag_id")

        if not flag_id:
            raise ValueError("ExperimentRunner: Missing flag_id from AppConfig.")

        # Equal split for all variants
        allocation = {
            v.variant_id: round(100 / len(variants), 2) for v in variants
        }

        # Apply allocation
        await self.kernel.run_async(
            plugin_name="AppConfigPlugin",
            function_name="update_traffic_allocation",
            input_vars={"flag_id": flag_id, "allocation": allocation}
        )

        return {
            "experiment_name": experiment_name,
            "variants": list(allocation.keys()),
            "traffic_allocation": allocation,
            "primary_metric": "conversion_rate",
            "guardrails": ["unsubscribe_rate", "complaint_rate"],
            "feature_flag_id": flag_id,
            "status": "ACTIVE"
        }

    # ───────────────────────────────────────────────────────────────
    # Statistical Analysis
    # ───────────────────────────────────────────────────────────────
    async def run_statistical_analysis(
        self,
        experiment_name: str
    ) -> Dict[str, Any]:
        """
        Fetch metrics + significance and return:
        {
            "variant_results": {...},
            "winner": "B",
            "is_significant": True,
            "guardrail_status": "OK",
            "recommendation": "Deploy Variant B"
        }
        """

        # Get experiment metrics
        metrics_raw = await self.kernel.run_async(
            plugin_name="MetricsPlugin",
            function_name="get_experiment_metrics",
            input_vars={"experiment_name": experiment_name}
        )
        metrics = self._parse_plugin_response(metrics_raw)

        # Compute statistical significance
        signif_raw = await self.kernel.run_async(
            plugin_name="MetricsPlugin",
            function_name="calculate_significance",
            input_vars={"metrics": metrics}
        )
        signif = self._parse_plugin_response(signif_raw)

        # Guardrails
        guardrail_status = "OK"
        control = signif.get("control", {})

        for variant_id, stats in signif.items():
            if variant_id == "control":
                continue

            unsub_ok = stats.get("unsubscribe_rate", 0) <= 1.2 * control.get("unsubscribe_rate", 1e-6)
            complaint_ok = stats.get("complaint_rate", 0) <= 1.1 * control.get("complaint_rate", 1e-6)

            if not (unsub_ok and complaint_ok):
                guardrail_status = "VIOLATED"

        # Winner
        winner = None
        is_significant = False

        for variant_id, stats in signif.items():
            if variant_id == "control":
                continue

            if stats.get("p_value", 1) < 0.05 and stats.get("uplift", 0) > 0:
                winner = variant_id
                is_significant = True
                break

        # Final decision token
        if guardrail_status == "VIOLATED":
            recommendation = "<HALT_EXPERIMENT>"
        elif is_significant:
            recommendation = f"Deploy Variant {winner} to full audience"
        else:
            recommendation = "<NO_DECISION_YET>"

        return {
            "variant_results": signif,
            "winner": winner,
            "is_significant": is_significant,
            "guardrail_status": guardrail_status,
            "recommendation": recommendation
        }
