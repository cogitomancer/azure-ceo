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
        from semantic_kernel.functions import KernelArguments
        from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
        
        # Create execution settings for Azure OpenAI
        settings = AzureChatPromptExecutionSettings(
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        # Create kernel arguments with settings
        arguments = KernelArguments(settings=settings)
        
        # Collect plugins for the agent
        plugins = self.get_plugins()
        
        # Create agent first
        agent = ChatCompletionAgent(
            name=self.agent_name,
            instructions=self.instructions,
            kernel=self.kernel,
            arguments=arguments,
        )
        
        # Register plugin functions on the agent
        for plugin in plugins:
            plugin_name = getattr(plugin, "plugin_name", plugin.__class__.__name__)
            logger.info(
                "Registering plugin %s for agent %s",
                plugin_name,
                self.agent_name,
            )
            
            # Call the plugin's register method to add its functions to the agent
            if hasattr(plugin, 'register'):
                try:
                    plugin.register(agent)
                    logger.info(
                        "Successfully registered functions from plugin %s",
                        plugin_name
                    )
                except Exception as e:
                    logger.error(
                        "Failed to register plugin %s: %s",
                        plugin_name,
                        e,
                        exc_info=True
                    )
            else:
                logger.warning(
                    "Plugin %s does not have a register() method, skipping",
                    plugin_name
                )

        return agent
