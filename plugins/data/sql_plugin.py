"""
SQL plugin for direct database queries.
"""

from semantic_kernel.functions import kernel_function
from typing import Annotated
import pyodbc
import logging


class SQLPlugin:
    """Plugin for executing SQL queries against customer database."""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.connection_string = config.get("sql", {}).get("connection_string")
    
    @kernel_function(
        name="execute_sql",
        description="Execute SQL query against customer database"
    )
    async def execute_sql(
        self,
        query: Annotated[str, "SQL query to execute"]
    ) -> Annotated[str, "Query results"]:
        """
        Execute SQL query with safety checks.
        Only SELECT queries allowed.
        """
        
        # Safety check
        if not query.strip().upper().startswith("SELECT"):
            return "ERROR: Only SELECT queries are allowed"
        
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                
                rows = cursor.fetchall()
                
                if not rows:
                    return "No results found"
                
                # Format results
                result = f"Found {len(rows)} rows:\n"
                for row in rows[:10]:  # Limit to 10 rows
                    result += str(row) + "\n"
                
                return result
                
        except Exception as e:
            self.logger.error(f"SQL execution error: {e}")
            return f"ERROR: {str(e)}"
