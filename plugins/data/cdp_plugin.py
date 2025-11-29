"""
CDP Plugin — Azure SQL Database backed audience segmentation.

Uses company-specific SQL databases and customer tables:
- Hudson Street Bakery: hudson_street_marketing.customers_hudson_street
- Microsoft: microsoft_marketing.customers_microsoft

Customer data loaded from tables/ CSV files into Azure SQL Database.
"""

from __future__ import annotations

import logging
from typing import Annotated, Dict, Any

from semantic_kernel.functions import kernel_function
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class CDPPlugin(BasePlugin):
    """
    Plugin for retrieving *anonymized, aggregated* customer segment data
    from Azure SQL Database.

    This plugin NEVER returns PII.
    Uses company-specific SQL Database configuration based on COMPANY_ID.
    """

    def __init__(self, config: dict):
        super().__init__(name="CDPPlugin")
        self.config = config

        # Get company-specific SQL Database configuration
        self.company_sql_config = self._get_company_sql_config()
        
        sql_cfg = config.get("sql", {})
        self.database = self.company_sql_config.get("database", sql_cfg.get("database", "marketing_data"))
        self.customer_table = self.company_sql_config.get("customer_table", "customers")
        self.company_name = self.company_sql_config.get("company_name", "Unknown")
        
        logger.info(f"CDPPlugin initialized for {self.company_name} using database: {self.database}")

    def _get_company_sql_config(self) -> Dict[str, Any]:
        """Get company-specific SQL Database configuration."""
        try:
            from services.company_data_service import CompanyDataService
            service = CompanyDataService()
            sql_config = service.get_sql_config()
            sql_config["company_name"] = service.get_company_info()["name"]
            return sql_config
        except Exception as e:
            logger.warning(f"Could not load company SQL config: {e}")
            return {"database": "marketing_data", "customer_table": "customers", "company_name": "Unknown"}

    # ============================================================
    # TOOL: QUERY CUSTOMER SEGMENTS
    # ============================================================

    @kernel_function(
        name="query_customer_segments",
        description="Retrieve anonymized segment statistics from Azure SQL Database"
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
            self.logger.error(f"SQL Database unavailable, using mock data. Error: {e}")
            return self._mock_segment(criteria)

    # ============================================================
    # TOOL: GET SEGMENT DETAILS
    # ============================================================

    @kernel_function(
        name="get_segment_details",
        description="Retrieve extended metadata for a given SQL segment ID"
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
        """
        Return mock segment data based on company and criteria.
        Uses local tables/ data when Azure Synapse is unavailable.
        """
        crit = criteria.lower()
        
        # Try to load from local customer data
        try:
            from services.company_data_service import CompanyDataService
            service = CompanyDataService()
            segments = service.get_customer_segments()
            total = sum(segments.values()) if segments else 0
            
            if total > 0:
                return {
                    "segment_id": f"{self.customer_table}_filtered",
                    "estimated_size": total,
                    "segments": segments,
                    "company": self.company_name,
                    "status": "mock_from_local_data"
                }
        except Exception as e:
            logger.debug(f"Could not load local segment data: {e}")

        # Fallback mock data by company
        if "hudson" in self.company_name.lower() or "bakery" in self.company_name.lower():
            # Hudson Street Bakery mock segments
            if "loyal" in crit or "regular" in crit:
                return {
                    "segment_id": "customers_loyal_bakery",
                    "estimated_size": 2500,
                    "avg_purchases": 8.2,
                    "avg_ltv": 450,
                    "company": self.company_name,
                    "status": "mock"
                }
            if "new" in crit or "first" in crit:
                return {
                    "segment_id": "customers_new_bakery",
                    "estimated_size": 1200,
                    "avg_purchases": 1.5,
                    "avg_ltv": 35,
                    "company": self.company_name,
                    "status": "mock"
                }
            return {
                "segment_id": "customers_all_bakery",
                "estimated_size": 5800,
                "avg_purchases": 4.1,
                "avg_ltv": 185,
                "company": self.company_name,
                "status": "mock"
            }
        
        # Microsoft / Enterprise mock segments
        if "enterprise" in crit or "large" in crit:
            return {
                "segment_id": "customers_enterprise",
                "estimated_size": 1500,
                "avg_purchases": 12.5,
                "avg_ltv": 125000,
                "company": self.company_name,
                "status": "mock"
            }
        if "smb" in crit or "small" in crit:
            return {
                "segment_id": "customers_smb",
                "estimated_size": 8500,
                "avg_purchases": 3.2,
                "avg_ltv": 8500,
                "company": self.company_name,
                "status": "mock"
            }

        return {
            "segment_id": f"{self.customer_table}_all_active",
            "estimated_size": 45000,
            "avg_purchases": 2.8,
            "avg_ltv": 210,
            "company": self.company_name,
            "status": "mock"
        }
