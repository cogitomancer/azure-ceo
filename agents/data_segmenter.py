from __future__ import annotations

import json
import logging
from typing import List, Dict, Any

from agents.base_agent import BaseMarketingAgent
from plugins.data.cdp_plugin import CDPPlugin
from plugins.data.sql_plugin import SQLPlugin
from plugins.content.rag_plugin import RAGPlugin

logger = logging.getLogger(__name__)


class DataSegmenterAgent(BaseMarketingAgent):
    """
    Converts strategic audience intents into concrete, structured customer segments.
    """

    def __init__(self, kernel, config):
        super().__init__(kernel, config, agent_key="DataSegmenter")

        # Override YAML with full persona
        self.instructions = """
You are the Data Segmenter for Azure CEO's autonomous marketing team.

PRIMARY RESPONSIBILITIES:
1. Translate StrategyLead guidance into concrete, anonymized audience segments.
2. Generate segmentation logic using SQL or CDP-style filters.
3. Retrieve or estimate:
   - Segment size (exact or estimated)
   - Behavioral patterns
   - Value indicators (LTV buckets, churn risk)
4. Provide structured, reusable segmentation objects.

TOOLS:
- query_customer_segments      (CDP)
- execute_sql                  (Synapse DW)
- get_segment_details          (CDP)
- retrieve_product_info        (RAG grounding)
- extract_citations            (RAG citation generation)

RULES:
- NO PII (no email, phone, name, address).
- Always specify time window + data source.
- Use qualitative labels if numeric precision is unavailable.
- Flag stale data or missing dimensions.
- Provide actionable guidance for:
    - ContentCreator
    - ExperimentRunner

OUTPUT FORMAT:
{
  "segments": [
    {
      "name": "High-LTV Active Runners",
      "logic": "purchased_running_category_last_90d AND ltv_bucket='high'",
      "estimated_size": 12400,
      "responsiveness": "high",
      "insights": [...],
      "notes_for_content_creator": "...",
      "notes_for_experiment_runner": "..."
    }
  ]
}
"""

    def get_plugins(self) -> list:
        return [
            CDPPlugin(self.config),
            SQLPlugin(self.config),
            RAGPlugin(self.config)
        ]

    # ───────────────────────────────────────────────────────────────
    #   MAIN EXECUTION ENTRYPOINT
    # ───────────────────────────────────────────────────────────────
    async def segment_audience(self, strategy_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Primary segmentation method:
        - Takes structured dict from StrategyLead
        - Calls Semantic Kernel to translate into segmentation spec
        - Normalizes + validates output
        """

        if not isinstance(strategy_payload, dict):
            raise ValueError("DataSegmenterAgent: strategy_payload must be dict.")

        # Invoke SK
        try:
            result = await self.kernel.run_async(strategy_payload)
        except TypeError:
            result = await self.kernel.run_async(
                function_name="default",
                input_vars=strategy_payload
            )

        parsed = self._parse_llm_output(result)

        #
        # Validate segments structure
        #
        segments_raw = parsed.get("segments", [])

        if not segments_raw:
            logger.warning("DataSegmenterAgent: No segments returned from LLM.")
            return {"segments": []}

        #
        # Normalize each segment object
        #
        normalized_segments = []

        for seg in segments_raw:
            try:
                normalized = {
                    "name": seg.get("name", "Unnamed Segment"),
                    "logic": seg.get("logic", ""),
                    "estimated_size": seg.get("estimated_size", None),
                    "responsiveness": seg.get("responsiveness", "unknown"),
                    "insights": seg.get("insights", []),
                    "notes_for_content_creator": seg.get("notes_for_content_creator", ""),
                    "notes_for_experiment_runner": seg.get("notes_for_experiment_runner", "")
                }
                normalized_segments.append(normalized)
            except Exception as e:
                logger.error(f"Malformed segment object from LLM: {seg}", exc_info=True)

        return {"segments": normalized_segments}

    # ───────────────────────────────────────────────────────────────
    #   INTERNAL PARSER (LLM → dict)
    # ───────────────────────────────────────────────────────────────
    def _parse_llm_output(self, result: Any) -> Dict[str, Any]:
        """
        Normalize SK output:
        - Handles SK chat objects with .value
        - Handles JSON strings
        - Returns a dict or raises ValueError
        """

        # SK result.value
        if hasattr(result, "value"):
            try:
                return json.loads(result.value)
            except Exception:
                pass

        # JSON string
        if isinstance(result, str):
            try:
                return json.loads(result)
            except Exception as e:
                raise ValueError(
                    "DataSegmenterAgent: LLM output was not valid JSON."
                ) from e

        # Already dict
        if isinstance(result, dict):
            return result

        raise ValueError(
            f"DataSegmenterAgent: Unrecognized output format from SK: {type(result)}"
        )
