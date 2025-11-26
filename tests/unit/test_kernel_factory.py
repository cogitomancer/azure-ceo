"""
Unit tests for `core.kernel_factory.KernelFactory`.

These tests patch Azure and SDK dependencies so the kernel creation
can be validated without network or Azure credentials.
"""

import os
import sys
import pytest
import types
from unittest.mock import Mock, patch


# Ensure repository root is on sys.path so we can import package modules reliably
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# Create lightweight fake `semantic_kernel` package tree so importing
# `core.kernel_factory` doesn't require the real dependency during tests.
sem = types.ModuleType("semantic_kernel")
sem.Kernel = Mock
connectors = types.ModuleType("semantic_kernel.connectors")
ai_mod = types.ModuleType("semantic_kernel.connectors.ai")
open_ai_mod = types.ModuleType("semantic_kernel.connectors.ai.open_ai")
open_ai_mod.AzureChatCompletion = Mock
ai_mod.open_ai = open_ai_mod
connectors.ai = ai_mod
sem.connectors = connectors

# Create fake filters submodule (required by filter imports)
filters_mod = types.ModuleType("semantic_kernel.filters")
filters_mod.FilterTypes = Mock
filters_mod.FunctionInvocationContext = Mock
sem.filters = filters_mod

# Create fake azure.ai.contentsafety module tree (required by prompt_safety_filter)
azure_mod = types.ModuleType("azure")
azure_ai = types.ModuleType("azure.ai")
azure_ai_contentsafety = types.ModuleType("azure.ai.contentsafety")
azure_ai_contentsafety.ContentSafetyClient = Mock
azure_ai_contentsafety_models = types.ModuleType("azure.ai.contentsafety.models")
azure_ai_contentsafety_models.AnalyzeTextOptions = Mock
azure_ai.contentsafety = azure_ai_contentsafety
azure_mod.ai = azure_ai

sys.modules.setdefault("semantic_kernel", sem)
sys.modules.setdefault("semantic_kernel.connectors", connectors)
sys.modules.setdefault("semantic_kernel.connectors.ai", ai_mod)
sys.modules.setdefault("semantic_kernel.connectors.ai.open_ai", open_ai_mod)
sys.modules.setdefault("semantic_kernel.filters", filters_mod)
sys.modules.setdefault("azure.ai", azure_ai)
sys.modules.setdefault("azure.ai.contentsafety", azure_ai_contentsafety)
sys.modules.setdefault("azure.ai.contentsafety.models", azure_ai_contentsafety_models)


def test_create_kernel_uses_kernel_and_registers_services_and_filters():
    # Minimal config required by KernelFactory
    config = {
        "azure_monitor": {"connection_string": "InstrumentationKey=fake"},
        "azure_openai": {
            "deployment_name": "test-deploy",
            "endpoint": "https://fake.openai.azure.com/",
            "api_version": "2024-06-01"
        }
    }

    # Patch heavy dependencies in the module under test and filters
    with patch("core.kernel_factory.Kernel") as MockKernel, \
         patch("core.kernel_factory.AzureChatCompletion") as MockAzureChat, \
         patch("core.kernel_factory.configure_azure_monitor") as mock_configure, \
         patch("core.kernel_factory.DefaultAzureCredential") as MockCredential, \
         patch("filters.prompt_safety_filter.PromptSafetyFilter", Mock), \
         patch("filters.function_auth_filter.FunctionAuthorizationFilter", Mock), \
         patch("filters.pii_filter.PIIFilter", Mock):

        # Make DefaultAzureCredential return an object with get_token
        cred_instance = Mock()
        cred_instance.get_token.return_value = Mock(token="fake-token")
        MockCredential.return_value = cred_instance

        # Prepare the mocked kernel instance
        kernel_instance = MockKernel.return_value

        # Import inside the patched context to ensure patches affect runtime
        from core.kernel_factory import KernelFactory

        factory = KernelFactory(config)
        kernel = factory.create_kernel(service_id="svc1")

        # Assert a Kernel was instantiated and returned
        MockKernel.assert_called_once()
        assert kernel is kernel_instance

        # AzureChatCompletion should be constructed and passed to kernel.add_service
        MockAzureChat.assert_called_once()
        kernel_instance.add_service.assert_called()

        # Three filters are registered in create_kernel
        assert kernel_instance.add_filter.call_count >= 3
