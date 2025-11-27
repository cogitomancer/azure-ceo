from enum import Enum

class CreativeMode(str, Enum):
    PRECISION = "precision"
    BRAND_VOICE = "brand_voice"
    ADAPTIVE_CREATIVE = "adaptive_creative"
    HIGH_VARIANCE = "high_variance"
    DIVERGENT_IDEATION = "divergent_ideation"
