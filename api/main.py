"""
FastAPI application for REST API endpoints.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import logging
import json
import traceback

from core.kernel_factory import KernelFactory
from core.orchestrator import MarketingOrchestrator
from workflows.campaign_creation import CampaignCreationWorkflow
from config.azure_config import load_config
from services.company_data_service import CompanyDataService, get_company_service


# ======================================================================
# Initialization
# ======================================================================

# IMPORTANT: Load config and configure Azure Monitor BEFORE setting up logging
# This ensures Application Insights logging exporter is properly initialized
try:
    config = load_config()
    
    # Configure Azure Monitor first (this sets up OpenTelemetry logging)
    from azure.monitor.opentelemetry import configure_azure_monitor
    connection_string = config.get("azure_monitor", {}).get("connection_string")
    if connection_string:
        # Configure Azure Monitor - this automatically sets up logging, metrics, and tracing
        configure_azure_monitor(
            connection_string=connection_string
        )
        print("✓ Azure Monitor (Application Insights) configured")
        # Show first 50 chars of connection string for verification
        if len(connection_string) > 50:
            print(f"  Connection string: {connection_string[:50]}...")
        else:
            print(f"  Connection string: {connection_string}")
    else:
        print("⚠ Azure Monitor connection string not found - logs will only appear locally")
        print("  Set APPLICATIONINSIGHTS_CONNECTION_STRING environment variable")
        print("  Expected format: InstrumentationKey=xxx;IngestionEndpoint=https://...")
except Exception as e:
    print(f"⚠ Failed to load config or configure Azure Monitor: {e}")
    import traceback
    traceback.print_exc()
    config = None

# Now configure logging (Azure Monitor logging exporter is already set up)
# IMPORTANT: Don't use force=True as it removes OpenTelemetry handlers
root_logger = logging.getLogger()
if not root_logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=False  # Preserve OpenTelemetry handlers
    )
else:
    # Just set the level if handlers already exist
    root_logger.setLevel(logging.INFO)

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
    expose_headers=["*"],
)

# Global exception handler to ensure CORS headers are always present
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions and ensure CORS headers are present."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__,
            "path": str(request.url),
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with CORS headers."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers."""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Initialize kernel factory with error handling
try:
    if config:
        # Don't configure Azure Monitor again - it's already configured above
        # Just create the kernel factory (it will skip Azure Monitor setup if already configured)
        kernel_factory = KernelFactory(config)
        logger.info("API initialized successfully")
    else:
        kernel_factory = None
        logger.warning("API initialized without configuration")
except Exception as e:
    logger.error(f"Failed to initialize API: {e}", exc_info=True)
    # Set to None so we can handle gracefully in endpoints
    config = None
    kernel_factory = None


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
    if kernel_factory is None or config is None:
        raise HTTPException(
            status_code=503,
            detail="Service not initialized. Check backend logs for configuration errors."
        )
    return MarketingOrchestrator(kernel_factory, config)


# ======================================================================
# Routes
# ======================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint - should always succeed even if company service fails."""
    try:
        company = get_company_service()
        company_info = company.get_company_info()
        return {
            "status": "healthy",
            "service": "marketing-agent-api",
            "version": "1.0.0",
            "company": company_info.get("name", "Unknown"),
            "company_id": company_info.get("id", "unknown"),
        }
    except Exception as e:
        logger.error(f"Health check error (non-fatal): {e}")
        # Return healthy status even if company service fails
        return {
            "status": "healthy",
            "service": "marketing-agent-api",
            "version": "1.0.0",
            "company": "Unknown",
            "company_id": "unknown",
            "warning": "Company service unavailable",
        }


# ----------------------------------------------------------------------
# Company Data Endpoints
# ----------------------------------------------------------------------

@app.get("/company")
async def get_current_company():
    """Get current company info, Azure resources, and data summary."""
    try:
        company = get_company_service()
        info = company.get_company_info()
        products = company.get_product_list()
        segments = company.get_customer_segments()
        
        # Get Azure resource configuration
        azure_search_config = company.get_azure_search_config()
        synapse_config = company.get_synapse_config()
        cosmos_config = company.get_cosmos_config()
        
        return {
            "company": info,
            "products_count": len(products),
            "customer_segments": segments,
            "available_companies": CompanyDataService.list_companies(),
            "azure_resources": {
                "search": azure_search_config,
                "synapse": synapse_config,
                "cosmos": cosmos_config,
            },
        }
    except Exception as e:
        logger.error(f"Error getting company data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load company data: {str(e)}"
        )


@app.get("/company/products")
async def get_company_products(limit: int = 20):
    """Get company product catalog."""
    try:
        company = get_company_service()
        products = company.get_product_list()[:limit]
        return {
            "company": company.get_company_info()["name"],
            "products": products,
            "total": len(company.get_product_list()),
        }
    except Exception as e:
        logger.error(f"Error getting products: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/company/products/search")
async def search_products(q: str):
    """Search company products."""
    try:
        company = get_company_service()
        results = company.search_products(q)
        return {
            "query": q,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Error searching products: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/company/brand-rules")
async def get_brand_rules():
    """Get company brand rules and guidelines."""
    try:
        company = get_company_service()
        return {
            "company": company.get_company_info()["name"],
            "brand_rules": company.get_brand_rules(),
            "banned_phrases": company.get_banned_phrases(),
            "tone_guidelines": company.get_tone_guidelines(),
        }
    except Exception as e:
        logger.error(f"Error getting brand rules: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/company/customers")
async def get_customer_data():
    """Get customer segment summary."""
    try:
        company = get_company_service()
        return {
            "company": company.get_company_info()["name"],
            "segments": company.get_customer_segments(),
            "total_customers": len(company.get_customers()),
        }
    except Exception as e:
        logger.error(f"Error getting customer data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
        session_id = f"stream_{request.name.replace(' ', '_').replace('/', '_')}"
        
        # Get company info for the stream
        company = get_company_service()
        company_info = company.get_company_info()

        # Save campaign metadata when stream starts
        try:
            await orchestrator.state_manager.save_campaign_metadata(
                session_id=session_id,
                campaign_name=request.name,
                objective=request.objective,
                created_by=request.created_by,
                status="in_progress"
            )
        except Exception as e:
            logger.warning(f"Failed to save campaign metadata: {e}")

        yield f"data: {json.dumps({'event': 'started', 'campaign': request.name, 'company': company_info['name'], 'company_id': company_info['id']})}\n\n"

        try:
            message_count = 0
            logger.info(f"[Stream] Starting workflow execution for session {session_id}, objective: {request.objective}")

            async for message in orchestrator.execute_campaign_request(
                objective=request.objective,
                session_id=session_id
            ):
                logger.info(f"[Stream] Received message #{message_count + 1} from workflow")
                message_count += 1

                # Try multiple ways to extract agent name (matching orchestrator logic)
                agent_name = "Unknown"
                if hasattr(message, "name") and message.name:
                    agent_name = message.name
                elif hasattr(message, "metadata") and hasattr(message.metadata, "agent") and message.metadata.agent:
                    agent_name = message.metadata.agent
                elif hasattr(message, "author") and message.author:
                    agent_name = message.author
                elif hasattr(message, "items"):
                    for item in message.items:
                        if hasattr(item, "name") and item.name:
                            agent_name = item.name
                            break
                        elif hasattr(item, "author") and item.author:
                            agent_name = item.author
                            break
                
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

                # Safety cutoff
                if message_count > 30:
                    try:
                        await orchestrator.state_manager.update_campaign_status(session_id, "stopped")
                    except Exception as e:
                        logger.warning(f"Failed to update campaign status: {e}")
                    yield f"data: {json.dumps({'event': 'stopped', 'reason': 'message_limit'})}\n\n"
                    break

            # Stream ended - mark as completed and send completion event with campaign data
            # Always send completion event, even if no messages were received
            if message_count == 0:
                # No messages received - this indicates the workflow didn't execute
                logger.warning(f"No messages received from workflow for session {session_id}. Workflow may have failed silently.")
                yield f"data: {json.dumps({'event': 'error', 'message': 'Workflow execution failed - no messages received from agents. Check backend logs for details.'})}\n\n"
            else:
                try:
                    await orchestrator.state_manager.update_campaign_status(session_id, "completed")
                    
                    # Get final campaign state from Cosmos DB
                    final_state = await orchestrator.state_manager.load_state(session_id)
                    
                    # Collect all agent messages for LLM summarization
                    agent_messages = []
                    for msg in final_state.get("messages", []):
                        agent = msg.get("agent", "")
                        content = msg.get("content", "")
                        if agent and agent != "user" and content:
                            agent_messages.append(f"[{agent}]: {content}")
                    
                    # Generate natural language summary using LLM
                    natural_summary = ""
                    try:
                        from semantic_kernel.contents import ChatHistory
                        from semantic_kernel.contents import ChatMessageContent, AuthorRole
                        
                        kernel = orchestrator.kernel
                        
                        # Create a prompt for summarization
                        # Limit agent messages to avoid token limits (take last 15 messages)
                        recent_messages = agent_messages[-15:] if len(agent_messages) > 15 else agent_messages
                        
                        summary_prompt = f"""You are a marketing campaign analyst. Based on the original campaign objective and the work completed by multiple AI agents, provide a clear, natural language summary of what was accomplished.

Original Campaign Objective:
{request.objective}

Campaign Name: {request.name}

Agent Work Completed:
{chr(10).join(recent_messages)}

Please provide a comprehensive, natural language summary that:
1. Directly addresses the original campaign objective and answers the user's question
2. Summarizes what each agent accomplished (Strategy Lead, Data Segmenter, Content Creator, Compliance Officer, Experiment Runner)
3. Highlights key findings: segments identified, content variants created, compliance status, and experiment configuration
4. Presents the information in a clear, executive-friendly format
5. Answers the user's question directly and completely

Write in natural, conversational language - NOT JSON or technical format. Be specific about what was delivered. Format as a clear, readable response that the user can understand immediately."""

                        # Use kernel chat completion service to generate summary
                        chat_service = kernel.get_service(service_id="default")
                        
                        chat_history = ChatHistory()
                        chat_history.add_user_message(summary_prompt)
                        
                        # Get execution settings
                        settings_class = chat_service.get_prompt_execution_settings_class()
                        settings = settings_class(temperature=0.7, max_tokens=2000)
                        
                        # Invoke the chat service
                        response = await chat_service.get_chat_message_content(
                            chat_history=chat_history,
                            settings=settings
                        )
                        
                        if response:
                            if hasattr(response, "content") and response.content:
                                natural_summary = str(response.content)
                            elif hasattr(response, "text") and response.text:
                                natural_summary = str(response.text)
                            elif hasattr(response, "value") and response.value:
                                natural_summary = str(response.value)
                            else:
                                natural_summary = str(response)
                        else:
                            natural_summary = "Summary generation completed."
                            
                        logger.info(f"Generated natural language summary ({len(natural_summary)} chars)")
                        
                    except Exception as e:
                        logger.error(f"Failed to generate LLM summary: {e}", exc_info=True)
                        # Fallback to basic summary
                        agents_list = list(set(m.get('agent') for m in final_state.get('messages', []) if m.get('agent') and m.get('agent') != 'user'))
                        natural_summary = f"Campaign '{request.name}' has been completed successfully. All agents ({', '.join(agents_list)}) have finished their work. The campaign addressed your objective: {request.objective[:200]}..."
                    
                    # Build campaign summary
                    campaign_summary = {
                        "session_id": session_id,
                        "campaign_name": final_state.get("campaign_name", request.name),
                        "objective": final_state.get("objective", request.objective),
                        "status": final_state.get("status", "completed"),
                        "total_messages": message_count,
                        "agents_involved": list(set(m.get("agent") for m in final_state.get("messages", []) if m.get("agent") != "user")),
                        "summary": natural_summary,  # Natural language summary from LLM
                        "created_at": final_state.get("created_at"),
                        "last_updated": final_state.get("last_updated"),
                    }
                    
                except Exception as e:
                    logger.warning(f"Failed to get campaign summary: {e}", exc_info=True)
                    campaign_summary = {
                        "session_id": session_id,
                        "campaign_name": request.name,
                        "objective": request.objective,
                        "status": "completed",
                        "total_messages": message_count,
                        "summary": f"Campaign '{request.name}' completed successfully with {message_count} messages.",
                    }
                
                yield f"data: {json.dumps({'event': 'completed', 'campaign': campaign_summary})}\n\n"

        except Exception as e:
            logger.error(f"SSE Error: {e}", exc_info=True)
            # Update campaign status to failed
            try:
                await orchestrator.state_manager.update_campaign_status(session_id, "failed")
            except Exception as update_error:
                logger.warning(f"Failed to update campaign status: {update_error}")
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


# ----------------------------------------------------------------------
# Campaign Retrieval
# ----------------------------------------------------------------------

@app.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    """Get campaign details from Cosmos DB."""
    try:
        orchestrator = await get_orchestrator()
        state = await orchestrator.state_manager.load_state(campaign_id)
        
        return {
            "id": state.get("id", campaign_id),
            "name": state.get("campaign_name", "Unknown Campaign"),
            "objective": state.get("objective", ""),
            "status": state.get("status", "unknown"),
            "created_by": state.get("created_by", "system"),
            "created_at": state.get("created_at"),
            "last_updated": state.get("last_updated"),
            "messages": state.get("messages", []),
            "message_count": len(state.get("messages", [])),
            "agents_involved": list(set(m.get("agent") for m in state.get("messages", []) if m.get("agent") != "user")),
        }
    except Exception as e:
        logger.error(f"Error getting campaign {campaign_id}: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Campaign not found: {campaign_id}")


@app.get("/campaigns/debug/all-items")
async def debug_all_items(limit: int = 20):
    """Debug endpoint to see all items in Cosmos DB."""
    try:
        orchestrator = await get_orchestrator()
        state_manager = orchestrator.state_manager
        await state_manager._initialize()
        
        # Query all items
        # In SDK v4.x, cross-partition queries are enabled by default when partition key is not specified
        query = "SELECT * FROM c ORDER BY c._ts DESC"
        items = []
        async for item in state_manager.container.query_items(query=query):
            items.append({
                "id": item.get("id"),
                "sessionId": item.get("sessionId"),
                "type": item.get("type"),
                "campaign_name": item.get("campaign_name"),
                "status": item.get("status"),
                "has_messages": len(item.get("messages", [])) > 0,
                "message_count": len(item.get("messages", [])),
            })
            if len(items) >= limit:
                break
        
        return {
            "total_items": len(items),
            "items": items,
        }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/campaigns")
async def list_campaigns(status: Optional[str] = None, limit: int = 10):
    """List campaigns from Cosmos DB."""
    try:
        logger.info(f"Listing campaigns - status: {status}, limit: {limit}")
        orchestrator = await get_orchestrator()
        campaigns = await orchestrator.state_manager.list_campaigns(status=status, limit=limit)
        logger.info(f"Returning {len(campaigns)} campaigns to frontend")
        
        return {
            "campaigns": campaigns,
            "total": len(campaigns),
            "limit": limit,
        }
    except Exception as e:
        print(f"[API] ERROR in list_campaigns: {e}")
        import traceback
        print(f"[API] Traceback: {traceback.format_exc()}")
        logger.error(f"Error listing campaigns: {e}", exc_info=True)
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "campaigns": [],
            "total": 0,
            "limit": limit,
            "error": str(e),
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
