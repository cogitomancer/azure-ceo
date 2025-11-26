"""
Function invocation filter - controls which agents can call which tools.
"""

from semantic_kernel.filters import FilterTypes, FunctionInvocationContext
import logging


class FunctionAuthorizationFilter:
    """
    Filter that enforces authorization rules for function calls.
    Prevents agents from executing unauthorized actions.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Define authorization matrix: agent -> allowed functions
        self.authorization_matrix = {
            "StrategyLead": ["*"],  # Manager can call any function
            "DataSegmenter": [
                "query_customer_segments",
                "get_segment_details",
                "execute_sql"
            ],
            "ContentCreator": [
                "retrieve_product_info",
                "extract_citations"
            ],
            "ComplianceOfficer": [
                "analyze_content_safety",
                "validate_brand_compliance",
                "check_groundedness"
            ],
            "ExperimentRunner": [
                "create_feature_flag",
                "update_traffic_allocation",
                "calculate_significance",
                "get_experiment_metrics"
            ]
        }
        
        # High-risk functions requiring additional validation
        self.high_risk_functions = [
            "activate_segment",
            "create_feature_flag",
            "update_traffic_allocation"
        ]
    
    async def on_function_invocation(self, context: FunctionInvocationContext):
        """
        Called before function execution.
        Validates agent authorization and applies risk controls.
        """
        
        agent_name = context.metadata.get("agent_name", "Unknown")
        function_name = context.function.name
        
        self.logger.info(
            f"Authorization check: {agent_name} -> {function_name}"
        )
        
        # 1. Check if agent is authorized for this function
        if not self._is_authorized(agent_name, function_name):
            self.logger.warning(
                f"Authorization denied: {agent_name} attempted to call {function_name}"
            )
            raise AuthorizationException(
                f"Agent '{agent_name}' is not authorized to call '{function_name}'"
            )
        
        # 2. Apply high-risk function controls
        if function_name in self.high_risk_functions:
            self._validate_high_risk_call(context)
        
        self.logger.info(f"Authorization granted for {function_name}")
    
    def _is_authorized(self, agent_name: str, function_name: str) -> bool:
        """Check if agent is authorized to call function."""
        
        allowed_functions = self.authorization_matrix.get(agent_name, [])
        
        # Wildcard permission
        if "*" in allowed_functions:
            return True
        
        # Explicit permission
        return function_name in allowed_functions
    
    def _validate_high_risk_call(self, context: FunctionInvocationContext):
        """
        Additional validation for high-risk functions.
        Example: Limit audience size for experiments.
        """
        
        function_name = context.function.name
        
        if function_name == "create_feature_flag":
            # Ensure initial exposure is limited
            args = context.arguments
            traffic_allocation = args.get("traffic_allocation", "")
            
            # Parse allocations
            try:
                allocations = [int(x) for x in traffic_allocation.split(",")]
                total_exposure = sum(allocations)
                
                # Policy: No more than 10% initial exposure without approval
                if total_exposure > 10:
                    raise AuthorizationException(
                        f"High-risk policy violation: Initial experiment exposure "
                        f"({total_exposure}%) exceeds 10% limit. Requires human approval."
                    )
            except Exception as e:
                self.logger.warning(f"Failed to validate traffic allocation: {e}")
        
        elif function_name == "activate_segment":
            # Log all segment activations for audit
            segment_id = context.arguments.get("segment_id")
            destination = context.arguments.get("destination")
            
            self.logger.info(
                f"HIGH-RISK ACTION: Activating segment {segment_id} to {destination}",
                extra={"audit": True}
            )


class AuthorizationException(Exception):
    """Custom exception for authorization failures."""
    pass