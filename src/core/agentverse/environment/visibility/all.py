"""All Visibility Module"""

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

class AllVisibilityConfig(VisibilityConfig):
    """Configuration for all visibility"""
    allow_self_visibility: bool = False
    enforce_reciprocal: bool = True
    track_connections: bool = True
    validate_connections: bool = True
    
    model_config = ConfigDict(
        extra="allow"
    )

class AllMetrics(VisibilityMetrics):
    """Additional metrics for all visibility"""
    total_connections: int = 0
    reciprocal_connections: int = 0
    connection_changes: int = 0
    agent_visibility: Dict[str, Dict[str, int]] = Field(default_factory=dict)

@visibility
class AllVisibility(BaseVisibility):
    """All visibility implementation"""
    
    name = "all_visibility"
    description = "Provides visibility to all components"
    version = "1.0.0"
    
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
                
            # Allow all visibility
            result = True
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.update(allowed=result, duration=duration)
            
            return result
            
        except Exception as e:
            logger.error(f"Visibility check failed: {str(e)}")
            return False 