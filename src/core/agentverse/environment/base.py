"""Base environment interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class EnvironmentConfig(BaseModel):
    """Environment configuration"""
    id: Optional[str] = None
    type: str
    name: Optional[str] = None
    max_agents: int = 10
    memory_size: int = 1000
    visibility: str = "group"
    logging: bool = True
    metadata: Dict[str, Any] = {}

class BaseEnvironment(ABC):
    """Base class for all environments"""
    
    def __init__(self, config: EnvironmentConfig):
        """Initialize environment"""
        self.config = config
        
    @abstractmethod
    async def step(self) -> Any:
        """Execute one environment step"""
        pass
        
    @abstractmethod
    async def reset(self) -> None:
        """Reset environment state"""
        pass
        
    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Get environment metrics"""
        pass 