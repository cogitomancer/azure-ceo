"""
Reusable prompt templates for Azure CEO multi-agent system.
"""

from typing import Dict


class PromptTemplates:
    """
    Central library of reusable prompt templates used across
    Strategy Lead, Content Creator, Compliance, and Experiment Runner agents.
    """

    # ------------------------------------------------------------
    # STRATEGY DECOMPOSITION
    # ------------------------------------------------------------
    @staticmethod
    def strategy_decomposition(objective: str) -> str:
        """Template for decomposing high-level business objectives."""
        return f"""
You are the Strategy Lead for an enterprise autonomous marketing team.

Your task: Decompose the following business objective into specific, actionable,
multi-agent tasks.

Objective:
{objective}

Break this down into:
1. Audience identification requirements
2. Content creation requirements
3. Compliance validation requirements
4. Experimentation setup requirements

For each requirement, specify:
- What information is needed
- Which agent owns it (DataSegmenter, ContentCreator, ComplianceOfficer, ExperimentRunner)

Output a structured breakdown:
""".strip()

    # ------------------------------------------------------------
    # CONTENT GENERATION
    # ------------------------------------------------------------
    @staticmethod
    def content_generation(segment_info: str, product_info: str) -> str:
        """Template for structured, grounded content generation."""
        return f"""
You are a Senior Marketing Copywriter. Generate personalized marketing messages
grounded in verified product documentation.

Target Audience:
{segment_info}

Product Information (Grounded Sources Only):
{product_info}

Create exactly 3 variants:
- Variant A: Feature-focused (technical capabilities)
- Variant B: Benefit-focused (customer value)
- Variant C: Urgency-focused (time-sensitive motivation)

STRICT REQUIREMENTS:
1. Every product claim MUST include a citation: [Source: X, Page Y]
2. Tone: Professional, confident, and on-brand
3. Length: 100–150 words per variant
4. Include a compelling subject line for each

Output structured JSON:
{{
  "variants": [
    {{
      "variant_id": "A",
      "subject": "...",
      "body": "...",
      "citations": [...]
    }},
    ...
  ]
}}

Generate the variants now:
""".strip()

    # ------------------------------------------------------------
    # COMPLIANCE REVIEW
    # ------------------------------------------------------------
    @staticmethod
    def compliance_review(content: str) -> str:
        """Template for safety + brand compliance evaluation."""
        return f"""
You are the Compliance & Safety Officer for an enterprise marketing system.

CONTENT TO REVIEW:
{content}

Evaluate each variant for:
1. Safety (hate, violence, sexual, self-harm)
2. Brand rules (tone, prohibited terms, competitor mentions)
3. Citation accuracy (all claims must be grounded)
4. Unsubstantiated promises or claims

For EACH variant provide:
- Decision: APPROVED or REJECTED
- If REJECTED, list specific violations and actionable fixes

Return a structured compliance report:
""".strip()

    # ------------------------------------------------------------
    # EXPERIMENT SETUP
    # ------------------------------------------------------------
    @staticmethod
    def experiment_setup(variants: Dict, segment_size: int) -> str:
        """Template for A/B/n experiment configuration."""
        return f"""
You are the Experiment Engineering Lead configuring an A/B/n test.

Variants Under Test:
{variants}

Segment Size: {segment_size:,} users

Define the experiment configuration:
1. Recommended traffic allocation (consider safety + statistical power)
2. Primary metric (e.g., conversion_rate)
3. Guardrail metrics (unsubscribe_rate, complaint_rate)
4. Minimum required sample size
5. Recommended test duration (days)
6. Conditions for early stopping

Output structured experiment configuration JSON:
""".strip()
