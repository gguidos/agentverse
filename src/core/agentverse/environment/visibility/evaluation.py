"""Evaluation Visibility Module"""

from typing import Dict, Set, Any, Optional
from pydantic import Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.environment.visibility.base import (
    BaseVisibility,
    VisibilityConfig,
    VisibilityMetrics
)
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.exceptions import ActionError
from src.core.agentverse.environment.decorators import visibility

logger = logging.getLogger(__name__)

class EvaluationVisibilityConfig(VisibilityConfig):
    """Configuration for evaluation visibility"""
    blind_final_rounds: bool = True
    final_round_count: Optional[int] = None
    track_phase_changes: bool = True
    allow_self_visibility: bool = True
    
    model_config = ConfigDict(
        extra="allow"
    )

class EvaluationMetrics(VisibilityMetrics):
    """Additional metrics for evaluation visibility"""
    blind_rounds: int = 0
    full_rounds: int = 0
    phase_changes: int = 0
    phase_durations: Dict[str, float] = Field(default_factory=dict)

@visibility
class EvaluationVisibility(BaseVisibility):
    """Evaluation-specific visibility implementation"""
    
    name = "evaluation_visibility"
    description = "Provides visibility control for evaluation phases"
    version = "1.0.0"
    
    def __init__(self, config: Optional[EvaluationVisibilityConfig] = None):
        super().__init__(config or EvaluationVisibilityConfig())
        self.metrics = EvaluationMetrics()
        self.current_phase = "full"
        self.phase_start = None
    
    async def check_visibility(
        self,
        source: str,
        target: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check visibility between source and target"""
        try:
            start_time = datetime.utcnow()
            
            # Basic validation
            if not source or not target:
                return False
                
            # Check self visibility
            if source == target:
                return self.config.allow_self_visibility
                
            # Check current phase
            result = self.current_phase == "full"
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.update(allowed=result, duration=duration)
            
            # Track phase-specific metrics
            if result:
                self.metrics.full_rounds += 1
            else:
                self.metrics.blind_rounds += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Evaluation visibility check failed: {str(e)}")
            return False
    
    def switch_phase(self, phase: str) -> None:
        """Switch visibility phase"""
        if phase not in ["full", "blind"]:
            raise ValueError(f"Invalid phase: {phase}")
            
        if phase != self.current_phase:
            self.metrics.phase_changes += 1
            
            # Track phase duration
            if self.phase_start:
                duration = (datetime.utcnow() - self.phase_start).total_seconds()
                self.metrics.phase_durations[self.current_phase] = duration
            
            self.current_phase = phase
            self.phase_start = datetime.utcnow() 