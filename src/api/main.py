# Azure CEO - Starter API (FastAPI)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from azure.storage.queue import QueueuClient
import os
import json
import base64

# Intialize FastAPI app
app = FastAPI(title="Azure CEO - Customer Personalization Orchestrator")

#Data Model for Customer Event
class CustomerEvent(BaseModel):
    event_id: str
    user_id: str
    timestamp: str
    event_type: str
    payload: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt_12345",
                "user_id": "usr_888",
                "timestamp": "2023-10-27T10:00:00Z",
                "event_type": "product_view",
                "payload": {"product_category": "summer_wear", "last_purchase_days": 30}
            }
        }


@app.get("/")
def root():
    return {"status": "Azure CEO API running"}

@app.get("/health")
async def health_check():
    return{"status": "healthy", "service": "Azure CEO Orchestrator"}

@app.post("/ingest-event")
async def ingest_event(event: CustomerEvent):
    """Ingest a customer event that triggers the 7 Agent Workflow via Queue"""
    try: 
        #1. Get Connection String
        #in local dev, this uses 'UseDevelopmentStorage=true' from local.settings.json
        conn_str = os.getenv("AzureWebJobsStorage")
        if not conn_str:
            raise HTTPException(status_code=500, detail="AzureWebJJobsStorage not configured")
        
        #2, Connect to Queue

        queue_name = 'ai-job-queue'
        queue_client = QueueClient.from_connection_string(conn_str, queue_name)

        #3. Ensure Queue Exists

        try:
            queue_client.create_queue()
        except Exception:
            pass #Queue already exists
        
        #4. Send Message (Base64 encoded for Azure Functions Queue Trigger)
        message_body = json.dumps(event.model_dump())
        message_bytes = message.body.encode('utf-8')
        base64_message = base64.b64encode(message_bytes).decode('utf-8')

        queue_client.send_message(base64_message)

        return {
            "status": "accepted",
            "message": "Event queued for orchestration",
            "event_id": event.event_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest event: {str(e)}")