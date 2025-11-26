"""
Pytest configuration for cleaner test output.
"""
import pytest


def pytest_configure(config):
    """Configure pytest for cleaner output."""
    config.option.verbose = 1


def pytest_itemcollected(item):
    """Use test docstrings as display names."""
    if item._obj.__doc__:
        # Strip the docstring and use it as the node ID
        item._nodeid = item.obj.__doc__.strip()

