"""Self Visibility Module"""

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

@visibility
class SelfVisibility(BaseVisibility):
    """Self-only visibility implementation"""
    
    name = "self_visibility"
    description = "Provides self-only visibility control"
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
                
            # Only allow self visibility
            result = source == target
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.update(allowed=result, duration=duration)
            
            return result
            
        except Exception as e:
            logger.error(f"Self visibility check failed: {str(e)}")
            return False 