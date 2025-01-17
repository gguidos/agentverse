"""Simple Visibility Module"""

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

class SimpleVisibilityConfig(VisibilityConfig):
    """Configuration for simple visibility"""
    allow_self_visibility: bool = False
    broadcast_enabled: bool = True
    track_broadcasts: bool = True
    validate_broadcasts: bool = True
    
    model_config = ConfigDict(
        extra="allow"
    )

class SimpleMetrics(VisibilityMetrics):
    """Additional metrics for simple visibility"""
    broadcasts: int = 0
    direct_messages: int = 0
    agent_connections: Dict[str, int] = Field(default_factory=dict)

@visibility
class SimpleVisibility(BaseVisibility):
    """Simple visibility implementation"""
    
    name = "simple_visibility"
    description = "Provides basic visibility control"
    version = "1.0.0"
    
    def __init__(self, config: Optional[SimpleVisibilityConfig] = None):
        super().__init__(config or SimpleVisibilityConfig())
        self.metrics = SimpleMetrics()
        
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
                
            # Check broadcast
            is_broadcast = context and context.get("broadcast", False)
            if is_broadcast and self.config.broadcast_enabled:
                if self.config.track_broadcasts:
                    self.metrics.broadcasts += 1
                return True
                
            # Track direct message
            self.metrics.direct_messages += 1
            
            # Track connection
            if source not in self.metrics.agent_connections:
                self.metrics.agent_connections[source] = 0
            self.metrics.agent_connections[source] += 1
            
            # Default allow
            result = True
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.update(allowed=result, duration=duration)
            
            return result
            
        except Exception as e:
            logger.error(f"Simple visibility check failed: {str(e)}")
            return False 