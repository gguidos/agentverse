"""Task Factory Module"""

from typing import Dict, Any, Optional, List
from pydantic import Field

from src.core.agentverse.factories.base import BaseFactory, FactoryConfig
from src.core.agentverse.entities.task import Task, TaskConfig

class TaskFactoryConfig(FactoryConfig):
    """Task factory configuration"""
    priority: str = "medium"
    requirements: List[str] = Field(default_factory=list)
    deadline: Optional[str] = None

class TaskFactory(BaseFactory[Task]):
    """Factory for creating tasks"""
    
    @classmethod
    async def create(
        cls,
        config: TaskFactoryConfig,
        **kwargs
    ) -> Task:
        """Create a task instance"""
        if not await cls.validate_config(config):
            raise ValueError("Invalid task configuration")
            
        task_config = TaskConfig(
            id=kwargs.get("id"),
            type=config.type,
            name=config.name,
            priority=config.priority,
            requirements=config.requirements,
            deadline=config.deadline,
            metadata=config.metadata
        )
        
        return Task(config=task_config)
    
    @classmethod
    async def validate_config(
        cls,
        config: TaskFactoryConfig
    ) -> bool:
        """Validate task factory configuration"""
        valid_priorities = ["low", "medium", "high"]
        if config.priority not in valid_priorities:
            return False
        return True
    
    @classmethod
    def get_defaults(cls) -> Dict[str, Any]:
        """Get default task configuration"""
        return {
            "type": "default",
            "priority": "medium",
            "requirements": [],
            "deadline": None
        } 