"""Base LLM interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseLLM(ABC):
    """Base class for LLM implementations"""
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """Initialize LLM with config"""
        pass
        
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response for prompt"""
        pass
        
    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> str:
        """Stream response for prompt"""
        pass 