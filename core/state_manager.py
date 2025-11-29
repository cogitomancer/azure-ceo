"""
State persistence using Azure Cosmos DB for conversation history.
Uses company-specific containers (e.g., hudson_street_campaigns).
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import re

from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
from azure.identity.aio import DefaultAzureCredential

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages agent conversation state in Azure Cosmos DB.
    Uses company-specific containers from CompanyDataService.
    """

    def __init__(self, config: dict):
        self.config = config
        self.credential = None
        self.client = None
        self.database = None
        self.container = None
        self._initialized = False

    def _get_company_container_name(self) -> str:
        """Get company-specific container name."""
        try:
            from services.company_data_service import CompanyDataService
            service = CompanyDataService()
            cosmos_config = service.get_cosmos_config()
            return cosmos_config.get("container", self.config["cosmos_db"]["container_name"])
        except Exception as e:
            logger.warning(f"Could not get company container, using default: {e}")
            return self.config["cosmos_db"]["container_name"]

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

        # Get company-specific container name
        container_name = self._get_company_container_name()
        
        # Get or create database and container
        self.database = self.client.get_database_client(cosmos_cfg["database_name"])
        
        # Try to create container if it doesn't exist
        try:
            self.container = await self.database.create_container_if_not_exists(
                id=container_name,
                partition_key=PartitionKey(path="/sessionId")
            )
            logger.info(f"Cosmos DB container ready: {container_name}")
        except Exception as e:
            # Fall back to just getting the container client
            logger.warning(f"Could not create container, trying to get existing: {e}")
            self.container = self.database.get_container_client(container_name)

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
                "sessionId": session_id,  # Ensure partition key is set
                "messages": [],
                "status": "new",
                "created_at": datetime.utcnow().isoformat()
            }

    async def save_state(self, session_id: str, message: dict):
        """Append a message and persist."""
        await self._initialize()

        state = await self.load_state(session_id)

        # Always ensure ID is preserved
        state["id"] = session_id
        state["sessionId"] = session_id  # Ensure partition key is set

        # Handle both dict and object inputs
        if isinstance(message, dict):
            agent = message.get("agent", "unknown")
            role = str(message.get("role", "assistant"))
            content = message.get("content", "")
        else:
            agent = getattr(message, "name", "unknown")
            role = str(getattr(message, "role", "assistant"))
            content = getattr(message, "content", "")

        # Append structured message
        message_entry = {
            "agent": agent,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        state["messages"].append(message_entry)

        state["last_updated"] = datetime.utcnow().isoformat()
        
        # Log what we're saving
        logger.info(
            f"[StateManager] Saving message to Cosmos DB - "
            f"Session: {session_id}, Agent: {agent}, Role: {role}, "
            f"Content length: {len(content)} chars, Total messages: {len(state['messages'])}"
        )

        # Write to Cosmos
        try:
            await self.container.upsert_item(state)
            logger.info(f"[StateManager] Successfully saved message from {agent} to Cosmos DB")
        except Exception as e:
            logger.error(f"[StateManager] Failed to save message to Cosmos DB: {e}", exc_info=True)
            raise

    async def save_campaign_metadata(
        self, 
        session_id: str, 
        campaign_name: str, 
        objective: str, 
        created_by: str = "system",
        status: str = "in_progress"
    ):
        """Save campaign metadata to the session state."""
        await self._initialize()

        state = await self.load_state(session_id)
        state["id"] = session_id
        state["sessionId"] = session_id
        state["campaign_name"] = campaign_name
        state["objective"] = objective
        state["created_by"] = created_by
        state["status"] = status
        state["type"] = "campaign"  # Mark as campaign for querying
        
        if "created_at" not in state:
            state["created_at"] = datetime.utcnow().isoformat()
        
        state["last_updated"] = datetime.utcnow().isoformat()

        await self.container.upsert_item(state)
        logger.info(
            f"Saved campaign metadata for {campaign_name} (session: {session_id}) - "
            f"type: {state.get('type')}, status: {state.get('status')}, "
            f"has_campaign_name: {'campaign_name' in state}"
        )

    async def update_campaign_status(self, session_id: str, status: str):
        """Update campaign status."""
        await self._initialize()
        
        state = await self.load_state(session_id)
        state["status"] = status
        state["last_updated"] = datetime.utcnow().isoformat()
        
        # Ensure type is preserved if it was set
        if "type" not in state and "campaign_name" in state:
            state["type"] = "campaign"
        
        await self.container.upsert_item(state)

    async def list_campaigns(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List all campaigns from Cosmos DB."""
        try:
            await self._initialize()
        except Exception as init_error:
            logger.error(f"Error during initialization: {init_error}", exc_info=True)
            raise

        try:
            logger.info(f"Querying campaigns - status: {status}, limit: {limit}")
            if status:
                query = "SELECT * FROM c WHERE IS_DEFINED(c.campaign_name) AND c.status = @status ORDER BY c._ts DESC"
                parameters = [{"name": "@status", "value": status}]
            else:
                query = "SELECT * FROM c WHERE IS_DEFINED(c.campaign_name) ORDER BY c._ts DESC"
                parameters = None
            
            print(f"[list_campaigns] Query: {query}")
            logger.info(f"[list_campaigns] Query: {query}")
            if parameters:
                print(f"[list_campaigns] Parameters: {parameters}")
                logger.info(f"[list_campaigns] Parameters: {parameters}")
            
            items = []
            query_count = 0
            
            # Build query_items call with proper parameters
            # In SDK v4.x, cross-partition queries are enabled by default when partition key is not specified
            query_params = parameters if parameters else []
            
            # Build kwargs for query_items
            query_kwargs = {"query": query}
            if query_params:
                query_kwargs["parameters"] = query_params
            
            async for item in self.container.query_items(**query_kwargs):
                query_count += 1
                
                # Skip items without campaign_name or with empty campaign_name
                campaign_name = item.get("campaign_name")
                if not campaign_name or campaign_name.strip() == "":
                    continue
                # Extract segment and experiment info from messages if available
                segment_id = None
                segment_size = 0
                experiment_id = None
                compliance_check_passed = False
                
                # Try to extract structured data from messages
                messages = item.get("messages", [])
                for msg in messages:
                    content = msg.get("content", "").lower()
                    agent = msg.get("agent", "").lower()
                    
                    # Look for segment information
                    if "segment" in content and "id" in content:
                        # Try to extract segment ID from content
                        import re
                        seg_match = re.search(r'segment[_\s]?id[:\s]+([a-z0-9_-]+)', content, re.IGNORECASE)
                        if seg_match:
                            segment_id = seg_match.group(1)
                    
                    # Look for experiment information
                    if "experiment" in content and "id" in content:
                        exp_match = re.search(r'experiment[_\s]?id[:\s]+([a-z0-9_-]+)', content, re.IGNORECASE)
                        if exp_match:
                            experiment_id = exp_match.group(1)
                    
                    # Check for compliance approval
                    if "compliance" in agent or "compliance" in content:
                        if "passed" in content or "approved" in content or "compliant" in content:
                            compliance_check_passed = True
                
                # Convert to campaign format
                campaign = {
                    "id": item.get("id", item.get("sessionId", "unknown")),
                    "name": item.get("campaign_name", "Unnamed Campaign"),
                    "objective": item.get("objective", ""),
                    "status": item.get("status", "unknown"),
                    "created_by": item.get("created_by", "system"),
                    "created_at": item.get("created_at"),
                    "last_updated": item.get("last_updated"),
                    "message_count": len(messages),
                    "agents_involved": list(set(m.get("agent") for m in messages if m.get("agent") and m.get("agent") != "user")),
                    "segment_id": segment_id or item.get("segment_id"),
                    "segment_size": item.get("segment_size", segment_size),
                    "experiment_id": experiment_id or item.get("experiment_id"),
                    "compliance_check_passed": item.get("compliance_check_passed", compliance_check_passed),
                }
                items.append(campaign)
                
                if len(items) >= limit:
                    break
            
            logger.info(f"Query processed {query_count} items, found {len(items)} valid campaigns")
            return items
            
        except Exception as e:
            logger.error(f"Error listing campaigns: {e}", exc_info=True)
            return []

    async def close(self):
        """Close resources cleanly."""
        if self.client:
            await self.client.close()
        if self.credential:
            await self.credential.close()
