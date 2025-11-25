"""
Customer Data Platform plugin for audience segmentation.
"""

from semantic_kernel.functions import kernel_function
from typing import Annotated
import httpx
from azure.identity import DefaultAzureCredential


class CDPPlugin:
    """
    Plugin for interacting with Adobe Real-Time CDP API.
    Provides audience segmentation and activation capabilities.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.credential = DefaultAzureCredential()
        self.base_url = config["cdp"]["endpoint"]
        self.org_id = config["cdp"]["org_id"]
    
    @kernel_function(
        name="query_cdp",
        description="Search for audience segments in the Customer Data Platform"
    )
    async def query_cdp(
        self,
        segment_criteria: Annotated[str, "Natural language description of target audience"]
    ) -> Annotated[str, "Segment details including size and characteristics"]:
        """
        Query CDP for audience segments matching criteria.
        
        Returns anonymized segment metadata, never raw PII.
        """
        
        # Convert natural language to CDP query
        # In production, this would use CDP's GraphQL or REST API
        query = {
            "query": segment_criteria,
            "orgId": self.org_id,
            "fields": ["segmentId", "name", "size", "lastUpdated"]
        }
        
        async with httpx.AsyncClient() as client:
            # Add authentication token
            token = self.credential.get_token("https://platform.adobe.io/.default")
            
            response = await client.post(
                f"{self.base_url}/segments/search",
                json=query,
                headers={
                    "Authorization": f"Bearer {token.token}",
                    "x-gw-ims-org-id": self.org_id,
                    "x-api-key": self.config["cdp"]["api_key"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Format response without PII
                result = f"Found {len(data['segments'])} matching segments:\n"
                for seg in data["segments"]:
                    result += f"- {seg['name']}: {seg['size']:,} users (ID: {seg['segmentId']})\n"
                
                return result
            else:
                return f"Error querying CDP: {response.status_code} - {response.text}"
    
    @kernel_function(
        name="activate_segment",
        description="Activate a segment for campaign delivery"
    )
    async def activate_segment(
        self,
        segment_id: Annotated[str, "CDP segment identifier"],
        destination: Annotated[str, "Delivery platform (e.g., 'marketo', 'braze')"]
    ) -> Annotated[str, "Activation status"]:
        """Activate segment to delivery platform."""
        
        async with httpx.AsyncClient() as client:
            token = self.credential.get_token("https://platform.adobe.io/.default")
            
            response = await client.post(
                f"{self.base_url}/segments/{segment_id}/activate",
                json={"destination": destination},
                headers={
                    "Authorization": f"Bearer {token.token}",
                    "x-gw-ims-org-id": self.org_id
                }
            )
            
            if response.status_code == 200:
                return f"Segment {segment_id} activated to {destination}"
            else:
                return f"Activation failed: {response.text}"