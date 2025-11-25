"""
    Main orchestration engine for multi agent coordination.
"""

from core.kernel_factory import KernelFactory
from semantic_kernel.contents import ChatHistory, ChatMessageContent, AuthorRole
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import SequentialSelectionStrategy
from typing import AsyncGenerator, List
import logging

from agents.strategy_lead import StrategyLeadAgent
from agents.data_segmenter import DataSegmenterAgent
from agents.content_creator import ContentCreatorAgent
from agents.compliance_officer import ComplianceOfficerAgent
from agents.experiment_runner import ExperimentRunnerAgent
from core.state_manager import StateManager


class MarketingOrchestrator:
    """

     Orchestrates the multi-agent marketing team to execute campaigns.
     Implements the Group Chat pattern from Semantic Kernel with hierarchial coordination.
    """

    def __init__(self, kernel_factory: KernelFactory, config: dict):
        self.kernel = kernel_factory.create_kernel()
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.state_manager = StateManager(config)

        #Intialize specialized agents
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
        
        # Use KernelFunctionSelectionStrategy for intelligent agent selection
        selection_function = self.kernel_factory.create_kernel().create_function(
            plugin_name="selection",
            function_name="determine_next_speaker",
            prompt="""
            Analyze the conversation and determine which agent should speak next.
            
            Available agents:
            - StrategyLead: Manages overall workflow, makes decisions, assigns tasks
            - DataSegmenter: Queries customer data, performs segmentation analysis
            - ContentCreator: Generates marketing copy with citations
            - ComplianceOfficer: Reviews content for safety and brand compliance
            - ExperimentRunner: Configures and manages A/B tests
            
            Conversation history:
            {{$history}}
            
            Return ONLY the agent name that should speak next.
            If the goal is complete, return "TERMINATE".
            """
        )
        
        selection_strategy = KernelFunctionSelectionStrategy(
            function=selection_function,
            kernel=self.kernel_factory.create_kernel(),
            result_parser=lambda result: result.value
        )
        
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
        async for message in self.group_chat.invoke():
            # Save state after each interaction
            await self.state_manager.save_state(session_id, message)
            
            # Log agent activity
            self.logger.info(
                f"Agent: {message.name}, Role: {message.role}, "
                f"Content length: {len(message.content)}"
            )
            
            yield message
            
            # Check for termination
            if "TERMINATE" in message.content or "<APPROVED>" in message.content:
                self.logger.info("Campaign execution completed successfully")
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