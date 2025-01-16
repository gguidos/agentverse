"""
AgentVerse core implementation
"""

import logging
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

from src.core.agentverse.agents import BaseAgent
from src.core.agentverse.environment import BaseEnvironment
from src.core.agentverse.message import Message
from src.core.agentverse.message_bus import BaseMessageBus, InMemoryMessageBus
from src.core.agentverse.resources import ResourceManager
from src.core.agentverse.recovery import RetryHandler
from src.core.agentverse.exceptions import AgentVerseError

logger = logging.getLogger(__name__)

class AgentVerseConfig(BaseModel):
    """Configuration for AgentVerse"""
    max_agents: int = Field(default=10, description="Maximum number of agents")
    max_messages: int = Field(default=1000, description="Maximum number of messages")
    enable_retry: bool = Field(default=True, description="Enable retry mechanism")
    enable_resources: bool = Field(default=True, description="Enable resource management")
    environment_config: Optional[Dict[str, Any]] = Field(default=None, description="Environment configuration")
    message_bus_config: Optional[Dict[str, Any]] = Field(default=None, description="Message bus configuration")

class AgentVerse:
    """Core AgentVerse implementation"""
    
    def __init__(
        self,
        agents: List[BaseAgent],
        config: Optional[AgentVerseConfig] = None,
        environment: Optional[BaseEnvironment] = None,
        message_bus: Optional[BaseMessageBus] = None,
        resource_manager: Optional[ResourceManager] = None,
        retry_handler: Optional[RetryHandler] = None,
        **kwargs
    ):
        """Initialize AgentVerse
        
        Args:
            agents: List of agents
            config: Optional configuration
            environment: Optional environment
            message_bus: Optional message bus
            resource_manager: Optional resource manager
            retry_handler: Optional retry handler
            **kwargs: Additional arguments
        """
        self.config = config or AgentVerseConfig()
        
        if len(agents) > self.config.max_agents:
            raise AgentVerseError(
                message="Too many agents",
                details={"max": self.config.max_agents, "actual": len(agents)}
            )
            
        self.agents = agents
        self.environment = environment
        self.message_bus = message_bus or InMemoryMessageBus()
        self.resource_manager = resource_manager or ResourceManager()
        self.retry_handler = retry_handler or RetryHandler()
        
        # Initialize components
        self._initialize()
    
    def _initialize(self):
        """Initialize components"""
        # Register agents with message bus
        for agent in self.agents:
            self.message_bus.subscribe("global", agent.name)
    
    async def process_message(self, message: Message) -> Message:
        """Process message through system
        
        Args:
            message: Input message
            
        Returns:
            Response message
            
        Raises:
            AgentVerseError: If processing fails
        """
        try:
            # Check resources if enabled
            if self.config.enable_resources:
                await self.resource_manager.check_resources()
            
            # Process through environment if available
            if self.environment:
                message = await self.environment.step(message)
            
            # Publish to message bus
            await self.message_bus.publish("global", message)
            
            # Get target agent
            agent = self._get_agent(message.receiver_id)
            
            # Process with retry if enabled
            if self.config.enable_retry:
                @self.retry_handler.handle
                async def process():
                    return await agent.process_message(message)
                return await process()
            else:
                return await agent.process_message(message)
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            raise AgentVerseError(
                message="Failed to process message",
                details={"error": str(e)}
            )
    
    def _get_agent(self, agent_id: str) -> BaseAgent:
        """Get agent by ID
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent instance
            
        Raises:
            AgentVerseError: If agent not found
        """
        for agent in self.agents:
            if agent.name == agent_id:
                return agent
        raise AgentVerseError(f"Agent not found: {agent_id}")

__all__ = [
    "AgentVerse",
    "AgentVerseConfig"
] 