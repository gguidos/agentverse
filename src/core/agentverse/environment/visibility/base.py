"""Base Visibility Module"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from src.core.agentverse.environment.visibility.audit import VisibilityAudit

logger = logging.getLogger(__name__)

class VisibilityMetrics(BaseModel):
    """Visibility metrics tracking"""
    
    # Access tracking
    total_checks: int = 0
    allowed_checks: int = 0
    denied_checks: int = 0
    
    # Performance tracking
    check_durations: List[float] = Field(default_factory=list)
    last_check: Optional[datetime] = None
    
    # Rule tracking
    rule_evaluations: int = 0
    rule_matches: int = 0
    
    # Custom metrics
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def update(self, allowed: bool, duration: float) -> None:
        """Update metrics with check result"""
        self.total_checks += 1
        if allowed:
            self.allowed_checks += 1
        else:
            self.denied_checks += 1
        
        self.check_durations.append(duration)
        self.last_check = datetime.utcnow()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get computed statistics"""
        return {
            "total_checks": self.total_checks,
            "allowed_ratio": self.allowed_checks / max(1, self.total_checks),
            "avg_duration": sum(self.check_durations) / max(1, len(self.check_durations)),
            "rule_match_ratio": self.rule_matches / max(1, self.rule_evaluations)
        }

class VisibilityConfig(BaseModel):
    """Visibility configuration"""
    enable_audit: bool = True
    audit_logger: str = "visibility.audit"
    default_allow: bool = False

class BaseVisibility(ABC):
    """Base class for visibility control"""
    
    def __init__(self, config: Optional[VisibilityConfig] = None):
        self.config = config or VisibilityConfig()
        self.audit = VisibilityAudit(self.config.audit_logger) if self.config.enable_audit else None
        self.metrics = VisibilityMetrics()
    
    @abstractmethod
    async def check_visibility(
        self,
        source: str,
        target: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check visibility between source and target"""
        pass
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get visibility metrics"""
        return self.metrics.get_stats()
    
    async def _log_rule_evaluation(
        self,
        rule_id: str,
        inputs: Dict[str, Any],
        result: bool,
        **kwargs
    ) -> None:
        """Log rule evaluation"""
        if self.audit:
            self.audit.log_rule_evaluation(
                rule_id=rule_id,
                inputs=inputs,
                result=result,
                **kwargs
            )

__all__ = [
    "VisibilityMetrics",
    "VisibilityConfig",
    "BaseVisibility"
] 