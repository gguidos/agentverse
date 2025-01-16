"""Resource Entity Module"""

from typing import Dict, Any, List, Optional
from pydantic import Field

from src.core.agentverse.environment.entities.base import (
    BaseEntity,
    EntityConfig,
    EntityState
)

class ResourceState(EntityState):
    """Resource state model"""
    usage: float = 0.0
    available: bool = True
    access_count: int = 0

class ResourceConfig(EntityConfig):
    """Resource configuration"""
    capacity: float = 100.0
    access_policy: Dict[str, List[str]] = Field(default_factory=dict)

class Resource(BaseEntity):
    """Resource entity implementation"""
    
    def __init__(self, config: ResourceConfig):
        super().__init__(config)
        self.state = ResourceState()
    
    async def update(self, updates: Dict[str, Any]) -> None:
        """Update resource state"""
        await super().update(updates)
        
        if "usage" in updates:
            self.state.usage = updates["usage"]
        if "available" in updates:
            self.state.available = updates["available"]
        if "access_count" in updates:
            self.state.access_count = updates["access_count"]
    
    async def validate(self) -> bool:
        """Validate resource state"""
        if self.state.usage > self.config.capacity:
            return False
        return True 