"""
FastAPI application for REST API endpoints.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict
import logging
import json

from core.kernel_factory import KernelFactory
from core.orchestrator import MarketingOrchestrator
from workflows.campaign_creation import CampaignCreationWorkflow
from config.azure_config import load_config


# ======================================================================
# Initialization
# ======================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise Marketing Agent API",
    description="REST API for multi-agent marketing automation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = load_config()
kernel_factory = KernelFactory(config)


# ======================================================================
# Models
# ======================================================================

class CampaignRequest(BaseModel):
    name: str
    objective: str
    created_by: str = "api_user"


class CampaignResponse(BaseModel):
    id: str
    name: str
    objective: str
    status: str
    segment_id: Optional[str]
    segment_size: int
    experiment_id: Optional[str]
    compliance_check_passed: bool


class SegmentRequest(BaseModel):
    name: str
    description: str
    criteria: Dict


class ExperimentResultsRequest(BaseModel):
    experiment_id: str
    variant_name: str
    impressions: int
    conversions: int


class ContentValidationRequest(BaseModel):
    content: str


async def get_orchestrator():
    """DI for orchestrator."""
    return MarketingOrchestrator(kernel_factory, config)


# ======================================================================
# Routes
# ======================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "marketing-agent-api",
        "version": "1.0.0",
    }


# ----------------------------------------------------------------------
# Create Campaign (Full Workflow)
# ----------------------------------------------------------------------

@app.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(request: CampaignRequest, background_tasks: BackgroundTasks):

    try:
        workflow = CampaignCreationWorkflow(kernel_factory, config)

        campaign = await workflow.execute(
            campaign_name=request.name,
            objective=request.objective,
            created_by=request.created_by,
        )

        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            objective=campaign.objective,
            status=campaign.status.value,
            segment_id=campaign.segment_id,
            segment_size=campaign.segment_size,
            experiment_id=campaign.experiment_id,
            compliance_check_passed=campaign.compliance_check_passed,
        )

    except Exception as e:
        logger.error(f"Campaign creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------
# Streaming Campaign Execution (SSE)
# ----------------------------------------------------------------------

@app.post("/campaigns/stream")
async def create_campaign_stream(request: CampaignRequest):

    async def event_generator():

        orchestrator = await get_orchestrator()
        session_id = f"stream_{request.name.replace(' ', '_')}"

        yield f"data: {json.dumps({'event': 'started', 'campaign': request.name})}\n\n"

        try:
            message_count = 0

            async for message in orchestrator.execute_campaign_request(
                objective=request.objective,
                session_id=session_id
            ):
                message_count += 1

                agent_name = getattr(message.metadata, "agent", None) or getattr(message, "name", "Unknown")
                role = getattr(message.metadata, "role", None) or str(getattr(message, "role", "assistant"))
                text = getattr(message, "content", "")

                event_payload = {
                    "event": "agent_message",
                    "message_id": message_count,
                    "agent_name": agent_name,
                    "agent_role": str(role),
                    "content": text,
                }

                yield f"data: {json.dumps(event_payload)}\n\n"

                # termination logic
                lower = text.lower()
                if "terminate" in lower or "<approved>" in lower:
                    yield f"data: {json.dumps({'event': 'completed', 'total_messages': message_count})}\n\n"
                    break

                # safety cutoff
                if message_count > 30:
                    yield f"data: {json.dumps({'event': 'stopped', 'reason': 'message_limit'})}\n\n"
                    break

        except Exception as e:
            logger.error(f"SSE Error: {e}")
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        },
    )


# ----------------------------------------------------------------------
# Campaign Retrieval
# ----------------------------------------------------------------------

@app.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    return {
        "id": campaign_id,
        "status": "active",
        "message": "Campaign details placeholder",
    }


@app.get("/campaigns")
async def list_campaigns(status: Optional[str] = None, limit: int = 10):
    return {
        "campaigns": [],
        "total": 0,
        "limit": limit,
    }


# ----------------------------------------------------------------------
# Segment Creation
# ----------------------------------------------------------------------

@app.post("/segments")
async def create_segment(request: SegmentRequest):
    try:
        return {
            "id": f"seg_{request.name}",
            "name": request.name,
            "description": request.description,
            "criteria": request.criteria,
            "size": 0,
            "status": "created",
        }
    except Exception as e:
        logger.error(f"Segment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------
# Experiment Results
# ----------------------------------------------------------------------

@app.post("/experiments/{experiment_id}/results")
async def record_experiment_results(experiment_id: str, request: ExperimentResultsRequest):
    try:
        return {
            "experiment_id": experiment_id,
            "variant": request.variant_name,
            "recorded": True,
        }
    except Exception as e:
        logger.error(f"Experiment update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/experiments/{experiment_id}/analysis")
async def get_experiment_analysis(experiment_id: str):

    try:
        from utils.statistical_analysis import StatisticalAnalyzer

        analyzer = StatisticalAnalyzer()
        test = analyzer.calculate_two_proportion_test(
            conversions_a=100,
            visits_a=1000,
            conversions_b=120,
            visits_b=1000,
        )

        return {
            "experiment_id": experiment_id,
            "analysis": test,
            "recommendation": analyzer.generate_recommendation(test)
        }

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------
# Content Safety Validation
# ----------------------------------------------------------------------

@app.post("/content/validate")
async def validate_content(request: ContentValidationRequest):

    try:
        from services.content_safety_service import ContentSafetyService

        svc = ContentSafetyService(config)
        result = await svc.analyze_text(request.content)
        await svc.close()

        return {
            "is_safe": result.get("is_safe", True),
            "violations": result.get("violations", []),
            "categories": result.get("categories", {}),
        }

    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
