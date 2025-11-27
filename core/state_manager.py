"""
State persistence using Azure Cosmos DB for conversation history.
"""

from datetime import datetime
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential


class StateManager:
    """
    Manages agent conversation state in Azure Cosmos DB.
    """

    def __init__(self, config: dict):
        self.config = config
        self.credential = None
        self.client = None
        self.container = None
        self._initialized = False

    async def _initialize(self):
        """Initialize Cosmos DB client and container (idempotent)."""
        if self._initialized:
            return

        cosmos_cfg = self.config["cosmos_db"]
        cosmos_key = cosmos_cfg.get("key")

        # Use key if supplied, otherwise managed identity
        if cosmos_key:
            self.client = CosmosClient(
                url=cosmos_cfg["endpoint"],
                credential=cosmos_key
            )
        else:
            self.credential = DefaultAzureCredential()
            self.client = CosmosClient(
                url=cosmos_cfg["endpoint"],
                credential=self.credential
            )

        database = self.client.get_database_client(cosmos_cfg["database_name"])
        self.container = database.get_container_client(cosmos_cfg["container_name"])

        self._initialized = True

    async def load_state(self, session_id: str) -> dict:
        """Load or initialize state for a session."""
        await self._initialize()

        try:
            item = await self.container.read_item(
                item=session_id,
                partition_key=session_id
            )
            return item
        except Exception:
            # State not found → initialize new
            return {
                "id": session_id,
                "messages": [],
                "status": "new",
                "created_at": datetime.utcnow().isoformat()
            }

    async def save_state(self, session_id: str, message: object):
        """Append a message and persist."""
        await self._initialize()

        state = await self.load_state(session_id)

        # Always ensure ID is preserved
        state["id"] = session_id

        # Append structured message
        state["messages"].append({
            "agent": message.name,
            "role": str(message.role),
            "content": message.content,
            "timestamp": datetime.utcnow().isoformat()
        })

        state["last_updated"] = datetime.utcnow().isoformat()

        # Write to Cosmos
        await self.container.upsert_item(state)

    async def close(self):
        """Close resources cleanly."""
        if self.client:
            await self.client.close()
        if self.credential:
            await self.credential.close()
