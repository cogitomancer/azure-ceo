"""
Azure Monitor service for logging and telemetry.
Provides custom metrics and detailed tracking for Application Insights.
"""

from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode
import logging
from typing import Dict, Any


class MonitorService:
    """
    Client for Azure Monitor / Application Insights.
    Provides custom metrics, traces, and logging with Application Insights integration.
    Note: Azure Monitor is already configured in KernelFactory via configure_azure_monitor().
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Get tracer and meter (Azure Monitor already configured by KernelFactory)
        self.tracer = trace.get_tracer("marketing_agents")
        self.meter = metrics.get_meter("marketing_agents")
        
        # Create custom metrics for Application Insights
        try:
            self.token_counter = self.meter.create_counter(
                name="marketing.agent.tokens",
                description="Total tokens used by marketing agents",
                unit="tokens"
            )
            
            self.cost_counter = self.meter.create_counter(
                name="marketing.agent.cost",
                description="Estimated cost of agent operations in USD",
                unit="usd"
            )
            
            self.agent_call_counter = self.meter.create_counter(
                name="marketing.agent.calls",
                description="Number of agent function calls",
                unit="calls"
            )
            
            self.campaign_counter = self.meter.create_counter(
                name="marketing.campaigns",
                description="Number of campaigns executed",
                unit="campaigns"
            )
            
            self.logger.info("Application Insights custom metrics initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize custom metrics: {e}")
    
    def start_span(self, name: str, attributes: Dict[str, Any] = None):
        """Start a new tracing span."""
        return self.tracer.start_as_current_span(
            name=name,
            attributes=attributes or {}
        )
    
    def log_agent_activity(
        self,
        agent_name: str,
        function_name: str,
        tokens_used: int = 0,
        success: bool = True,
        error: str = None
    ):
        """
        Log agent activity with custom dimensions to Application Insights.
        
        This creates custom metrics and traces that will appear in App Insights:
        - Metrics: marketing.agent.tokens, marketing.agent.cost, marketing.agent.calls
        - Traces: Logged as custom events with dimensions
        """
        
        attributes = {
            "agent": agent_name,
            "function": function_name,
            "success": str(success)
        }
        
        if error:
            attributes["error"] = error
        
        try:
            # Record metrics (will appear in Application Insights Metrics)
            if tokens_used > 0:
                self.token_counter.add(tokens_used, attributes)
                
                # Estimate cost (GPT-4: ~$0.03 per 1K tokens)
                cost = tokens_used * 0.00003
                self.cost_counter.add(cost, attributes)
            
            self.agent_call_counter.add(1, attributes)
        except Exception as e:
            self.logger.warning(f"Failed to record metrics: {e}")
        
        # Log event with custom dimensions (will appear in App Insights Traces)
        if success:
            self.logger.info(
                f"🤖 Agent Activity: {agent_name}.{function_name} (tokens: {tokens_used})",
                extra={
                    "custom_dimensions": attributes,
                    "tokens": tokens_used,
                    "agent": agent_name
                }
            )
        else:
            self.logger.error(
                f"❌ Agent Error: {agent_name}.{function_name} - {error}",
                extra={
                    "custom_dimensions": attributes,
                    "agent": agent_name,
                    "error": error
                }
            )
    
    def log_experiment_event(
        self,
        experiment_name: str,
        variant: str,
        event_type: str,
        user_id: str = None
    ):
        """
        Log experiment events for analysis in Application Insights.
        Events appear in App Insights > Custom Events.
        """
        
        attributes = {
            "experiment": experiment_name,
            "variant": variant,
            "event_type": event_type
        }
        
        if user_id:
            attributes["user_id"] = user_id
        
        self.logger.info(
            f"🧪 Experiment Event: {event_type} - {experiment_name} (variant: {variant})",
            extra={
                "custom_dimensions": attributes,
                "experiment": experiment_name,
                "variant": variant
            }
        )
    
    def log_campaign_start(self, campaign_id: str, objective: str):
        """Log campaign start event."""
        try:
            self.campaign_counter.add(1, {
                "campaign_id": campaign_id,
                "event": "start"
            })
        except Exception:
            pass
        
        self.logger.info(
            f"📊 Campaign Started: {campaign_id}",
            extra={
                "custom_dimensions": {
                    "campaign_id": campaign_id,
                    "objective": objective[:100],
                    "event": "campaign_start"
                }
            }
        )
    
    def log_campaign_complete(self, campaign_id: str, message_count: int):
        """Log campaign completion event."""
        try:
            self.campaign_counter.add(1, {
                "campaign_id": campaign_id,
                "event": "complete"
            })
        except Exception:
            pass
        
        self.logger.info(
            f"✅ Campaign Completed: {campaign_id} ({message_count} messages)",
            extra={
                "custom_dimensions": {
                    "campaign_id": campaign_id,
                    "message_count": message_count,
                    "event": "campaign_complete"
                }
            }
        )
    
    def log_safety_violation(
        self,
        agent_name: str,
        violation_type: str,
        severity: int,
        content_preview: str
    ):
        """Log safety policy violations."""
        
        attributes = {
            "agent": agent_name,
            "violation_type": violation_type,
            "severity": severity,
            "content_preview": content_preview[:100]
        }
        
        self.logger.warning(
            f"Safety violation: {violation_type}",
            extra={"custom_dimensions": attributes, "audit": True}
        )
