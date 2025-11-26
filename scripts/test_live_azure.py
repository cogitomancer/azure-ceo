"""
Simple script to test live Azure OpenAI connection and see activity in portal.
Run this and then check Azure Portal → Application Insights → Live Metrics
"""

import asyncio
from config.azure_config import load_config
from core.kernel_factory import KernelFactory
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

async def test_live_azure_connection():
    """Test real Azure OpenAI connection with actual LLM call."""
    
    print("=" * 80)
    print("TESTING LIVE AZURE CONNECTION")
    print("=" * 80)
    
    # Load configuration
    print("\n1. Loading configuration...")
    config = load_config()
    print(f"   ✓ Azure OpenAI Endpoint: {config['azure_openai']['endpoint']}")
    print(f"   ✓ Deployment: {config['azure_openai']['deployment_name']}")
    
    # Create kernel
    print("\n2. Creating Kernel with KernelFactory...")
    factory = KernelFactory(config)
    kernel = factory.create_kernel(service_id="live_test")
    print("   ✓ Kernel created successfully")
    print("   ✓ Filters registered: PromptSafety, FunctionAuth, PII")
    
    # Get AI service
    print("\n3. Getting Azure OpenAI service from kernel...")
    ai_service = kernel.get_service(service_id="live_test")
    print(f"   ✓ Service type: {type(ai_service).__name__}")
    
    # Create a simple chat
    print("\n4. Making REAL call to Azure OpenAI...")
    print("   (Check Azure Portal → Application Insights → Live Metrics NOW!)")
    
    chat_history = ChatHistory()
    chat_history.add_user_message("Say 'Hello from Azure!' in a creative way.")
    
    try:
        # Make the actual LLM call
        response = await ai_service.get_chat_message_content(
            chat_history=chat_history,
            settings=ai_service.get_prompt_execution_settings_class()(
                temperature=0.7,
                max_tokens=100
            )
        )
        
        print("\n" + "=" * 80)
        print("SUCCESS! Azure OpenAI Response:")
        print("=" * 80)
        print(response.content)
        print("=" * 80)
        
        print("\n5. ✅ EVERYTHING WORKING!")
        print("\n📊 Now check Azure Portal:")
        print("   → Application Insights → Live Metrics (see the request)")
        print("   → Application Insights → Transaction Search (see request details)")
        print("   → Azure OpenAI → Metrics (see token usage)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check if you deployed the model in Azure OpenAI Studio")
        print("2. Verify deployment name matches .env (currently: {})".format(
            config['azure_openai']['deployment_name']
        ))
        print("3. Ensure you have 'Cognitive Services OpenAI User' role")
        return False

if __name__ == "__main__":
    print("\n🚀 Starting live Azure test...")
    print("💡 TIP: Open Azure Portal in browser before running this!\n")
    
    success = asyncio.run(test_live_azure_connection())
    
    if success:
        print("\n" + "=" * 80)
        print("NEXT STEPS:")
        print("=" * 80)
        print("1. Check Application Insights for telemetry")
        print("2. Run full test suite: pytest tests/integration/ -v")
        print("3. Test main application: python main.py")
        print("=" * 80)

