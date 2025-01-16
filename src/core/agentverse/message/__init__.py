"""
AgentVerse Message Module

This module provides message types and utilities for agent communication.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field, model_validator

class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class MessageStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"

class Message(BaseModel):
    """Message model"""
    
    content: str = Field(description="Message content")
    type: MessageType = Field(description="Message type")
    role: MessageRole = Field(description="Message role")
    id: str = Field(default_factory=lambda: f"msg_{datetime.now().timestamp()}")
    timestamp: datetime = Field(default_factory=datetime.now)
    sender_id: Optional[str] = Field(default=None, description="Sender ID")
    receiver_id: Optional[str] = Field(default=None, description="Receiver ID")
    parent_id: Optional[str] = Field(default=None, description="Parent message ID")
    status: MessageStatus = Field(default=MessageStatus.PENDING)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    @classmethod
    def user(cls, content: str, **kwargs) -> "Message":
        """Create a user message"""
        return cls(
            content=content,
            type=MessageType.USER,
            role=MessageRole.USER,
            **kwargs
        )

    @classmethod
    def assistant(cls, content: str, **kwargs) -> "Message":
        """Create an assistant message"""
        return cls(
            content=content,
            type=MessageType.ASSISTANT,
            role=MessageRole.ASSISTANT,
            **kwargs
        )

    @classmethod
    def system(cls, content: str, **kwargs) -> "Message":
        """Create a system message"""
        return cls(
            content=content,
            type=MessageType.SYSTEM,
            role=MessageRole.SYSTEM,
            **kwargs
        )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "content": "Hello world",
                "type": "user",
                "role": "user",
                "sender_id": "user_123",
                "receiver_id": "assistant_1"
            }]
        }
    }

__all__ = [
    "Message",
    "MessageType",
    "MessageRole",
    "MessageStatus"
] 