"""
Statistical analysis plugin for experiment evaluation.
"""

from semantic_kernel.functions import kernel_function
from typing import Annotated
import math
from scipy import stats


class MetricsPlugin:
    """
    Plugin for calculating statistical significance and experiment metrics.
    Provides rigorous analysis for proving uplift.
    """
    
    def __init__(self, config: dict):
        self.config = config
    
    @kernel_function(
        name="calculate_significance",
        description="Calculate statistical significance between experiment variants"
    )
    async def calculate_significance(
        self,
        variant_a_conversions: Annotated[int, "Number of conversions for variant A"],
        variant_a_visits: Annotated[int, "Number of visits for variant A"],
        variant_b_conversions: Annotated[int, "Number of conversions for variant B"],
        variant_b_visits: Annotated[int, "Number of visits for variant B"]
    ) -> Annotated[str, "Statistical analysis results"]:
        """
        Perform two-proportion z-test to determine statistical significance.
        """
        
        # Calculate conversion rates
        rate_a = variant_a_conversions / variant_a_visits
        rate_b = variant_b_conversions / variant_b_visits
        
        # Calculate uplift
        uplift = ((rate_b - rate_a) / rate_a) * 100
        
        # Pooled proportion for z-test
        pooled_p = (variant_a_conversions + variant_b_conversions) / (variant_a_visits + variant_b_visits)
        pooled_se = math.sqrt(pooled_p * (1 - pooled_p) * (1/variant_a_visits + 1/variant_b_visits))
        
        # Calculate z-score
        z_score = (rate_b - rate_a) / pooled_se
        
        # Calculate p-value (two-tailed)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        # Calculate confidence interval (95%)
        se_diff = math.sqrt((rate_a * (1-rate_a) / variant_a_visits) + 
                           (rate_b * (1-rate_b) / variant_b_visits))
        ci_lower = (rate_b - rate_a) - (1.96 * se_diff)
        ci_upper = (rate_b - rate_a) + (1.96 * se_diff)
        
        # Determine significance
        is_significant = p_value < 0.05
        
        result = f"""
        === Statistical Analysis ===
        
        Variant A (Control):
        - Conversions: {variant_a_conversions:,}
        - Visits: {variant_a_visits:,}
        - Conversion Rate: {rate_a*100:.2f}%
        
        Variant B (Treatment):
        - Conversions: {variant_b_conversions:,}
        - Visits: {variant_b_visits:,}
        - Conversion Rate: {rate_b*100:.2f}%
        
        Results:
        - Uplift: {uplift:+.2f}%
        - P-value: {p_value:.4f}
        - Z-score: {z_score:.2f}
        - 95% CI: [{ci_lower*100:.2f}%, {ci_upper*100:.2f}%]
        - Statistical Significance: {'YES' if is_significant else 'NO'}
        
        Recommendation:
        """
        
        if is_significant:
            if uplift > 0:
                result += f"Variant B shows SIGNIFICANT improvement. Deploy to full audience."
            else:
                result += f"Variant B shows SIGNIFICANT decline. Keep control variant."
        else:
            result += f"No significant difference detected. Extend test duration or try new variants."
        
        return result