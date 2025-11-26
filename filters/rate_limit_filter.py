"""
Rate limiting and cost control filter.
"""

from semantic_kernel.filters import FilterTypes, FunctionInvocationContext
import time
from collections import defaultdict
import logging


class RateLimitFilter:
    """
    Filter that enforces rate limits and cost controls.
    Prevents runaway costs and abuse.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Token tracking per agent
        self.agent_token_usage = defaultdict(int)
        self.agent_call_counts = defaultdict(int)
        self.reset_interval = 3600  # Reset counters every hour
        self.last_reset = time.time()
        
        # Limits from config
        self.max_tokens_per_agent = config.get("rate_limits", {}).get("max_tokens_per_hour", 100000)
        self.max_calls_per_agent = config.get("rate_limits", {}).get("max_calls_per_hour", 1000)
    
    async def on_function_invocation(self, context: FunctionInvocationContext):
        """
        Track and enforce rate limits before and during function execution.
        Also tracks token usage if available in metadata.
        """
        
        # Reset counters if interval passed
        if time.time() - self.last_reset > self.reset_interval:
            self._reset_counters()
        
        agent_name = context.metadata.get("agent_name", "Unknown")
        
        # Increment call count
        self.agent_call_counts[agent_name] += 1
        
        # Check call limit
        if self.agent_call_counts[agent_name] > self.max_calls_per_agent:
            self.logger.warning(
                f"Rate limit exceeded: {agent_name} has made "
                f"{self.agent_call_counts[agent_name]} calls this hour"
            )
            raise RateLimitException(
                f"Rate limit exceeded for agent '{agent_name}'. "
                f"Maximum {self.max_calls_per_agent} calls per hour."
            )
        
        # Track token usage if available in metadata
        tokens_used = context.metadata.get("tokens_used", 0)
        if tokens_used > 0:
            self.agent_token_usage[agent_name] += tokens_used
            
            # Check token limit (warning only, don't block)
            if self.agent_token_usage[agent_name] > self.max_tokens_per_agent:
                self.logger.warning(
                    f"Token limit exceeded: {agent_name} has used "
                    f"{self.agent_token_usage[agent_name]} tokens this hour"
                )
        
        # Log usage for monitoring
        self.logger.info(
            f"Rate limit tracking: {agent_name} - "
            f"Calls: {self.agent_call_counts[agent_name]}/{self.max_calls_per_agent}, "
            f"Tokens: {self.agent_token_usage[agent_name]}/{self.max_tokens_per_agent}"
        )
    
    async def on_function_invocation_complete(self, context: FunctionInvocationContext):
        """
        Track token usage after function completion.
        """
        
        agent_name = context.metadata.get("agent_name", "Unknown")
        
        # Extract token usage from result metadata
        tokens_used = context.metadata.get("tokens_used", 0)
        self.agent_token_usage[agent_name] += tokens_used
        
        # Check token limit
        if self.agent_token_usage[agent_name] > self.max_tokens_per_agent:
            self.logger.warning(
                f"Token limit exceeded: {agent_name} has used "
                f"{self.agent_token_usage[agent_name]} tokens this hour"
            )
            # Don't block completed call, but log for alerting
    
    def _reset_counters(self):
        """Reset usage counters."""
        self.logger.info("Resetting rate limit counters")
        self.agent_token_usage.clear()
        self.agent_call_counts.clear()
        self.last_reset = time.time()


class RateLimitException(Exception):
    """Custom exception for rate limit violations."""
    pass
