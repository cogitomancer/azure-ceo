"""
    Main orchestration engine for multi agent coordination.
"""

from core.kernel_factory import KernelFactory
from semantic_kernel.contents import ChatHistory, ChatMessageContent, AuthorRole
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import SequentialSelectionStrategy, KernelFunctionSelectionStrategy
from typing import AsyncGenerator, List
import logging

from agents.strategy_lead import StrategyLeadAgent
from agents.data_segmenter import DataSegmenterAgent
from agents.content_creator import ContentCreatorAgent
from agents.compliance_officer import ComplianceOfficerAgent
from agents.experiment_runner import ExperimentRunnerAgent
from core.state_manager import StateManager
from services.monitor_service import MonitorService


class MarketingOrchestrator:
    """

     Orchestrates the multi-agent marketing team to execute campaigns.
     Implements the Group Chat pattern from Semantic Kernel with hierarchial coordination.
    """

    def __init__(self, kernel_factory: KernelFactory, config: dict):
        self.kernel_factory = kernel_factory
        self.kernel = kernel_factory.create_kernel()
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.state_manager = StateManager(config)
        self.monitor = MonitorService(config)  # Application Insights monitoring

        #Initialize specialized agents
        self.agents = self._initialize_agents()

      #Create agent group chat with custom selection strategy
        self.group_chat = self._create_group_chat()

    
    def _initialize_agents(self) -> List[ChatCompletionAgent]:
        """Initialize specialized agents with their configurations."""
        agents = [
            StrategyLeadAgent(self.kernel_factory.create_kernel(), self.config).create(),
            DataSegmenterAgent(self.kernel_factory.create_kernel(), self.config).create(),
            ContentCreatorAgent(self.kernel_factory.create_kernel(), self.config).create(),
            ComplianceOfficerAgent(self.kernel_factory.create_kernel(), self.config).create(),
            ExperimentRunnerAgent(self.kernel_factory.create_kernel(), self.config).create()
        ]
        self.logger.info(f"Initialized {len(agents)} agents.")
        return agents
    
    def _create_group_chat(self) -> AgentGroupChat:
        """Create the agent group chat with orchestration strategy."""
        
        # Use SequentialSelectionStrategy which calls agents in order:
        # 1. StrategyLead -> Plans campaign strategy
        # 2. DataSegmenter -> Identifies target audience
        # 3. ContentCreator -> Creates message variants
        # 4. ComplianceOfficer -> Validates content
        # 5. ExperimentRunner -> Configures A/B test
        # This ensures a proper workflow where each agent's output informs the next
        selection_strategy = SequentialSelectionStrategy()
        
        return AgentGroupChat(
            agents=self.agents,
            selection_strategy=selection_strategy
        )
    
    async def execute_campaign_request(
        self, 
        objective: str, 
        session_id: str
    ) -> AsyncGenerator[ChatMessageContent, None]:
        """
        Execute a high-level campaign objective through agent collaboration.
        
        Args:
            objective: CEO's goal (e.g., "Increase runner segment conversion by 15%")
            session_id: Unique session identifier for state management
            
        Yields:
            Agent responses as they are generated
        """
        
        self.logger.info(f"Starting campaign execution: {objective}")
        
        # Log campaign start to Application Insights
        self.monitor.log_campaign_start(session_id, objective)
        
        # Load or create conversation state
        state = await self.state_manager.load_state(session_id)
        
        # Add initial user message
        initial_message = ChatMessageContent(
            role=AuthorRole.USER,
            content=f"""
            Campaign Objective: {objective}
            
            Requirements:
            1. Identify and size the target segment
            2. Generate 3 message variants with grounded product claims
            3. Ensure all content passes safety validation
            4. Configure A/B/n experiment with statistical monitoring
            5. Provide citation for all product claims
            
            Execute this campaign following enterprise governance policies.
            """
        )
        
        await self.group_chat.add_chat_message(initial_message)
        
        # Stream agent responses
        message_count = 0
        async for message in self.group_chat.invoke():
            message_count += 1
            
            # Save state after each interaction
            await self.state_manager.save_state(session_id, message)
            
            # Log agent activity to Application Insights
            self.monitor.log_agent_activity(
                agent_name=message.name,
                function_name="generate_response",
                tokens_used=len(message.content) // 4,  # Rough token estimate
                success=True
            )
            
            # Log to standard logger
            self.logger.info(
                f"Agent: {message.name}, Role: {message.role}, "
                f"Content length: {len(message.content)}"
            )
            
            yield message
            
            # Check for termination
            if "TERMINATE" in message.content or "<APPROVED>" in message.content:
                self.logger.info("Campaign execution completed successfully")
                self.monitor.log_campaign_complete(session_id, message_count)
                break
    
    async def get_campaign_status(self, session_id: str) -> dict:
        """Retrieve current campaign execution status."""
        state = await self.state_manager.load_state(session_id)
        
        return {
            "session_id": session_id,
            "messages": len(state.get("messages", [])),
            "agents_involved": list(set(msg.get("agent") for msg in state.get("messages", []))),
            "status": state.get("status", "in_progress"),
            "last_updated": state.get("last_updated")
        }