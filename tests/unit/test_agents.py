"""
Unit tests for agent implementations.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from semantic_kernel import Kernel

from agents.strategy_lead import StrategyLeadAgent
from agents.data_segmenter import DataSegmenterAgent
from agents.content_creator import ContentCreatorAgent


class TestAgents:
    """Test agent initialization and behavior."""
    
    @pytest.fixture
    def mock_kernel(self):
        """Create mock Semantic Kernel."""
        return Mock(spec=Kernel)
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            "agents": {
                "StrategyLead": {
                    "model": "gpt-4o",
                    "temperature": 0.7
                },
                "DataSegmenter": {
                    "model": "gpt-4-turbo",
                    "temperature": 0.3
                },
                "ContentCreator": {
                    "model": "gpt-4o",
                    "temperature": 0.8
                }
            }
        }
    
    def test_strategy_lead_initialization(self, mock_kernel, config):
        """Test StrategyLead agent creation."""
        agent = StrategyLeadAgent(mock_kernel, config)
        
        assert agent.agent_name == "StrategyLead"
        assert "orchestrator" in agent.instructions.lower()
        assert isinstance(agent.get_plugins(), list)
    
    def test_data_segmenter_initialization(self, mock_kernel, config):
        """Test DataSegmenter agent creation."""
        agent = DataSegmenterAgent(mock_kernel, config)
        
        assert agent.agent_name == "DataSegmenter"
        assert "data analyst" in agent.instructions.lower()
        assert len(agent.get_plugins()) > 0
    
    def test_content_creator_initialization(self, mock_kernel, config):
        """Test ContentCreator agent creation."""
        agent = ContentCreatorAgent(mock_kernel, config)
        
        assert agent.agent_name == "ContentCreator"
        assert "copywriter" in agent.instructions.lower()
        assert "citation" in agent.instructions.lower()
