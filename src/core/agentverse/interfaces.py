"""Core interfaces"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime

class BaseAgent(ABC):
    """Base agent interface"""
    
    @abstractmethod
    async def process_message(self, message: Any) -> Any:
        """Process incoming message"""
        pass

class BaseEnvironment(ABC):
    """Base environment interface"""
    
    @abstractmethod
    async def step(self, **kwargs) -> Any:
        """Execute environment step"""
        pass
    
    @abstractmethod
    async def reset(self) -> None:
        """Reset environment state"""
        pass

class EnvironmentStepResult(BaseModel):
    """Result from environment step"""
    output: str = Field(description="Step output")
    logs: List[str] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)
    done: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

__all__ = [
    "BaseAgent",
    "BaseEnvironment",
    "EnvironmentStepResult"
] 