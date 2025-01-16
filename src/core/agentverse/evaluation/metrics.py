from typing import Dict, Any, List, Optional, ClassVar
from pydantic import BaseModel, Field
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TextQualityMetrics(BaseModel):
    """Metrics for evaluating text quality"""
    
    # Core quality metrics
    coherence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Measure of text flow and logical connection"
    )
    relevance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Relevance to the given context or query"
    )
    accuracy: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Factual accuracy of the content"
    )
    completeness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Completeness of the response"
    )
    
    # Additional quality aspects
    clarity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Clarity and understandability"
    )
    conciseness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Efficiency of expression"
    )
    consistency: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Internal consistency of information"
    )
    creativity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Level of creative and original thinking"
    )
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_id: Optional[str] = None
    
    # Configurable weights for scoring
    METRIC_WEIGHTS: ClassVar[Dict[str, float]] = {
        'coherence': 0.2,
        'relevance': 0.2,
        'accuracy': 0.2,
        'completeness': 0.2,
        'clarity': 0.05,
        'conciseness': 0.05,
        'consistency': 0.05,
        'creativity': 0.05
    }
    
    @property
    def core_metrics_score(self) -> float:
        """Calculate score based on core metrics only"""
        core_metrics = ['coherence', 'relevance', 'accuracy', 'completeness']
        weights = {k: v for k, v in self.METRIC_WEIGHTS.items() if k in core_metrics}
        
        # Normalize weights
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}
        
        return sum(
            getattr(self, metric) * weight 
            for metric, weight in weights.items()
        )
    
    @property
    def overall_score(self) -> float:
        """Calculate overall quality score including all metrics"""
        return sum(
            getattr(self, metric) * weight 
            for metric, weight in self.METRIC_WEIGHTS.items()
        )
    
    def get_scores_by_category(self) -> Dict[str, Dict[str, float]]:
        """Get scores organized by category"""
        return {
            "core_metrics": {
                "coherence": self.coherence,
                "relevance": self.relevance,
                "accuracy": self.accuracy,
                "completeness": self.completeness,
                "score": self.core_metrics_score
            },
            "additional_metrics": {
                "clarity": self.clarity,
                "conciseness": self.conciseness,
                "consistency": self.consistency,
                "creativity": self.creativity
            },
            "overall": {
                "score": self.overall_score
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary with scores and metadata"""
        return {
            **self.get_scores_by_category(),
            "metadata": {
                "timestamp": self.timestamp.isoformat(),
                "context_id": self.context_id
            }
        }
    
    @classmethod
    def from_scores(cls, scores: Dict[str, float], context_id: Optional[str] = None) -> 'TextQualityMetrics':
        """Create metrics instance from score dictionary"""
        return cls(
            coherence=scores.get('coherence', 0.0),
            relevance=scores.get('relevance', 0.0),
            accuracy=scores.get('accuracy', 0.0),
            completeness=scores.get('completeness', 0.0),
            clarity=scores.get('clarity', 0.0),
            conciseness=scores.get('conciseness', 0.0),
            consistency=scores.get('consistency', 0.0),
            creativity=scores.get('creativity', 0.0),
            context_id=context_id
        )
    
    def update(self, new_scores: Dict[str, float]) -> None:
        """Update metrics with new scores"""
        for metric, score in new_scores.items():
            if hasattr(self, metric) and isinstance(score, (int, float)):
                if 0.0 <= score <= 1.0:
                    setattr(self, metric, score)
                else:
                    logger.warning(f"Invalid score value for {metric}: {score}")
    
    def get_improvement_suggestions(self) -> List[str]:
        """Generate improvement suggestions based on metrics"""
        suggestions = []
        threshold = 0.7  # Threshold for suggesting improvements
        
        if self.coherence < threshold:
            suggestions.append("Improve logical flow and connections between ideas")
        if self.relevance < threshold:
            suggestions.append("Enhance relevance to the given context/query")
        if self.accuracy < threshold:
            suggestions.append("Verify and improve factual accuracy")
        if self.completeness < threshold:
            suggestions.append("Provide more comprehensive coverage")
        if self.clarity < threshold:
            suggestions.append("Improve clarity and understandability")
        if self.conciseness < threshold:
            suggestions.append("Make expression more concise")
        if self.consistency < threshold:
            suggestions.append("Ensure better internal consistency")
        
        return suggestions
    
    def get_strengths(self) -> List[str]:
        """Identify strong points based on metrics"""
        strengths = []
        threshold = 0.8  # Threshold for identifying strengths
        
        metric_descriptions = {
            'coherence': 'Strong logical flow',
            'relevance': 'Highly relevant content',
            'accuracy': 'Excellent factual accuracy',
            'completeness': 'Comprehensive coverage',
            'clarity': 'Very clear and understandable',
            'conciseness': 'Efficiently expressed',
            'consistency': 'Highly consistent',
            'creativity': 'Creative and original'
        }
        
        for metric, description in metric_descriptions.items():
            if getattr(self, metric) >= threshold:
                strengths.append(description)
        
        return strengths 