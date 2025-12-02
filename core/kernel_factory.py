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
        # Don't create credential until we know we need it (lazy initialization)
        self._credential = None

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
        - Azure OpenAI (API Key or Managed Identity)
        - Governance filters (PII, Safety, Auth, Rate Limits)
        """
        kernel = Kernel()

        # Get Azure OpenAI config
        openai_config = self.config["azure_openai"]
        api_key = openai_config.get("api_key")
        endpoint = openai_config.get("endpoint", "")
        
        # Clean up endpoint URL - remove any path/query parameters if present
        if endpoint:
            # Remove path and query parameters
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(endpoint)
            # Reconstruct with just scheme, netloc (no path, params, query, fragment)
            endpoint = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
            # Remove trailing slash
            endpoint = endpoint.rstrip('/')
        
        # Log what we found (without exposing the key)
        if api_key:
            logger.info(f"Azure OpenAI API key found: {'*' * min(len(api_key), 8)}... (length: {len(api_key)})")
        else:
            logger.warning("Azure OpenAI API key not found in config, will use Azure AD token provider")
        
        logger.info(f"Azure OpenAI endpoint: {endpoint}")
        logger.info(f"Azure OpenAI deployment: {openai_config.get('deployment_name')}")
        
        # Build AzureChatCompletion arguments
        service_args = {
            "service_id": service_id,
            "deployment_name": openai_config["deployment_name"],
            "endpoint": endpoint,
            "api_version": openai_config["api_version"],
        }
        
        # Use API key if available and not empty, otherwise use Azure AD token provider
        # IMPORTANT: Only pass ONE authentication method - either api_key OR ad_token_provider, not both
        if api_key and api_key.strip():
            logger.info("✓ Using API key authentication for Azure OpenAI")
            service_args["api_key"] = api_key.strip()
            # Explicitly ensure we don't pass ad_token_provider when using api_key
            if "ad_token_provider" in service_args:
                del service_args["ad_token_provider"]
        else:
            logger.warning("⚠ Using Azure AD token provider for Azure OpenAI (API key not available or empty)")
            if api_key is None:
                logger.warning("  → API key is None (not found in config)")
            elif not api_key.strip():
                logger.warning("  → API key is empty string")
            service_args["ad_token_provider"] = self._get_token_provider()
            # Explicitly ensure we don't pass api_key when using ad_token_provider
            if "api_key" in service_args:
                del service_args["api_key"]

        # Log final service args (without sensitive data)
        logger.info(f"Creating AzureChatCompletion with: service_id={service_id}, deployment={openai_config['deployment_name']}, endpoint={endpoint}, auth_method={'api_key' if 'api_key' in service_args else 'ad_token_provider'}")

        # Chat completion service
        try:
            azure_openai_service = AzureChatCompletion(**service_args)
            logger.info("✓ AzureChatCompletion service created successfully")
        except Exception as e:
            logger.error(f"✗ Failed to create AzureChatCompletion: {e}", exc_info=True)
            raise

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
        # Lazy initialization of credential
        if self._credential is None:
            logger.info("Initializing DefaultAzureCredential for Azure AD authentication")
            self._credential = DefaultAzureCredential()

        def token_provider():
            token = self._credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )
            return token.token

        return token_provider
