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
        initial_content = f"""
            Campaign Objective: {objective}

            Requirements:
            1. Identify and size the target segment
            2. Generate grounded variants
            3. Safety validation required
            4. Configure A/B/n experiment
            5. All claims require citations

            Execute with enterprise governance.
            """
        
        initial = ChatMessageContent(
            role=AuthorRole.USER,
            content=initial_content
        )

        # Save initial user message
        await self.state_manager.save_state(
            session_id,
            {
                "agent": "user",
                "role": "user",
                "content": initial_content,
            }
        )

        await self.group_chat.add_chat_message(initial)

        # ==== STREAM RESPONSE CYCLE ====
        self.logger.info(f"[Orchestrator] Starting group_chat.invoke() iteration for session {session_id}")

        try:
            async for message in self.group_chat.invoke():
                self.logger.info(f"[Orchestrator] Received message from group_chat.invoke()")

                # Extract safe values
                text = getattr(message, "content", None) or getattr(message, "value", "")
                message_role = getattr(message, "role", None) or getattr(message, "author_role", None)
                
                # Try multiple ways to extract agent name from Semantic Kernel message
                agent_name = "unknown_agent"
                
                # Method 1: Check message.name directly
                if hasattr(message, "name") and message.name:
                    agent_name = message.name
                # Method 2: Check message.metadata.agent
                elif hasattr(message, "metadata") and hasattr(message.metadata, "agent") and message.metadata.agent:
                    agent_name = message.metadata.agent
                # Method 3: Check message.author
                elif hasattr(message, "author") and message.author:
                    agent_name = message.author
                # Method 4: Check message.items for agent info (some SK versions)
                elif hasattr(message, "items"):
                    for item in message.items:
                        if hasattr(item, "name") and item.name:
                            agent_name = item.name
                            break
                        elif hasattr(item, "author") and item.author:
                            agent_name = item.author
                            break
                
                # Log for debugging - show what we extracted
                self.logger.info(
                    f"[Orchestrator] Message from agent: {agent_name}, "
                    f"role: {message_role}, content length: {len(text)} chars, "
                    f"message type: {type(message).__name__}"
                )
                
                # Log message attributes for debugging
                if self.logger.isEnabledFor(logging.DEBUG):
                    attrs = [attr for attr in dir(message) if not attr.startswith('_')]
                    self.logger.debug(f"Message attributes: {attrs}")
                    if hasattr(message, "metadata"):
                        self.logger.debug(f"Message metadata: {message.metadata}")

                # Log agent activity first (non-blocking)
                self.monitor.log_agent_activity(
                    agent_name=agent_name,
                    function_name="generate_response",
                    tokens_used=max(1, len(text.split())),
                    success=True,
                )

                self.logger.info(
                    f"[{agent_name}] ({message_role}) → {len(text)} chars"
                )

                # Yield message immediately to keep stream responsive
                yield message

                # Save state after yielding (non-blocking for stream, but still saves)
                # This ensures ALL messages from ALL agents are persisted
                # Wrapped in try/except so failures don't break the workflow
                try:
                    await self.state_manager.save_state(
                        session_id,
                        {
                            "agent": agent_name,
                            "role": str(message_role) if message_role else "assistant",
                            "content": text,
                        }
                    )
                    self.logger.debug(f"[Orchestrator] Saved message from {agent_name} to Cosmos DB")
                except Exception as e:
                    # Log error but don't break workflow
                    self.logger.warning(f"[Orchestrator] Failed to save message from {agent_name}: {e}")

                # Termination condition - only check for explicit "terminate" keyword
                # Let SequentialSelectionStrategy handle natural flow through all agents
                lower = text.lower()
                if "terminate" in lower:
                    self.monitor.log_campaign_complete(session_id)
                    self.logger.info(f"[Orchestrator] Termination keyword detected, ending workflow")
                    break
        except Exception as e:
            self.logger.error(f"[Orchestrator] Error in group_chat.invoke() iteration: {e}", exc_info=True)
            raise

    async def get_campaign_status(self, session_id: str) -> dict:
        state = await self.state_manager.load_state(session_id)
        return {
            "session_id": session_id,
            "messages": len(state.get("messages", [])),
            "agents_involved": list(set(m.get("agent") for m in state.get("messages", []))),
            "status": state.get("status", "in_progress"),
            "last_updated": state.get("last_updated"),
        }
