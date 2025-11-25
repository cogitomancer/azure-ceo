"""
Input validation utilities.
"""

import re
from typing import List, Optional


class Validators:
    """Input validation helpers."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_campaign_name(name: str) -> tuple[bool, Optional[str]]:
        """Validate campaign name."""
        if not name or len(name) < 3:
            return False, "Campaign name must be at least 3 characters"
        
        if len(name) > 100:
            return False, "Campaign name must be less than 100 characters"
        
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
            return False, "Campaign name can only contain letters, numbers, spaces, hyphens and underscores"
        
        return True, None
    
    @staticmethod
    def validate_traffic_allocation(allocation: List[int]) -> tuple[bool, Optional[str]]:
        """Validate traffic allocation percentages."""
        if not allocation:
            return False, "Traffic allocation cannot be empty"
        
        if sum(allocation) != 100:
            return False, f"Traffic allocation must sum to 100% (currently {sum(allocation)}%)"
        
        if any(a < 0 or a > 100 for a in allocation):
            return False, "Each allocation must be between 0 and 100"
        
        return True, None
    
    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        # Remove potential SQL injection patterns
        text = re.sub(r'[;\'"\\]', '', text)
        
        # Remove script tags
        text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text.strip()