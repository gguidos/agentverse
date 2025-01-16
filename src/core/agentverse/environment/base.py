"""
Base environment interface
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.core.agentverse.message import Message
from src.core.agentverse.exceptions import EnvironmentError

class EnvironmentConfig(BaseModel):
    """Environment configuration"""
    name: str
    description: Optional[str] = None
    max_steps: int = 100
    max_agents: int = 10
    track_metrics: bool = True
    save_history: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseEnvironment(ABC):
    """Abstract base class for environments"""
    
    def __init__(self, config: Optional[EnvironmentConfig] = None):
        self.config = config or EnvironmentConfig(name="default")
        self.steps = 0
        self.history: List[Message] = []
        self.metrics: Dict[str, Any] = {}
    
    @abstractmethod
    async def step(self, message: Message) -> Message:
        """Execute one environment step
        
        Args:
            message: Input message
            
        Returns:
            Response message
            
        Raises:
            EnvironmentError: If step execution fails
        """
        pass
    
    @abstractmethod
    async def reset(self) -> None:
        """Reset environment state
        
        Raises:
            EnvironmentError: If reset fails
        """
        pass
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get environment metrics
        
        Returns:
            Dictionary of metrics
        """
        return {
            "steps": self.steps,
            "history_length": len(self.history),
            **self.metrics
        }
    
    async def validate_message(self, message: Message) -> bool:
        """Validate message for environment
        
        Args:
            message: Message to validate
            
        Returns:
            Whether message is valid
        """
        return bool(message.content and message.type) 