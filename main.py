"""
Main Application point for Enterprise Marketing Agent
"""
import asyncio
import logging
from azure.identity import DefaultAzureCredential
from core.kernel_factory import KernelFactory
from core.orchestrator import MarketingOrchestrator
from config.azure_config import load_config

config = load_config()

# Configure Azure Monitor first (this sets up OpenTelemetry logging)
from azure.monitor.opentelemetry import configure_azure_monitor
try:
    connection_string = config.get("azure_monitor", {}).get("connection_string")
    if connection_string:
        # Configure Azure Monitor - this automatically sets up logging, metrics, and tracing
        configure_azure_monitor(
            connection_string=connection_string
        )
        print("✓ Azure Monitor (Application Insights) configured")
        # Show first 50 chars of connection string for verification
        if len(connection_string) > 50:
            print(f"  Connection string: {connection_string[:50]}...")
        else:
            print(f"  Connection string: {connection_string}")
    else:
        print("⚠ Azure Monitor connection string not found - logs will only appear locally")
        print("  Set APPLICATIONINSIGHTS_CONNECTION_STRING environment variable")
        print("  Expected format: InstrumentationKey=xxx;IngestionEndpoint=https://...")
except Exception as e:
    print(f"⚠ Azure Monitor initialization failed: {e} - logs will only appear locally")
    import traceback
    traceback.print_exc()

root_logger = logging.getLogger()
if not root_logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=False  # Preserve OpenTelemetry handlers
    )
else:
    # Just set the level if handlers already exist
    root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

async def main():
    """
    Main execution function of the multiagents
    """

    logging.info("Initializing Marketing Agent System")

    #Create Kernel
    kernel_factory = KernelFactory(config)
    kernel = kernel_factory.create_kernel()


    #Create orchestrator
    orchestrator = MarketingOrchestrator(kernel_factory, config)

    session_id = "campaign_001"

    logger.info(f"Executing campaign: {campaign_objective[:100]}...")

    # Execute campaign through agent collaboration

    async for message in orchestrator.execute_campaign_request(
        objective=campaign_objective,
        session_id=session_id
    ):
        logger.info(f"\n{'='*60}")
        logger.info(f"Agent: {message.name}")
        logger.info(f"{'='*60}")
        logger.info(message.content)
        logger.info(f"{'='*60}\n")
    
    # Get final status
    status = await orchestrator.get_campaign_status(session_id)
    logger.info(f"Campaign Status: {status}")
    
    # Cleanup
    await orchestrator.state_manager.close()
    logger.info("Campaign execution completed")


if __name__ == "__main__":
    asyncio.run(main())