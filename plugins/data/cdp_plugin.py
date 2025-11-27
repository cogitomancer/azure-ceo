"""
CDP Plugin — Azure Synapse backed audience segmentation.
"""

from __future__ import annotations

import logging
from typing import Annotated, Dict, Any

from semantic_kernel.functions import kernel_function
from plugins.base_plugin import BasePlugin


class CDPPlugin(BasePlugin):
    """
    Plugin for retrieving *anonymized, aggregated* customer segment data
    from Azure Synapse Analytics.

    This plugin NEVER returns PII.
    """

    def __init__(self, config: dict):
        super().__init__(name="CDPPlugin")
        self.config = config
        self.logger = logging.getLogger(__name__)

        syn_cfg = config.get("synapse", {})
        self.database = syn_cfg.get("database", "marketing_data")

    # ============================================================
    # TOOL: QUERY CUSTOMER SEGMENTS
    # ============================================================

    @kernel_function(
        name="query_customer_segments",
        description="Retrieve anonymized segment statistics from Azure Synapse"
    )
    async def query_customer_segments(
        self,
        criteria: Annotated[str, "Natural language description such as 'active runners'"]
    ) -> Annotated[Dict[str, Any], "Structured segment metadata (no PII)"]:
        """
        Converts natural language → segment table → Synapse query.
        Produces a structured JSON-safe dict.
        """

        segment_table = self._map_to_segment_table(criteria)

        try:
            from plugins.data.sql_plugin import SQLPlugin
            sql = SQLPlugin(self.config)

            query = f"""
                SELECT 
                    COUNT(*) AS customer_count,
                    AVG(total_purchases) AS avg_purchases,
                    AVG(lifetime_value) AS avg_ltv
                FROM {self.database}.dbo.{segment_table}
                WHERE is_active = 1
            """

            result = await sql.execute_sql(query)
            return self._build_segment_response(segment_table, result)

        except Exception as e:
            self.logger.error(f"Synapse unavailable, using mock data. Error: {e}")
            return self._mock_segment(criteria)

    # ============================================================
    # TOOL: GET SEGMENT DETAILS
    # ============================================================

    @kernel_function(
        name="get_segment_details",
        description="Retrieve extended metadata for a given Synapse segment ID"
    )
    async def get_segment_details(
        self,
        segment_id: Annotated[str, "Segment table name such as 'customers_active_runners'"]
    ) -> Annotated[Dict[str, Any], "Extended segment metadata"]:
        """
        Secondary tool for deeper profile pull.
        """

        try:
            from plugins.data.sql_plugin import SQLPlugin
            sql = SQLPlugin(self.config)

            query = f"""
                SELECT
                    COUNT(*) AS total_customers,
                    AVG(engagement_score) AS avg_engagement
                FROM {self.database}.dbo.{segment_id}
                WHERE is_active = 1
            """

            raw = await sql.execute_sql(query)
            return {
                "segment_id": segment_id,
                "total_customers": raw.get("total_customers", None),
                "avg_engagement": raw.get("avg_engagement", None),
                "status": "ok"
            }

        except Exception as e:
            self.logger.error(f"get_segment_details fallback: {e}")
            return {
                "segment_id": segment_id,
                "total_customers": 12500,
                "avg_engagement": 0.62,
                "status": "mock"
            }

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    def _map_to_segment_table(self, criteria: str) -> str:
        mapping = {
            "runner": "customers_active_runners",
            "running": "customers_active_runners",
            "hiker": "customers_hikers",
            "hiking": "customers_hikers",
            "new": "customers_new",
            "loyal": "customers_loyal",
            "engaged": "customers_highly_engaged",
        }

        query_l = criteria.lower()
        for k, v in mapping.items():
            if k in query_l:
                return v

        return "customers_all_active"

    def _build_segment_response(self, table: str, row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "segment_id": table,
            "estimated_size": row.get("customer_count", None),
            "avg_purchases": row.get("avg_purchases", None),
            "avg_ltv": row.get("avg_ltv", None),
            "status": "ok",
        }

    def _mock_segment(self, criteria: str) -> Dict[str, Any]:
        crit = criteria.lower()

        if "runner" in crit or "running" in crit:
            return {
                "segment_id": "customers_active_runners",
                "estimated_size": 12500,
                "avg_purchases": 4.1,
                "avg_ltv": 320,
                "status": "mock"
            }

        if "new" in crit:
            return {
                "segment_id": "customers_new",
                "estimated_size": 8300,
                "avg_purchases": 1.2,
                "avg_ltv": 125,
                "status": "mock"
            }

        return {
            "segment_id": "customers_all_active",
            "estimated_size": 45000,
            "avg_purchases": 2.8,
            "avg_ltv": 210,
            "status": "mock"
        }
