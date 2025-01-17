"""
Base interfaces and abstract classes
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from src.core.agentverse.message import Message
from src.core.agentverse.exceptions import AgentError

class AgentConfig(BaseModel):
    """Base agent configuration"""
    
    name: str = Field(description="Agent name")
    description: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None
    memory_config: Optional[Dict[str, Any]] = None

class BaseAgent(ABC):
    """Abstract base class for agents"""
    
    def __init__(
        self,
        name: str,
        llm: Optional['BaseLLM'] = None,  # Use string to avoid circular import
        config: Optional[AgentConfig] = None,
        **kwargs
    ):
        self.name = name
        self.llm = llm
        self.config = config or AgentConfig(name=name)
        self.metadata = kwargs
        
    @abstractmethod
    async def process_message(self, message: Message) -> Message:
        """Process incoming message"""
        pass
    
    def reset(self) -> None:
        """Reset agent state"""
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"

__all__ = [
    "BaseAgent",
    "AgentConfig"
] 