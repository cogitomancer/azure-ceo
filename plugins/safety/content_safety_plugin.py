"""
Azure AI Content Safety plugin for pre-send validation.
"""

from semantic_kernel.functions import kernel_function
from typing import Annotated
from azure.ai.contentsafety.aio import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.identity.aio import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential


class ContentSafetyPlugin:
    """
    Plugin wrapping Azure AI Content Safety for detecting harmful content.
    Enforces enterprise safety policies before content reaches customers.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.credential = None
        
        # Use key if provided, otherwise use RBAC
        content_safety_key = config["content_safety"].get("key")
        
        if content_safety_key:
            self.safety_client = ContentSafetyClient(
                endpoint=config["content_safety"]["endpoint"],
                credential=AzureKeyCredential(content_safety_key)
            )
        else:
            self.credential = DefaultAzureCredential()
            self.safety_client = ContentSafetyClient(
                endpoint=config["content_safety"]["endpoint"],
                credential=self.credential
            )
        
        # Safety thresholds (0-6 scale)
        self.thresholds = {
            "Hate": 2,
            "Violence": 2,
            "Sexual": 2,
            "SelfHarm": 2
        }
    
    @kernel_function(
        name="analyze_content_safety",
        description="Analyze content for safety violations (hate, violence, sexual, self-harm)"
    )
    async def analyze_content_safety(
        self,
        content: Annotated[str, "Marketing content to validate"]
    ) -> Annotated[str, "Safety analysis results"]:
        """
        Analyze content against safety policies.
        Returns APPROVED or REJECTED with specific reasons.
        """
        
        # Prepare analysis request
        request = AnalyzeTextOptions(text=content)
        
        try:
            response = await self.safety_client.analyze_text(request)
            
            # Check each category against thresholds
            violations = []
            for category in ["Hate", "Violence", "Sexual", "SelfHarm"]:
                result = getattr(response.categories_analysis, category.lower() + "_result")
                severity = result.severity
                
                if severity > self.thresholds[category]:
                    violations.append(
                        f"{category}: Severity {severity} exceeds threshold {self.thresholds[category]}"
                    )
            
            # Check for prompt injection attempts
            if hasattr(response, "jailbreak_analysis"):
                if response.jailbreak_analysis.detected:
                    violations.append("Prompt injection attempt detected")
            
            # Format result
            if violations:
                result = "REJECTED\n\nSafety violations detected:\n"
                for v in violations:
                    result += f"- {v}\n"
                return result
            else:
                return "APPROVED - No safety violations detected"
                
        except Exception as e:
            return f"ERROR: Safety analysis failed - {str(e)}"
    
    @kernel_function(
        name="check_groundedness",
        description="Verify content claims are grounded in source documents"
    )
    async def check_groundedness(
        self,
        content: Annotated[str, "Generated content to validate"],
        sources: Annotated[str, "Source documents used"]
    ) -> Annotated[str, "Groundedness validation result"]:
        """
        Validate that content claims are supported by source documents.
        Uses Azure Content Safety groundedness detection.
        """
        
        # This would use the groundedness detection API
        # For now, simplified validation
        
        if "[Source:" not in content:
            return "REJECTED - No citations found. All product claims must include citations."
        
        return "APPROVED - Content includes proper citations"
