"""
Main orchestration engine for multi-agent coordination.
"""

from core.kernel_factory import KernelFactory
from semantic_kernel.contents import ChatMessageContent, AuthorRole
from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.agents.strategies import SequentialSelectionStrategy
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
    Orchestrates the multi-agent team using the SK Group Chat pattern.
    """

    def __init__(self, kernel_factory: KernelFactory, config: dict):
        self.kernel_factory = kernel_factory
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.monitor = MonitorService(config)
        self.state_manager = StateManager(config)

        # Shared kernel for agent memory continuity
        self.kernel = kernel_factory.create_kernel()

        # Initialize agents
        self.agents = self._initialize_agents()

        # Group chat with sequential execution
        self.group_chat = self._create_group_chat()

    def _initialize_agents(self) -> List[AgentGroupChat]:
        shared_kernel = self.kernel

        agents = [
            StrategyLeadAgent(shared_kernel, self.config).create(),
            DataSegmenterAgent(shared_kernel, self.config).create(),
            ContentCreatorAgent(shared_kernel, self.config).create(),
            ComplianceOfficerAgent(shared_kernel, self.config).create(),
            ExperimentRunnerAgent(shared_kernel, self.config).create(),
        ]

        self.logger.info(f"Initialized {len(agents)} agents.")
        return agents

    def _create_group_chat(self) -> AgentGroupChat:
        selection = SequentialSelectionStrategy()
        return AgentGroupChat(agents=self.agents, selection_strategy=selection)

    async def execute_campaign_request(
        self, 
        objective: str, 
        session_id: str
    ) -> AsyncGenerator[ChatMessageContent, None]:

        self.logger.info(f"Starting campaign execution: {objective}")
        self.monitor.log_campaign_start(session_id, objective)

        # Load session state
        state = await self.state_manager.load_state(session_id)

        # Initial user instruction
        initial = ChatMessageContent(
            role=AuthorRole.USER,
            content=f"""
            Campaign Objective: {objective}

            Requirements:
            1. Identify and size the target segment
            2. Generate grounded variants
            3. Safety validation required
            4. Configure A/B/n experiment
            5. All claims require citations

            Execute with enterprise governance.
            """
        )

        await self.group_chat.add_chat_message(initial)

        # ==== STREAM RESPONSE CYCLE ====

        async for message in self.group_chat.invoke():

            # Extract safe values
            text = getattr(message, "content", None) or getattr(message, "value", "")
            agent_name = getattr(message, "name", "unknown_agent")
            message_role = getattr(message, "role", None) or getattr(message, "author_role", None)

            # Save state
            await self.state_manager.save_state(
                session_id,
                {
                    "agent": agent_name,
                    "role": message_role,
                    "content": text,
                }
            )

            # Log
            self.monitor.log_agent_activity(
                agent_name=agent_name,
                function_name="generate_response",
                tokens_used=max(1, len(text.split())),
                success=True,
            )

            self.logger.info(
                f"[{agent_name}] ({message_role}) → {len(text)} chars"
            )

            yield message

            # Termination condition
            lower = text.lower()
            if "terminate" in lower or "<approved>" in lower:
                self.monitor.log_campaign_complete(session_id)
                break

    async def get_campaign_status(self, session_id: str) -> dict:
        state = await self.state_manager.load_state(session_id)
        return {
            "session_id": session_id,
            "messages": len(state.get("messages", [])),
            "agents_involved": list(set(m.get("agent") for m in state.get("messages", []))),
            "status": state.get("status", "in_progress"),
            "last_updated": state.get("last_updated"),
        }
