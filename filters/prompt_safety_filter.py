"""
Pre-LLM prompt validation filter - first line of defense.
"""

from semantic_kernel.filters import FilterTypes, FunctionInvocationContext
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.identity import DefaultAzureCredential
import logging
import re


class PromptSafetyFilter:
    """
    Filter that validates prompts before they reach the LLM.
    Blocks jailbreak attempts, unsafe content, and PII leakage.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.credential = DefaultAzureCredential()
        
        # Initialize Content Safety client
        self.safety_client = ContentSafetyClient(
            endpoint=config["content_safety"]["endpoint"],
            credential=self.credential
        )
    
    async def on_prompt_rendering(self, context: FunctionInvocationContext):
        """
        Called before prompt is sent to LLM.
        Validates safety and blocks if violations detected.
        """
        
        # Get rendered prompt
        prompt_text = context.function.prompt_template_config.template
        
        self.logger.info(f"Validating prompt for function: {context.function.name}")
        
        # 1. Check for prompt injection attempts
        if self._detect_prompt_injection(prompt_text):
            self.logger.warning("Prompt injection detected - blocking request")
            raise SecurityException("Prompt injection attempt detected and blocked")
        
        # 2. Validate content safety
        safety_result = await self._analyze_safety(prompt_text)
        if not safety_result["is_safe"]:
            self.logger.warning(f"Unsafe prompt detected: {safety_result['violations']}")
            raise SecurityException(
                f"Prompt safety violation: {', '.join(safety_result['violations'])}"
            )
        
        # 3. Check for excessive PII
        pii_detected = self._detect_pii(prompt_text)
        if pii_detected:
            self.logger.warning(f"PII detected in prompt: {pii_detected}")
            # Don't block, but log for audit
            context.metadata["pii_detected"] = pii_detected
        
        self.logger.info("Prompt validation passed")
    
    def _detect_prompt_injection(self, text: str) -> bool:
        """
        Detect common jailbreak and prompt injection patterns.
        """
        
        # Patterns indicating potential injection
        injection_patterns = [
            r"ignore (previous|above|all) instructions?",
            r"disregard (previous|above|all) (instructions?|rules?)",
            r"you are now",
            r"new (instructions?|rules?|system prompt)",
            r"</system>",  # Attempting to close system tags
            r"<\|im_start\|>",  # ChatML injection
        ]
        
        text_lower = text.lower()
        for pattern in injection_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    async def _analyze_safety(self, text: str) -> dict:
        """
        Use Azure Content Safety to analyze prompt.
        """
        
        try:
            request = AnalyzeTextOptions(text=text)
            response = await self.safety_client.analyze_text(request)
            
            violations = []
            thresholds = {"Hate": 2, "Violence": 2, "Sexual": 2, "SelfHarm": 2}
            
            for category, threshold in thresholds.items():
                result = getattr(response.categories_analysis, category.lower() + "_result")
                if result.severity > threshold:
                    violations.append(f"{category} (severity: {result.severity})")
            
            return {
                "is_safe": len(violations) == 0,
                "violations": violations
            }
        
        except Exception as e:
            self.logger.error(f"Safety analysis failed: {e}")
            # Fail secure - if safety check fails, block the request
            return {
                "is_safe": False,
                "violations": ["Safety analysis error"]
            }
    
    def _detect_pii(self, text: str) -> list:
        """
        Detect common PII patterns (email, phone, SSN).
        """
        
        pii_found = []
        
        # Email pattern
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            pii_found.append("email")
        
        # Phone number patterns
        if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text):
            pii_found.append("phone")
        
        # SSN pattern
        if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
            pii_found.append("ssn")
        
        # Credit card pattern
        if re.search(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', text):
            pii_found.append("credit_card")
        
        return pii_found


class SecurityException(Exception):
    """Custom exception for security violations."""
    pass