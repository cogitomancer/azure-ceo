from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel import Kernel
import logging

logger = logging.getLogger(__name__)


class BaseMarketingAgent:
    """
    Base class for all agents. Loads instructions and model settings from config.
    Supports plugin/tool registration for all agent subclasses.
    """

    def __init__(self, kernel: Kernel, config: dict, agent_key: str):
        self.kernel = kernel
        self.config = config

        agent_cfg = config["agents"][agent_key]

        self.agent_name = agent_cfg["name"]
        self.instructions = agent_cfg["instructions"]
        self.model = agent_cfg["model"]
        self.temperature = agent_cfg["temperature"]
        self.max_tokens = agent_cfg["max_tokens"]

    def get_plugins(self):
        """
        Overridden by subclasses.

        Should return a list of plugin instances. Each plugin may:
        - implement .register(agent)  → custom registration
        - or just be a plain object with @kernel_function methods
          → we will add it to the kernel via kernel.add_plugin(...)
        """
        return []

    def create(self) -> ChatCompletionAgent:
        """
        Create and return a ChatCompletionAgent with execution settings +
        registered tools/plugins.
        """
        agent = ChatCompletionAgent(
            name=self.agent_name,
            instructions=self.instructions,
            kernel=self.kernel,
            execution_settings={
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
        )

        # 🔥 Plugin registration, backward-compatible
        for plugin in self.get_plugins():
            # 1) If plugin knows how to register itself, let it
            if hasattr(plugin, "register") and callable(getattr(plugin, "register")):
                try:
                    plugin.register(agent)
                    logger.info(
                        "Registered plugin %s via .register() for agent %s",
                        plugin.__class__.__name__,
                        self.agent_name,
                    )
                except Exception as e:
                    logger.error(
                        "Error registering plugin %s via .register(): %s",
                        plugin.__class__.__name__,
                        e,
                    )
                    raise
            else:
                # 2) Fallback: add as a Semantic Kernel plugin
                try:
                    # Name plugin after its class unless overridden
                    plugin_name = getattr(plugin, "plugin_name", plugin.__class__.__name__)
                    self.kernel.add_plugin(plugin, plugin_name)
                    logger.info(
                        "Registered plugin %s on kernel as '%s' for agent %s",
                        plugin.__class__.__name__,
                        plugin_name,
                        self.agent_name,
                    )
                except Exception as e:
                    logger.error(
                        "Error registering plugin %s on kernel: %s",
                        plugin.__class__.__name__,
                        e,
                    )
                    raise

        return agent
