"""Agent Entity Module"""

from typing import Dict, Any, List, Optional
from pydantic import Field, BaseModel

from src.core.agentverse.entities.base import (
    BaseEntity,
    EntityConfig,
    EntityState
)

class AgentState(EntityState):
    """Agent state model"""
    status: str = "idle"
    memory_usage: float = 0.0
    task_count: int = 0
    capabilities: List[str] = Field(default_factory=list)

class AgentConfig(BaseModel):
    """Agent configuration"""
    id: str
    type: str
    name: str
    capabilities: List[str] = []
    max_tasks: int = 5
    memory_limit: float = 100.0
    metadata: Dict[str, Any] = {}
    llm: Any = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with fallback"""
        return getattr(self, key, default)

class Agent(BaseEntity):
    """Agent entity implementation"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.state = AgentState(capabilities=config.capabilities)
    
    async def update(self, updates: Dict[str, Any]) -> None:
        """Update agent state"""
        await super().update(updates)
        
        if "status" in updates:
            self.state.status = updates["status"]
        if "memory_usage" in updates:
            self.state.memory_usage = updates["memory_usage"]
        if "task_count" in updates:
            self.state.task_count = updates["task_count"]
    
    async def validate(self) -> bool:
        """Validate agent state"""
        if self.state.task_count > self.config.max_tasks:
            return False
        if self.state.memory_usage > self.config.memory_limit:
            return False
        return True 