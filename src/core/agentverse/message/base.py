"""
Base message types for agent communication
"""

from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class MessageType(str, Enum):
    """Message type enumeration"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    ERROR = "error"
    EVENT = "event"

class MessageRole(str, Enum):
    """Message role enumeration"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"

class MessageStatus(str, Enum):
    """Message status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Message(BaseModel):
    """Base message class for agent communication"""
    
    # Required fields
    content: str
    type: MessageType
    role: MessageRole
    
    # Optional fields
    id: Optional[str] = Field(default_factory=lambda: f"msg_{datetime.utcnow().timestamp()}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender_id: Optional[str] = None
    receiver_id: Optional[str] = None
    parent_id: Optional[str] = None
    status: MessageStatus = MessageStatus.PENDING
    
    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        """Pydantic config"""
        use_enum_values = True
        arbitrary_types_allowed = True
    
    @classmethod
    def system(cls, content: str, **kwargs) -> "Message":
        """Create system message"""
        return cls(
            content=content,
            type=MessageType.SYSTEM,
            role=MessageRole.SYSTEM,
            **kwargs
        )
    
    @classmethod
    def user(cls, content: str, **kwargs) -> "Message":
        """Create user message"""
        return cls(
            content=content,
            type=MessageType.USER,
            role=MessageRole.USER,
            **kwargs
        )
    
    @classmethod
    def assistant(cls, content: str, **kwargs) -> "Message":
        """Create assistant message"""
        return cls(
            content=content,
            type=MessageType.ASSISTANT,
            role=MessageRole.ASSISTANT,
            **kwargs
        )
    
    @classmethod
    def function(cls, content: str, **kwargs) -> "Message":
        """Create function message"""
        return cls(
            content=content,
            type=MessageType.FUNCTION,
            role=MessageRole.FUNCTION,
            **kwargs
        )
    
    @classmethod
    def error(cls, content: str, **kwargs) -> "Message":
        """Create error message"""
        return cls(
            content=content,
            type=MessageType.ERROR,
            role=MessageRole.SYSTEM,
            status=MessageStatus.FAILED,
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "content": self.content,
            "type": self.type,
            "role": self.role,
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "parent_id": self.parent_id,
            "status": self.status,
            "metadata": self.metadata,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary"""
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

__all__ = [
    "Message",
    "MessageType",
    "MessageRole",
    "MessageStatus"
] 