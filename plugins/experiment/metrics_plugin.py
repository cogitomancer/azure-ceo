"""
Stable statistical analysis plugin for multi-variant A/B/n experiments.
"""

from semantic_kernel.functions import kernel_function
from typing import Annotated, Dict, Any
import math
import json


class MetricsPlugin:
    """
    Provides statistical evaluation across A/B/n experiments.
    Uses pure math (no SciPy) for max stability.
    
    Computes:
    - conversion rate
    - uplift vs control
    - pooled z-test
    - p-value
    - 95% confidence interval
    """

    def __init__(self, config: dict):
        self.config = config

    # ----------------------------------------------------------------------
    # P-value approximation — stable SciPy replacement
    # ----------------------------------------------------------------------
    def _normal_cdf(self, x: float) -> float:
        """Cumulative distribution function of standard normal."""
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

    # ----------------------------------------------------------------------
    @kernel_function(
        name="calculate_significance",
        description="Run multi-variant statistical analysis using pooled z-test."
    )
    async def calculate_significance(
        self,
        metrics_json: Annotated[str, "JSON metrics per variant"]
    ) -> Annotated[str, "JSON statistical significance results"]:
        """
        Input format (from ExperimentRunner):

        {
            "control": { "conversions": 120, "visits": 4000, "unsubscribe_rate": 0.01 },
            "A":       { "conversions": 150, "visits": 4100, "unsubscribe_rate": 0.012 },
            "B":       { "conversions": 165, "visits": 4050, "unsubscribe_rate": 0.009 }
        }
        """

        try:
            metrics: Dict[str, Any] = json.loads(metrics_json)
        except Exception:
            return json.dumps({"error": "Invalid JSON passed to calculate_significance"})

        if "control" not in metrics:
            return json.dumps({"error": "Metrics must include a 'control' variant"})

        control = metrics["control"]
        results = {}

        rate_control = control["conversions"] / max(control["visits"], 1)

        # ------------------------------------------------------------------
        # Evaluate EACH variant independently vs control
        # ------------------------------------------------------------------
        for vid, data in metrics.items():
            conv = data["conversions"]
            visits = max(data["visits"], 1)
            rate = conv / visits

            # pooled proportion
            pooled_p = (control["conversions"] + conv) / (control["visits"] + visits)
            pooled_se = math.sqrt(pooled_p * (1 - pooled_p) * (1/control["visits"] + 1/visits))

            if pooled_se == 0:
                z = 0
            else:
                z = (rate - rate_control) / pooled_se

            # p-value (two-tailed)
            p_value = 2 * (1 - self._normal_cdf(abs(z)))

            # 95% confidence interval (difference in proportions)
            se_diff = math.sqrt(
                (rate_control * (1-rate_control) / control["visits"]) +
                (rate * (1-rate) / visits)
            )
            ci_low = (rate - rate_control) - 1.96 * se_diff
            ci_high = (rate - rate_control) + 1.96 * se_diff

            uplift = ((rate - rate_control) / rate_control) * 100 if rate_control > 0 else 0

            results[vid] = {
                "conversions": conv,
                "visits": visits,
                "conversion_rate": rate,
                "uplift_percent": uplift,
                "z_score": z,
                "p_value": p_value,
                "ci_95": [ci_low, ci_high],
                "unsubscribe_rate": data.get("unsubscribe_rate"),
                "complaint_rate": data.get("complaint_rate")
            }

        # ------------------------------------------------------------------
        # Winner Determination
        # ------------------------------------------------------------------
        significant_winner = None
        for vid, stats in results.items():
            if vid == "control":
                continue
            if stats["p_value"] < 0.05 and stats["uplift_percent"] > 0:
                significant_winner = vid
                break

        output = {
            "results": results,
            "significant_winner": significant_winner
        }

        return json.dumps(output, indent=2)
