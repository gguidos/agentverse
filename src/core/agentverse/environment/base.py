"""Base environment interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseEnvironment(ABC):
    """Base class for all environments"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize environment"""
        self.name = name
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