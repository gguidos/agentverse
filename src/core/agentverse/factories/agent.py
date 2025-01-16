"""Agent Factory Module"""

from typing import Dict, Any, Optional
from pydantic import Field

from src.core.agentverse.factories.base import BaseFactory, FactoryConfig
from src.core.agentverse.entities.agent import Agent, AgentConfig

class AgentFactoryConfig(FactoryConfig):
    """Agent factory configuration"""
    capabilities: Optional[list] = Field(default_factory=list)
    max_tasks: int = 5
    memory_limit: float = 100.0

class AgentFactory(BaseFactory[Agent]):
    """Factory for creating agents"""
    
    @classmethod
    async def create(
        cls,
        config: AgentFactoryConfig,
        **kwargs
    ) -> Agent:
        """Create an agent instance
        
        Args:
            config: Agent factory configuration
            **kwargs: Additional creation options
            
        Returns:
            Created agent instance
        """
        # Validate config
        if not await cls.validate_config(config):
            raise ValueError("Invalid agent configuration")
            
        # Create agent config
        agent_config = AgentConfig(
            id=kwargs.get("id"),
            type=config.type,
            name=config.name,
            capabilities=config.capabilities,
            max_tasks=config.max_tasks,
            memory_limit=config.memory_limit,
            metadata=config.metadata
        )
        
        # Create agent
        return Agent(config=agent_config)
    
    @classmethod
    async def validate_config(
        cls,
        config: AgentFactoryConfig
    ) -> bool:
        """Validate agent factory configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        if config.max_tasks < 1:
            return False
        if config.memory_limit <= 0:
            return False
        return True
    
    @classmethod
    def get_defaults(cls) -> Dict[str, Any]:
        """Get default agent configuration
        
        Returns:
            Default configuration values
        """
        return {
            "type": "default",
            "capabilities": [],
            "max_tasks": 5,
            "memory_limit": 100.0
        } 