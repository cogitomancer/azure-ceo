"""
Abstract base class for all specialized agents
"""

from semantic_kernel import Kernel
#TODO:Refactor to use Kernel Factory
from semantic_kernel.agents import ChatCompletionAgent
from abc import ABC, abstractmethod


class BaseMarketingAgent(ABC):
    """Base class for all marketing agents with custom functionality"""

    def __init__(self, kernel: Kernel, config: dict):
        self.kernel = kernel
        self.config = config
        self.agent_config = config["agents"][self.agent_name]

    
    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Return the agent's unique identifer"""
        pass

    @property
    @abstractmethod
    def instructions(self) -> str:
        """Return the agent's system instructions"""
        pass

    @abstractmethod
    def get_plugins(self) -> list:
        """Return list of plugins this agent uses."""
        pass

    def create(self) -> ChatCompletionAgent:
        """Create and configure the ChatCompletionAgent"""

        #add agent specific plugins to kernel first
        for plugin in self.get_plugins():
            self.kernel.add_plugin(plugin)

        agent = ChatCompletionAgent(
            kernel=self.kernel,
            name=self.agent_name,
            instructions=self.instructions  # This calls the property method
        )

        return agent