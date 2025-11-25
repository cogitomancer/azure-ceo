"""
Reusable prompt templates for agents.
"""

from typing import Dict


class PromptTemplates:
    """Collection of prompt templates for different agent tasks."""
    
    @staticmethod
    def strategy_decomposition(objective: str) -> str:
        """Template for decomposing high-level objectives."""
        return f"""
You are the Strategy Lead for a marketing campaign. Your task is to decompose 
the following business objective into specific, actionable tasks for your team.

Objective: {objective}

Break this down into:
1. Audience identification requirements
2. Content creation requirements  
3. Compliance validation requirements
4. Experimentation setup requirements

For each requirement, specify what information is needed and which team member 
(DataSegmenter, ContentCreator, ComplianceOfficer, ExperimentRunner) should handle it.

Provide your task breakdown:
"""
    
    @staticmethod
    def content_generation(segment_info: str, product_info: str) -> str:
        """Template for content generation."""
        return f"""
You are a marketing copywriter creating personalized campaign messages.

Target Audience:
{segment_info}

Product Information:
{product_info}

Create 3 message variants:
- Variant A: Feature-focused (highlight technical capabilities)
- Variant B: Benefit-focused (emphasize customer outcomes)
- Variant C: Urgency-focused (create time-sensitive motivation)

Requirements:
1. Every product claim MUST include a citation [Source: X, Page Y]
2. Maintain professional but enthusiastic tone
3. Each variant should be 100-150 words
4. Include compelling subject line for each

Generate the variants:
"""
    
    @staticmethod
    def compliance_review(content: str) -> str:
        """Template for compliance review."""
        return f"""
You are a Compliance Officer reviewing marketing content for approval.

Content to Review:
{content}

Evaluate for:
1. Safety violations (hate, violence, sexual, self-harm content)
2. Brand compliance (tone, prohibited terms, competitor mentions)
3. Citation accuracy (all claims properly sourced)
4. Unsubstantiated claims or promises

For each variant, provide:
- Decision: APPROVED or REJECTED
- If REJECTED, specific issues and recommendations

Your review:
"""
    
    @staticmethod
    def experiment_setup(variants: Dict, segment_size: int) -> str:
        """Template for experiment configuration."""
        return f"""
You are an Experiment Engineer configuring an A/B/n test.

Variants to Test:
{variants}

Target Audience Size: {segment_size:,} users

Configure the experiment:
1. Recommend traffic allocation (considering safety and statistical power)
2. Define primary metric (conversion_rate, click_rate, etc.)
3. Define guardrail metrics (unsubscribe_rate, complaint_rate)
4. Calculate minimum sample size needed
5. Recommend test duration

Provide your experiment configuration:
"""
