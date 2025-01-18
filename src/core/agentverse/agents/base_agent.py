"""Base Agent Module"""

from typing import Optional, List, TYPE_CHECKING, Any, Dict
from datetime import datetime
from abc import ABC, abstractmethod

# Import BaseMemory directly since we need it for type annotation
from src.core.agentverse.memory.base import BaseMemory

if TYPE_CHECKING:
    from src.core.agentverse.llm import BaseLLM
    from src.core.agentverse.message import Message

class BaseAgent(ABC):
    """Base agent class"""
    
    def __init__(
        self,
        name: str,
        llm: Any,
        memory: Optional[BaseMemory] = None,
        parser: Any = None,
        prompt_template: str = "You are an AI assistant.",
        tools: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ):
        self.name = name
        self.llm = llm
        self.memory = memory
        self.parser = parser
        self.prompt_template = prompt_template
        self.tools = tools or {}
        self.metadata = metadata or {}
        self.message_history: List['Message'] = []
    
    @abstractmethod
    async def process_message(self, message: str) -> str:
        """Process incoming message"""
        raise NotImplementedError 