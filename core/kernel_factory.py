"""
Semantic Kernel initialization with Azure services and security configurations
"""

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.filters import FilterTypes
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
import logging

logger = logging.getLogger(__name__)


class KernelFactory:
    """Factory for creating configured Semantic Kernel instances."""

    def __init__(self, config: dict):
        self.config = config
        self.credential = DefaultAzureCredential()

        # Initialize Azure Monitor for observability
        configure_azure_monitor(
            connection_string=config["azure_monitor"]["connection_string"]
        )

    
    def create_kernel(self, service_id: str = "default") -> Kernel:
        """
        Create a Semantic Kernel with Azure OpenAI connection.
        
        Args:
            service_id: Identifier for the AI service configuration
            
        Returns:
            Configured Kernel instance with all filters registered
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

        # Register all filters for governance and security
        self._register_filters(kernel)

        return kernel
    
    def _register_filters(self, kernel: Kernel):
        """Register all security and governance filters."""
        from filters.prompt_safety_filter import PromptSafetyFilter
        from filters.function_auth_filter import FunctionAuthorizationFilter
        from filters.pii_filter import PIIFilter
        from filters.rate_limit_filter import RateLimitFilter
        
        # Initialize filters
        prompt_filter = PromptSafetyFilter(self.config)
        auth_filter = FunctionAuthorizationFilter(self.config)
        pii_filter = PIIFilter(self.config)
        rate_limit_filter = RateLimitFilter(self.config)
        
        # Register prompt filters (executed before prompt reaches LLM)
        kernel.add_filter(FilterTypes.PROMPT_RENDERING, prompt_filter.on_prompt_rendering)
        kernel.add_filter(FilterTypes.PROMPT_RENDERING, pii_filter.on_prompt_rendering)
        
        # Register function invocation filters (executed before function calls)
        kernel.add_filter(FilterTypes.FUNCTION_INVOCATION, auth_filter.on_function_invocation)
        kernel.add_filter(FilterTypes.FUNCTION_INVOCATION, rate_limit_filter.on_function_invocation)
        
        # Note: Rate limit completion tracking is handled within the filter itself
        # FUNCTION_INVOCATION_COMPLETE is not available in current SK version
        
        logger.info("Filters registered: PromptSafety, PII, FunctionAuth, RateLimit")

    def _get_token_provider(self):
        """Get Azure AD token provider for managed identity authentication."""
        async def token_provider():
            token = self.credential.get_token("https://cognitiveservices.azure.com/.default")
            return token.token
        return token_provider
