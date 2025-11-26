"""
Statistical analysis utilities for A/B testing.
"""

import math
from scipy import stats
from typing import Tuple, Dict
import logging


class StatisticalAnalyzer:
    """Perform statistical analysis on experiment results."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_two_proportion_test(
        self,
        conversions_a: int,
        visits_a: int,
        conversions_b: int,
        visits_b: int,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Perform two-proportion z-test.
        
        Returns:
            Dict with uplift, p_value, confidence_interval, is_significant
        """
        
        # Calculate conversion rates
        rate_a = conversions_a / visits_a if visits_a > 0 else 0
        rate_b = conversions_b / visits_b if visits_b > 0 else 0
        
        # Calculate uplift
        uplift = ((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0
        
        # Pooled proportion for z-test
        pooled_p = (conversions_a + conversions_b) / (visits_a + visits_b)
        pooled_se = math.sqrt(pooled_p * (1 - pooled_p) * (1/visits_a + 1/visits_b))
        
        # Calculate z-score
        z_score = (rate_b - rate_a) / pooled_se if pooled_se > 0 else 0
        
        # Calculate p-value (two-tailed)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        # Calculate confidence interval
        se_diff = math.sqrt(
            (rate_a * (1-rate_a) / visits_a) + 
            (rate_b * (1-rate_b) / visits_b)
        )
        z_critical = stats.norm.ppf((1 + confidence_level) / 2)
        ci_lower = (rate_b - rate_a) - (z_critical * se_diff)
        ci_upper = (rate_b - rate_a) + (z_critical * se_diff)
        
        # Determine significance
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
        
        self.logger.info(
            f"Statistical test: uplift={uplift:.2f}%, p={p_value:.4f}, "
            f"significant={is_significant}"
        )
        
        return result
    
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
            baseline_rate: Current conversion rate (e.g., 0.05 for 5%)
            minimum_detectable_effect: Minimum uplift to detect (e.g., 0.20 for 20%)
            power: Statistical power (default 0.80 for 80%)
            significance: Significance level (default 0.05)
        """
        
        # Z-scores for power and significance
        z_alpha = stats.norm.ppf(1 - significance/2)
        z_beta = stats.norm.ppf(power)
        
        # Expected rate for variant B
        rate_b = baseline_rate * (1 + minimum_detectable_effect)
        
        # Pooled rate
        pooled_rate = (baseline_rate + rate_b) / 2
        
        # Sample size calculation
        numerator = (z_alpha + z_beta) ** 2 * 2 * pooled_rate * (1 - pooled_rate)
        denominator = (rate_b - baseline_rate) ** 2
        
        sample_size = math.ceil(numerator / denominator)
        
        self.logger.info(f"Required sample size per variant: {sample_size:,}")
        
        return sample_size
    
    def generate_recommendation(self, result: Dict) -> str:
        """Generate human-readable recommendation from test results."""
        
        if not result["is_significant"]:
            return (
                "No statistically significant difference detected. "
                "Recommend extending test duration or trying new variants."
            )
        
        if result["uplift_percentage"] > 0:
            return (
                f"Variant B shows significant improvement "
                f"({result['uplift_percentage']:+.2f}% uplift, p={result['p_value']:.4f}). "
                f"Recommend deploying Variant B to full audience."
            )
        else:
            return (
                f"Variant B shows significant decline "
                f"({result['uplift_percentage']:+.2f}% change, p={result['p_value']:.4f}). "
                f"Recommend keeping control variant (A)."
            )
