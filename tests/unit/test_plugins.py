"""
Unit tests for plugin implementations.
"""

import pytest
import json
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
        
        # Pass metrics as JSON string as expected by the method
        metrics_json = json.dumps({
            "control": {"conversions": 100, "visits": 1000, "unsubscribe_rate": 0.01},
            "A": {"conversions": 120, "visits": 1000, "unsubscribe_rate": 0.012}
        })
        
        result = await plugin.calculate_significance(metrics_json=metrics_json)
        
        assert "uplift" in result.lower() or "results" in result.lower()
        assert "p_value" in result.lower()
        assert "significant" in result.lower() or "winner" in result.lower()
