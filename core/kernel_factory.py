"""
Semantic Kernel initialization with Azure services and security configurations.
"""

import logging
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.filters import FilterTypes
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor

logger = logging.getLogger(__name__)


class KernelFactory:
    """Factory for creating fully configured Semantic Kernel instances."""

    def __init__(self, config: dict):
        self.config = config
        self.credential = DefaultAzureCredential()

        # Azure Monitor initialization
        # Note: configure_azure_monitor is idempotent - safe to call multiple times
        # It's typically configured at application startup (main.py/api/main.py),
        # but we configure it here as a fallback for other usage contexts
        try:
            connection_string = config.get("azure_monitor", {}).get("connection_string")
            if connection_string:
                configure_azure_monitor(connection_string=connection_string)
                logger.debug("Azure Monitor configured in KernelFactory (may be redundant if already configured at startup)")
            else:
                logger.debug("Azure Monitor connection string not provided in config")
        except Exception as e:
            logger.warning(f"Azure Monitor initialization failed: {e}")

    def create_kernel(self, service_id: str = "default") -> Kernel:
        """
        Create a Semantic Kernel configured with:
        - Azure OpenAI (MSI)
        - Governance filters (PII, Safety, Auth, Rate Limits)
        """
        kernel = Kernel()

        # Chat completion service
        azure_openai_service = AzureChatCompletion(
            service_id=service_id,
            deployment_name=self.config["azure_openai"]["deployment_name"],
            endpoint=self.config["azure_openai"]["endpoint"],
            api_version=self.config["azure_openai"]["api_version"],
            ad_token_provider=self._get_token_provider(),
        )

        # ADD MODEL SERVICE PROPERLY
        kernel.add_service(azure_openai_service)

        # Register all governance filters
        self._register_filters(kernel)

        logger.info(f"Kernel created with service '{service_id}'")
        return kernel

    def _register_filters(self, kernel: Kernel):
        """Register SK governance filters."""
        from filters.prompt_safety_filter import PromptSafetyFilter
        from filters.function_auth_filter import FunctionAuthorizationFilter
        from filters.pii_filter import PIIFilter
        from filters.rate_limit_filter import RateLimitFilter

        prompt_filter = PromptSafetyFilter(self.config)
        auth_filter = FunctionAuthorizationFilter(self.config)
        pii_filter = PIIFilter(self.config)
        rate_limit_filter = RateLimitFilter(self.config)

        # PROMPT FILTER CHAIN
        kernel.add_filter(
            FilterTypes.PROMPT_RENDERING, prompt_filter.on_prompt_rendering
        )
        kernel.add_filter(
            FilterTypes.PROMPT_RENDERING, pii_filter.on_prompt_rendering
        )

        # FUNCTION INVOCATION FILTER CHAIN
        kernel.add_filter(
            FilterTypes.FUNCTION_INVOCATION, auth_filter.on_function_invocation
        )
        kernel.add_filter(
            FilterTypes.FUNCTION_INVOCATION, rate_limit_filter.on_function_invocation
        )

        logger.info(
            "Filters registered: PromptSafety, PII, FunctionAuth, RateLimit"
        )

    def _get_token_provider(self):
        """Azure AD Managed Identity token provider (sync)."""

        def token_provider():
            token = self.credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )
            return token.token

        return token_provider
