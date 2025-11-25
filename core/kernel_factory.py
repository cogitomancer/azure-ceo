"""
Semantic Kernel intialization with Azure serviceand security configurations
"""

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor


class KernelFactory:
    """Factory for creating configured Semantic Kernel instances."""

    def __init__(self, config: dict):
        self.config = config
        self.credential = DefaultAzureCredential()

        #intialise azure monitor for observalibility
        configure_azure_monitor(
            connection_string=config["azure_monitor"]["connection_string"]
        )

    
    def create_kernel(self, service_id: str = "default") -> Kernel:
        """
        Create a Semantic Kernel with Azure OpenAI connection.
        
        Args:
            service_id: Identifier for the AI service configuration
            
        Returns:
            Configured Kernel instance
        """


        # Instantiate a Semantic Kernel and add OpenAI Chat completion service
        kernel = Kernel()

        # OpenAI Chat completion service with managed identity
        azure_openai_service = AzureChatCompletion(
            service_id=service_id,
            deployment_name=self.config["azure_openai"]["deployment_name"],
            endpoint=self.config["azure_openai"]["endpoint"],
            api_version=self.config["azure_openai"]["api_version"],
            ad_token_provider=self._get_token_provider()
        )

        kernel.add_service(azure_openai_service)


        #Register filter for governance
        from filters.prompt_safety_filter import PromptSafetyFilter
        from filters.function_auth_filter import FunctionAuthorizationFilter
        from filters.pii_filter import PIIFilter


        kernel.add_filter("prompt_rendering", PromptSafetyFilter(self.config))
        kernel.add_filter("function_invocation", FunctionAuthorizationFilter(self.config))
        kernel.add_filter("prompt_rendering", PIIFilter(self.config))


        return kernel
    

    def _get_token_provider(self):
        """Get Azure AD token provider for managed identity authentication."""
        async def token_provider():
            token = self.credential.get_token("https://cognitiveservices.azure.com/.default")
            return token.token
        return token_provider