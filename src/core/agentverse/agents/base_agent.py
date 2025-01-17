"""Base Agent Module"""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from src.core.agentverse.interfaces import BaseAgent
from src.core.agentverse.message import Message

if TYPE_CHECKING:
    from src.core.agentverse.llm import BaseLLM

class BaseAgent(BaseAgent):
    """Base agent class"""
    
    def __init__(
        self,
        name: str,
        llm: Optional['BaseLLM'] = None,
        llm_service: Optional['BaseLLM'] = None,  # For backward compatibility
        **kwargs
    ):
        self.name = name
        self.llm = llm or llm_service
        self.message_history: List[Message] = []
    
    async def process_message(self, message: Message) -> Message:
        """Process incoming message"""
        raise NotImplementedError 