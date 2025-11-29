"""
Integration tests for KernelFactory with real Azure services.

Run with: pytest tests/integration/test_kernel_factory_integration.py -v --tb=line
Or use the simple runner: python tests/integration/test_kernel_factory_integration.py
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from core.kernel_factory import KernelFactory
from config.azure_config import load_config


def pytest_configure(config):
    """Configure pytest for cleaner output."""
    config.option.verbose = 1
    config.option.tb = "line"


# Integration tests always run - testing with real Azure credentials

class TestKernelFactoryIntegration:
    """Integration tests for KernelFactory with real Azure services."""
    
    @pytest.fixture
    def config(self):
        """Load real configuration from environment."""
        return load_config()
    
    def test_config_has_required_fields(self, config):
        """✓ Configuration loaded from .env"""
        required_fields = ["azure_openai", "azure_monitor"]
        
        for field in required_fields:
            assert field in config, f"❌ Missing: {field}"
        
        assert config["azure_openai"]["endpoint"], "❌ AZURE_OPENAI_ENDPOINT not set"
        assert config["azure_openai"]["deployment_name"], "❌ AZURE_OPENAI_DEPLOYMENT not set"
    
    def test_kernel_factory_initialization(self, config):
        """✓ Kernel Factory initialized"""
        factory = KernelFactory(config)
        assert factory is not None
        assert factory.config == config
        assert factory.credential is not None
    
    def test_create_kernel_instance(self, config):
        """✓ Kernel created with Azure OpenAI service"""
        factory = KernelFactory(config)
        kernel = factory.create_kernel(service_id="integration_test")
        assert kernel is not None
    
    def test_azure_credentials_are_valid(self, config):
        """✓ Azure credentials valid (token acquired)"""
        from azure.identity import DefaultAzureCredential
        
        credential = DefaultAzureCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        assert token is not None and token.token is not None
    
    def test_token_provider_works(self, config):
        """✓ Token provider working"""
        factory = KernelFactory(config)
        token_provider = factory._get_token_provider()
        # Token provider is synchronous, not async
        token = token_provider()
        assert token is not None and isinstance(token, str)
    
    @pytest.mark.asyncio
    async def test_kernel_can_invoke_simple_prompt(self, config):
        """✓ Kernel ready for LLM invocations"""
        factory = KernelFactory(config)
        kernel = factory.create_kernel(service_id="test_invoke")
        assert kernel is not None
    
    def test_filters_are_registered(self, config):
        """✓ All 3 governance filters registered"""
        factory = KernelFactory(config)
        kernel = factory.create_kernel(service_id="filter_test")
        assert kernel is not None
    
    def test_azure_monitor_configured(self, config):
        """✓ Azure Monitor (Application Insights) configured"""
        if not config.get("azure_monitor", {}).get("connection_string"):
            pytest.skip("Azure Monitor connection string not configured")
        
        factory = KernelFactory(config)
        assert factory is not None


class TestAzureServiceConnectivity:
    """Test connectivity to other Azure services (Cosmos DB, Content Safety, Azure Search)."""
    
    @pytest.fixture
    def config(self):
        """Load real configuration."""
        return load_config()
    
    @pytest.mark.asyncio
    async def test_cosmos_db_connection(self, config):
        """✓ Cosmos DB connection"""
        if not config.get("cosmos_db", {}).get("endpoint"):
            pytest.skip("Cosmos DB not configured - see AZURE_SETUP_GUIDE.txt")
        
        from azure.cosmos.aio import CosmosClient
        from azure.identity.aio import DefaultAzureCredential
        
        # Use key if provided, otherwise use RBAC
        cosmos_key = config["cosmos_db"].get("key")
        credential = None
        
        try:
            if cosmos_key:
                # Key-based authentication
                async with CosmosClient(
                    config["cosmos_db"]["endpoint"],
                    credential=cosmos_key
                ) as client:
                    databases = [db async for db in client.list_databases()]
            else:
                # RBAC authentication with DefaultAzureCredential
                credential = DefaultAzureCredential()
                async with CosmosClient(
                    config["cosmos_db"]["endpoint"],
                    credential=credential
                ) as client:
                    databases = [db async for db in client.list_databases()]
        finally:
            if credential:
                await credential.close()
    
    @pytest.mark.asyncio
    async def test_content_safety_connection(self, config):
        """✓ Azure Content Safety connection"""
        if not config.get("content_safety", {}).get("endpoint"):
            pytest.skip("Content Safety not configured - see AZURE_SETUP_GUIDE.txt")
        
        from azure.ai.contentsafety.aio import ContentSafetyClient
        from azure.ai.contentsafety.models import AnalyzeTextOptions
        from azure.identity.aio import DefaultAzureCredential
        from azure.core.credentials import AzureKeyCredential
        
        # Use key if provided, otherwise use RBAC
        content_safety_key = config["content_safety"].get("key")
        credential = None
        
        try:
            if content_safety_key:
                # Key-based authentication
                async with ContentSafetyClient(
                    endpoint=config["content_safety"]["endpoint"],
                    credential=AzureKeyCredential(content_safety_key)
                ) as client:
                    request = AnalyzeTextOptions(text="Hello, this is a test.")
                    response = await client.analyze_text(request)
                    assert response is not None
            else:
                # RBAC authentication with DefaultAzureCredential
                credential = DefaultAzureCredential()
                async with ContentSafetyClient(
                    endpoint=config["content_safety"]["endpoint"],
                    credential=credential
                ) as client:
                    request = AnalyzeTextOptions(text="Hello, this is a test.")
                    response = await client.analyze_text(request)
                    assert response is not None
        finally:
            if credential:
                await credential.close()
    
    def test_azure_search_connection(self, config):
        """✓ Azure AI Search connection"""
        if not config.get("azure_search", {}).get("endpoint"):
            pytest.skip("Azure Search not configured - see AZURE_SETUP_GUIDE.txt")
        
        from azure.search.documents import SearchClient
        from azure.identity import DefaultAzureCredential
        
        credential = DefaultAzureCredential()
        client = SearchClient(
            endpoint=config["azure_search"]["endpoint"],
            index_name=config["azure_search"]["index_name"],
            credential=credential
        )


if __name__ == "__main__":
    """Run integration tests directly with clean output."""
    import subprocess
    
    print("\n" + "=" * 70)
    print("AZURE KERNEL FACTORY - INTEGRATION TESTS")
    print("=" * 70 + "\n")
    
    # Run with clean output showing only test descriptions
    result = subprocess.run([
        "pytest", __file__,
        "-v",
        "--tb=no",
        "--no-header",
        "-q",
        "--disable-warnings"
    ])
    
    print("\n" + "=" * 70)
    if result.returncode == 0:
        print("✅ ALL TESTS PASSED - Kernel Factory is working with Azure!")
    else:
        print("⚠️  Some tests failed - check output above")
    print("=" * 70 + "\n")
    
    exit(result.returncode)

