"""
Integration tests for agent orchestration.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from core.kernel_factory import KernelFactory
from core.orchestrator import MarketingOrchestrator


class TestOrchestration:
    """Test multi-agent orchestration."""
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            "azure_openai": {
                "endpoint": "https://test.openai.azure.com/",
                "deployment_name": "gpt-4o",
                "api_version": "2024-02-01"
            },
            "cosmos_db": {
                "endpoint": "https://test.documents.azure.com:443/",
                "database_name": "test_db",
                "container_name": "test_container"
            },
            "azure_monitor": {
                "connection_string": "InstrumentationKey=test"
            },
            "agents": {
                "StrategyLead": {},
                "DataSegmenter": {},
                "ContentCreator": {},
                "ComplianceOfficer": {},
                "ExperimentRunner": {}
            }
        }
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Azure services")
    async def test_campaign_workflow(self, config):
        """Test end-to-end campaign workflow."""
        kernel_factory = KernelFactory(config)
        kernel = kernel_factory.create_kernel()
        
        orchestrator = MarketingOrchestrator(kernel, config)
        
        objective = "Test campaign for integration testing"
        session_id = "test_session_001"
        
        message_count = 0
        async for message in orchestrator.execute_campaign_request(objective, session_id):
            message_count += 1
            assert message.content is not None
        
        assert message_count > 0
