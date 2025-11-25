"""
PII redaction filter - masks sensitive data in prompts.
"""

from semantic_kernel.filters import FilterTypes, FunctionInvocationContext
import re
import logging


class PIIFilter:
    """
    Filter that detects and redacts PII from prompts.
    Ensures sensitive data doesn't reach LLMs or logs.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.redaction_enabled = config.get("pii_redaction", {}).get("enabled", True)
    
    async def on_prompt_rendering(self, context: FunctionInvocationContext):
        """
        Scan and redact PII before prompt reaches LLM.
        """
        
        if not self.redaction_enabled:
            return
        
        prompt_text = context.function.prompt_template_config.template
        
        # Apply redaction patterns
        redacted_text, redactions = self._redact_pii(prompt_text)
        
        if redactions:
            self.logger.warning(
                f"PII redacted from prompt: {', '.join(redactions)}",
                extra={"audit": True}
            )
            
            # Update prompt with redacted version
            context.function.prompt_template_config.template = redacted_text
            
            # Log redaction in metadata
            context.metadata["pii_redacted"] = redactions
    
    def _redact_pii(self, text: str) -> tuple[str, list]:
        """
        Apply regex patterns to redact common PII types.
        
        Returns:
            (redacted_text, list_of_redaction_types)
        """
        
        redactions = []
        redacted = text
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, redacted):
            redacted = re.sub(email_pattern, '[EMAIL_REDACTED]', redacted)
            redactions.append("email")
        
        # Phone numbers (various formats)
        phone_patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # 123-456-7890
            r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',       # (123) 456-7890
            r'\+\d{1,3}\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'  # +1 123-456-7890
        ]
        for pattern in phone_patterns:
            if re.search(pattern, redacted):
                redacted = re.sub(pattern, '[PHONE_REDACTED]', redacted)
                if "phone" not in redactions:
                    redactions.append("phone")
        
        # Social Security Numbers
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        if re.search(ssn_pattern, redacted):
            redacted = re.sub(ssn_pattern, '[SSN_REDACTED]', redacted)
            redactions.append("ssn")
        
        # Credit card numbers (basic pattern)
        cc_pattern = r'\b(?:\d{4}[- ]?){3}\d{4}\b'
        if re.search(cc_pattern, redacted):
            redacted = re.sub(cc_pattern, '[CC_REDACTED]', redacted)
            redactions.append("credit_card")
        
        # IP addresses (can be sensitive in some contexts)
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        if re.search(ip_pattern, redacted):
            redacted = re.sub(ip_pattern, '[IP_REDACTED]', redacted)
            redactions.append("ip_address")
        
        # Physical addresses (simplified - catches street addresses)
        address_pattern = r'\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b'
        if re.search(address_pattern, redacted, re.IGNORECASE):
            redacted = re.sub(address_pattern, '[ADDRESS_REDACTED]', redacted, flags=re.IGNORECASE)
            redactions.append("address")
        
        return redacted, redactions
