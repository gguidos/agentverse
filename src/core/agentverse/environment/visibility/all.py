from typing import Dict, Set, Any, Optional, ClassVar
from pydantic import Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.environment.visibility.base import (
    BaseVisibility,
    VisibilityConfig,
    VisibilityMetrics
)
from src.core.agentverse.environment.registry import visibility_registry
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.exceptions import ActionError

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

@visibility_registry.register("all")
class AllVisibility(BaseVisibility):
    """Visibility handler where all agents can see each other"""
    
    name: ClassVar[str] = "all_visibility"
    description: ClassVar[str] = "Full visibility handler for all agents"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[AllVisibilityConfig] = None
    ):
        super().__init__(config=config or AllVisibilityConfig())
        self.all_metrics = AllMetrics()
    
    async def _update_visibility(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Make all agents visible to each other
        
        Args:
            environment: Environment to update visibility for
            
        Raises:
            ActionError: If update fails
        """
        try:
            start_time = datetime.utcnow()
            
            # Get all agent names
            agent_names = {agent.name for agent in environment.agents}
            
            # Track old visibility for change detection
            old_visibility = (
                self.state.visibility_map.copy()
                if self.config.track_changes
                else {}
            )
            
            # Update visibility for each agent
            for agent in environment.agents:
                # Set visibility (optionally including self)
                visible = (
                    agent_names if self.config.allow_self_visibility
                    else agent_names - {agent.name}
                )
                
                # Update visibility map
                self.state.visibility_map[agent.name] = visible
                
                # Update agent's receiver set if supported
                if hasattr(agent, 'set_receiver'):
                    await agent.set_receiver(visible)
            
            # Validate connections if configured
            if self.config.validate_connections:
                self._validate_connections()
            
            # Track changes if configured
            if self.config.track_changes:
                self._track_visibility_changes(old_visibility)
            
            # Update metrics
            self._update_connection_metrics()
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(duration)
            
        except Exception as e:
            logger.error(f"All visibility update failed: {str(e)}")
            raise ActionError(
                message=str(e),
                action=self.name,
                details={
                    "agents": len(environment.agents),
                    "self_visible": self.config.allow_self_visibility
                }
            )
    
    def _validate_connections(self) -> None:
        """Validate visibility connections
        
        Raises:
            ActionError: If validation fails
        """
        # Check all agents have visibility entries
        agent_names = set(self.state.visibility_map.keys())
        for agent in agent_names:
            visible = self.state.visibility_map.get(agent, set())
            
            # Check visibility set exists
            if not visible:
                raise ActionError(
                    message=f"Missing visibility for agent {agent}",
                    action=self.name,
                    details={"agent": agent}
                )
            
            # Check reciprocal visibility if configured
            if self.config.enforce_reciprocal:
                for target in visible:
                    target_visible = self.state.visibility_map.get(target, set())
                    if agent not in target_visible:
                        raise ActionError(
                            message=f"Non-reciprocal visibility between {agent} and {target}",
                            action=self.name,
                            details={
                                "agent": agent,
                                "target": target
                            }
                        )
    
    def _track_visibility_changes(
        self,
        old_visibility: Dict[str, Set[str]]
    ) -> None:
        """Track visibility changes
        
        Args:
            old_visibility: Previous visibility state
        """
        for agent, new_visible in self.state.visibility_map.items():
            old_visible = old_visibility.get(agent, set())
            
            # Track changes
            if new_visible != old_visible:
                self.all_metrics.connection_changes += 1
                
                # Update agent visibility stats
                stats = self.all_metrics.agent_visibility.setdefault(
                    agent,
                    {"added": 0, "removed": 0}
                )
                stats["added"] += len(new_visible - old_visible)
                stats["removed"] += len(old_visible - new_visible)
    
    def _update_connection_metrics(self) -> None:
        """Update connection metrics"""
        total = 0
        reciprocal = 0
        
        for agent, visible in self.state.visibility_map.items():
            total += len(visible)
            
            if self.config.enforce_reciprocal:
                for target in visible:
                    target_visible = self.state.visibility_map.get(target, set())
                    if agent in target_visible:
                        reciprocal += 1
        
        self.all_metrics.total_connections = total
        self.all_metrics.reciprocal_connections = reciprocal // 2  # Count each pair once
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics including all visibility metrics
        
        Returns:
            Combined metrics
        """
        metrics = super().get_metrics()
        all_metrics = self.all_metrics.model_dump()
        
        # Add connection ratio
        if self.all_metrics.total_connections > 0:
            all_metrics["reciprocal_ratio"] = (
                self.all_metrics.reciprocal_connections /
                (self.all_metrics.total_connections / 2)  # Divide by 2 for pairs
            )
        
        metrics.update(all_metrics)
        return metrics
    
    def reset(self) -> None:
        """Reset visibility state"""
        super().reset()
        self.all_metrics = AllMetrics()
        logger.info(f"Reset {self.name} visibility handler") 