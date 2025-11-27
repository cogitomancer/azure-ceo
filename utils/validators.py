"""
Input validation utilities.
"""

import re
from typing import List, Optional, Tuple


class Validators:
    """Input validation helpers with enterprise-safe hardening."""

    # ---------------------------------------------------------
    # EMAIL
    # ---------------------------------------------------------
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        # Stricter RFC-like regex (still lightweight)
        pattern = (
            r"^(?=.{3,254}$)"                         # total length
            r"[a-zA-Z0-9._%+-]+@"                    # local part
            r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"         # domain
        )
        return re.match(pattern, email) is not None

    # ---------------------------------------------------------
    # CAMPAIGN NAME
    # ---------------------------------------------------------
    @staticmethod
    def validate_campaign_name(name: str) -> Tuple[bool, Optional[str]]:
        """Validate campaign name used in UI + workflow configs."""
        
        if not name:
            return False, "Campaign name cannot be empty."

        if len(name) < 3:
            return False, "Campaign name must be at least 3 characters."

        if len(name) > 100:
            return False, "Campaign name must be less than 100 characters."

        # Allow basic punctuation but prevent control chars / weird Unicode attacks
        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", name):
            return (
                False,
                "Campaign name may only contain letters, numbers, spaces, hyphens, and underscores."
            )

        return True, None

    # ---------------------------------------------------------
    # ALLOCATION
    # ---------------------------------------------------------
    @staticmethod
    def validate_traffic_allocation(allocation: List[int]) -> Tuple[bool, Optional[str]]:
        """Validate traffic allocation percentages."""
        
        if not allocation:
            return False, "Traffic allocation cannot be empty."

        if sum(allocation) != 100:
            return (
                False,
                f"Traffic allocation must sum to 100% (currently {sum(allocation)}%)."
            )

        if any(a < 0 or a > 100 for a in allocation):
            return False, "Each allocation must be between 0 and 100."

        return True, None

    # ---------------------------------------------------------
    # SANITIZATION
    # ---------------------------------------------------------
    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """
        Sanitize user input to prevent injection, XSS, and prompt-injection attempts.
        This is intentionally lightweight and does not break normal text input.
        """
        if not text:
            return ""

        # Remove SQL/'dangerous' characters
        text = re.sub(r"[;\"'\\]", "", text)

        # Remove <script> tags (even obfuscated forms)
        text = re.sub(
            r"<\s*script[^>]*>.*?<\s*/\s*script\s*>",
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL
        )

        # Remove prompt-injection style patterns
        text = re.sub(
            r"(?i)(ignore\s+previous\s+instructions|"
            r"override\s+rules|"
            r"disregard\s+constraints|"
            r"system:\s*)",
            "",
            text,
        )

        # Remove invisible Unicode control characters
        text = re.sub(r"[\u202E\u202A\u202B\u202C\u202D]", "", text)

        return text.strip()
