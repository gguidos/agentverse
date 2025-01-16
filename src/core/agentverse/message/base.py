from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid

class MessageMetadata(BaseModel):
    """Message metadata"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    target: Optional[str] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    priority: int = 0
    ttl: Optional[int] = None
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class BaseMessage(BaseModel):
    """Base message class"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    content: Dict[str, Any] = Field(default_factory=dict)
    metadata: MessageMetadata = Field(default_factory=MessageMetadata)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class ChatMessage(BaseMessage):
    """Chat message type"""
    type: str = "chat"
    role: str
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None

class CommandMessage(BaseMessage):
    """Command message type"""
    type: str = "command"
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
class EventMessage(BaseMessage):
    """Event message type"""
    type: str = "event"
    event_type: str
    data: Dict[str, Any] = Field(default_factory=dict)

class StateMessage(BaseMessage):
    """State message type"""
    type: str = "state"
    state_type: str
    state: Dict[str, Any] = Field(default_factory=dict)

class ErrorMessage(BaseMessage):
    """Error message type"""
    type: str = "error"
    error_type: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

# Message type registry
MESSAGE_TYPES = {
    "chat": ChatMessage,
    "command": CommandMessage,
    "event": EventMessage,
    "state": StateMessage,
    "error": ErrorMessage
}

def create_message(
    type: str,
    **kwargs
) -> BaseMessage:
    """Create message of specified type
    
    Args:
        type: Message type
        **kwargs: Message fields
        
    Returns:
        Message instance
        
    Raises:
        ValueError: If type is invalid
    """
    if type not in MESSAGE_TYPES:
        raise ValueError(f"Invalid message type: {type}")
        
    message_class = MESSAGE_TYPES[type]
    return message_class(**kwargs) 