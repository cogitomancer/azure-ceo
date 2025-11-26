"""
Integration tests for agent orchestration.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.kernel_factory import KernelFactory
from core.orchestrator import MarketingOrchestrator
from config.azure_config import load_config


class TestOrchestration:
    """Test multi-agent orchestration."""
    
    @pytest.fixture
    def live_config(self):
        """Load real Azure configuration from .env"""
        return load_config()
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, live_config):
        """Test that orchestrator can be initialized with real Azure services."""
        print("\n🔧 Initializing Kernel Factory...")
        kernel_factory = KernelFactory(live_config)
        
        print("✓ Creating orchestrator...")
        orchestrator = MarketingOrchestrator(kernel_factory, live_config)
        
        # Verify orchestrator components
        assert orchestrator.kernel is not None, "Kernel should be initialized"
        assert orchestrator.kernel_factory is not None, "Kernel factory should be stored"
        assert orchestrator.config is not None, "Config should be stored"
        assert orchestrator.state_manager is not None, "State manager should be initialized"
        
        print("✓ Orchestrator initialized successfully")
        
    @pytest.mark.asyncio
    async def test_agents_initialization(self, live_config):
        """Test that all 5 agents are properly initialized."""
        print("\n🤖 Testing agent initialization...")
        kernel_factory = KernelFactory(live_config)
        orchestrator = MarketingOrchestrator(kernel_factory, live_config)
        
        # Verify all agents are created
        assert len(orchestrator.agents) == 5, "Should have 5 agents"
        
        agent_names = [agent.name for agent in orchestrator.agents]
        expected_agents = ["StrategyLead", "DataSegmenter", "ContentCreator", "ComplianceOfficer", "ExperimentRunner"]
        
        for expected_name in expected_agents:
            assert expected_name in agent_names, f"{expected_name} should be initialized"
            print(f"  ✓ {expected_name} agent created")
        
        print("✓ All agents initialized successfully")
    
    @pytest.mark.asyncio
    async def test_group_chat_creation(self, live_config):
        """Test that agent group chat is properly configured."""
        print("\n💬 Testing group chat creation...")
        kernel_factory = KernelFactory(live_config)
        orchestrator = MarketingOrchestrator(kernel_factory, live_config)
        
        # Verify group chat exists
        assert orchestrator.group_chat is not None, "Group chat should be initialized"
        
        # Verify agents are in group chat
        group_agents = orchestrator.group_chat.agents
        assert len(group_agents) == 5, "Group chat should have 5 agents"
        
        print(f"✓ Group chat created with {len(group_agents)} agents")
        
    @pytest.mark.asyncio
    async def test_state_manager_integration(self, live_config):
        """Test state manager is properly integrated."""
        print("\n💾 Testing state manager integration...")
        kernel_factory = KernelFactory(live_config)
        orchestrator = MarketingOrchestrator(kernel_factory, live_config)
        
        test_session_id = "test_orchestration_session_001"
        
        # Test loading state (should return empty or existing state)
        state = await orchestrator.state_manager.load_state(test_session_id)
        assert state is not None, "Should return a state object"
        
        print(f"✓ State manager integrated successfully")
        print(f"  Session ID: {test_session_id}")
        print(f"  State keys: {list(state.keys())}")
        
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="This is a long-running test - enable manually for full e2e testing")
    async def test_simple_campaign_execution(self, live_config):
        """Test a simple campaign execution (full e2e test - long running)."""
        print("\n🚀 Testing simple campaign execution (THIS WILL TAKE TIME)...")
        kernel_factory = KernelFactory(live_config)
        orchestrator = MarketingOrchestrator(kernel_factory, live_config)
        
        objective = "Create a simple welcome email for new customers"
        session_id = "test_campaign_execution_001"
        
        print(f"Objective: {objective}")
        print(f"Session ID: {session_id}")
        print("Executing campaign...")
        
        message_count = 0
        async for message in orchestrator.execute_campaign_request(objective, session_id):
            message_count += 1
            print(f"\n--- Message {message_count} ---")
            print(f"Agent: {message.name}")
            print(f"Role: {message.role}")
            print(f"Content preview: {message.content[:200]}...")
            
            # Safety check - don't run forever
            if message_count > 20:
                print("⚠️ Stopping after 20 messages for safety")
                break
                
            # Check for completion
            if "TERMINATE" in message.content or "<APPROVED>" in message.content:
                print("✓ Campaign completed successfully!")
                break
        
        assert message_count > 0, "Should have received at least one message"
        print(f"\n✓ Campaign execution test completed with {message_count} messages")
        
    @pytest.mark.asyncio
    async def test_get_campaign_status(self, live_config):
        """Test campaign status retrieval."""
        print("\n📊 Testing campaign status retrieval...")
        kernel_factory = KernelFactory(live_config)
        orchestrator = MarketingOrchestrator(kernel_factory, live_config)
        
        test_session_id = "test_status_check_001"
        
        # Get status for a session (should work even if session doesn't exist)
        status = await orchestrator.get_campaign_status(test_session_id)
        
        assert status is not None, "Should return status object"
        assert "session_id" in status, "Status should include session_id"
        assert status["session_id"] == test_session_id, "Session ID should match"
        
        print("✓ Campaign status retrieval working")
        print(f"  Status: {status}")


class TestOrchestrationErrorHandling:
    """Test error handling in orchestration."""
    
    @pytest.fixture
    def live_config(self):
        """Load real Azure configuration from .env"""
        return load_config()
    
    @pytest.mark.asyncio
    async def test_invalid_session_id_handling(self, live_config):
        """Test handling of very long or unusual session IDs."""
        print("\n🧪 Testing session ID handling...")
        kernel_factory = KernelFactory(live_config)
        orchestrator = MarketingOrchestrator(kernel_factory, live_config)
        
        # Test with various session ID formats
        test_cases = [
            "simple_id",
            "id-with-dashes",
            "id_with_underscores",
            "id123with456numbers",
        ]
        
        for session_id in test_cases:
            try:
                status = await orchestrator.get_campaign_status(session_id)
                assert status is not None
                print(f"  ✓ Session ID '{session_id}' handled correctly")
            except Exception as e:
                pytest.fail(f"Failed to handle session ID '{session_id}': {e}")
