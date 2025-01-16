from typing import Dict, Any, Optional, List
from pydantic import Field
from datetime import datetime

from src.core.agentverse.message.base import (
    BaseMessage,
    MessageMetadata,
    ChatMessage as BaseChatMessage
)

class ChatRole:
    """Chat roles"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"

class ChatMetadata(MessageMetadata):
    """Chat message metadata"""
    conversation_id: Optional[str] = None
    thread_id: Optional[str] = None
    parent_id: Optional[str] = None
    sequence: Optional[int] = None

class ChatMessage(BaseChatMessage):
    """Enhanced chat message"""
    metadata: ChatMetadata = Field(default_factory=ChatMetadata)
    
    @classmethod
    def system(cls, content: str, **kwargs) -> "ChatMessage":
        """Create system message"""
        return cls(
            role=ChatRole.SYSTEM,
            content=content,
            **kwargs
        )
    
    @classmethod
    def user(cls, content: str, **kwargs) -> "ChatMessage":
        """Create user message"""
        return cls(
            role=ChatRole.USER,
            content=content,
            **kwargs
        )
    
    @classmethod
    def assistant(cls, content: str, **kwargs) -> "ChatMessage":
        """Create assistant message"""
        return cls(
            role=ChatRole.ASSISTANT,
            content=content,
            **kwargs
        )
    
    @classmethod
    def function(
        cls,
        name: str,
        content: str,
        **kwargs
    ) -> "ChatMessage":
        """Create function message"""
        return cls(
            role=ChatRole.FUNCTION,
            name=name,
            content=content,
            **kwargs
        ) 