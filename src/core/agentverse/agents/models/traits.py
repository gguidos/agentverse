from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class EvaluationStyle(Enum):
    SKEPTIC = "skeptic"        # Questions everything, high bar for acceptance
    OPTIMISTIC = "optimistic"  # Focuses on positives, sees potential
    REALISTIC = "realistic"    # Balanced view, evidence-based
    CRITICAL = "critical"      # Focuses on finding flaws
    NEUTRAL = "neutral"        # Purely objective, no bias
    CONSTRUCTIVE = "constructive"  # Focuses on improvement opportunities

class EvaluatorTraits(BaseModel):
    """Configuration for evaluator personality traits"""
    style: EvaluationStyle = EvaluationStyle.NEUTRAL
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Threshold for accepting statements as true"
    )
    bias_factors: Dict[str, float] = Field(
        default_factory=dict,
        description="Specific biases and their strengths (0.0 to 1.0)"
    )
    focus_areas: List[str] = Field(
        default_factory=list,
        description="Areas to pay special attention to"
    )

    class Config:
        use_enum_values = True 