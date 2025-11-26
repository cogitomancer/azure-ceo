"""
Unit tests for plugin implementations.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from plugins.experiment.metrics_plugin import MetricsPlugin


class TestPlugins:
    """Test plugin functionality."""
    
    @pytest.fixture
    def config(self):
        return {}
    
    @pytest.mark.asyncio
    async def test_statistical_calculation(self, config):
        """Test statistical significance calculation."""
        plugin = MetricsPlugin(config)
        
        result = await plugin.calculate_significance(
            variant_a_conversions=100,
            variant_a_visits=1000,
            variant_b_conversions=120,
            variant_b_visits=1000
        )
        
        assert "uplift" in result.lower()
        assert "p-value" in result.lower()
        assert "significant" in result.lower()
