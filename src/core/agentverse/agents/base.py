"""Base agent interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, config: Dict[str, Any], llm: 'BaseLLM'):
        """Initialize agent with config and LLM"""
        super().__init__()  # Initialize ABC
        self.config = config
        self.llm = llm
        self.name = config.get("name", "agent")
    
    @abstractmethod
    async def process_message(self, message: str) -> str:
        """Process incoming message and return response"""
        pass 