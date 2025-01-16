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
    visibility_changes: int = 0
    agent_connections: Dict[str, int] = Field(default_factory=dict)

@visibility_registry.register("simple")
class SimpleVisibility(BaseVisibility):
    """Basic visibility handler where all agents can see each other"""
    
    name: ClassVar[str] = "simple_visibility"
    description: ClassVar[str] = "Basic visibility handler with full visibility"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[SimpleVisibilityConfig] = None
    ):
        super().__init__(config=config or SimpleVisibilityConfig())
        self.simple_metrics = SimpleMetrics()
    
    async def _update_visibility(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Update agent visibility to allow full visibility
        
        Args:
            environment: Environment to update visibility for
            
        Raises:
            ActionError: If update fails
        """
        try:
            start_time = datetime.utcnow()
            
            # Get all agent names
            agent_names = {agent.name for agent in environment.agents}
            
            # Track visibility changes
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
                
                # Update connection metrics
                self.simple_metrics.agent_connections[agent.name] = len(visible)
            
            # Track changes if configured
            if self.config.track_changes:
                self._track_visibility_changes(old_visibility)
            
            # Validate broadcasts if configured
            if self.config.validate_broadcasts:
                await self._validate_broadcasts(environment)
            
            # Update duration metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(duration)
            
        except Exception as e:
            logger.error(f"Simple visibility update failed: {str(e)}")
            raise ActionError(
                message=str(e),
                action=self.name,
                details={
                    "agents": len(environment.agents),
                    "self_visible": self.config.allow_self_visibility
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
            if new_visible != old_visible:
                self.simple_metrics.visibility_changes += 1
    
    async def _validate_broadcasts(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Validate broadcast messages
        
        Args:
            environment: Environment to validate
            
        Raises:
            ActionError: If validation fails
        """
        if not self.config.broadcast_enabled:
            return
            
        for message in environment.state.message_history:
            if not message.receiver:
                continue
                
            # Check if broadcast
            is_broadcast = "all" in message.receiver
            if is_broadcast:
                self.simple_metrics.broadcasts += 1
                
                # Validate broadcast permissions
                if not self.config.broadcast_enabled:
                    raise ActionError(
                        message="Broadcasting is disabled",
                        action=self.name,
                        details={
                            "sender": message.sender,
                            "receiver": message.receiver
                        }
                    )
            else:
                self.simple_metrics.direct_messages += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics including simple metrics
        
        Returns:
            Combined metrics
        """
        metrics = super().get_metrics()
        simple_metrics = self.simple_metrics.model_dump()
        
        # Add message distribution
        total_messages = (
            self.simple_metrics.broadcasts +
            self.simple_metrics.direct_messages
        )
        if total_messages > 0:
            simple_metrics["broadcast_ratio"] = (
                self.simple_metrics.broadcasts / total_messages
            )
        
        # Add average connections
        if self.simple_metrics.agent_connections:
            simple_metrics["avg_connections"] = (
                sum(self.simple_metrics.agent_connections.values()) /
                len(self.simple_metrics.agent_connections)
            )
        
        metrics.update(simple_metrics)
        return metrics
    
    def reset(self) -> None:
        """Reset visibility state"""
        super().reset()
        self.simple_metrics = SimpleMetrics()
        logger.info(f"Reset {self.name} visibility handler") 