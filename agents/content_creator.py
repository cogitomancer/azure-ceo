from __future__ import annotations

import json
import logging
from typing import List, Dict, Any

from agents.base_agent import BaseMarketingAgent
from plugins.content.rag_plugin import RAGPlugin

from models.customer_event import CustomerEvent
from models.variant import Variant
from models.citation import Citation
from models.content_grounding import GroundedContent

logger = logging.getLogger(__name__)


class ContentCreatorAgent(BaseMarketingAgent):
    """
    Generates grounded, on-brand marketing message variants using RAG data
    and Semantic Kernel. Produces 3 variants: Feature, Benefit, Urgency.
    """

    def __init__(self, kernel, config):
        super().__init__(kernel, config, agent_key="ContentCreator")

        # Override YAML persona with full structured instructions
        self.instructions = """
You are a Senior Marketing Copywriter specializing in personalized campaigns.

Responsibilities:
1. Generate compelling marketing copy for email, SMS, and push.
2. Create 3 variants:
      A = Feature-focused  
      B = Benefit-focused  
      C = Urgency-focused
3. ALL product claims must be grounded in verified source documents from RAG.
4. Every factual statement MUST include a citation.
5. Maintain brand voice and tone, no hallucinated features, pricing, or claims.

TOOLS:
- retrieve_product_info
- extract_citations

RULES:
- Use inline citations: “... [Source: <doc>, page X]”.
- Variants must differ in structure + messaging angle.
- NO unsupported claims, no invented product capabilities.
- Output STRICT JSON:
{
  "variants": [
    {
      "variant_id": "A",
      "subject": "...",
      "body": "...",
      "citations": [...],
      "mode": "feature_focused"
    }
  ]
}
"""

    def get_plugins(self) -> list:
        return [RAGPlugin(self.config)]

    #
    # ───────────────────────────────────────────────────────────────────────────
    #   ASYNC VARIANT GENERATION (RAG + SK)
    # ───────────────────────────────────────────────────────────────────────────
    #
    async def generate_grounded_variants(
        self,
        event: CustomerEvent,
        grounding: GroundedContent
    ) -> List[Variant]:

        #
        # Validate grounding
        #
        if not grounding.grounded_items:
            raise ValueError(
                "ContentCreatorAgent: No grounded_items provided from RAGPlugin."
            )

        # Safely derive event context
        event_text = (
            event.metadata.get("text")
            or event.metadata.get("raw_text")
            or event.event_type
        )

        # Build SK input payload
        sk_input: Dict[str, Any] = {
            "event_text": event_text,
            "grounded_items": [item.model_dump() for item in grounding.grounded_items],
            "citations": [c.model_dump() for c in grounding.citations or []],
            "top_k": grounding.top_k,
        }

        #
        # SK Invocation (v1.39–compatible)
        #
        try:
            result = await self.kernel.run_async(sk_input)
        except TypeError:
            # SK fallback for older function signatures
            result = await self.kernel.run_async(
                function_name="default",
                input_vars=sk_input
            )

        #
        # Normalize output: string → dict
        #
        parsed = self._parse_llm_output(result)

        #
        # Extract variants
        #
        raw_variants = parsed.get("variants", [])

        if not raw_variants:
            raise ValueError("ContentCreatorAgent: No variants returned from LLM.")

        #
        # Convert to Pydantic Variant models
        #
        variants: List[Variant] = []
        for v in raw_variants:
            try:
                # Normalize missing citations → []
                citations_data = v.get("citations") or []

                v["citations"] = [
                    Citation(**c) if isinstance(c, dict) else c
                    for c in citations_data
                ]

                variants.append(Variant(**v))

            except Exception as e:
                logger.error("Invalid variant format from LLM", exc_info=True)
                raise ValueError(f"Invalid variant: {v}") from e

        #
        # We expect 3 variants, but don’t crash the system — warn instead
        #
        if len(variants) != 3:
            logger.warning(
                f"ContentCreatorAgent: Expected 3 variants (A/B/C) but got {len(variants)}."
            )

        return variants

    #
    # ───────────────────────────────────────────────────────────────────────────
    #   INTERNAL PARSER (LLM → dict)
    # ───────────────────────────────────────────────────────────────────────────
    #
    def _parse_llm_output(self, result: Any) -> Dict[str, Any]:
        """
        Normalize SK output:
        - Handles SK chat objects with .value
        - Handles JSON strings
        - Ensures final result is a dict
        """

        # result.value → AzureChatCompletion or SK message
        if hasattr(result, "value"):
            try:
                return json.loads(result.value)
            except Exception:
                pass

        # Plain JSON string
        if isinstance(result, str):
            try:
                return json.loads(result)
            except Exception:
                raise ValueError(
                    "ContentCreatorAgent: LLM returned non-JSON string output."
                )

        # Already a dict
        if isinstance(result, dict):
            return result

        raise ValueError(
            f"ContentCreatorAgent: Unrecognized SK output type: {type(result)}"
        )
