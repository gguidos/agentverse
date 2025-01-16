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

class SelfOnlyConfig(VisibilityConfig):
    """Configuration for self-only visibility"""
    allow_system_messages: bool = True
    system_sender: str = "system"
    track_message_types: bool = True
    validate_receivers: bool = True
    
    model_config = ConfigDict(
        extra="allow"
    )

class SelfOnlyMetrics(VisibilityMetrics):
    """Additional metrics for self-only visibility"""
    self_messages: int = 0
    system_messages: int = 0
    blocked_messages: int = 0
    message_types: Dict[str, int] = Field(default_factory=dict)

@visibility_registry.register("self_only")
class SelfOnlyVisibility(BaseVisibility):
    """Visibility handler where agents can only see their own messages"""
    
    name: ClassVar[str] = "self_only_visibility"
    description: ClassVar[str] = "Visibility handler for self-only messaging"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[SelfOnlyConfig] = None
    ):
        super().__init__(config=config or SelfOnlyConfig())
        self.self_metrics = SelfOnlyMetrics()
    
    async def _update_visibility(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Set each agent to only see themselves
        
        Args:
            environment: Environment to update visibility for
            
        Raises:
            ActionError: If update fails
        """
        try:
            start_time = datetime.utcnow()
            
            for agent in environment.agents:
                # Set basic self visibility
                visible = {agent.name}
                
                # Add system visibility if configured
                if (
                    self.config.allow_system_messages and
                    self.config.system_sender
                ):
                    visible.add(self.config.system_sender)
                
                # Update visibility map
                self.state.visibility_map[agent.name] = visible
                
                # Update agent's receiver set if supported
                if hasattr(agent, 'set_receiver'):
                    await agent.set_receiver(visible)
                    
                # Update metrics
                self._update_agent_metrics(agent.name, environment)
            
            # Validate if configured
            if self.config.validate_receivers:
                self._validate_receivers(environment)
            
            # Update duration metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(duration)
            
        except Exception as e:
            logger.error(f"Failed to set self-only visibility: {str(e)}")
            raise ActionError(
                message=str(e),
                action=self.name,
                details={
                    "agents": len(environment.agents),
                    "system_enabled": self.config.allow_system_messages
                }
            )
    
    def _validate_receivers(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Validate message receivers
        
        Args:
            environment: Environment to validate
            
        Raises:
            ActionError: If validation fails
        """
        for message in environment.state.message_history:
            if not message.receiver:
                continue
                
            # Check receivers are valid
            for receiver in message.receiver:
                if receiver not in self.state.visibility_map:
                    if (
                        not self.config.allow_system_messages or
                        receiver != self.config.system_sender
                    ):
                        raise ActionError(
                            message=f"Invalid message receiver: {receiver}",
                            action=self.name,
                            details={
                                "sender": message.sender,
                                "receiver": message.receiver
                            }
                        )
    
    def _update_agent_metrics(
        self,
        agent_name: str,
        environment: BaseEnvironment
    ) -> None:
        """Update metrics for an agent
        
        Args:
            agent_name: Agent to update metrics for
            environment: Environment instance
        """
        if not self.config.track_message_types:
            return
            
        # Get agent's messages
        messages = [
            msg for msg in environment.state.message_history
            if msg.sender == agent_name
        ]
        
        # Update message type counts
        for message in messages:
            if message.sender == agent_name:
                self.self_metrics.self_messages += 1
            elif message.sender == self.config.system_sender:
                self.self_metrics.system_messages += 1
            else:
                self.self_metrics.blocked_messages += 1
            
            # Track message types
            msg_type = message.metadata.get("type", "unknown")
            self.self_metrics.message_types[msg_type] = (
                self.self_metrics.message_types.get(msg_type, 0) + 1
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics including self-only metrics
        
        Returns:
            Combined metrics
        """
        metrics = super().get_metrics()
        self_metrics = self.self_metrics.model_dump()
        
        # Add message distribution
        total_messages = (
            self.self_metrics.self_messages +
            self.self_metrics.system_messages +
            self.self_metrics.blocked_messages
        )
        if total_messages > 0:
            self_metrics["self_message_ratio"] = (
                self.self_metrics.self_messages / total_messages
            )
            self_metrics["system_message_ratio"] = (
                self.self_metrics.system_messages / total_messages
            )
            self_metrics["blocked_message_ratio"] = (
                self.self_metrics.blocked_messages / total_messages
            )
        
        metrics.update(self_metrics)
        return metrics
    
    def reset(self) -> None:
        """Reset visibility state"""
        super().reset()
        self.self_metrics = SelfOnlyMetrics()
        logger.info(f"Reset {self.name} visibility handler") 