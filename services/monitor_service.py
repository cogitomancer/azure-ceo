"""
Azure Monitor service for logging and telemetry.
"""

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode
import logging
from typing import Dict, Any


class MonitorService:
    """Client for Azure Monitor / Application Insights."""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configure Azure Monitor
        configure_azure_monitor(
            connection_string=config["azure_monitor"]["connection_string"]
        )
        
        # Get tracer and meter
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)
        
        # Create custom metrics
        self.token_counter = self.meter.create_counter(
            name="agent_tokens_used",
            description="Total tokens used by agents",
            unit="tokens"
        )
        
        self.cost_counter = self.meter.create_counter(
            name="agent_cost",
            description="Estimated cost of agent operations",
            unit="usd"
        )
        
        self.agent_call_counter = self.meter.create_counter(
            name="agent_calls",
            description="Number of agent function calls",
            unit="calls"
        )
    
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
        """Log agent activity with custom dimensions."""
        
        attributes = {
            "agent": agent_name,
            "function": function_name,
            "success": success
        }
        
        if error:
            attributes["error"] = error
        
        # Record metrics
        if tokens_used > 0:
            self.token_counter.add(tokens_used, attributes)
            
            # Estimate cost (rough approximation)
            cost = tokens_used * 0.00001  # $0.01 per 1K tokens
            self.cost_counter.add(cost, attributes)
        
        self.agent_call_counter.add(1, attributes)
        
        # Log event
        if success:
            self.logger.info(
                f"Agent activity: {agent_name}.{function_name}",
                extra={"custom_dimensions": attributes}
            )
        else:
            self.logger.error(
                f"Agent error: {agent_name}.{function_name} - {error}",
                extra={"custom_dimensions": attributes}
            )
    
    def log_experiment_event(
        self,
        experiment_name: str,
        variant: str,
        event_type: str,
        user_id: str = None
    ):
        """Log experiment events for analysis."""
        
        attributes = {
            "experiment": experiment_name,
            "variant": variant,
            "event_type": event_type
        }
        
        if user_id:
            attributes["user_id"] = user_id
        
        self.logger.info(
            f"Experiment event: {event_type}",
            extra={"custom_dimensions": attributes}
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
