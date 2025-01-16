"""Environment Factory Module"""

from typing import Dict, Any, Optional
from pydantic import Field

from src.core.agentverse.factories.base import BaseFactory, FactoryConfig
from src.core.agentverse.environment.base import BaseEnvironment, EnvironmentConfig

class EnvironmentFactoryConfig(FactoryConfig):
    """Environment factory configuration"""
    max_agents: int = 10
    memory_size: int = 1000
    visibility: str = "group"
    logging: bool = True

class EnvironmentFactory(BaseFactory[BaseEnvironment]):
    """Factory for creating environments"""
    
    @classmethod
    async def create(
        cls,
        config: EnvironmentFactoryConfig,
        **kwargs
    ) -> BaseEnvironment:
        """Create an environment instance"""
        if not await cls.validate_config(config):
            raise ValueError("Invalid environment configuration")
            
        env_config = EnvironmentConfig(
            id=kwargs.get("id"),
            type=config.type,
            name=config.name,
            max_agents=config.max_agents,
            memory_size=config.memory_size,
            visibility=config.visibility,
            logging=config.logging,
            metadata=config.metadata
        )
        
        return BaseEnvironment(config=env_config)
    
    @classmethod
    async def validate_config(
        cls,
        config: EnvironmentFactoryConfig
    ) -> bool:
        """Validate environment factory configuration"""
        if config.max_agents < 1:
            return False
        if config.memory_size < 0:
            return False
        return True
    
    @classmethod
    def get_defaults(cls) -> Dict[str, Any]:
        """Get default environment configuration"""
        return {
            "type": "default",
            "max_agents": 10,
            "memory_size": 1000,
            "visibility": "group",
            "logging": True
        } 