from typing import Dict, Any, Optional, List
from pydantic import Field
from enum import Enum

from src.core.agentverse.message.base import (
    BaseMessage,
    MessageMetadata,
    CommandMessage as BaseCommandMessage
)

class CommandType(str, Enum):
    """Command types"""
    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    RESET = "reset"
    UPDATE = "update"
    QUERY = "query"
    ACTION = "action"

class CommandMetadata(MessageMetadata):
    """Command message metadata"""
    requires_response: bool = False
    timeout: Optional[int] = None
    retries: int = 0
    max_retries: int = 3

class CommandMessage(BaseCommandMessage):
    """Enhanced command message"""
    metadata: CommandMetadata = Field(default_factory=CommandMetadata)
    
    @classmethod
    def create(
        cls,
        action: str,
        parameters: Dict[str, Any] = None,
        **kwargs
    ) -> "CommandMessage":
        """Create command message"""
        return cls(
            action=action,
            parameters=parameters or {},
            **kwargs
        )
    
    @property
    def requires_response(self) -> bool:
        """Check if command requires response"""
        return self.metadata.requires_response 