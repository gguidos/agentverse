"""Task Entity Module"""

from typing import Dict, Any, List, Optional
from pydantic import Field

from src.core.agentverse.entities.base import (
    BaseEntity,
    EntityConfig,
    EntityState
)

class TaskState(EntityState):
    """Task state model"""
    status: str = "pending"
    progress: float = 0.0
    assigned_to: Optional[str] = None

class TaskConfig(EntityConfig):
    """Task configuration"""
    priority: str = "medium"
    requirements: List[str] = Field(default_factory=list)
    deadline: Optional[str] = None

class Task(BaseEntity):
    """Task entity implementation"""
    
    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.state = TaskState()
    
    async def update(self, updates: Dict[str, Any]) -> None:
        """Update task state"""
        await super().update(updates)
        
        if "status" in updates:
            self.state.status = updates["status"]
        if "progress" in updates:
            self.state.progress = updates["progress"]
        if "assigned_to" in updates:
            self.state.assigned_to = updates["assigned_to"]
    
    async def validate(self) -> bool:
        """Validate task state"""
        if self.state.progress > 100.0:
            return False
        return True 