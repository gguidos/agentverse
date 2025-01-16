"""Resource Factory Module"""

from typing import Dict, Any, Optional, List
from pydantic import Field

from src.core.agentverse.factories.base import BaseFactory, FactoryConfig
from src.core.agentverse.entities.resource import Resource, ResourceConfig

class ResourceFactoryConfig(FactoryConfig):
    """Resource factory configuration"""
    capacity: float = 100.0
    access_policy: Dict[str, List[str]] = Field(default_factory=dict)

class ResourceFactory(BaseFactory[Resource]):
    """Factory for creating resources"""
    
    @classmethod
    async def create(
        cls,
        config: ResourceFactoryConfig,
        **kwargs
    ) -> Resource:
        """Create a resource instance"""
        if not await cls.validate_config(config):
            raise ValueError("Invalid resource configuration")
            
        resource_config = ResourceConfig(
            id=kwargs.get("id"),
            type=config.type,
            name=config.name,
            capacity=config.capacity,
            access_policy=config.access_policy,
            metadata=config.metadata
        )
        
        return Resource(config=resource_config)
    
    @classmethod
    async def validate_config(
        cls,
        config: ResourceFactoryConfig
    ) -> bool:
        """Validate resource factory configuration"""
        if config.capacity <= 0:
            return False
        return True
    
    @classmethod
    def get_defaults(cls) -> Dict[str, Any]:
        """Get default resource configuration"""
        return {
            "type": "default",
            "capacity": 100.0,
            "access_policy": {
                "read": [],
                "write": []
            }
        } 