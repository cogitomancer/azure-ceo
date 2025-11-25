"""
FastAPI application for REST API endpoints.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import logging

from core.kernel_factory import KernelFactory
from core.orchestrator import MarketingOrchestrator
from workflows.campaign_creation import CampaignCreationWorkflow
from config.azure_config import load_config

# Initialize
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise Marketing Agent API",
    description="REST API for multi-agent marketing automation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
config = load_config()
kernel_factory = KernelFactory(config)
kernel = kernel_factory.create_kernel()


# Request/Response Models
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
    criteria: dict


class ExperimentResultsRequest(BaseModel):
    experiment_id: str
    variant_name: str
    impressions: int
    conversions: int


# Dependency injection
async def get_orchestrator():
    """Get orchestrator instance."""
    return MarketingOrchestrator(kernel, config)


# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "marketing-agent-api",
        "version": "1.0.0"
    }


@app.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    request: CampaignRequest,
    background_tasks: BackgroundTasks
):
    """Create a new marketing campaign."""
    
    try:
        workflow = CampaignCreationWorkflow(kernel, config)
        campaign = await workflow.execute(
            campaign_name=request.name,
            objective=request.objective,
            created_by=request.created_by
        )
        
        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            objective=campaign.objective,
            status=campaign.status.value,
            segment_id=campaign.segment_id,
            segment_size=campaign.segment_size,
            experiment_id=campaign.experiment_id,
            compliance_check_passed=campaign.compliance_check_passed
        )
    
    except Exception as e:
        logger.error(f"Campaign creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    """Get campaign details."""
    
    # In production, fetch from Cosmos DB
    return {
        "id": campaign_id,
        "status": "active",
        "message": "Campaign details"
    }


@app.get("/campaigns")
async def list_campaigns(
    status: Optional[str] = None,
    limit: int = 10
):
    """List all campaigns."""
    
    # In production, query Cosmos DB
    return {
        "campaigns": [],
        "total": 0,
        "limit": limit
    }


@app.post("/segments")
async def create_segment(request: SegmentRequest):
    """Create audience segment."""
    
    try:
        # Call DataSegmenter agent
        orchestrator = await get_orchestrator()
        
        # Implementation would query CDP
        return {
            "id": f"seg_{request.name}",
            "name": request.name,
            "description": request.description,
            "size": 0,
            "status": "created"
        }
    
    except Exception as e:
        logger.error(f"Segment creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/experiments/{experiment_id}/results")
async def record_experiment_results(
    experiment_id: str,
    request: ExperimentResultsRequest
):
    """Record experiment results."""
    
    try:
        # Update experiment metrics in Cosmos DB
        return {
            "experiment_id": experiment_id,
            "variant": request.variant_name,
            "recorded": True
        }
    
    except Exception as e:
        logger.error(f"Results recording error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/experiments/{experiment_id}/analysis")
async def get_experiment_analysis(experiment_id: str):
    """Get statistical analysis of experiment."""
    
    try:
        from utils.statistical_analysis import StatisticalAnalyzer
        
        analyzer = StatisticalAnalyzer()
        
        # In production, fetch real data from Cosmos DB
        result = analyzer.calculate_two_proportion_test(
            conversions_a=100,
            visits_a=1000,
            conversions_b=120,
            visits_b=1000
        )
        
        recommendation = analyzer.generate_recommendation(result)
        
        return {
            "experiment_id": experiment_id,
            "analysis": result,
            "recommendation": recommendation
        }
    
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/content/validate")
async def validate_content(content: str):
    """Validate content for safety and compliance."""
    
    try:
        from services.content_safety_service import ContentSafetyService
        
        safety_service = ContentSafetyService(config)
        result = await safety_service.analyze_text(content)
        await safety_service.close()
        
        return {
            "is_safe": result["is_safe"],
            "violations": result["violations"],
            "categories": result["categories"]
        }
    
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
