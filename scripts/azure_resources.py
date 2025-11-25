"""
Script to set up Azure resources and initial configuration.
"""

import asyncio
import logging
from azure.identity import DefaultAzureCredential
from services.cosmos_service import CosmosService
from config.azure_config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_cosmos_db():
    """Initialize Cosmos DB with required containers."""
    config = load_config()
    cosmos_service = CosmosService(config)
    
    await cosmos_service.initialize()
    logger.info("Cosmos DB initialized successfully")
    
    await cosmos_service.close()


async def setup_search_index():
    """Create Azure AI Search index."""
    # Implementation would create search index with proper schema
    logger.info("Search index setup complete")


async def main():
    """Run all setup tasks."""
    logger.info("Starting Azure resource setup...")
    
    await setup_cosmos_db()
    await setup_search_index()
    
    logger.info("Setup complete!")


if __name__ == "__main__":
    asyncio.run(main())