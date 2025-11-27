from __future__ import annotations

import json
import logging
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

from models.customer_event import CustomerEvent
from models.content_grounding import GroundedContent
from models.variant import Variant

logger = logging.getLogger(__name__)


class CreativeMode(str, Enum):
    """
    Professional, enterprise-friendly names for variant generation modes.
    These can map to different temperature ranges / risk profiles.
    """
    PRECISION = "precision"                    # Very low creativity, compliance-safe
    BRAND_VOICE = "brand_voice"                # On-brand, lightly adaptive
    ADAPTIVE_CREATIVE = "adaptive_creative"    # Trend-aware, campaign testing
    HIGH_VARIANCE = "high_variance"            # Bold exploration, candidate discovery
    DIVERGENT_IDEATION = "divergent_ideation"  # Internal-only, maximal divergence


# Default temperature mapping – can be tuned in config if needed.
TEMPERATURE_BY_MODE: Dict[CreativeMode, float] = {
    CreativeMode.PRECISION: 0.1,
    CreativeMode.BRAND_VOICE: 0.5,
    CreativeMode.ADAPTIVE_CREATIVE: 0.8,
    CreativeMode.HIGH_VARIANCE: 1.1,
    CreativeMode.DIVERGENT_IDEATION: 1.4,
}


class VariantGenerationConfig(BaseModel):
    """
    Configuration for how variants should be generated.
    This is orchestration-level control for creative risk & output size.
    """

    mode: CreativeMode = Field(
        default=CreativeMode.BRAND_VOICE,
        description="Creative mode controlling temperature and style."
    )

    n_variants: int = Field(
        default=3,
        ge=1,
        le=10,
        description="How many variants to generate for this event."
    )

    max_output_tokens: int = Field(
        default=300,
        ge=64,
        le=2048,
        description="Maximum tokens per variant response from the model."
    )

    channel: str = Field(
        default="email",
        description="Target channel: email | sms | push (for copy length / style hints)."
    )


class VariantBatchResult(BaseModel):
    """
    Container for all variants generated for a given event and grounding bundle.
    This is what the StrategyLead/ExperimentRunner can use downstream.
    """

    customer_event_id: str
    mode: CreativeMode
    temperature: float
    variants: List[Variant]


def build_variant_prompt(
    event: CustomerEvent,
    grounding: GroundedContent,
    config: VariantGenerationConfig,
) -> str:
    """
    Build a system-style prompt for the LLM that:

    - Explains the brand-safe behavior
    - Injects retrieved grounded items as the ONLY approved source
    - Instructs the model to generate multiple labeled variants
    - Ensures citations / source IDs are attached

    The model is expected to return STRICT JSON which we later parse.
    """

    # Summarize retrieved grounded items
    item_blocks: List[str] = []
    for idx, item in enumerate(grounding.grounded_items):
        item_id = item.chunk_id or f"item_{idx+1}"
        preview_text = item.text.strip().replace("\n", " ")
        if len(preview_text) > 240:
            preview_text = preview_text[:240] + "..."

        item_blocks.append(
            f"- id: {item_id}\n"
            f"  source: {item.source}\n"
            f"  score: {item.score}\n"
            f"  text: \"{preview_text}\""
        )

    items_block = "\n".join(item_blocks) if item_blocks else "None"

    # Event context
    event_json = event.model_dump_json(indent=2)

    prompt = f"""
You are Azure CEO's Variant Generation Agent, working inside an enterprise,
multi-agent marketing system.

Your responsibilities:
- Generate marketing message variants that are grounded in approved documentation.
- Use ONLY the provided grounded items as factual sources.
- Attach source IDs so downstream agents can verify citations.
- Respect the requested creative mode and channel.

Customer Event Context (JSON):
{event_json}

RAG Grounding (Top-{grounding.top_k} retrieved items):
{items_block}

Creative Mode: {config.mode.value}
Channel: {config.channel}
Number of Variants: {config.n_variants}

OUTPUT REQUIREMENTS (STRICT JSON):

Return ONLY JSON with this structure, no commentary:

{{
  "variants": [
    {{
      "variant_id": "A",
      "subject": "Short subject line (if channel supports it, else null)",
      "body": "Full body copy with inline bracket-style citations where appropriate.",
      "mode": "{config.mode.value}",
      "source_content_ids": ["item_1", "item_2"]
    }},
    ...
  ]
}}

RULES:
- Do NOT hallucinate features, pricing, promotions, or competitors.
- Every factual product claim MUST be supported by the grounded items.
- Inline citations should refer to source_content_ids, e.g.:
  "Our new cushioning system reduces impact [item_1]".
- If the channel is "sms", keep body under ~160 characters when possible.
- If the channel is "push", keep body concise and punchy.
- If the channel is "email", you may use 1–2 short paragraphs.
""".strip()

    return prompt


def _extract_json_block(raw_content: str) -> str:
    """
    Best-effort extraction of the JSON block in case the model
    wraps it with extra prose. Keeps things defensive.
    """
    raw_content = raw_content.strip()
    if raw_content.startswith("{") and raw_content.endswith("}"):
        return raw_content

    first = raw_content.find("{")
    last = raw_content.rfind("}")
    if first != -1 and last != -1 and last > first:
        return raw_content[first:last + 1]

    return raw_content  # fallback


def parse_variant_response(
    raw_content: str,
    config: VariantGenerationConfig,
) -> List[Variant]:
    """
    Parse LLM output into a list of Variant objects.

    Expects STRICT JSON in the form:
    {
      "variants": [
        {
          "variant_id": "A",
          "subject": "...",
          "body": "...",
          "mode": "brand_voice",
          "source_content_ids": ["item_1"]
        }
      ]
    }

    - Unknown fields are ignored.
    - Missing fields fall back to safe defaults.
    """

    cleaned = _extract_json_block(raw_content)

    try:
        parsed = json.loads(cleaned)
    except Exception as e:
        logger.error("Failed to parse variant JSON: %s", e)
        return [
            Variant(
                variant_id="FALLBACK",
                subject=None,
                body="Fallback variant: model did not return valid JSON.",
                mode=config.mode.value,
                citations=[],
                embeddings=None,
                score=None,
            )
        ]

    raw_variants = parsed.get("variants", [])
    variants: List[Variant] = []

    for idx, v in enumerate(raw_variants[: config.n_variants]):
        variant_id = v.get("variant_id") or chr(ord("A") + idx)
        subject = v.get("subject")
        body = v.get("body") or ""
        mode_str = v.get("mode") or config.mode.value

        # We ignore source_content_ids here; they can later be
        # resolved into full Citation objects by a RAG/citation service.
        variants.append(
            Variant(
                variant_id=variant_id,
                subject=subject,
                body=body,
                mode=mode_str,
                citations=[],      # Compliance / RAG pipeline fills this later
                embeddings=None,
                score=None,
            )
        )

    if not variants:
        variants.append(
            Variant(
                variant_id="FALLBACK",
                subject=None,
                body="Fallback variant: no variants could be parsed from model output.",
                mode=config.mode.value,
                citations=[],
                embeddings=None,
                score=None,
            )
        )

    return variants


async def generate_variants_for_event(
    *,
    # NOTE: we do NOT depend on Semantic Kernel directly here, so this
    # helper can be used both by your SK-based ContentCreatorAgent
    # *or* by a lower-level Azure OpenAI client.
    llm_call_fn,
    event: CustomerEvent,
    grounding: GroundedContent,
    config: Optional[VariantGenerationConfig] = None,
) -> VariantBatchResult:
    """
    High-level helper that:

    1. Builds a mode-aware, RAG-grounded prompt.
    2. Calls the provided LLM function (llm_call_fn).
    3. Parses the response into your shared Variant model.
    4. Returns a VariantBatchResult for downstream agents.

    `llm_call_fn` should be an async callable with signature:

        async def llm_call_fn(prompt: str, temperature: float, max_tokens: int) -> str:
            ...

    This keeps the helper **framework-agnostic** (works with SK, direct AOAI, etc.).
    """

    if config is None:
        config = VariantGenerationConfig()

    temperature = TEMPERATURE_BY_MODE[config.mode]

    prompt = build_variant_prompt(event, grounding, config)

    # Allan wires this to SK or Azure OpenAI.
    raw_content = await llm_call_fn(
        prompt=prompt,
        temperature=temperature,
        max_tokens=config.max_output_tokens,
    )

    variants = parse_variant_response(raw_content, config)

    return VariantBatchResult(
        customer_event_id=event.event_id,
        mode=config.mode,
        temperature=temperature,
        variants=variants,
    )
