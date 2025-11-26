"""
Main Application point for Enterprise Marketing Agent
"""
import asyncio
import logging
from azure.identity import DefaultAzureCredential
from core.kernel_factory import KernelFactory
from core.orchestrator import MarketingOrchestrator
from config.azure_config import load_config

#configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """
    Main execution function of the multiagents
    """

    #Load Configuration
    config = load_config()
    logging.info("Initializing Marketing Agent System")

    #Create Kernel
    kernel_factory = KernelFactory(config)
    kernel = kernel_factory.create_kernel()


    #Create orchestrator
    orchestrator = MarketingOrchestrator(kernel_factory, config)


    #Example: CEO's high level objective
    #TODO: This should come from my react client
    campaign_objective = """
    Launch a promotional campaign for our new UltraRun Pro sneakers targeting 
    high-value running enthusiasts. The goal is to achieve a 15% increase in 
    conversion rate compared to our baseline.
    
    Requirements:
    - Target users who purchased running shoes in the last 6 months with LTV > $200
    - Highlight the new Rebound Foam technology
    - Create 3 message variants for testing
    - Ensure all claims are properly cited from product documentation
    - Set up A/B test with statistical monitoring
    """

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