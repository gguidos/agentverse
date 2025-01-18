from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class EvaluationStyle(Enum):
    SKEPTIC = "skeptic"
    OPTIMISTIC = "optimistic"
    REALISTIC = "realistic"
    CRITICAL = "critical"
    NEUTRAL = "neutral"
    CONSTRUCTIVE = "constructive"

class FocusArea(Enum):
    ACCURACY = "accuracy"
    LOGIC = "logic"
    EVIDENCE = "evidence"
    CONSISTENCY = "consistency"
    RELEVANCE = "relevance"
    BIAS = "bias"

class BiasType(Enum):
    CONFIRMATION = "confirmation"
    RECENCY = "recency"
    AUTHORITY = "authority"

class EvaluatorTraits(BaseModel):
    """Configuration for evaluator personality traits"""
    style: EvaluationStyle = EvaluationStyle.NEUTRAL
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Threshold for accepting statements as true"
    )
    bias_factors: Dict[BiasType, float] = Field(
        default_factory=dict,
        description="Specific biases and their strengths (0.0 to 1.0)"
    )
    focus_areas: List[FocusArea] = Field(
        default_factory=list,
        description="Areas to pay special attention to"
    )

    class Config:
        use_enum_values = True 