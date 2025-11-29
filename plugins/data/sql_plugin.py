"""SQL Plugin — Safe, read-only DB access for marketing workflows.

Uses Azure SQL Database for customer segmentation queries.
Connection via AZURE_SQL_CONNECTION_STRING environment variable.

Fallback: Uses local CSV files from tables/ directory when Azure SQL is unavailable.
"""

from __future__ import annotations

import os
import logging
import asyncio
import re
import csv
from pathlib import Path
from typing import Annotated, Dict, Any, List

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

from semantic_kernel.functions import kernel_function
from plugins.base_plugin import BasePlugin


class SQLPlugin(BasePlugin):
    """
    Safe SQL execution plugin for Azure SQL Database.
    - Read-only
    - SELECT-only
    - No PII returned (enforced in consuming agents)
    - Compatible with Semantic Kernel 1.39
    """

    def __init__(self, config: dict):
        super().__init__(name="SQLPlugin")
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Determine if we should use local CSV fallback
        self.use_local_csv = os.getenv("USE_LOCAL_CSV", "false").lower() in ("true", "1", "yes")

        # Try environment variable first, then config
        self.connection_string = os.getenv("AZURE_SQL_CONNECTION_STRING")
        
        if not self.connection_string:
            sql_cfg = config.get("sql", {})
            self.connection_string = sql_cfg.get("connection_string")

        # If no connection string or local CSV forced, use local CSV fallback
        if not self.connection_string or self.use_local_csv or not PYODBC_AVAILABLE:
            self.use_local_csv = True
            self.logger.info("SQLPlugin using local CSV fallback mode.")
            self._load_csv_data()
        else:
            self.logger.info("SQLPlugin using Azure SQL Database.")
    
    def _load_csv_data(self):
        """Load CSV data from tables/ directory for local fallback."""
        self._csv_tables: Dict[str, List[Dict[str, Any]]] = {}
        
        # Determine company from config or env
        company_id = os.getenv("COMPANY_ID", "hudson_street").lower()
        
        # Map company_id to folder name
        folder_map = {
            "hudson_street": "Hudson_street",
            "microsoft": "Microsoft"
        }
        folder_name = folder_map.get(company_id, "Hudson_street")
        
        tables_path = Path(__file__).parent.parent.parent / "tables" / folder_name
        
        # Load customers.csv as the primary table
        customers_file = tables_path / "customers.csv"
        if customers_file.exists():
            try:
                with open(customers_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    self._csv_tables["customers"] = list(reader)
                self.logger.info(f"Loaded {len(self._csv_tables['customers'])} rows from customers.csv")
            except Exception as e:
                self.logger.error(f"Error loading customers.csv: {e}")
                self._csv_tables["customers"] = []
        else:
            self.logger.warning(f"customers.csv not found at {customers_file}")
            self._csv_tables["customers"] = []

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

        # Use local CSV or Azure SQL based on configuration
        if self.use_local_csv:
            return self._run_csv_query(query)
        
        # Offload blocking pyodbc work into a thread
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run_sql_blocking, query)

        return result

    # ============================================================
    #  INTERNAL: BLOCKING SQL EXECUTION
    # ============================================================

    def _run_sql_blocking(self, query: str) -> Dict[str, Any]:
        """Executes SQL in sync mode (inside thread executor)."""
        if not PYODBC_AVAILABLE:
            return {
                "status": "error",
                "message": "pyodbc not available, use local CSV mode",
                "rows": []
            }

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
    
    # ============================================================
    #  LOCAL CSV QUERY ENGINE
    # ============================================================
    
    def _run_csv_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a SQL-like query against local CSV data.
        
        Supports basic SELECT queries with:
        - SELECT * or SELECT col1, col2
        - FROM table_name (currently only 'customers')
        - WHERE col = 'value' AND/OR col = 'value'
        - LIMIT N
        """
        try:
            query_lower = query.lower().strip()
            
            # Parse table name from FROM clause
            from_match = re.search(r'from\s+(\w+)', query_lower)
            if not from_match:
                return {
                    "status": "error",
                    "message": "Could not parse table name from query",
                    "rows": []
                }
            
            table_name = from_match.group(1)
            
            # Get data from the table
            if table_name not in self._csv_tables:
                return {
                    "status": "error",
                    "message": f"Table '{table_name}' not found. Available: {list(self._csv_tables.keys())}",
                    "rows": []
                }
            
            rows = self._csv_tables[table_name].copy()
            
            # Apply WHERE filters
            where_match = re.search(r'where\s+(.+?)(?:limit|order|group|$)', query_lower, re.DOTALL)
            if where_match:
                where_clause = where_match.group(1).strip()
                rows = self._apply_where_filters(rows, where_clause)
            
            # Parse SELECT columns
            select_match = re.search(r'select\s+(.+?)\s+from', query_lower)
            if select_match:
                columns_str = select_match.group(1).strip()
                if columns_str != '*':
                    selected_cols = [c.strip() for c in columns_str.split(',')]
                    rows = [{k: v for k, v in row.items() if k.lower() in [c.lower() for c in selected_cols]} for row in rows]
            
            # Apply LIMIT
            limit_match = re.search(r'limit\s+(\d+)', query_lower)
            limit = int(limit_match.group(1)) if limit_match else 50
            rows = rows[:limit]
            
            # Get columns from result
            columns = list(rows[0].keys()) if rows else []
            
            return {
                "status": "ok",
                "row_count": len(rows),
                "columns": columns,
                "rows": rows,
                "source": "local_csv"
            }
            
        except Exception as e:
            self.logger.error(f"CSV query error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "rows": []
            }
    
    def _apply_where_filters(self, rows: List[Dict], where_clause: str) -> List[Dict]:
        """
        Apply WHERE clause filters to rows.
        
        Supports:
        - col = 'value' or col = "value"
        - col > N, col < N, col >= N, col <= N (for numeric)
        - col LIKE '%pattern%'
        - AND / OR combinations
        """
        # Split by AND/OR (simple parsing)
        # Handle AND first (higher precedence)
        conditions = []
        
        # Simple tokenization - split by AND/OR
        parts = re.split(r'\s+(and|or)\s+', where_clause, flags=re.IGNORECASE)
        
        operators = []
        for i, part in enumerate(parts):
            if part.lower() in ('and', 'or'):
                operators.append(part.lower())
            else:
                conditions.append(part.strip())
        
        def evaluate_condition(row: Dict, condition: str) -> bool:
            """Evaluate a single condition against a row."""
            # Handle LIKE
            like_match = re.match(r"(\w+)\s+like\s+['\"](.+)['\"]", condition, re.IGNORECASE)
            if like_match:
                col, pattern = like_match.groups()
                col_value = str(row.get(col, row.get(col.lower(), ""))).lower()
                # Convert SQL LIKE to regex
                regex_pattern = pattern.replace('%', '.*').replace('_', '.').lower()
                return bool(re.match(f"^{regex_pattern}$", col_value))
            
            # Handle comparison operators
            comp_match = re.match(r"(\w+)\s*(>=|<=|!=|<>|=|>|<)\s*['\"]?([^'\"]+)['\"]?", condition)
            if comp_match:
                col, op, value = comp_match.groups()
                col_value = row.get(col, row.get(col.lower(), ""))
                
                # Try numeric comparison
                try:
                    col_num = float(col_value)
                    val_num = float(value)
                    if op == '=': return col_num == val_num
                    if op == '!=': return col_num != val_num
                    if op == '<>': return col_num != val_num
                    if op == '>': return col_num > val_num
                    if op == '<': return col_num < val_num
                    if op == '>=': return col_num >= val_num
                    if op == '<=': return col_num <= val_num
                except (ValueError, TypeError):
                    # String comparison
                    col_str = str(col_value).lower()
                    val_str = str(value).lower()
                    if op == '=': return col_str == val_str
                    if op == '!=': return col_str != val_str
                    if op == '<>': return col_str != val_str
                    return False
            
            return True  # Unknown condition format, pass through
        
        filtered_rows = []
        for row in rows:
            if not conditions:
                filtered_rows.append(row)
                continue
            
            # Evaluate all conditions
            results = [evaluate_condition(row, cond) for cond in conditions]
            
            # Combine with AND/OR
            if not operators:
                if results[0]:
                    filtered_rows.append(row)
            else:
                result = results[0]
                for i, op in enumerate(operators):
                    if i + 1 < len(results):
                        if op == 'and':
                            result = result and results[i + 1]
                        else:  # or
                            result = result or results[i + 1]
                if result:
                    filtered_rows.append(row)
        
        return filtered_rows
