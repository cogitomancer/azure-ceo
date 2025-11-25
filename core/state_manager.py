"""
State persistenece usingAzure Cosmos DB for conversation history and context.
"""
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from datetime import datetime

class StateManager:
    """
    Manages agent conversation state in Azure Cosmos DB.
    """

    def __init__(self, config: dict):
        self.config = config()
        self.credential = DefaultAzureCredential()
        self.client = None
        self.container = None

    async def _intialize(self):
        """Intialize Cosmos DB client and container."""
        if self.client is None:
            self.client = CosmosClient(
                url=self.config["cosmos_db"]["endpoint"],
                credential=self.credential
            )
            database = self.client.get_database_client(self.config["cosmos_db"]["database_name"])
            self.container = database.get_container_client(self.config["cosmos_db"]["container_name"])
    
    async def load_state(self, session_id: str) -> dict:
        """Load conversation state for a session"""
        await self._intialize()
    
        try:
            item = await self.container.read_item(item=session_id, partition_key=session_id)
            return item
        except Exception:
            #return empty state empty not found
            return {
                "id": session_id,
                "message": [],
                "status": "new",
                "created_at": datetime.utcnow().isoformat()
           }
    async def save_state(self, session_id: str, message: object):
        """Save conversation state with new message"""
        await self._intialize()

        state = await self.load_state(session_id)

         # Append new message
        state["messages"].append({
            "agent": message.name,
            "role": str(message.role),
            "content": message.content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        state["last_updated"] = datetime.utcnow().isoformat()
        
        # Upsert to Cosmos DB
        await self.container.upsert_item(state)
    
    async def close(self):
        """Close Cosmos DB client."""
        if self.client:
            await self.client.close()