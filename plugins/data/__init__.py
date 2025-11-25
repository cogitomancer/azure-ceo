"""
Data access plugins for CDP and database queries.
"""

from .cdp_plugin import CDPPlugin
from .sql_plugin import SQLPlugin

__all__ = ["CDPPlugin"]