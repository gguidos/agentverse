"""Group Visibility Module"""

from typing import Dict, Set, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
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

class GroupConfig(BaseModel):
    """Configuration for a group"""
    name: str
    members: Set[str] = Field(default_factory=set)
    visible_to: Set[str] = Field(default_factory=set)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GroupVisibilityConfig(VisibilityConfig):
    """Configuration for group visibility"""
    allow_cross_group: bool = False
    track_group_changes: bool = True
    validate_groups: bool = True
    
    model_config = ConfigDict(
        extra="allow"
    )

class GroupMetrics(VisibilityMetrics):
    """Additional metrics for group visibility"""
    total_groups: int = 0
    group_changes: int = 0
    cross_group_visibility: int = 0
    group_memberships: Dict[str, Set[str]] = Field(default_factory=dict)

@visibility
class GroupVisibility(BaseVisibility):
    """Group-based visibility implementation"""
    
    name = "group_visibility"
    description = "Provides group-based visibility control"
    version = "1.0.0"
    
    def __init__(self, config: Optional[GroupVisibilityConfig] = None):
        super().__init__(config or GroupVisibilityConfig())
        self.groups: Dict[str, GroupConfig] = {}
        self.metrics = GroupMetrics()
    
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
                
            # Check group memberships
            source_groups = {
                group_name
                for group_name, group in self.groups.items()
                if source in group.members
            }
            
            target_groups = {
                group_name
                for group_name, group in self.groups.items()
                if target in group.members
            }
            
            # Check visibility rules
            result = False
            
            # Same group visibility
            if source_groups & target_groups:
                result = True
                
            # Cross-group visibility if enabled
            elif self.config.allow_cross_group:
                for source_group in source_groups:
                    group = self.groups[source_group]
                    if target_groups & group.visible_to:
                        result = True
                        self.metrics.cross_group_visibility += 1
                        break
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.update(allowed=result, duration=duration)
            
            return result
            
        except Exception as e:
            logger.error(f"Group visibility check failed: {str(e)}")
            return False 