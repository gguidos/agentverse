"""Base Agent Module"""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from src.core.agentverse.llm import BaseLLM
    from src.core.agentverse.message import Message

class BaseAgent(ABC):
    """Base agent class"""
    
    def __init__(
        self,
        name: str,
        llm: Optional['BaseLLM'] = None,
        **kwargs
    ):
        self.name = name
        self.llm = llm
        self.message_history: List['Message'] = []
    
    @abstractmethod
    async def process_message(self, message: 'Message') -> 'Message':
        """Process incoming message"""
        raise NotImplementedError 