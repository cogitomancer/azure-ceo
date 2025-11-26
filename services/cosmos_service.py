"""
Azure Cosmos DB service for state persistence.
"""

from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
from azure.identity.aio import DefaultAzureCredential
import logging
from typing import Dict, Optional, List


class CosmosService:
    """Client for Cosmos DB operations."""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.credential = None
        
        # Use key-based auth if provided, otherwise use RBAC with DefaultAzureCredential
        cosmos_key = config["cosmos_db"].get("key")
        
        if cosmos_key:
            self.logger.info("Using Cosmos DB key-based authentication")
            self.client = CosmosClient(
                url=config["cosmos_db"]["endpoint"],
                credential=cosmos_key
            )
        else:
            self.logger.info("Using Cosmos DB RBAC authentication (DefaultAzureCredential)")
            self.credential = DefaultAzureCredential()
            self.client = CosmosClient(
                url=config["cosmos_db"]["endpoint"],
                credential=self.credential
            )
        
        self.database_name = config["cosmos_db"]["database_name"]
        self.container_name = config["cosmos_db"]["container_name"]
        
        self.database = None
        self.container = None
    
    async def initialize(self):
        """Initialize database and container."""
        
        # Create database if not exists
        self.database = await self.client.create_database_if_not_exists(
            id=self.database_name
        )
        
        # Create container if not exists
        self.container = await self.database.create_container_if_not_exists(
            id=self.container_name,
            partition_key=PartitionKey(path="/sessionId")
        )
        
        self.logger.info(f"Cosmos DB initialized: {self.database_name}/{self.container_name}")
    
    async def upsert_item(self, item: Dict) -> Dict:
        """Upsert an item in the container."""
        
        if not self.container:
            await self.initialize()
        
        try:
            result = await self.container.upsert_item(body=item)
            return result
        except Exception as e:
            self.logger.error(f"Upsert item error: {e}")
            raise
    
    async def read_item(self, item_id: str, partition_key: str) -> Optional[Dict]:
        """Read an item from the container."""
        
        if not self.container:
            await self.initialize()
        
        try:
            result = await self.container.read_item(
                item=item_id,
                partition_key=partition_key
            )
            return result
        except Exception as e:
            self.logger.warning(f"Read item not found: {e}")
            return None
    
    async def query_items(self, query: str, parameters: List = None) -> List[Dict]:
        """Query items from the container."""
        
        if not self.container:
            await self.initialize()
        
        try:
            items = self.container.query_items(
                query=query,
                parameters=parameters or [],
                enable_cross_partition_query=True
            )
            
            results = []
            async for item in items:
                results.append(item)
            
            return results
        except Exception as e:
            self.logger.error(f"Query error: {e}")
            return []
    
    async def delete_item(self, item_id: str, partition_key: str):
        """Delete an item from the container."""
        
        if not self.container:
            await self.initialize()
        
        try:
            await self.container.delete_item(
                item=item_id,
                partition_key=partition_key
            )
            self.logger.info(f"Deleted item: {item_id}")
        except Exception as e:
            self.logger.error(f"Delete error: {e}")
            raise
    
    async def close(self):
        """Close the client connection."""
        await self.client.close()
        if self.credential:
            await self.credential.close()