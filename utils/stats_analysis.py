"""
Statistical analysis utilities for A/B testing.
"""

import math
from scipy import stats
from typing import Dict, Tuple
import logging


class StatisticalAnalyzer:
    """Perform statistical analysis on experiment results."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    # ---------------------------------------------------------------------
    # TWO-PROPORTION Z TEST
    # ---------------------------------------------------------------------
    def calculate_two_proportion_test(
        self,
        conversions_a: int,
        visits_a: int,
        conversions_b: int,
        visits_b: int,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Perform a two-proportion z-test.

        Returns:
            Dict containing:
                - rate_a
                - rate_b
                - uplift_percentage
                - p_value
                - z_score
                - confidence_interval
                - is_significant
                - confidence_level
        """

        # -------------------------------
        # Prevent divide-by-zero
        # -------------------------------
        if visits_a <= 0 or visits_b <= 0:
            raise ValueError("Visits for both variants must be greater than zero.")

        # Rates
        rate_a = conversions_a / visits_a
        rate_b = conversions_b / visits_b

        # Uplift (%)
        uplift = ((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0.0

        # -------------------------------
        # Z-Test Calculations
        # -------------------------------
        pooled_p = (conversions_a + conversions_b) / (visits_a + visits_b)
        pooled_se = math.sqrt(
            pooled_p * (1 - pooled_p) * (1 / visits_a + 1 / visits_b)
        )

        z_score = (rate_b - rate_a) / pooled_se if pooled_se > 0 else 0.0

        # Two-tailed p-value
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

        # -------------------------------
        # Confidence Interval
        # -------------------------------
        se_diff = math.sqrt(
            (rate_a * (1 - rate_a) / visits_a) +
            (rate_b * (1 - rate_b) / visits_b)
        )

        z_critical = stats.norm.ppf((1 + confidence_level) / 2)

        ci_lower = (rate_b - rate_a) - (z_critical * se_diff)
        ci_upper = (rate_b - rate_a) + (z_critical * se_diff)

        # Significance check
        alpha = 1 - confidence_level
        is_significant = p_value < alpha

        result = {
            "rate_a": rate_a,
            "rate_b": rate_b,
            "uplift_percentage": uplift,
            "p_value": p_value,
            "z_score": z_score,
            "confidence_interval": (ci_lower, ci_upper),
            "is_significant": is_significant,
            "confidence_level": confidence_level
        }

        # Logging summary (clean one-liner)
        self.logger.info(
            f"[A/B TEST] rate_a={rate_a:.4f}, rate_b={rate_b:.4f}, "
            f"uplift={uplift:+.2f}%, p={p_value:.4f}, significant={is_significant}"
        )

        return result

    # ---------------------------------------------------------------------
    # POWER ANALYSIS — SAMPLE SIZE REQUIREMENTS
    # ---------------------------------------------------------------------
    def calculate_sample_size_required(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float,
        power: float = 0.80,
        significance: float = 0.05
    ) -> int:
        """
        Calculate required sample size per variant.

        Args:
            baseline_rate: Conversion rate for control (0.00–1.00)
            minimum_detectable_effect: Percentage improvement you want to detect (0.20 = 20%)
            power: Desired statistical power (default 80%)
            significance: Type I error level (default 5%)

        Returns:
            Minimum required sample size per variant.
        """

        if baseline_rate <= 0 or minimum_detectable_effect <= 0:
            raise ValueError("Rates and effects must be greater than zero.")

        z_alpha = stats.norm.ppf(1 - significance / 2)
        z_beta = stats.norm.ppf(power)

        # Expected treatment rate
        rate_b = baseline_rate * (1 + minimum_detectable_effect)
        pooled = (baseline_rate + rate_b) / 2

        numerator = (z_alpha + z_beta) ** 2 * 2 * pooled * (1 - pooled)
        denominator = (rate_b - baseline_rate) ** 2

        if denominator <= 0:
            raise ValueError("Invalid minimum detectable effect; denominator is zero.")

        sample_size = math.ceil(numerator / denominator)

        self.logger.info(f"[POWER] Required sample size per variant = {sample_size:,}")

        return sample_size

    # ---------------------------------------------------------------------
    # RECOMMENDATIONS
    # ---------------------------------------------------------------------
    def generate_recommendation(self, result: Dict) -> str:
        """Produce a readable recommendation summary."""
        uplift = result["uplift_percentage"]
        p_value = result["p_value"]

        if not result["is_significant"]:
            return (
                "No statistically significant difference detected. "
                "Recommend extending test duration or introducing new variants."
            )

        if uplift > 0:
            return (
                f"Variant B shows significant improvement "
                f"({uplift:+.2f}% uplift, p={p_value:.4f}). "
                "Recommended: Deploy Variant B to full audience."
            )
        else:
            return (
                f"Variant B shows significant decline "
                f"({uplift:+.2f}% change, p={p_value:.4f}). "
                "Recommended: Retain Variant A as control."
            )
