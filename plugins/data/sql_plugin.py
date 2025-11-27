"""
SQL Plugin — Safe, read-only DB access for marketing workflows.
"""

from __future__ import annotations

import logging
import pyodbc
import asyncio
from typing import Annotated, Dict, Any, List

from semantic_kernel.functions import kernel_function
from plugins.base_plugin import BasePlugin


class SQLPlugin(BasePlugin):
    """
    Safe SQL execution plugin.
    - Read-only
    - SELECT-only
    - No PII returned (enforced in consuming agents)
    - Compatible with Semantic Kernel 1.39
    """

    def __init__(self, config: dict):
        super().__init__(name="SQLPlugin")
        self.config = config
        self.logger = logging.getLogger(__name__)

        sql_cfg = config.get("sql", {})
        self.connection_string = sql_cfg.get("connection_string")

        if not self.connection_string:
            self.logger.warning("SQLPlugin initialized without a connection string.")

    # ============================================================
    #  TOOL: EXECUTE SQL
    # ============================================================

    @kernel_function(
        name="execute_sql",
        description="Execute a safe SQL SELECT query and return JSON results."
    )
    async def execute_sql(
        self,
        query: Annotated[str, "MUST be a SELECT query. Never returns PII."]
    ) -> Annotated[Dict[str, Any], "JSON result with rows, columns, and status"]:
        """
        Runs a SELECT-only SQL query using pyodbc in a non-blocking way.
        Returns uniform JSON dicts so downstream agents can parse them.
        """

        # Enforce read-only policy
        if not query.strip().lower().startswith("select"):
            return {
                "status": "error",
                "message": "Only SELECT queries are permitted",
                "rows": []
            }

        # Offload blocking pyodbc work into a thread
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run_sql_blocking, query)

        return result

    # ============================================================
    #  INTERNAL: BLOCKING SQL EXECUTION
    # ============================================================

    def _run_sql_blocking(self, query: str) -> Dict[str, Any]:
        """Executes SQL in sync mode (inside thread executor)."""

        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            cursor.execute(query)

            columns = [col[0] for col in cursor.description]
            rows_raw = cursor.fetchall()

            # Convert to JSON-safe rows
            rows = [dict(zip(columns, row)) for row in rows_raw]

            cursor.close()
            conn.close()

            return {
                "status": "ok",
                "row_count": len(rows),
                "columns": columns,
                "rows": rows[:50]  # safety limit
            }

        except Exception as e:
            self.logger.error(f"SQL error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "rows": []
            }
